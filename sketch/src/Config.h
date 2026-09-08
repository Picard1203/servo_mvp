#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>

namespace config {

constexpr uint8_t  kServoId        = 1;
constexpr uint32_t kServoBaud      = 1000000UL;
constexpr uint8_t  kBusReadRetries = 4;

constexpr uint16_t kCountsPerTurn         = 4096;
constexpr float    kServoDegPerOutputDeg  = 44.0F / 30.0F;
constexpr int8_t   kServoDirection        = 1;

constexpr bool    kMultiTurnEnabled = false;
constexpr uint8_t kAngleResolution  = 1;

constexpr uint8_t  kDeadbandCounts     = 0;
constexpr uint8_t  kDefaultAcceleration = 50;
constexpr uint16_t kTorqueLimit        = 1000;
// The minimum drive applied when the arm is off target. It trades two
// opposite failures against each other: too high and the arm hunts around
// the target and never stops, too low and it stops short and stays there.
// Measured across 176 trials at four values, oscillation rises with this
// number and stopping short falls, so no value avoids both - 55 is the
// highest that never once oscillated (0 of 44 trials), leaving the short
// landing to be corrected in software, which it can be. Verified on the
// bench proxy only; a real arm carries more friction, so expect to revisit.
constexpr uint16_t kMinStartForce      = 55;
constexpr uint8_t  kPositionGainP      = 24;

constexpr uint32_t kConsoleBaud = 115200UL;

constexpr uint8_t  kEthernetCsPin = 10;
constexpr uint16_t kApiPort       = 8000;
// Must match relay_chunk_bytes in Python per RELAY_NOTES.md rule 5.
constexpr uint16_t kRelayChunkBytes = 224;
constexpr uint8_t  kMaxRelaySockets = 6;

constexpr uint8_t kLogRingCapacity   = 32;
// Bounded per RELAY_NOTES.md rule 3 so loop() yields.
constexpr uint8_t kMcuLogDrainPerTick = 4;

}  // namespace config
#endif  // CONFIG_H
