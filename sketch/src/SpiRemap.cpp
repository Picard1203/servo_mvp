#include "SpiRemap.h"

#include <Arduino.h>

namespace board {
namespace {

/// Returns the GPIO port block for the given index.
/// @param port_index 2 for GPIOC, 3 for GPIOD.
/// @return Pointer to the port registers.
GPIO_TypeDef* PortFor(uint8_t port_index) {
  return port_index == 3 ? GPIOD : GPIOC;
}

}  // namespace

void SpiRemap::SetAlternateFunction(uint8_t port_index, uint8_t pin) {
  GPIO_TypeDef* port = PortFor(port_index);
  const uint32_t mode_mask = ~(0x3UL << (pin * 2));
  port->MODER = (port->MODER & mode_mask) | (0x2UL << (pin * 2));
  if (pin < 8) {
    port->AFR[0] = (port->AFR[0] & ~(0xFUL << (pin * 4))) |
                   (static_cast<uint32_t>(kAlternateFunctionSpi2) << (pin * 4));
  } else {
    const uint8_t high = static_cast<uint8_t>(pin - 8);
    port->AFR[1] = (port->AFR[1] & ~(0xFUL << (high * 4))) |
                   (static_cast<uint32_t>(kAlternateFunctionSpi2) <<
                    (high * 4));
  }
}

void SpiRemap::ReleaseTopHeaderCopies() {
  pinMode(11, INPUT);
  pinMode(12, INPUT);
  pinMode(13, INPUT);
}

void SpiRemap::ApplyJspiMapping() {
  SetAlternateFunction(3, 1);
  SetAlternateFunction(2, 2);
  SetAlternateFunction(2, 3);
  ReleaseTopHeaderCopies();
}

}  // namespace board
