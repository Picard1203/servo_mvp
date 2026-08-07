#include "ServoBus.h"

#include <Arduino.h>
#include <SCServo.h>

#include "ServoRegisters.h"

namespace servo {
namespace {
constexpr uint8_t kRetryDelayMs = 4;
constexpr uint8_t kEepromSettleMs = 12;
}  // namespace

ServoBus::ServoBus(SMS_STS& driver, uint8_t servo_id, uint8_t retries)
    : driver_(driver), servo_id_(servo_id),
      retries_(retries == 0 ? 1 : retries) {}

bool ServoBus::Ping() {
  for (uint8_t attempt = 0; attempt < retries_; ++attempt) {
    if (driver_.Ping(servo_id_) == servo_id_) return true;
    delay(kRetryDelayMs);
  }
  return false;
}

int ServoBus::ReadByte(uint8_t address) {
  for (uint8_t attempt = 0; attempt < retries_; ++attempt) {
    const int value = driver_.readByte(servo_id_, address);
    if (value != -1) return value;
    delay(kRetryDelayMs);
  }
  return -1;
}

int ServoBus::ReadWord(uint8_t address) {
  for (uint8_t attempt = 0; attempt < retries_; ++attempt) {
    const int value = driver_.readWord(servo_id_, address);
    if (value != -1) return value;
    delay(kRetryDelayMs);
  }
  return -1;
}

bool ServoBus::WriteByte(uint8_t address, uint8_t value) {
  return driver_.writeByte(servo_id_, address, value) != -1;
}

bool ServoBus::WriteWord(uint8_t address, int16_t value) {
  return driver_.writeWord(servo_id_, address, value) != -1;
}

bool ServoBus::WriteEepromByte(uint8_t address, uint8_t value) {
  const int current = ReadByte(address);
  if (current == static_cast<int>(value)) return true;  // save a write cycle
  driver_.unLockEprom(servo_id_);
  const bool ok = WriteByte(address, value);
  driver_.LockEprom(servo_id_);
  delay(kEepromSettleMs);
  return ok;
}

bool ServoBus::WriteEepromWord(uint8_t address, int16_t value) {
  const int current = ReadWord(address);
  if (current == static_cast<int>(value)) return true;
  driver_.unLockEprom(servo_id_);
  const bool ok = WriteWord(address, value);
  driver_.LockEprom(servo_id_);
  delay(kEepromSettleMs);
  return ok;
}

bool ServoBus::Refresh() {
  for (uint8_t attempt = 0; attempt < retries_; ++attempt) {
    if (driver_.FeedBack(servo_id_) != -1) return true;
    delay(kRetryDelayMs);
  }
  return false;
}

}  // namespace servo
