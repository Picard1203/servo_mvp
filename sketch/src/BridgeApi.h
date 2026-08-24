// The contract between this sketch and the Python backend.
//
// Five servo functions plus the network relay callbacks. Payloads are plain
// comma-separated strings rather than a binary struct: they cost a few bytes
// more, they are readable in a log when something goes wrong, and neither
// side can silently drift from a field order the other assumes.
//
// Requests (Linux -> sketch):
//   servo_read              ""                       -> snapshot CSV
//   servo_move              "counts,speed,accel"     -> "ok" | "err"
//   servo_stop              ""                       -> "ok" | "err"
//   servo_set_deadband      "counts"                 -> "ok" | "err"
//   servo_configure_range   "multiturn,amplification"-> "ok" | "err"
//   get_status              (no payload)             -> "ready" | "no-servo"
//
// Notifies (sketch -> Linux):
//   mcu_log   level, message, event, arg1, arg2, uptime_s  (backlog D3)
//     Drained from DiagLog, one event at a time - not batched, so an older
//     one is never held up behind delivery of a newer one.
//
// ServoController::CentreHere() is deliberately NOT exposed here. Our
// calibration is a software relabel recorded in SQLite; letting the servo
// also hold a position offset would create two competing sources of truth
// for where zero is.
//
// Snapshot CSV field order (also documented on the Python side):
//   valid,counts,moving,temp_c,volt_v,curr_a,torque_kgcm,load,status_bits
#ifndef BRIDGE_API_H
#define BRIDGE_API_H

#include <stdint.h>

#include "NetworkRelay.h"
#include "ServoController.h"

namespace api {

class BridgeApi {
 public:
  /// @param controller Servo operations.
  /// @param relay      Network relay, or nullptr when no shield is fitted.
  BridgeApi(servo::ServoController& controller, net::NetworkRelay* relay);

  /// Registers every Bridge callback. Call once at startup.
  void Register();

  /// Drains the diagnostic ring (DiagLog) toward the Bridge, bounded by
  /// Config::kMcuLogDrainPerTick per call. Call from Tick().
  void DrainDiagLog();

  /// @return The singleton instance, used by the C-style Bridge callbacks.
  static BridgeApi* instance() { return instance_; }

  /// Formats a snapshot as the documented CSV payload.
  /// @param snapshot Reading to format.
  /// @param out      Destination buffer.
  /// @param size     Size of the destination buffer.
  static void FormatSnapshot(const servo::ServoSnapshot& snapshot, char* out,
                             uint16_t size);

  /// @return The servo controller.
  servo::ServoController& controller() { return controller_; }

  /// @return The relay, or nullptr.
  net::NetworkRelay* relay() { return relay_; }

 private:
  static BridgeApi* instance_;
  servo::ServoController& controller_;
  net::NetworkRelay* relay_;
};

}  // namespace api
#endif  // BRIDGE_API_H
