#include "BridgeApi.h"

#include <Arduino.h>
#include <Arduino_RouterBridge.h>

#include <stdio.h>
#include <stdlib.h>

#include "Config.h"

namespace api {

BridgeApi* BridgeApi::instance_ = nullptr;

namespace {

constexpr uint16_t kSnapshotBufferBytes = 128;

/// Reads the n-th comma separated integer from a payload.
/// @param payload Comma separated values.
/// @param index   Zero based field index.
/// @param fallback Returned when the field is absent.
/// @return The parsed value, or the fallback.
long FieldAt(const String& payload, uint8_t index, long fallback) {
  int start = 0;
  for (uint8_t current = 0; current <= index; ++current) {
    const int comma = payload.indexOf(',', start);
    if (current == index) {
      const String field =
          comma < 0 ? payload.substring(start) : payload.substring(start,
                                                                  comma);
      if (field.length() == 0) return fallback;
      return field.toInt();
    }
    if (comma < 0) return fallback;
    start = comma + 1;
  }
  return fallback;
}

const char* Ack(bool ok) { return ok ? "ok" : "err"; }

// ---- Bridge callbacks. Free functions because the Bridge takes plain
// ---- function pointers; they delegate straight to the singleton.

String HandleServoRead(String /*unused*/) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("0,0,0,0,0,0,0,0,0");
  const servo::ServoSnapshot snapshot = api->controller().ReadSnapshot();
  char buffer[kSnapshotBufferBytes];
  BridgeApi::FormatSnapshot(snapshot, buffer, sizeof(buffer));
  return String(buffer);
}

String HandleServoMove(String payload) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String(Ack(false));
  servo::MoveCommand command;
  command.target_counts = static_cast<int32_t>(FieldAt(payload, 0, 0));
  command.speed_counts_per_second =
      static_cast<uint16_t>(FieldAt(payload, 1, 1));
  command.acceleration = static_cast<uint8_t>(
      FieldAt(payload, 2, config::kDefaultAcceleration));
  return String(Ack(api->controller().Move(command)));
}

String HandleServoStop(String /*unused*/) {
  BridgeApi* api = BridgeApi::instance();
  return String(Ack(api != nullptr && api->controller().Stop()));
}

String HandleSetDeadband(String payload) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String(Ack(false));
  const uint8_t counts = static_cast<uint8_t>(FieldAt(payload, 0, 0));
  return String(Ack(api->controller().SetDeadband(counts)));
}

String HandleConfigureRange(String payload) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String(Ack(false));
  const bool multi_turn = FieldAt(payload, 0, 0) != 0;
  const uint8_t amplification = static_cast<uint8_t>(FieldAt(payload, 1, 1));
  return String(Ack(api->controller().ConfigureRange(multi_turn,
                                                    amplification)));
}

// Python calls this with no payload at all (system.py health check), so it
// must take no parameter - a String parameter here fails to bind.
String HandleGetStatus() {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("no-servo");
  const servo::ServoSnapshot snapshot = api->controller().ReadSnapshot();
  String status(snapshot.valid ? "ready" : "no-servo");
  if (api->relay() != nullptr) {
    // Relay pressure belongs in the health line: a growing rejected count is
    // the signature of the browser wanting more parallel connections than the
    // W5500 has slots for, and it is otherwise completely invisible.
    status += " relay=";
    status += static_cast<int>(api->relay()->connections_total());
    status += "/rejected=";
    status += static_cast<int>(api->relay()->rejected_total());
  }
  return status;
}

// ---- network relay -----------------------------------------------------
//
// These four signatures are NOT free choices: they must match what
// app/relay/bridge_relay.py declares, which is
//     net_open(slot, client_ip)   net_rx(slot, data)   net_close(slot)
//     net_tx(slot, data)          net_shutdown(slot)
// Typed arguments and MsgPack::bin_t for the payload, not a packed string -
// the byte stream is binary and must survive intact.

/// Linux -> shield: write a reply to a connected client.
/// @param slot Connection slot.
/// @param data Raw bytes to send.
/// @return 1 on success, 0 otherwise.
int HandleNetTx(int slot, MsgPack::bin_t<uint8_t> data) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr || api->relay() == nullptr) return 0;
  return api->relay()->WriteToClient(static_cast<uint8_t>(slot), data.data(),
                                     static_cast<uint16_t>(data.size()))
             ? 1
             : 0;
}

/// Linux -> shield: close a client connection.
/// @param slot Connection slot.
/// @return Always 1.
int HandleNetShutdown(int slot) {
  BridgeApi* api = BridgeApi::instance();
  if (api != nullptr && api->relay() != nullptr) {
    api->relay()->CloseClient(static_cast<uint8_t>(slot));
  }
  return 1;
}

/// Shield -> Linux: a client connected.
void ForwardClientOpen(uint8_t slot, const char* client_ip) {
  Bridge.notify("net_open", static_cast<int>(slot), String(client_ip));
}

/// Shield -> Linux: bytes arrived from a client.
void ForwardClientBytes(uint8_t slot, const uint8_t* data, uint16_t length) {
  MsgPack::bin_t<uint8_t> payload(data, data + length);
  Bridge.notify("net_rx", static_cast<int>(slot), payload);
}

/// Shield -> Linux: a client disconnected.
void ForwardClientClose(uint8_t slot) {
  Bridge.notify("net_close", static_cast<int>(slot));
}

}  // namespace

BridgeApi::BridgeApi(servo::ServoController& controller,
                     net::NetworkRelay* relay)
    : controller_(controller), relay_(relay) {
  instance_ = this;
}

void BridgeApi::FormatSnapshot(const servo::ServoSnapshot& snapshot,
                               char* out, uint16_t size) {
  snprintf(out, size, "%d,%ld,%d,%.1f,%.2f,%.3f,%.2f,%d,%u",
           snapshot.valid ? 1 : 0,
           static_cast<long>(snapshot.raw_counts),
           snapshot.moving ? 1 : 0,
           static_cast<double>(snapshot.temperature_c),
           static_cast<double>(snapshot.voltage_v),
           static_cast<double>(snapshot.current_a),
           static_cast<double>(snapshot.torque_kgcm),
           static_cast<int>(snapshot.load_duty),
           static_cast<unsigned>(snapshot.faults.ToStatusByte()));
}

void BridgeApi::Register() {
  Bridge.provide("servo_read", HandleServoRead);
  Bridge.provide("servo_move", HandleServoMove);
  Bridge.provide("servo_stop", HandleServoStop);
  Bridge.provide("servo_set_deadband", HandleSetDeadband);
  Bridge.provide("servo_configure_range", HandleConfigureRange);
  Bridge.provide("get_status", HandleGetStatus);

  if (relay_ != nullptr) {
    // provide_safe: these are called from the Bridge thread while loop() may
    // be inside the relay.
    Bridge.provide_safe("net_tx", HandleNetTx);
    Bridge.provide_safe("net_shutdown", HandleNetShutdown);
    relay_->SetSinks(ForwardClientOpen, ForwardClientBytes,
                     ForwardClientClose);
  }
}

}  // namespace api
