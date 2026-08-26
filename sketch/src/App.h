#ifndef APP_H
#define APP_H

#include <stdint.h>

namespace app {

class App {
 public:
  /// Initialises console, servo, Ethernet relay, and Bridge API.
  static void Begin();

  /// Services the relay, drains diagnostics, and yields CPU.
  static void Tick();
};

}  // namespace app
#endif  // APP_H
