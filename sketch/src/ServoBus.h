// Thin, retrying wrapper around the SCServo SMS_STS driver.
//
// Everything that touches the serial bus goes through here, which keeps the
// retry policy and the EEPROM unlock ritual in exactly one place.
#ifndef SERVO_BUS_H
#define SERVO_BUS_H

#include <stdint.h>

class SMS_STS;

namespace servo {

class ServoBus {
 public:
  /// @param driver     The SCServo driver, already bound to a serial port.
  /// @param servo_id   Bus address of the servo.
  /// @param retries    Read attempts before reporting failure.
  ServoBus(SMS_STS& driver, uint8_t servo_id, uint8_t retries);

  /// Checks that the servo answers.
  /// @return True when the servo replies with its own id.
  bool Ping();

  /// Reads one byte, retrying transient bus misses.
  /// @param address Register address.
  /// @return The value, or -1 when every attempt failed.
  int ReadByte(uint8_t address);

  /// Reads two bytes, retrying transient bus misses.
  /// @param address Register address of the low byte.
  /// @return The value, or -1 when every attempt failed.
  int ReadWord(uint8_t address);

  /// Writes one byte to a volatile (SRAM) register.
  /// @param address Register address.
  /// @param value   Value to write.
  /// @return True on success.
  bool WriteByte(uint8_t address, uint8_t value);

  /// Writes two bytes to a volatile (SRAM) register.
  /// @param address Register address of the low byte.
  /// @param value   Value to write.
  /// @return True on success.
  bool WriteWord(uint8_t address, int16_t value);

  /// Writes one byte to an EEPROM register, unlocking and re-locking.
  /// Skips the write when the register already holds the value, because
  /// EEPROM has a finite number of write cycles.
  /// @param address Register address.
  /// @param value   Value to write.
  /// @return True on success or when no write was needed.
  bool WriteEepromByte(uint8_t address, uint8_t value);

  /// Writes two bytes to an EEPROM register, unlocking and re-locking.
  /// @param address Register address of the low byte.
  /// @param value   Value to write.
  /// @return True on success or when no write was needed.
  bool WriteEepromWord(uint8_t address, int16_t value);

  /// Pulls the whole telemetry block in one bus round trip.
  /// @return True when the block was read.
  bool Refresh();

  /// @return The driver, for the few calls with no register equivalent.
  SMS_STS& driver() { return driver_; }

  /// @return The configured bus address.
  uint8_t servo_id() const { return servo_id_; }

 private:
  SMS_STS& driver_;
  uint8_t servo_id_;
  uint8_t retries_;
};

}  // namespace servo
#endif  // SERVO_BUS_H
