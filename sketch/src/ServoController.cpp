#include "ServoController.h"

#include <Arduino.h>
#include <SCServo.h>

#include "DiagLog.h"
#include "ServoRegisters.h"
#include "SignMagnitude.h"

namespace servo {
namespace {

constexpr uint8_t kPhaseMultiTurnBit = 1 << 4;

uint8_t ClampDeadband(uint8_t counts) {
  return counts > units::kMaxDeadZone ? units::kMaxDeadZone : counts;
}

uint16_t ClampMinStartForce(uint16_t force) {
  return force > units::kMaxTorqueLimit ? units::kMaxTorqueLimit : force;
}

uint8_t ClampByteRegister(int16_t value) {
  if (value < 0) return 0;
  if (value > 255) return 255;
  return static_cast<uint8_t>(value);
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
                            uint8_t deadband_counts, uint16_t torque_limit,
                            uint16_t min_start_force) {
  if (!bus_.Ping()) return false;
  bool ok = ConfigureRange(multi_turn, angle_resolution);
  ok = SetDeadband(deadband_counts) && ok;
  ok = SetMinStartForce(min_start_force) && ok;
  ok = bus_.WriteWord(reg::kTorqueLimit,
                      static_cast<int16_t>(torque_limit)) && ok;
  // EnableTorque: 0 fail / 1 success, never -1.
  ok = bus_.driver().EnableTorque(bus_.servo_id(), 1) != 0 && ok;
  return ok;
}

ServoSnapshot ServoController::ReadSnapshot() {
  ServoSnapshot snapshot;
  if (!bus_.Refresh()) return snapshot;

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
  if (command.target_counts < 0 ||
      command.target_counts > static_cast<int32_t>(units::kCountsPerTurn) - 1) {
    diag::DiagLog::Push(diag::log_level::kWarn,
                        "Move rejected: target outside one servo turn",
                        "mcu.servo.move_rejected_out_of_range",
                        command.target_counts);
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
  // WritePosEx: 0 fail / 1 success, never -1.
  return bus_.driver().WritePosEx(bus_.servo_id(), target, speed,
                                  acceleration) != 0;
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

bool ServoController::SetMinStartForce(uint16_t force) {
  const uint16_t clamped = ClampMinStartForce(force);
  return bus_.WriteEepromWord(reg::kMinStartForce,
                              static_cast<int16_t>(clamped));
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
  ok = bus_.WriteEepromByte(reg::kMode, 0) && ok;
  return ok;
}

bool ServoController::ClearFault() {
  diag::DiagLog::Push(diag::log_level::kInfo,
                      "Fault-clear issued: re-commanding current position",
                      "mcu.servo.fault_clear_issued");
  return Stop();
}

bool ServoController::CentreHere() {
  return bus_.WriteByte(reg::kTorqueSwitch, units::kCentrePositionCommand);
}

bool ServoController::SetTorque(bool enabled) {
  bool ok = true;
  if (enabled) {
    const int32_t here = ReadRawCounts();
    MoveCommand hold;
    hold.target_counts = here;
    hold.speed_counts_per_second = 1;
    hold.acceleration = 0;
    ok = Move(hold) && ok;
  }
  // EnableTorque: 0 fail / 1 success, never -1.
  ok = bus_.driver().EnableTorque(bus_.servo_id(), enabled ? 1 : 0) != 0 &&
       ok;
  return ok;
}

int ServoController::ReadTorqueRegister() {
  return bus_.ReadByte(reg::kTorqueSwitch);
}

TuningSnapshot ServoController::ReadTuningRegisters() {
  TuningSnapshot snapshot;
  const int p = bus_.ReadByte(reg::kPositionP);
  const int d = bus_.ReadByte(reg::kPositionD);
  const int i = bus_.ReadByte(reg::kPositionI);
  const int min_start_force = bus_.ReadWord(reg::kMinStartForce);
  const int cw = bus_.ReadByte(reg::kCwDeadZone);
  const int ccw = bus_.ReadByte(reg::kCcwDeadZone);
  if (p < 0 || d < 0 || i < 0 || min_start_force < 0 || cw < 0 || ccw < 0) {
    return snapshot;
  }
  snapshot.position_p = static_cast<uint8_t>(p);
  snapshot.position_d = static_cast<uint8_t>(d);
  snapshot.position_i = static_cast<uint8_t>(i);
  snapshot.min_start_force = static_cast<uint16_t>(min_start_force);
  snapshot.cw_dead_zone = static_cast<uint8_t>(cw);
  snapshot.ccw_dead_zone = static_cast<uint8_t>(ccw);
  snapshot.valid = true;
  return snapshot;
}

bool ServoController::WriteTuningRegisters(int16_t p, int16_t d, int16_t i,
                                           int16_t min_start_force,
                                           int16_t cw, int16_t ccw) {
  bool ok = true;
  if (p >= 0) {
    ok = bus_.WriteEepromByte(reg::kPositionP, ClampByteRegister(p)) && ok;
  }
  if (d >= 0) {
    ok = bus_.WriteEepromByte(reg::kPositionD, ClampByteRegister(d)) && ok;
  }
  if (i >= 0) {
    ok = bus_.WriteEepromByte(reg::kPositionI, ClampByteRegister(i)) && ok;
  }
  if (min_start_force >= 0) {
    const uint16_t clamped =
        ClampMinStartForce(static_cast<uint16_t>(min_start_force));
    ok = bus_.WriteEepromWord(reg::kMinStartForce,
                              static_cast<int16_t>(clamped)) && ok;
  }
  if (cw >= 0) {
    ok = bus_.WriteEepromByte(reg::kCwDeadZone, ClampDeadband(
        static_cast<uint8_t>(ClampByteRegister(cw)))) && ok;
  }
  if (ccw >= 0) {
    ok = bus_.WriteEepromByte(reg::kCcwDeadZone, ClampDeadband(
        static_cast<uint8_t>(ClampByteRegister(ccw)))) && ok;
  }
  return ok;
}

int32_t ServoController::ReadPresentSpeed() {
  const int raw = bus_.ReadWord(reg::kPresentSpeed);
  if (raw < 0) return 0;
  return SignMagnitude::Decode(static_cast<uint16_t>(raw),
                               units::kPositionSignBit);
}

}  // namespace servo
