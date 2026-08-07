// Servo Control - MCU side.
//
// Deliberately thin. Every line of real logic lives in src/ as ordinary
// .h/.cpp pairs, which the Arduino build compiles recursively WITHOUT the
// .ino preprocessing (no concatenation, no generated prototypes). That is
// what lets the code be normal, reviewable, testable C++.
//
// See src/App.cpp for the composition root and src/BridgeApi.h for the
// contract with the Python backend.

#include "src/App.h"

void setup() { app::App::Begin(); }

void loop() { app::App::Tick(); }
