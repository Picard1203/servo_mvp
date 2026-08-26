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
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) {
    ++write_lock_timeouts_;
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
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;
  if (g_clients[slot]) g_clients[slot].stop();
  UnlockChip();
}

void NetworkRelay::Poll() {
  if (!ready_ || g_server == nullptr) return;

  // Edge disconnect detection per RELAY_NOTES.md rule 2.
  bool dropped[config::kMaxRelaySockets] = {false};
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;
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

  // Adopt connections with accept() per RELAY_NOTES.md rule 1.
  int opened = -1;
  char opened_ip[16] = {0};
  if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;
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
      fresh.stop();
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

  // Bulk read per slot per pass per RELAY_NOTES.md rule 4; lock released before sink per rule 7.
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    uint8_t buffer[config::kRelayChunkBytes];
    int read = 0;
    if (!LockChip(K_MSEC(kChipLockTimeoutMs))) return;
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

}

}  // namespace net
