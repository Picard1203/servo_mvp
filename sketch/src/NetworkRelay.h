// Pumps bytes between the Ethernet Shield and the FastAPI server running on
// the Linux side of the board.
//
// The shield is wired to the MCU, but the HTTP server lives on Linux, so the
// MCU accepts the TCP connection and relays the raw bytes over the Bridge.
// Each shield connection gets a slot; the Linux side answers on net_tx.
#ifndef NETWORK_RELAY_H
#define NETWORK_RELAY_H

#include <stdint.h>

namespace net {

class NetworkRelay {
 public:
  /// Called with bytes received from a shield client. The relay does not
  /// know what happens to them - this seam is what keeps it independent of
  /// the Bridge layer and testable in isolation.
  using ByteSink = void (*)(uint8_t slot, const uint8_t* data,
                            uint16_t length);
  /// Called when a client disconnects, so the Linux side can drop its socket.
  using CloseSink = void (*)(uint8_t slot);
  /// Called when a client connects. The Linux side opens its own socket to
  /// uvicorn on this signal; without it, bytes arrive for a slot that has no
  /// connection behind it and are discarded.
  using OpenSink = void (*)(uint8_t slot, const char* client_ip);

  /// @param cs_pin      Chip-select pin for the W5500.
  /// @param api_port    Port the Linux server listens on.
  /// @param chunk_bytes Maximum payload per Bridge frame.
  NetworkRelay(uint8_t cs_pin, uint16_t api_port, uint16_t chunk_bytes);

  /// Brings up SPI (with the JSPI remap), the shield and the listener.
  /// @param mac     Six-byte MAC address.
  /// @param ip      Static IPv4 address as four octets.
  /// @param gateway Gateway as four octets.
  /// @param subnet  Subnet mask as four octets.
  /// @return True when the W5500 answered and the listener started.
  bool Begin(const uint8_t mac[6], const uint8_t ip[4],
             const uint8_t gateway[4], const uint8_t subnet[4]);

  /// Registers the callbacks invoked on received bytes and on disconnect.
  /// @param on_bytes Receives client payloads.
  /// @param on_close Receives disconnect notifications.
  void SetSinks(OpenSink on_open, ByteSink on_bytes, CloseSink on_close);

  /// Accepts new clients and forwards received bytes. Call from loop().
  void Poll();

  /// Writes a reply from the Linux side back to a client.
  /// @param slot   Connection slot.
  /// @param data   Bytes to send.
  /// @param length Number of bytes.
  /// @return True when the slot was connected and the write succeeded.
  bool WriteToClient(uint8_t slot, const uint8_t* data, uint16_t length);

  /// Closes a client connection.
  /// @param slot Connection slot.
  void CloseClient(uint8_t slot);

  /// @return True when the W5500 was detected and configured.
  bool ready() const { return ready_; }

  /// @return Number of client connections accepted since boot.
  uint32_t connections_total() const { return connections_total_; }

  /// @return Connections refused because every slot was busy. A non-zero
  ///         value means the browser wants more parallel connections than
  ///         kMaxRelaySockets allows.
  uint32_t rejected_total() const { return rejected_total_; }

 private:
  uint8_t cs_pin_;
  uint16_t api_port_;
  uint16_t chunk_bytes_;
  bool ready_ = false;
  uint32_t connections_total_ = 0;
  uint32_t rejected_total_ = 0;
  bool was_up_[8] = {false};   // edge detection for disconnects
  OpenSink on_open_ = nullptr;
  ByteSink on_bytes_ = nullptr;
  CloseSink on_close_ = nullptr;
};

}  // namespace net
#endif  // NETWORK_RELAY_H
