// Host-native tests for the sketch's pure-logic classes.
//
// These classes deliberately have no Arduino dependency, so they compile and
// run on the development machine. Run them before every flash: they are
// instant, and they cover the maths that is hardest to debug on hardware.
//
//   cd sketch/tests/native && make
#include "../../src/AngleMath.h"
#include "../../src/ServoStatus.h"
#include "../../src/SignMagnitude.h"
#include "TinyTest.h"

using servo::AngleConverter;
using servo::ServoFaults;
using servo::SignMagnitude;

namespace {

// Our mechanism: 4096 counts per servo turn, 44:30 belt, normal direction.
AngleConverter MakeConverter(int8_t direction = 1) {
  return AngleConverter(4096, 44.0F / 30.0F, direction);
}

}  // namespace

// ----------------------------------------------------------- sign magnitude

TEST(sign_magnitude_decodes_positive_unchanged) {
  CHECK_EQ(SignMagnitude::Decode(0, 15), 0);
  CHECK_EQ(SignMagnitude::Decode(2048, 15), 2048);
  CHECK_EQ(SignMagnitude::Decode(4095, 15), 4095);
}

TEST(sign_magnitude_decodes_the_32700_symptom) {
  // The classic bug: a small negative read back as roughly 32700.
  CHECK_EQ(SignMagnitude::Decode(32773, 15), -5);
  CHECK_EQ(SignMagnitude::Decode(static_cast<uint16_t>((1U << 15) | 1U), 15),
           -1);
}

TEST(sign_magnitude_negative_zero_is_zero) {
  CHECK_EQ(SignMagnitude::Decode(32768, 15), 0);
}

TEST(sign_magnitude_uses_bit11_for_the_offset_register) {
  // Register 0x1F carries its sign in bit 11, not bit 15.
  CHECK_EQ(SignMagnitude::Decode(static_cast<uint16_t>((1U << 11) | 7U), 11),
           -7);
  CHECK_EQ(SignMagnitude::Decode(440, 11), 440);
}

TEST(sign_magnitude_round_trips) {
  for (int32_t value = -2000; value <= 2000; value += 137) {
    CHECK_EQ(SignMagnitude::Decode(SignMagnitude::Encode(value, 15), 15),
             value);
  }
}

// ------------------------------------------------------------- angle maths

TEST(angle_one_count_is_the_measured_output_resolution) {
  // (360/4096) * (30/44) = 0.059925 degrees at the output.
  CHECK_NEAR(MakeConverter().OutputDegreesPerCount(), 0.059925, 0.0001);
}

TEST(angle_round_trips_within_one_count) {
  const AngleConverter converter = MakeConverter();
  const float resolution = converter.OutputDegreesPerCount();
  for (float degrees = -90.0F; degrees <= 90.0F; degrees += 7.5F) {
    const int32_t counts = converter.CountsFromOutputDegrees(degrees);
    CHECK_NEAR(converter.OutputDegreesFromCounts(counts), degrees,
               resolution);
  }
}

TEST(angle_full_travel_window_fits_in_one_servo_turn) {
  // The operators asked for +/-90 degrees. 180 output degrees is 264 servo
  // degrees, which must stay inside one 4096-count turn so that no
  // multi-turn configuration is required.
  const AngleConverter converter = MakeConverter();
  const int32_t span = converter.CountsFromOutputDegrees(90.0F) -
                       converter.CountsFromOutputDegrees(-90.0F);
  CHECK_EQ(span, 3004);
  CHECK(span < 4096);
}

TEST(angle_direction_mirrors_counts_but_still_round_trips) {
  const AngleConverter forward = MakeConverter(1);
  const AngleConverter reversed = MakeConverter(-1);
  const int32_t a = forward.CountsFromOutputDegrees(30.0F);
  const int32_t b = reversed.CountsFromOutputDegrees(30.0F);
  CHECK(a > 0);
  CHECK(b < 0);
  CHECK_EQ(a, -b);
  // Applying the sign on both conversions keeps them self-consistent.
  CHECK_NEAR(reversed.OutputDegreesFromCounts(b), 30.0, 0.06);
}

