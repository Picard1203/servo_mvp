#include "ServoController.h"

#include <Arduino.h>
#include <SCServo.h>

#include "ServoRegisters.h"
#include "SignMagnitude.h"

namespace servo {
namespace {

constexpr uint8_t kPhaseMultiTurnBit = 1 << 4;

uint8_t ClampDeadband(uint8_t counts) {
  return counts > units::kMaxDeadZone ? units::kMaxDeadZone : counts;
}

uint8_t ClampAmplification(uint8_t amplification) {
  if (amplification < 1) return 1;
  if (amplification > units::kMaxAmplification) {
    return units::kMaxAmplification;
  }
  return amplification;
}

}  // namespace

ServoController::ServoController(ServoBus& bus) : bus_(bus) {}

bool ServoController::Begin(bool multi_turn, uint8_t angle_resolution,
                            uint8_t deadband_counts, uint16_t torque_limit) {
  if (!bus_.Ping()) return false;
  bool ok = ConfigureRange(multi_turn, angle_resolution);
  ok = SetDeadband(deadband_counts) && ok;
  ok = bus_.WriteWord(reg::kTorqueLimit,
                      static_cast<int16_t>(torque_limit)) && ok;
  ok = bus_.driver().EnableTorque(bus_.servo_id(), 1) != -1 && ok;
  return ok;
}

ServoSnapshot ServoController::ReadSnapshot() {
  ServoSnapshot snapshot;
  if (!bus_.Refresh()) return snapshot;  // valid stays false

  SMS_STS& driver = bus_.driver();
  const int id = bus_.servo_id();

  snapshot.raw_counts = driver.ReadPos(id);
  snapshot.moving = driver.ReadMove(id) != 0;
  snapshot.temperature_c = static_cast<float>(driver.ReadTemper(id));
  snapshot.voltage_v =
      static_cast<float>(driver.ReadVoltage(id)) * units::kVoltsPerCount;
  snapshot.current_a =
      static_cast<float>(driver.ReadCurrent(id)) * units::kAmpsPerCount;
  snapshot.torque_kgcm = snapshot.current_a * units::kKgCmPerAmp;
  snapshot.load_duty = static_cast<int16_t>(driver.ReadLoad(id));

  // The status register has no accessor in the library; read it directly.
  const int status = bus_.ReadByte(reg::kStatus);
  if (status >= 0) {
    snapshot.faults = ServoFaults::FromStatusByte(static_cast<uint8_t>(status));
  }
  snapshot.valid = true;
  return snapshot;
}

int32_t ServoController::ReadRawCounts() {
  const int position = bus_.driver().ReadPos(bus_.servo_id());
  return position == -1 ? 0 : static_cast<int32_t>(position);
}

bool ServoController::Move(const MoveCommand& command) {
  // Defence in depth. The Linux side checks reachability too, but the servo
  // clamps silently outside its angle limits - it stops early and still
  // acknowledges - so a bad target must never reach WritePosEx.
  if (command.target_counts < 0 ||
      command.target_counts > static_cast<int32_t>(units::kCountsPerTurn) - 1) {
    return false;
  }
  const int16_t target = static_cast<int16_t>(command.target_counts);
  const uint8_t acceleration =
      command.acceleration > units::kMaxAcceleration
          ? units::kMaxAcceleration
          : command.acceleration;
  uint16_t speed = command.speed_counts_per_second;
  if (speed == 0) speed = 1;
  if (speed > units::kMaxGoalSpeed) speed = units::kMaxGoalSpeed;
  return bus_.driver().WritePosEx(bus_.servo_id(), target, speed,
                                  acceleration) != -1;
}

bool ServoController::Stop() {
  const int32_t here = ReadRawCounts();
  MoveCommand hold;
  hold.target_counts = here;
  hold.speed_counts_per_second = 1;
  hold.acceleration = 0;
  return Move(hold);
}

bool ServoController::SetDeadband(uint8_t counts) {
  const uint8_t clamped = ClampDeadband(counts);
  const bool cw = bus_.WriteEepromByte(reg::kCwDeadZone, clamped);
  const bool ccw = bus_.WriteEepromByte(reg::kCcwDeadZone, clamped);
  return cw && ccw;
}

bool ServoController::ConfigureRange(bool multi_turn,
                                     uint8_t angle_resolution) {
  const int phase = bus_.ReadByte(reg::kPhase);
  if (phase < 0) return false;

  bool ok = true;
  if (multi_turn) {
    const uint8_t amplification = ClampAmplification(angle_resolution);
    ok = bus_.WriteEepromWord(reg::kMinAngleLimit, 0) && ok;
    ok = bus_.WriteEepromWord(reg::kMaxAngleLimit, 0) && ok;
    ok = bus_.WriteEepromByte(reg::kAngleResolution, amplification) && ok;
    ok = bus_.WriteEepromByte(
             reg::kPhase,
             static_cast<uint8_t>(phase) | kPhaseMultiTurnBit) && ok;
  } else {
    ok = bus_.WriteEepromWord(reg::kMinAngleLimit, 0) && ok;
    ok = bus_.WriteEepromWord(
             reg::kMaxAngleLimit,
             static_cast<int16_t>(units::kCountsPerTurn - 1)) && ok;
    ok = bus_.WriteEepromByte(reg::kAngleResolution, 1) && ok;
    ok = bus_.WriteEepromByte(
             reg::kPhase,
             static_cast<uint8_t>(phase) &
                 static_cast<uint8_t>(~kPhaseMultiTurnBit)) && ok;
  }
  // Position servo mode either way; step mode (3) is relative stepping and
  // is not what absolute positioning needs.
  ok = bus_.WriteEepromByte(reg::kMode, 0) && ok;
  return ok;
}

bool ServoController::ClearFault() {
  // Hardware rule: the overload de-rate is released by the next position
  // command, so re-commanding where we already are clears it without moving.
  return Stop();
}

bool ServoController::CentreHere() {
  return bus_.WriteByte(reg::kTorqueSwitch, units::kCentrePositionCommand);
}

}  // namespace servo
