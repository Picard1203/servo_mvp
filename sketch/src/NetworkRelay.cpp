#include "NetworkRelay.h"

#include <Arduino.h>
#include <stdio.h>
#include <Ethernet.h>
#include <SPI.h>

#include "Config.h"
#include "SpiRemap.h"

namespace net {
namespace {

EthernetServer* g_server = nullptr;
EthernetClient g_clients[config::kMaxRelaySockets];

}  // namespace

NetworkRelay::NetworkRelay(uint8_t cs_pin, uint16_t api_port,
                           uint16_t chunk_bytes)
    : cs_pin_(cs_pin), api_port_(api_port), chunk_bytes_(chunk_bytes) {}

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
    return false;
  }

  static EthernetServer server(api_port_);
  g_server = &server;
  g_server->begin();
  ready_ = true;
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
  EthernetClient& client = g_clients[slot];
  if (!client || !client.connected()) return false;
  return client.write(data, length) == length;
}

void NetworkRelay::CloseClient(uint8_t slot) {
  if (slot >= config::kMaxRelaySockets) return;
  if (g_clients[slot]) g_clients[slot].stop();
}

void NetworkRelay::Poll() {
  if (!ready_ || g_server == nullptr) return;

  // 1) Detect disconnects on the EDGE, FIRST. Reporting "closed" every pass for a
  //    slot that is merely idle would flood the Linux side with net_close.
  //    This MUST run before accepting: otherwise a slot whose client has
  //    just dropped can be handed to a new connection in the same pass while
  //    net_close for the old one has not been sent, and the Linux side then
  //    feeds the new connection's bytes into the old socket.
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    const bool up = g_clients[slot].connected();
    if (was_up_[slot] && !up) {
      g_clients[slot].stop();
      if (on_close_ != nullptr) on_close_(slot);
    }
    was_up_[slot] = up;
  }
  // 2) Adopt new connections.
  //
  // accept() hands over a connection EXACTLY ONCE and transfers ownership.
  // available() must NOT be used here: it returns whichever client currently
  // has unread data, and returns the SAME client again on every call, so an
  // accept loop built on it adopts one connection into several slots and
  // then forwards fragments of a single byte stream under different slot
  // numbers - which corrupts every request that follows.
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
    } else {
      g_clients[slot] = fresh;
      ++connections_total_;
      if (on_open_ != nullptr) {
        const IPAddress remote = fresh.remoteIP();
        char text[16];
        snprintf(text, sizeof(text), "%d.%d.%d.%d", remote[0], remote[1],
                 remote[2], remote[3]);
        on_open_(static_cast<uint8_t>(slot), text);
      }
    }
  }

  // 3) Pump shield -> Linux. One bulk read per slot per pass; never a byte
  //    at a time, and never blocking.
  for (uint8_t slot = 0; slot < config::kMaxRelaySockets; ++slot) {
    EthernetClient& client = g_clients[slot];
    if (!client.connected() || !client.available()) continue;
    uint8_t buffer[config::kRelayChunkBytes];
    const int read = client.read(buffer, sizeof(buffer));
    if (read > 0 && on_bytes_ != nullptr) {
      on_bytes_(slot, buffer, static_cast<uint16_t>(read));
    }
  }

}

}  // namespace net
