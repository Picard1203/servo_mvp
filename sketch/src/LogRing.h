#ifndef LOG_RING_H
#define LOG_RING_H

#include <stdint.h>
#include <stddef.h>

namespace diag {

/// Severity levels matching Logger461.
namespace log_level {
constexpr uint8_t kDebug = 0;
constexpr uint8_t kInfo = 1;
constexpr uint8_t kWarn = 2;
constexpr uint8_t kError = 3;
}  // namespace log_level

/// Diagnostic event with pointers to flash-resident string literals.
struct LogRecord {
  uint8_t level;
  uint32_t uptime_ms;
  const char* message;
  const char* event;
  int32_t arg1;
  int32_t arg2;
};

/// Bounded FIFO ring buffer of LogRecord entries.
template <size_t Capacity>
class LogRing {
 public:
  /// Adds one record, evicting the oldest if the ring is already full.
  /// @param record Log record to add.
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
  /// @param out Destination pointer for the popped record.
  /// @return False when the ring was empty; out is left untouched.
  bool Pop(LogRecord* out) {
    if (empty()) return false;
    *out = entries_[head_];
    head_ = (head_ + 1) % Capacity;
    --size_;
    return true;
  }

  /// Returns number of records currently queued.
  /// @return Number of records currently queued.
  size_t size() const { return size_; }

  /// Reports whether the ring buffer is empty.
  /// @return True when there is nothing to Pop().
  bool empty() const { return size_ == 0; }

  /// Returns count of records evicted by Push() when full.
  /// @return Records evicted by Push() because the ring was full.
  uint32_t dropped_total() const { return dropped_total_; }

 private:
  /// Reports whether the ring buffer is full.
  /// @return True when size equals capacity.
  bool full() const { return size_ == Capacity; }

  LogRecord entries_[Capacity] = {};
  size_t head_ = 0;
  size_t tail_ = 0;
  size_t size_ = 0;
  uint32_t dropped_total_ = 0;
};

}  // namespace diag
#endif  // LOG_RING_H
