// Every tunable in one place. Values match python/.env.example so the two
// halves of the system cannot drift apart silently.
#ifndef CONFIG_H
#define CONFIG_H

#include <stdint.h>

namespace config {

// ---- servo bus ----------------------------------------------------------
constexpr uint8_t  kServoId        = 1;
constexpr uint32_t kServoBaud      = 1000000UL;
constexpr uint8_t  kBusReadRetries = 4;   // transient single-register misses

// ---- mechanism ----------------------------------------------------------
constexpr uint16_t kCountsPerTurn         = 4096;
constexpr float    kServoDegPerOutputDeg  = 44.0F / 30.0F;
constexpr int8_t   kServoDirection        = 1;    // bench-confirmed +1

// ---- travel window ------------------------------------------------------
// +/-90 deg output = 264 servo deg = 3004 counts, comfortably inside one
// servo turn, so multi-turn is not needed. Kept configurable because the
// requirement has already changed once.
constexpr bool    kMultiTurnEnabled = false;
constexpr uint8_t kAngleResolution  = 1;   // amplification; 1 keeps 0.06 deg

// ---- servo tuning -------------------------------------------------------
// Measured landing error by dead zone: 0 -> 0.06 deg, 1 -> 0.10, 8 -> 0.52,
// 32 -> 1.98. Zero is the accurate choice.
constexpr uint8_t  kDeadbandCounts     = 0;
constexpr uint8_t  kDefaultAcceleration = 50;   // nothing changes above ~50
constexpr uint16_t kTorqueLimit        = 1000;  // full torque in service

// ---- console ------------------------------------------------------------
constexpr uint32_t kConsoleBaud = 115200UL;

// ---- Ethernet shield ----------------------------------------------------
constexpr uint8_t  kEthernetCsPin = 10;
constexpr uint16_t kApiPort       = 8000;   // the Linux side serves here
// Bytes per Bridge message. MUST match relay_chunk_bytes on the Python side.
// The working relay used 256; at 128 every payload costs twice as many Bridge
// round trips. Raise both together when you want that back.
constexpr uint16_t kRelayChunkBytes = 128;
// The W5500 has 8 hardware sockets and the listener consumes one.
constexpr uint8_t  kMaxRelaySockets = 6;

}  // namespace config
#endif  // CONFIG_H
