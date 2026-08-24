// Fixed-capacity ring buffer for diagnostic log records.
//
// Header-only and Arduino/Zephyr-free on purpose - see CONVENTIONS.md: this
// property is what makes the native test tier possible. Callers on the
// device (NetworkRelay) own the thread safety with their own k_mutex; this
// class assumes single-threaded access and never allocates or blocks.
#ifndef LOG_RING_H
#define LOG_RING_H

#include <stdint.h>
#include <stddef.h>

namespace diag {

/// Severity, matching the levels Logger461 already writes on the Linux side
/// (`app/core/logging_setup.py`), so a receiver there can forward these
/// verbatim instead of re-mapping a second scale.
namespace log_level {
constexpr uint8_t kDebug = 0;
constexpr uint8_t kInfo = 1;
constexpr uint8_t kWarn = 2;
constexpr uint8_t kError = 3;
}  // namespace log_level

/// One diagnostic event. `message` and `event` are expected to point at
/// flash-resident string literals (F(...) on the device) - the ring stores
/// pointers, never copies or owns the text.
struct LogRecord {
  uint8_t level;
  uint32_t uptime_ms;
  const char* message;
  const char* event;
  int32_t arg1;
  int32_t arg2;
};

/// Bounded FIFO of LogRecord. When full, Push() overwrites the oldest entry
/// rather than refusing the new one - the most recent state is what a
/// diagnostic ring exists to keep - and counts the eviction so a caller can
/// tell the drain is falling behind the producers.
template <size_t Capacity>
class LogRing {
 public:
  /// Adds one record, evicting the oldest if the ring is already full.
  /// @return False when an existing entry was evicted to make room.
  bool Push(const LogRecord& record) {
    const bool evicted = full();
    if (evicted) {
      head_ = (head_ + 1) % Capacity;
      --size_;
      ++dropped_total_;
    }
    entries_[tail_] = record;
    tail_ = (tail_ + 1) % Capacity;
    ++size_;
    return !evicted;
  }

  /// Removes and returns the oldest record.
  /// @return False when the ring was empty; `out` is left untouched.
  bool Pop(LogRecord* out) {
    if (empty()) return false;
    *out = entries_[head_];
    head_ = (head_ + 1) % Capacity;
    --size_;
    return true;
  }

  /// @return Number of records currently queued.
  size_t size() const { return size_; }

  /// @return True when there is nothing to Pop().
  bool empty() const { return size_ == 0; }

  /// @return Records evicted by Push() because the ring was full.
  uint32_t dropped_total() const { return dropped_total_; }

 private:
  bool full() const { return size_ == Capacity; }

  LogRecord entries_[Capacity] = {};
  size_t head_ = 0;
  size_t tail_ = 0;
  size_t size_ = 0;
  uint32_t dropped_total_ = 0;
};

}  // namespace diag
#endif  // LOG_RING_H
