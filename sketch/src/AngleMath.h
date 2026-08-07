// Conversion between output degrees and raw encoder counts.
//
// The belt makes the output turn more slowly than the servo:
//   output_deg = servo_deg * (30 / 44)
// One encoder count is 360/4096 = 0.0879 servo degrees, so at the output a
// single count is 0.0599 degrees. That is the true resolution; the Python
// side rounds displayed values to 0.06.
//
// Direction is applied to BOTH conversions so a reversed mounting stays
// self-consistent: a value converted to counts and back is unchanged.
//
// Header-only and Arduino-free so it is unit testable on a dev machine.
#ifndef ANGLE_MATH_H
#define ANGLE_MATH_H

#include <stdint.h>

namespace servo {

class AngleConverter {
 public:
  /// @param counts_per_turn         Encoder counts per servo revolution.
  /// @param servo_deg_per_output_deg Belt ratio, 44/30 for our mechanism.
  /// @param direction               +1 normal, -1 for a reversed mounting.
  AngleConverter(uint16_t counts_per_turn, float servo_deg_per_output_deg,
                 int8_t direction)
      : counts_per_turn_(counts_per_turn),
        counts_per_servo_deg_(static_cast<float>(counts_per_turn) / 360.0F),
        servo_deg_per_output_deg_(servo_deg_per_output_deg),
        direction_(direction >= 0 ? 1 : -1) {}

  /// Converts an output angle to counts relative to the baseline.
  /// @param output_deg Angle at the output, in degrees.
  /// @return Signed counts offset from the baseline.
  int32_t CountsFromOutputDegrees(float output_deg) const {
    const float servo_deg = output_deg * servo_deg_per_output_deg_ *
                            static_cast<float>(direction_);
    return RoundToInt(servo_deg * counts_per_servo_deg_);
  }

  /// Converts counts relative to the baseline into an output angle.
  /// @param counts Signed counts offset from the baseline.
  /// @return Angle at the output, in degrees.
  float OutputDegreesFromCounts(int32_t counts) const {
    const float servo_deg = static_cast<float>(counts) / counts_per_servo_deg_;
    return servo_deg / servo_deg_per_output_deg_ *
           static_cast<float>(direction_);
  }

  /// Returns the smallest output movement the hardware can express.
  /// @return Output degrees represented by one encoder count.
  float OutputDegreesPerCount() const {
    return 1.0F / (counts_per_servo_deg_ * servo_deg_per_output_deg_);
  }

  /// Converts an output speed into the servo's native units.
  /// @param degrees_per_second Output speed in degrees per second.
  /// @return Speed in counts per second, never below 1.
  uint16_t CountsPerSecondFromOutputSpeed(float degrees_per_second) const {
    const float counts = degrees_per_second * servo_deg_per_output_deg_ *
                         counts_per_servo_deg_;
    const int32_t rounded = RoundToInt(counts < 0 ? -counts : counts);
    if (rounded < 1) return 1;
    return static_cast<uint16_t>(rounded);
  }

  /// Reports whether a count target is inside the servo's physical range.
  ///
  /// The servo is configured with angle limits 0..counts_per_turn-1 and
  /// CLAMPS silently outside them: it stops early and still reports the
  /// command as accepted. Anything commanding a position must check first,
  /// or an unreachable target looks like a successful one.
  ///
  /// @param counts Absolute counts target.
  /// @return True when the servo can actually reach it.
  bool IsCountReachable(int32_t counts) const {
    return counts >= 0 && counts <= static_cast<int32_t>(counts_per_turn_) - 1;
  }

  /// @return Encoder counts per servo revolution.
  uint16_t counts_per_turn() const { return counts_per_turn_; }

  /// @return The configured direction, +1 or -1.
  int8_t direction() const { return direction_; }

 private:
  /// Rounds half away from zero without pulling in <cmath>.
  static int32_t RoundToInt(float value) {
    return static_cast<int32_t>(value >= 0 ? value + 0.5F : value - 0.5F);
  }

  uint16_t counts_per_turn_;
  float counts_per_servo_deg_;
  float servo_deg_per_output_deg_;
  int8_t direction_;
};

}  // namespace servo
#endif  // ANGLE_MATH_H
