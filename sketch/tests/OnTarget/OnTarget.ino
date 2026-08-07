// On-target smoke test for the servo sketch.
//
// WHY A SEPARATE SKETCH
//   Arduino's build only compiles the sketch root folder plus src/, so a
//   tests/ folder is ignored by the main build. Each test sketch therefore
//   lives in its own folder whose name matches its .ino - the standard
//   Arduino convention - and you open and upload it like any other sketch.
//
// WHAT IT COVERS
//   The pure-logic classes are already tested on the development machine
//   (see tests/native - run those first, they are instant). This sketch
//   covers only what a host cannot: that the real servo answers, that the
//   configuration writes stick, and that a commanded move actually lands.
//
// HOW TO RUN
//   1. Servo free-shafted, 12 V on the adapter.
//   2. Open this folder as a sketch and upload it.
//   3. Serial Monitor at 115200 over USB. It runs once and prints a tally.
//
// SAFETY
//   Motion is fenced to kSafeMin..kSafeMax and torque is limited throughout.

#include <SCServo.h>

#include "../../src/AngleMath.h"
#include "../../src/Config.h"
#include "../../src/ServoBus.h"
#include "../../src/ServoController.h"
#include "../../src/ServoRegisters.h"

// The pure-logic headers are header-only by design, so a test sketch can
// include them directly. The two hardware classes need their .cpp files,
// which Arduino will not pull in from a sibling folder - including them here
// is the standard workaround for a self-contained test sketch.
#include "../../src/ServoBus.cpp"
#include "../../src/ServoController.cpp"

namespace {

constexpr int32_t kSafeMin = 1200;
constexpr int32_t kSafeMax = 2900;
constexpr uint16_t kTestTorqueLimit = 400;

SMS_STS driver;
servo::ServoBus bus(driver, config::kServoId, config::kBusReadRetries);
servo::ServoController controller(bus);
servo::AngleConverter angles(config::kCountsPerTurn,
                             config::kServoDegPerOutputDeg,
                             config::kServoDirection);

int checks = 0;
int failures = 0;

void Check(bool ok, const char* what) {
  ++checks;
  Serial.print(ok ? F("  ok   ") : F("  FAIL "));
  Serial.println(what);
  if (!ok) ++failures;
}

void CheckNear(int32_t actual, int32_t expected, int32_t tolerance,
               const char* what) {
  const int32_t error = actual > expected ? actual - expected
                                          : expected - actual;
  ++checks;
  Serial.print(error <= tolerance ? F("  ok   ") : F("  FAIL "));
  Serial.print(what);
  Serial.print(F("   expected "));
  Serial.print(expected);
  Serial.print(F(", got "));
  Serial.print(actual);
  Serial.print(F(", error "));
  Serial.println(error);
  if (error > tolerance) ++failures;
}

/// Waits until the reported position stops changing, not merely until the
/// moving flag clears - the flag drops while the servo is still creeping.
bool WaitSettled(uint32_t timeout_ms) {
  const uint32_t started = millis();
  int32_t last = controller.ReadRawCounts();
  uint8_t stable = 0;
  while (millis() - started < timeout_ms) {
    delay(60);
    const int32_t now = controller.ReadRawCounts();
    if (now == last) {
      if (++stable >= 4) return true;
    } else {
      stable = 0;
    }
    last = now;
  }
  return false;
}

void MoveTo(int32_t counts, uint16_t speed) {
  servo::MoveCommand command;
  command.target_counts = counts;
  command.speed_counts_per_second = speed;
  command.acceleration = config::kDefaultAcceleration;
  controller.Move(command);
  WaitSettled(8000);
}

}  // namespace

void setup() {
  Serial.begin(config::kConsoleBaud);
  const uint32_t started = millis();
  while (!Serial && millis() - started < 3000) {
  }
  Serial1.begin(config::kServoBaud);
  driver.pSerial = &Serial1;
  delay(800);

  Serial.println();
  Serial.println(F("on-target servo tests"));

  // --- the servo answers -------------------------------------------------
  Check(bus.Ping(), "servo responds to ping");
  if (failures > 0) {
    Serial.println(F("no servo - stopping. check 12 V, wiring, id, baud."));
    return;
  }

  // --- startup configuration sticks --------------------------------------
  Check(controller.Begin(config::kMultiTurnEnabled, config::kAngleResolution,
                         config::kDeadbandCounts, kTestTorqueLimit),
        "Begin() configured the servo");
  Check(bus.ReadByte(servo::reg::kCwDeadZone) == config::kDeadbandCounts,
        "CW dead zone written");
  Check(bus.ReadByte(servo::reg::kCcwDeadZone) == config::kDeadbandCounts,
        "CCW dead zone written");
  Check(bus.ReadByte(servo::reg::kMode) == 0, "mode is position servo");

  // --- a snapshot is coherent --------------------------------------------
  const servo::ServoSnapshot snapshot = controller.ReadSnapshot();
  Check(snapshot.valid, "snapshot is valid");
  Check(snapshot.voltage_v > 10.0F && snapshot.voltage_v < 13.0F,
        "supply voltage is in range");
  Check(snapshot.temperature_c > 0.0F && snapshot.temperature_c < 80.0F,
        "temperature is plausible");
  Check(!snapshot.faults.Any(), "no faults raised at rest");

  // --- movement lands where asked ----------------------------------------
  MoveTo(kSafeMin + 400, 1000);
  const int32_t start = controller.ReadRawCounts();
  MoveTo(start + 400, 1000);
  CheckNear(controller.ReadRawCounts(), start + 400, 6,
            "moved +400 counts");

  // --- direction matches the configured sign -----------------------------
  Check(controller.ReadRawCounts() > start,
        "positive command increased the position");

  // --- stop holds position ------------------------------------------------
  const int32_t held = controller.ReadRawCounts();
  controller.Stop();
  delay(300);
  CheckNear(controller.ReadRawCounts(), held, 4, "stop held position");

  // --- angle maths agrees with the hardware ------------------------------
  const int32_t counts_for_30_deg = angles.CountsFromOutputDegrees(30.0F);
  CheckNear(counts_for_30_deg, 501, 1, "30 deg output is 501 counts");

  MoveTo(kSafeMin + 400, 1200);
  controller.SetDeadband(config::kDeadbandCounts);

  Serial.println();
  Serial.print(checks);
  Serial.print(F(" checks, "));
  Serial.print(failures);
  Serial.println(F(" failure(s)"));
}

void loop() {}
