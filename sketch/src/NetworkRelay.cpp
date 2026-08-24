#include "NetworkRelay.h"

#include <Arduino.h>
#include <stdio.h>
#include <Ethernet.h>
#include <SPI.h>

#include "Config.h"
#include "DiagLog.h"
#include "SpiRemap.h"

namespace net {
namespace {

EthernetServer* g_server = nullptr;
EthernetClient g_clients[config::kMaxRelaySockets];

// How long the Bridge thread waits for the W5500 before giving up.
//
// It waits with a deadline rather than forever on purpose: a blocked
// Bridge thread is the failure being fixed here, so a write that fails
// honestly and lets the Linux side retry beats one that hangs the RPC
// thread and takes servo_read down with it. The loop thread holds the
// chip only for one bulk read per slot, so this is generous.
constexpr int32_t kChipLockTimeoutMs = 50;

}  // namespace

NetworkRelay::NetworkRelay(uint8_t cs_pin, uint16_t api_port,
                           uint16_t chunk_bytes)
    : cs_pin_(cs_pin), api_port_(api_port), chunk_bytes_(chunk_bytes) {
  k_mutex_init(&chip_lock_);
}

bool NetworkRelay::LockChip(k_timeout_t timeout) {
  return k_mutex_lock(&chip_lock_, timeout) == 0;
}

void NetworkRelay::UnlockChip() {
  k_mutex_unlock(&chip_lock_);
}

bool NetworkRelay::Begin(const uint8_t mac[6], const uint8_t ip[4],
                         const uint8_t gateway[4], const uint8_t subnet[4]) {
  SPI.begin();
  board::SpiRemap::ApplyJspiMapping();

  Ethernet.init(cs_pin_);
  // The Ethernet library re-initialises the SPI pins, so the remap has to be
  // applied a second time or the shield goes back to being invisible.
  board::SpiRemap::ApplyJspiMapping();

  const IPAddress address(ip[0], ip[1], ip[2], ip[3]);
  const IPAddress gate(gateway[0], gateway[1], gateway[2], gateway[3]);
  const IPAddress mask(subnet[0], subnet[1], subnet[2], subnet[3]);
  Ethernet.begin(const_cast<uint8_t*>(mac), address, gate, gate, mask);
  delay(600);

  if (Ethernet.hardwareStatus() == EthernetNoHardware) {
    ready_ = false;
    diag::DiagLog::Push(diag::log_level::kError,
                        "Ethernet shield not detected",
                        "mcu.relay.not_ready");
    return false;
  }

  static EthernetServer server(api_port_);
  g_server = &server;
  g_server->begin();
  ready_ = true;
  diag::DiagLog::Push(diag::log_level::kInfo, "Ethernet relay ready",
                      "mcu.relay.ready", static_cast<int32_t>(api_port_));
  return true;
}

void NetworkRelay::SetSinks(OpenSink on_open, ByteSink on_bytes,
                            CloseSink on_close) {
  on_open_ = on_open;
  on_bytes_ = on_bytes;
  on_close_ = on_close;
}

bool NetworkRelay::WriteToClient(uint8_t slot, const uint8_t* data,
                                 uint16_t length) {
  if (slot >= config::kMaxRelaySockets) return false;
  // Runs on the Bridge thread (net_tx is registered with provide_safe,
  // which means "called from the Bridge thread while loop() may be inside
  // the relay" - it does NOT make anything safe on its own).
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) {
    ++write_lock_timeouts_;
    // arg2 carries the running total, same as the rejected-connection event
    // below - lets soak_report.py cross-check log-line counts against the
    // on-device counter and notice if DiagLog ever dropped one.
    diag::DiagLog::Push(diag::log_level::kWarn, "W5500 write-lock timeout",
                        "mcu.relay.write_lock_timeout",
                        static_cast<int32_t>(slot),
                        static_cast<int32_t>(write_lock_timeouts_));
    return false;
  }
  EthernetClient& client = g_clients[slot];
  bool written = false;
  if (client && client.connected()) {
    written = client.write(data, length) == length;
  }
  UnlockChip();
  return written;
}

