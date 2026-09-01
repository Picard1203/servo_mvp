#ifndef SERVO_TYPES_H
#define SERVO_TYPES_H

#include <stdint.h>

#include "ServoStatus.h"

namespace servo {

/// One coherent reading of the servo.
struct ServoSnapshot {
  int32_t raw_counts = 0;
  bool moving = false;
  float temperature_c = 0.0F;
  float voltage_v = 0.0F;
  float current_a = 0.0F;
  float torque_kgcm = 0.0F;
  int16_t load_duty = 0;
  ServoFaults faults;
  bool valid = false;
};

/// A movement request in the servo's own units.
struct MoveCommand {
  int32_t target_counts = 0;
  uint16_t speed_counts_per_second = 0;
  uint8_t acceleration = 0;
};

/// One coherent reading of the servo's control-loop tuning registers.
struct TuningSnapshot {
  uint8_t position_p = 0;
  uint8_t position_d = 0;
  uint8_t position_i = 0;
  uint16_t min_start_force = 0;
  uint8_t cw_dead_zone = 0;
  uint8_t ccw_dead_zone = 0;
  bool valid = false;
};

}  // namespace servo
#endif  // SERVO_TYPES_H
