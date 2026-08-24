#include "DiagLog.h"

namespace diag {

struct k_mutex DiagLog::lock_;
LogRing<config::kLogRingCapacity> DiagLog::ring_;

void DiagLog::Init() {
  k_mutex_init(&lock_);
}

void DiagLog::Push(uint8_t level, const char* message, const char* event,
                   int32_t arg1, int32_t arg2) {
  const LogRecord record{level, static_cast<uint32_t>(k_uptime_get()),
                         message, event, arg1, arg2};
  k_mutex_lock(&lock_, K_FOREVER);
  ring_.Push(record);
  k_mutex_unlock(&lock_);
}

bool DiagLog::Drain(LogRecord* out) {
  k_mutex_lock(&lock_, K_FOREVER);
  const bool got = ring_.Pop(out);
  k_mutex_unlock(&lock_);
  return got;
}

uint32_t DiagLog::dropped_total() {
  k_mutex_lock(&lock_, K_FOREVER);
  const uint32_t total = ring_.dropped_total();
  k_mutex_unlock(&lock_);
  return total;
}

}  // namespace diag
