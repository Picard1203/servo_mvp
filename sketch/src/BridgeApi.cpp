#include "BridgeApi.h"

#include <Arduino.h>
#include <Arduino_RouterBridge.h>

#include <stdio.h>
#include <stdlib.h>

#include "Config.h"
#include "DiagLog.h"

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

String HandleSetTorque(String payload) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String(Ack(false));
  const bool enabled = FieldAt(payload, 0, 0) != 0;
  return String(Ack(api->controller().SetTorque(enabled)));
}

String HandleReadTorque(String /*unused*/) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("err");
  const int value = api->controller().ReadTorqueRegister();
  if (value < 0) return String("err");
  return String(value);
}

String HandleReadTuning(String /*unused*/) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("0,0,0,0,0,0,0");
  const servo::TuningSnapshot snapshot =
      api->controller().ReadTuningRegisters();
  char buffer[64];
  snprintf(buffer, sizeof(buffer), "%d,%u,%u,%u,%u,%u,%u",
          snapshot.valid ? 1 : 0,
          static_cast<unsigned>(snapshot.position_p),
          static_cast<unsigned>(snapshot.position_d),
          static_cast<unsigned>(snapshot.position_i),
          static_cast<unsigned>(snapshot.min_start_force),
          static_cast<unsigned>(snapshot.cw_dead_zone),
          static_cast<unsigned>(snapshot.ccw_dead_zone));
  return String(buffer);
}

String HandleWriteTuning(String payload) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String(Ack(false));
  const int16_t p = static_cast<int16_t>(FieldAt(payload, 0, -1));
  const int16_t d = static_cast<int16_t>(FieldAt(payload, 1, -1));
  const int16_t i = static_cast<int16_t>(FieldAt(payload, 2, -1));
  const int16_t min_start_force =
      static_cast<int16_t>(FieldAt(payload, 3, -1));
  const int16_t cw = static_cast<int16_t>(FieldAt(payload, 4, -1));
  const int16_t ccw = static_cast<int16_t>(FieldAt(payload, 5, -1));
  return String(Ack(api->controller().WriteTuningRegisters(
      p, d, i, min_start_force, cw, ccw)));
}

String HandleReadSpeed(String /*unused*/) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("err");
  return String(static_cast<long>(api->controller().ReadPresentSpeed()));
}

String HandleGetStatus() {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr) return String("no-servo");
  const servo::ServoSnapshot snapshot = api->controller().ReadSnapshot();
  String status(snapshot.valid ? "ready" : "no-servo");
  if (api->relay() != nullptr) {
    status += " relay=";
    status += static_cast<int>(api->relay()->connections_total());
    status += "/rejected=";
    status += static_cast<int>(api->relay()->rejected_total());
  }
  status += "/diag_dropped=";
  status += static_cast<int>(diag::DiagLog::dropped_total());
  return status;
}

/// Linux -> shield: writes a reply to a connected client.
int HandleNetTx(int slot, MsgPack::bin_t<uint8_t> data) {
  BridgeApi* api = BridgeApi::instance();
  if (api == nullptr || api->relay() == nullptr) return 0;
  return api->relay()->WriteToClient(static_cast<uint8_t>(slot), data.data(),
                                     static_cast<uint16_t>(data.size()))
             ? 1
             : 0;
}

/// Linux -> shield: closes a client connection.
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

void ForwardDiagLog(const diag::LogRecord& record) {
  Bridge.notify("mcu_log", static_cast<int>(record.level),
               String(record.message), String(record.event),
               static_cast<int>(record.arg1), static_cast<int>(record.arg2),
               static_cast<int>(record.uptime_ms / 1000));
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
  Bridge.provide("servo_set_torque", HandleSetTorque);
  Bridge.provide("servo_read_torque", HandleReadTorque);
  Bridge.provide("servo_read_tuning", HandleReadTuning);
  Bridge.provide("servo_write_tuning", HandleWriteTuning);
  Bridge.provide("servo_read_speed", HandleReadSpeed);
  Bridge.provide("get_status", HandleGetStatus);

  if (relay_ != nullptr) {
    // provide_safe: called from Bridge thread per RELAY_NOTES.md rule 7.
    Bridge.provide_safe("net_tx", HandleNetTx);
    Bridge.provide_safe("net_shutdown", HandleNetShutdown);
    relay_->SetSinks(ForwardClientOpen, ForwardClientBytes,
                     ForwardClientClose);
  }
}

void BridgeApi::DrainDiagLog() {
  diag::LogRecord record;
  for (uint8_t drained = 0; drained < config::kMcuLogDrainPerTick;
      ++drained) {
    if (!diag::DiagLog::Drain(&record)) break;
    ForwardDiagLog(record);
  }
}

}  // namespace api
