// Routes SPI2 to the JSPI (ICSP) header so the Ethernet Shield is visible.
//
// The UNO Q device tree activates the D11-D13 pin mapping of SPI2, but a
// classic shield takes SPI from the ICSP header, which on this board is a
// DIFFERENT set of MCU pins (PD1 SCK, PC2 MISO, PC3 MOSI). Without this the
// library drives one set of pins while the shield listens on another, and
// Ethernet.hardwareStatus() reports EthernetNoHardware.
//
// Must be applied AFTER SPI.begin() and AGAIN after Ethernet.init(), because
// the Ethernet library re-initialises the SPI pins and undoes the first call.
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
