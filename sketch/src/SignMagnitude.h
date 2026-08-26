#ifndef SIGN_MAGNITUDE_H
#define SIGN_MAGNITUDE_H

#include <stdint.h>

namespace servo {

class SignMagnitude {
 public:
  /// Decodes a sign-magnitude field into a signed value.
  /// @param raw      Raw unsigned register value.
  /// @param sign_bit Index of the sign bit (15 for position, 11 for offset).
  /// @return The signed magnitude.
  static int32_t Decode(uint16_t raw, uint8_t sign_bit) {
    const uint16_t mask = static_cast<uint16_t>(1U << sign_bit);
    if (raw & mask) {
      return -static_cast<int32_t>(raw & static_cast<uint16_t>(mask - 1U));
    }
    return static_cast<int32_t>(raw);
  }

  /// Encodes a signed value back into a sign-magnitude field.
  /// @param value    Signed value to encode.
  /// @param sign_bit Index of the sign bit.
  /// @return The raw register value.
  static uint16_t Encode(int32_t value, uint8_t sign_bit) {
    const uint16_t mask = static_cast<uint16_t>(1U << sign_bit);
    if (value < 0) {
      const uint16_t magnitude =
          static_cast<uint16_t>(-value) & static_cast<uint16_t>(mask - 1U);
      return static_cast<uint16_t>(magnitude | mask);
    }
    return static_cast<uint16_t>(value) & static_cast<uint16_t>(mask - 1U);
  }
};

}  // namespace servo
#endif  // SIGN_MAGNITUDE_H
