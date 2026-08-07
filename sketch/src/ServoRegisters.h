// Feetech STS / Waveshare ST3215 control-table addresses and status bits.
//
// Source of truth: the official Feetech memory table, cross-checked against
// the SCServo library headers and confirmed by a full register dump from our
// own servo (firmware 3.9 / servo 9.3).
//
// WARNING: these are STS addresses. The SC series uses a DIFFERENT map (mode
// is at 19 there, 33 here). Always use the SMS_STS class, never SCSCL.
#ifndef SERVO_REGISTERS_H
#define SERVO_REGISTERS_H

#include <stdint.h>

namespace servo {
namespace reg {

// ---- EEPROM area (persistent; write only while unlocked via kLock) -------
constexpr uint8_t kFirmwareMajor    = 0x00;
constexpr uint8_t kFirmwareMinor    = 0x01;
constexpr uint8_t kServoMajor       = 0x03;
constexpr uint8_t kServoMinor       = 0x04;
constexpr uint8_t kId               = 0x05;
constexpr uint8_t kBaudRate         = 0x06;
constexpr uint8_t kReturnDelay      = 0x07;
constexpr uint8_t kResponseLevel    = 0x08;
constexpr uint8_t kMinAngleLimit    = 0x09;  // 2 bytes; 0 for multi-turn
constexpr uint8_t kMaxAngleLimit    = 0x0B;  // 2 bytes; 0 for multi-turn
constexpr uint8_t kMaxTemperature   = 0x0D;
constexpr uint8_t kMaxVoltage       = 0x0E;
constexpr uint8_t kMinVoltage       = 0x0F;
constexpr uint8_t kMaxTorque        = 0x10;  // 2 bytes
constexpr uint8_t kPhase            = 0x12;  // BIT4 = 1 enables multi-turn
constexpr uint8_t kUnloadCondition  = 0x13;
constexpr uint8_t kLedCondition     = 0x14;
constexpr uint8_t kPositionP        = 0x15;
constexpr uint8_t kPositionD        = 0x16;
constexpr uint8_t kPositionI        = 0x17;
constexpr uint8_t kMinStartForce    = 0x18;  // 2 bytes
constexpr uint8_t kCwDeadZone       = 0x1A;  // 0..32
constexpr uint8_t kCcwDeadZone      = 0x1B;  // 0..32
constexpr uint8_t kProtectCurrent   = 0x1C;  // 2 bytes, 6.5 mA units
constexpr uint8_t kAngleResolution  = 0x1E;  // amplification 1..3
constexpr uint8_t kPositionOffset   = 0x1F;  // 2 bytes, BIT11 is the sign
constexpr uint8_t kMode             = 0x21;  // 0 position, 1 speed, 2 pwm, 3 step
constexpr uint8_t kProtectTorque    = 0x22;
constexpr uint8_t kProtectTime      = 0x23;  // 10 ms units
constexpr uint8_t kOverloadTorque   = 0x24;
constexpr uint8_t kSpeedP           = 0x25;
constexpr uint8_t kOvercurrentTime  = 0x26;
constexpr uint8_t kSpeedI           = 0x27;

// ---- SRAM area (volatile) ------------------------------------------------
constexpr uint8_t kTorqueSwitch     = 0x28;  // 128 = set current position 2048
constexpr uint8_t kAcceleration     = 0x29;  // 100 step/s^2 units
constexpr uint8_t kGoalPosition     = 0x2A;  // 2 bytes, signed
constexpr uint8_t kRunTime          = 0x2C;  // 2 bytes (mode 2)
constexpr uint8_t kGoalSpeed        = 0x2E;  // 2 bytes, step/s
constexpr uint8_t kTorqueLimit      = 0x30;  // 2 bytes, 0..1000
constexpr uint8_t kLock             = 0x37;  // 0 unlocked, 1 locked
constexpr uint8_t kPresentPosition  = 0x38;  // 2 bytes
constexpr uint8_t kPresentSpeed     = 0x3A;  // 2 bytes
constexpr uint8_t kPresentLoad      = 0x3C;  // 2 bytes; PWM duty, NOT torque
constexpr uint8_t kPresentVoltage   = 0x3E;  // 0.1 V units
constexpr uint8_t kPresentTemp      = 0x3F;  // degrees C
constexpr uint8_t kAsyncFlag        = 0x40;
constexpr uint8_t kStatus           = 0x41;  // fault bits; no library constant
constexpr uint8_t kMoving           = 0x42;
constexpr uint8_t kPresentCurrent   = 0x45;  // 2 bytes, 6.5 mA units

}  // namespace reg

namespace status_bit {
constexpr uint8_t kVoltage     = 1 << 0;
constexpr uint8_t kSensor      = 1 << 1;
constexpr uint8_t kTemperature = 1 << 2;
constexpr uint8_t kCurrent     = 1 << 3;
constexpr uint8_t kAngle       = 1 << 4;
constexpr uint8_t kOverload    = 1 << 5;
}  // namespace status_bit

namespace units {
// Verified against the datasheet and cross-checked on the bench.
constexpr float kVoltsPerCount   = 0.1F;     // register 0x3E
constexpr float kAmpsPerCount    = 0.0065F;  // registers 0x1C and 0x45
constexpr float kKgCmPerAmp      = 11.0F;    // 12 V model; 2.7 A * 11 = 29.7
constexpr uint16_t kCountsPerTurn = 4096;
constexpr uint8_t kPositionSignBit = 15;     // goal position / speed fields
constexpr uint8_t kOffsetSignBit   = 11;     // register 0x1F only
constexpr uint8_t kMaxDeadZone     = 32;
constexpr uint8_t kMaxAmplification = 3;
constexpr uint16_t kMaxGoalSpeed   = 3400;
constexpr uint8_t kMaxAcceleration = 254;
constexpr uint16_t kMaxTorqueLimit = 1000;
constexpr uint8_t kCentrePositionCommand = 128;  // written to kTorqueSwitch
}  // namespace units

}  // namespace servo
#endif  // SERVO_REGISTERS_H
