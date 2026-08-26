#ifndef DIAG_LOG_H
#define DIAG_LOG_H

#include <zephyr/kernel.h>

#include "Config.h"
#include "LogRing.h"

namespace diag {

class DiagLog {
 public:
  /// Initialises the internal mutex.
  static void Init();

  /// Queues one diagnostic record.
  /// @param level Severity level (log_level::k*).
  /// @param message Flash-resident human-readable text.
  /// @param event Flash-resident dotted machine identifier.
  /// @param arg1 Optional integer argument.
  /// @param arg2 Optional integer argument.
  static void Push(uint8_t level, const char* message, const char* event,
                   int32_t arg1 = 0, int32_t arg2 = 0);

  /// Removes and returns the oldest queued record.
  /// @param out Destination pointer for the popped record.
  /// @return False when nothing was queued.
  static bool Drain(LogRecord* out);

  /// Returns count of records evicted because the ring was full.
  /// @return Records evicted because the ring was full.
  static uint32_t dropped_total();

 private:
  static struct k_mutex lock_;
  static LogRing<config::kLogRingCapacity> ring_;
};

}  // namespace diag
#endif  // DIAG_LOG_H
