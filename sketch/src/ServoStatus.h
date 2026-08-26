#ifndef SERVO_STATUS_H
#define SERVO_STATUS_H

#include <stdint.h>

#include "ServoRegisters.h"

namespace servo {

class ServoFaults {
 public:
  bool voltage = false;
  bool sensor = false;
  bool overheat = false;
  bool overcurrent = false;
  bool angle = false;
  bool overload = false;

  /// Builds a decoded fault set from the raw status byte.
  /// @param status Raw value of register 0x41.
  /// @return The decoded faults.
  static ServoFaults FromStatusByte(uint8_t status) {
    ServoFaults faults;
    faults.voltage = (status & status_bit::kVoltage) != 0;
    faults.sensor = (status & status_bit::kSensor) != 0;
    faults.overheat = (status & status_bit::kTemperature) != 0;
    faults.overcurrent = (status & status_bit::kCurrent) != 0;
    faults.angle = (status & status_bit::kAngle) != 0;
    faults.overload = (status & status_bit::kOverload) != 0;
    return faults;
  }

  /// Re-encodes the fault set as a status byte.
  /// @return The raw bit pattern.
  uint8_t ToStatusByte() const {
    uint8_t bits = 0;
    if (voltage) bits |= status_bit::kVoltage;
    if (sensor) bits |= status_bit::kSensor;
    if (overheat) bits |= status_bit::kTemperature;
    if (overcurrent) bits |= status_bit::kCurrent;
    if (angle) bits |= status_bit::kAngle;
    if (overload) bits |= status_bit::kOverload;
    return bits;
  }

  /// Reports whether any fault is set.
  /// @return True when at least one flag is raised.
  bool Any() const { return ToStatusByte() != 0; }
};

}  // namespace servo
#endif  // SERVO_STATUS_H
