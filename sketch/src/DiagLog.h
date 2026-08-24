// Process-wide diagnostic sink for the C++ side.
//
// Every hardware- or network-touching file (NetworkRelay, ServoBus,
// ServoController, BridgeApi) pushes here; App::Tick() drains it toward the
// Bridge. One ring, one lock, many producers - the same tradeoff
// BridgeApi::instance() already makes to avoid threading a reference
// through every class that needs it.
#ifndef DIAG_LOG_H
#define DIAG_LOG_H

#include <zephyr/kernel.h>

#include "Config.h"
#include "LogRing.h"

namespace diag {

class DiagLog {
 public:
  /// Initialises the internal mutex. Call once from App::Begin(), before
  /// the loop and Bridge threads can race on Push() - mirrors how
  /// NetworkRelay's own chip_lock_ is initialised in its constructor.
  static void Init();

  /// Queues one diagnostic record. Never blocks on anything but the
  /// internal lock, which is held only for an array write - safe to call
  /// from either thread, and safe to call while NetworkRelay's chip_lock_ is
  /// held (the ordering is always chip_lock_ then this lock, never the
  /// reverse, so there is no inversion risk). NOT a sink callback - it never
  /// touches the Bridge itself.
  /// @param message Flash-resident (F(...)) human-readable text.
  /// @param event   Flash-resident (F(...)) dotted machine identifier.
  static void Push(uint8_t level, const char* message, const char* event,
                   int32_t arg1 = 0, int32_t arg2 = 0);

  /// Removes and returns the oldest queued record. Call from Tick() only -
  /// App owns draining toward the Bridge.
  /// @return False when nothing was queued.
  static bool Drain(LogRecord* out);

  /// @return Records evicted because the ring was full - a non-zero value
  ///         means the drain is not keeping up with the producers.
  static uint32_t dropped_total();

 private:
  static struct k_mutex lock_;
  static LogRing<config::kLogRingCapacity> ring_;
};

}  // namespace diag
#endif  // DIAG_LOG_H
