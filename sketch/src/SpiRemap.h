#ifndef SPI_REMAP_H
#define SPI_REMAP_H

#include <stdint.h>

namespace board {

class SpiRemap {
 public:
  /// Applies the JSPI pin mapping and releases the D11-D13 copies.
  static void ApplyJspiMapping();

 private:
  static constexpr uint8_t kAlternateFunctionSpi2 = 5;

  /// Puts one pin into alternate-function mode.
  /// @param port_index 2 for GPIOC, 3 for GPIOD.
  /// @param pin        Pin number within the port.
  static void SetAlternateFunction(uint8_t port_index, uint8_t pin);

  /// Disconnects D11-D13 so they stop carrying duplicate SPI signals.
  static void ReleaseTopHeaderCopies();
};

}  // namespace board
#endif  // SPI_REMAP_H