void NetworkRelay::CloseClient(uint8_t slot) {
  if (slot >= config::kMaxRelaySockets) return;
  // Also the Bridge thread, via net_shutdown.
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;
  if (g_clients[slot]) g_clients[slot].stop();
  UnlockChip();
}

void NetworkRelay::Poll() {
  if (!ready_ || g_server == nullptr) return;

  // 1) Detect disconnects on the EDGE, FIRST. Reporting "closed" every pass for a
  //    slot that is merely idle would flood the Linux side with net_close.
  //    This MUST run before accepting: otherwise a slot whose client has
  //    just dropped can be handed to a new connection in the same pass while
  //    net_close for the old one has not been sent, and the Linux side then
  //    feeds the new connection's bytes into the old socket.
  //
  //    The chip work happens under the lock; the sinks are called after it
  //    is released, because a sink notifies Linux over the Bridge and the
  //    Bridge thread may be waiting for this lock inside net_tx.
  bool dropped[config::kMaxRelaySockets] = {false};
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;   // retry next tick
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    const bool up = g_clients[slot].connected();
    if (was_up_[slot] && !up) {
      g_clients[slot].stop();
      dropped[slot] = true;
    }
    was_up_[slot] = up;
  }
  UnlockChip();
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    if (dropped[slot] && (on_close_ != nullptr)) on_close_(slot);
  }
  // 2) Adopt new connections.
  //
  // accept() hands over a connection EXACTLY ONCE and transfers ownership.
  // available() must NOT be used here: it returns whichever client currently
  // has unread data, and returns the SAME client again on every call, so an
  // accept loop built on it adopts one connection into several slots and
  // then forwards fragments of a single byte stream under different slot
  // numbers - which corrupts every request that follows.
  int opened = -1;
  char opened_ip[16] = {0};
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;   // retry next tick
  EthernetClient fresh = g_server->accept();
  if (fresh) {
    int slot = -1;
    for (uint8_t index = 0; index < config::kMaxRelaySockets; ++index) {
      if (!g_clients[index].connected()) {
        slot = index;
        break;
      }
    }
    if (slot < 0) {
      fresh.stop();                       // full: refuse politely
      ++rejected_total_;
      diag::DiagLog::Push(diag::log_level::kWarn,
                          "Relay connection rejected: no slot",
                          "mcu.relay.rejected",
                          static_cast<int32_t>(rejected_total_));
    } else {
      g_clients[slot] = fresh;
      ++connections_total_;
      opened = slot;
      const IPAddress remote = fresh.remoteIP();
      snprintf(opened_ip, sizeof(opened_ip), "%d.%d.%d.%d", remote[0],
               remote[1], remote[2], remote[3]);
    }
  }
  UnlockChip();
  if ((opened >= 0) && (on_open_ != nullptr)) {
    on_open_(static_cast<uint8_t>(opened), opened_ip);
  }

  // 3) Pump shield -> Linux. One bulk read per slot per pass; never a byte
  //    at a time, and never blocking.
  //
  //    One slot at a time: take the chip, pull one chunk, release, then
  //    hand it to Linux. Holding the chip across on_bytes_ would block the
  //    Bridge thread inside net_tx for the whole round trip.
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    uint8_t buffer[config::kRelayChunkBytes];
    int read = 0;
    if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;  // retry next tick
    EthernetClient& client = g_clients[slot];
    if (client.connected() && client.available()) {
      read = client.read(buffer, sizeof(buffer));
    }
    UnlockChip();
    if ((read > 0) && (on_bytes_ != nullptr)) {
      on_bytes_(slot, buffer, static_cast<uint16_t>(read));
    }
  }

}

}  // namespace net
