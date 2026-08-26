#ifndef SERVO_REGISTERS_H
#define SERVO_REGISTERS_H

#include <stdint.h>

namespace servo {
namespace reg {

constexpr uint8_t kFirmwareMajor    = 0x00;
constexpr uint8_t kFirmwareMinor    = 0x01;
constexpr uint8_t kServoMajor       = 0x03;
constexpr uint8_t kServoMinor       = 0x04;
constexpr uint8_t kId               = 0x05;
constexpr uint8_t kBaudRate         = 0x06;
constexpr uint8_t kReturnDelay      = 0x07;
constexpr uint8_t kResponseLevel    = 0x08;
constexpr uint8_t kMinAngleLimit    = 0x09;
constexpr uint8_t kMaxAngleLimit    = 0x0B;
constexpr uint8_t kMaxTemperature   = 0x0D;
constexpr uint8_t kMaxVoltage       = 0x0E;
constexpr uint8_t kMinVoltage       = 0x0F;
constexpr uint8_t kMaxTorque        = 0x10;
constexpr uint8_t kPhase            = 0x12;
constexpr uint8_t kUnloadCondition  = 0x13;
constexpr uint8_t kLedCondition     = 0x14;
constexpr uint8_t kPositionP        = 0x15;
constexpr uint8_t kPositionD        = 0x16;
constexpr uint8_t kPositionI        = 0x17;
constexpr uint8_t kMinStartForce    = 0x18;
constexpr uint8_t kCwDeadZone       = 0x1A;
constexpr uint8_t kCcwDeadZone      = 0x1B;
constexpr uint8_t kProtectCurrent   = 0x1C;
constexpr uint8_t kAngleResolution  = 0x1E;
constexpr uint8_t kPositionOffset   = 0x1F;
constexpr uint8_t kMode             = 0x21;
constexpr uint8_t kProtectTorque    = 0x22;
constexpr uint8_t kProtectTime      = 0x23;
constexpr uint8_t kOverloadTorque   = 0x24;
constexpr uint8_t kSpeedP           = 0x25;
constexpr uint8_t kOvercurrentTime  = 0x26;
constexpr uint8_t kSpeedI           = 0x27;

constexpr uint8_t kTorqueSwitch     = 0x28;
constexpr uint8_t kAcceleration     = 0x29;
constexpr uint8_t kGoalPosition     = 0x2A;
constexpr uint8_t kRunTime          = 0x2C;
constexpr uint8_t kGoalSpeed        = 0x2E;
constexpr uint8_t kTorqueLimit      = 0x30;
constexpr uint8_t kLock             = 0x37;
constexpr uint8_t kPresentPosition  = 0x38;
constexpr uint8_t kPresentSpeed     = 0x3A;
constexpr uint8_t kPresentLoad      = 0x3C;
constexpr uint8_t kPresentVoltage   = 0x3E;
constexpr uint8_t kPresentTemp      = 0x3F;
constexpr uint8_t kAsyncFlag        = 0x40;
constexpr uint8_t kStatus           = 0x41;
constexpr uint8_t kMoving           = 0x42;
constexpr uint8_t kPresentCurrent   = 0x45;

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
constexpr float kVoltsPerCount   = 0.1F;
constexpr float kAmpsPerCount    = 0.0065F;
constexpr float kKgCmPerAmp      = 11.0F;
constexpr uint16_t kCountsPerTurn = 4096;
constexpr uint8_t kPositionSignBit = 15;
constexpr uint8_t kOffsetSignBit   = 11;
constexpr uint8_t kMaxDeadZone     = 32;
constexpr uint8_t kMaxAmplification = 3;
constexpr uint16_t kMaxGoalSpeed   = 3400;
constexpr uint8_t kMaxAcceleration = 254;
constexpr uint16_t kMaxTorqueLimit = 1000;
constexpr uint8_t kCentrePositionCommand = 128;
}  // namespace units

}  // namespace servo
#endif  // SERVO_REGISTERS_H
