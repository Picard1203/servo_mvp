// Composition root: builds the object graph once and drives it.
//
// Keeping this here rather than in the .ino means the wiring is ordinary
// C++ in a real translation unit - no preprocessor concatenation, no
// generated prototypes, and it can be read top to bottom.
#ifndef APP_H
#define APP_H

#include <stdint.h>

namespace app {

class App {
 public:
  /// Brings up the console, servo bus, servo configuration, Ethernet relay
  /// and Bridge API, in that order. Safe to call once from setup().
  static void Begin();

  /// Services the relay and the console. Call from loop(); never blocks.
  static void Tick();
};

}  // namespace app
#endif  // APP_H
