#ifndef NETWORK_RELAY_H
#define NETWORK_RELAY_H

#include <stdint.h>
#include <zephyr/kernel.h>

#include "Config.h"

namespace net {

class NetworkRelay {
 public:
  /// Callback for bytes received from a client.
  using ByteSink = void (*)(uint8_t slot, const uint8_t* data,
                            uint16_t length);
  /// Callback when a client disconnects.
  using CloseSink = void (*)(uint8_t slot);
  /// Callback when a client connects.
  using OpenSink = void (*)(uint8_t slot, const char* client_ip);

  /// Constructs a network relay.
  /// @param cs_pin Chip-select pin for the W5500.
  /// @param api_port Port the Linux server listens on.
  /// @param chunk_bytes Maximum payload per Bridge frame.
  NetworkRelay(uint8_t cs_pin, uint16_t api_port, uint16_t chunk_bytes);

  /// Brings up SPI, the shield and the listener.
  /// @param mac Six-byte MAC address.
  /// @param ip Static IPv4 address as four octets.
  /// @param gateway Gateway as four octets.
  /// @param subnet Subnet mask as four octets.
  /// @return True when the W5500 answered and the listener started.
  bool Begin(const uint8_t mac[6], const uint8_t ip[4],
             const uint8_t gateway[4], const uint8_t subnet[4]);

  /// Registers callbacks for client events.
  /// @param on_open Receives client connect notifications.
  /// @param on_bytes Receives client payloads.
  /// @param on_close Receives disconnect notifications.
  void SetSinks(OpenSink on_open, ByteSink on_bytes, CloseSink on_close);

  /// Accepts new clients and forwards received bytes.
  void Poll();

  /// Writes a reply from the Linux side back to a client.
  /// @param slot Connection slot.
  /// @param data Bytes to send.
  /// @param length Number of bytes.
  /// @return True when the slot was connected and the write succeeded.
  bool WriteToClient(uint8_t slot, const uint8_t* data, uint16_t length);

  /// Closes a client connection.
  /// @param slot Connection slot.
  void CloseClient(uint8_t slot);

  /// Reports whether the W5500 was initialized.
  /// @return True when the W5500 was detected and configured.
  bool ready() const { return ready_; }

  /// Returns count of client connections accepted since boot.
  /// @return Number of client connections accepted since boot.
  uint32_t connections_total() const { return connections_total_; }

  /// Returns count of connections refused due to no available slot.
  /// @return Connections refused because every slot was busy.
  uint32_t rejected_total() const { return rejected_total_; }

  /// Returns count of Bridge thread lock acquisition timeouts.
  /// @return Times the Bridge thread gave up waiting for the W5500.
  uint32_t write_lock_timeouts() const { return write_lock_timeouts_; }

 private:
  /// Takes the W5500 lock.
  /// @param timeout How long to wait for the chip.
  /// @return True when the lock was taken; false on timeout.
  bool LockChip(k_timeout_t timeout);

  /// Releases the W5500 lock.
  void UnlockChip();

  struct k_mutex chip_lock_;
  uint32_t write_lock_timeouts_ = 0;
  uint8_t cs_pin_;
  uint16_t api_port_;
  uint16_t chunk_bytes_;
  bool ready_ = false;
  uint32_t connections_total_ = 0;
  uint32_t rejected_total_ = 0;
  bool was_up_[8] = {false};
  OpenSink on_open_ = nullptr;
  ByteSink on_bytes_ = nullptr;
  CloseSink on_close_ = nullptr;
};

}  // namespace net
#endif  // NETWORK_RELAY_H
