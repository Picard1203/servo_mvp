// Data carried between the servo layer and the Bridge layer.
#ifndef SERVO_TYPES_H
#define SERVO_TYPES_H

#include <stdint.h>

#include "ServoStatus.h"

namespace servo {

/// One coherent reading of the servo. `valid` is false when the bus did not
/// answer; every other field is meaningless in that case.
struct ServoSnapshot {
  int32_t raw_counts = 0;
  bool moving = false;
  float temperature_c = 0.0F;
  float voltage_v = 0.0F;
  float current_a = 0.0F;
  float torque_kgcm = 0.0F;
  int16_t load_duty = 0;   // PWM duty of the drive output, NOT torque
  ServoFaults faults;
  bool valid = false;
};

/// A movement request in the servo's own units.
struct MoveCommand {
  int32_t target_counts = 0;
  uint16_t speed_counts_per_second = 0;
  uint8_t acceleration = 0;
};

}  // namespace servo
#endif  // SERVO_TYPES_H
