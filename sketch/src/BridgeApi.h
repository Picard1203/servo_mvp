#ifndef BRIDGE_API_H
#define BRIDGE_API_H

#include <stdint.h>

#include "NetworkRelay.h"
#include "ServoController.h"

namespace api {

class BridgeApi {
 public:
  /// Constructs the Bridge API binding.
  /// @param controller Servo operations.
  /// @param relay Network relay, or nullptr when no shield is fitted.
  BridgeApi(servo::ServoController& controller, net::NetworkRelay* relay);

  /// Registers every Bridge callback.
  void Register();

  /// Drains the diagnostic ring toward the Bridge.
  void DrainDiagLog();

  /// Returns the singleton instance.
  /// @return The singleton instance, used by the C-style Bridge callbacks.
  static BridgeApi* instance() { return instance_; }

  /// Formats a snapshot as the documented CSV payload.
  /// @param snapshot Reading to format.
  /// @param out Destination buffer.
  /// @param size Size of the destination buffer.
  static void FormatSnapshot(const servo::ServoSnapshot& snapshot, char* out,
                             uint16_t size);

  /// Returns the servo controller.
  /// @return The servo controller.
  servo::ServoController& controller() { return controller_; }

  /// Returns the relay, or nullptr.
  /// @return The relay, or nullptr.
  net::NetworkRelay* relay() { return relay_; }

 private:
  static BridgeApi* instance_;
  servo::ServoController& controller_;
  net::NetworkRelay* relay_;
};

}  // namespace api
#endif  // BRIDGE_API_H