TEST(angle_zero_maps_to_zero_in_both_directions) {
  CHECK_EQ(MakeConverter(1).CountsFromOutputDegrees(0.0F), 0);
  CHECK_EQ(MakeConverter(-1).CountsFromOutputDegrees(0.0F), 0);
}

TEST(angle_speed_conversion_never_returns_zero) {
  const AngleConverter converter = MakeConverter();
  CHECK_EQ(converter.CountsPerSecondFromOutputSpeed(0.0F), 1);
  CHECK_EQ(converter.CountsPerSecondFromOutputSpeed(-5.0F),
           converter.CountsPerSecondFromOutputSpeed(5.0F));
}

TEST(angle_speed_matches_the_measured_ceiling) {
  // The bench showed the servo saturating near 1100 counts/s, which is why
  // the backend caps output speed at 60 deg/s.
  const AngleConverter converter = MakeConverter();
  CHECK_NEAR(converter.CountsPerSecondFromOutputSpeed(60.0F), 1001.0, 3.0);
}

// ----------------------------------------------------------- status decode

TEST(status_zero_means_no_faults) {
  const ServoFaults faults = ServoFaults::FromStatusByte(0);
  CHECK(!faults.Any());
  CHECK(!faults.overload);
}

TEST(status_decodes_every_documented_bit) {
  CHECK(ServoFaults::FromStatusByte(1 << 0).voltage);
  CHECK(ServoFaults::FromStatusByte(1 << 1).sensor);
  CHECK(ServoFaults::FromStatusByte(1 << 2).overheat);
  CHECK(ServoFaults::FromStatusByte(1 << 3).overcurrent);
  CHECK(ServoFaults::FromStatusByte(1 << 4).angle);
  CHECK(ServoFaults::FromStatusByte(1 << 5).overload);
}

TEST(status_bit4_is_the_flag_the_backend_used_to_miss) {
  const ServoFaults faults = ServoFaults::FromStatusByte(1 << 4);
  CHECK(faults.angle);
  CHECK(faults.Any());
  CHECK(!faults.overload);
}

TEST(status_round_trips_through_the_byte) {
  for (uint8_t bits = 0; bits < 64; ++bits) {
    CHECK_EQ(ServoFaults::FromStatusByte(bits).ToStatusByte(), bits);
  }
}

TEST(status_combined_faults_decode_independently) {
  const ServoFaults faults = ServoFaults::FromStatusByte(
      servo::status_bit::kOverload | servo::status_bit::kCurrent);
  CHECK(faults.overload);
  CHECK(faults.overcurrent);
  CHECK(!faults.overheat);
  CHECK(!faults.angle);
}

// -------------------------------------------------- physical count limits

TEST(range_rejects_counts_below_zero) {
  // The failure that made a -90 command stop at 0: the servo clamps below
  // count 0 and still reports success, so nothing noticed.
  const AngleConverter converter = MakeConverter();
  CHECK(!converter.IsCountReachable(-1));
  CHECK(!converter.IsCountReachable(-1502));
}

TEST(range_rejects_counts_above_one_turn) {
  const AngleConverter converter = MakeConverter();
  CHECK(!converter.IsCountReachable(4096));
  CHECK(!converter.IsCountReachable(30000));
}

TEST(range_accepts_the_whole_single_turn) {
  const AngleConverter converter = MakeConverter();
  CHECK(converter.IsCountReachable(0));
  CHECK(converter.IsCountReachable(2048));
  CHECK(converter.IsCountReachable(4095));
}

TEST(range_a_datum_at_zero_strands_the_negative_half) {
  // With the baseline at count 0 every negative angle is unreachable. This
  // is why the datum defaults to the CENTRE of travel, not to zero.
  const AngleConverter converter = MakeConverter();
  const int32_t baseline_at_zero = 0;
  CHECK(!converter.IsCountReachable(
      baseline_at_zero + converter.CountsFromOutputDegrees(-90.0F)));
  const int32_t baseline_at_centre = 2048;
  CHECK(converter.IsCountReachable(
      baseline_at_centre + converter.CountsFromOutputDegrees(-90.0F)));
  CHECK(converter.IsCountReachable(
      baseline_at_centre + converter.CountsFromOutputDegrees(90.0F)));
}

int main() { return tiny_test::RunAll("sketch pure-logic tests"); }
