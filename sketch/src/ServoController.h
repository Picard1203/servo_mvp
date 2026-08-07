// The servo operations the Linux side actually asks for.
//
// This is the only class that knows how a request like "move to these counts"
// becomes register writes. Everything above it deals in ServoSnapshot and
// MoveCommand; everything below it is ServoBus.
#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <stdint.h>

#include "ServoBus.h"
#include "ServoTypes.h"

namespace servo {

class ServoController {
 public:
  /// @param bus Bus wrapper for the servo.
  explicit ServoController(ServoBus& bus);

  /// Applies the startup configuration: travel range then dead zone.
  /// @param multi_turn        Enable multi-turn absolute positioning.
  /// @param angle_resolution  Amplification 1..3 (multi-turn only).
  /// @param deadband_counts   Dead-zone width, 0..32.
  /// @param torque_limit      Torque ceiling, 0..1000.
  /// @return True when the servo answered and every step succeeded.
  bool Begin(bool multi_turn, uint8_t angle_resolution,
             uint8_t deadband_counts, uint16_t torque_limit);

  /// Reads one coherent snapshot in a single bus round trip.
  /// @return The snapshot; `valid` is false when the bus did not answer.
  ServoSnapshot ReadSnapshot();

  /// Reads only the absolute position.
  /// @return Signed multi-turn counts, or 0 when the read failed.
  int32_t ReadRawCounts();

  /// Starts a move toward an absolute counts target. A new position command
  /// also releases a tripped overload, which is the hardware's own rule.
  /// @param command Target, speed and acceleration in servo units.
  /// @return True when the command was accepted by the bus.
  bool Move(const MoveCommand& command);

  /// Stops motion by commanding the present position.
  /// @return True when the command was accepted.
  bool Stop();

  /// Writes the dead-zone registers. EEPROM, so this only writes when the
  /// value actually differs.
  /// @param counts Dead-zone width, clamped to 0..32.
  /// @return True on success.
  bool SetDeadband(uint8_t counts);

  /// Selects single-turn or multi-turn absolute positioning.
  ///
  /// Multi-turn is the documented sequence: both angle limits to 0, angle
  /// resolution to the amplification factor, phase BIT4 set, mode left at 0.
  /// Amplification coarsens every step by the same factor, so it is only
  /// worth enabling when the travel genuinely exceeds one servo turn.
  /// @param multi_turn       Enable multi-turn absolute positioning.
  /// @param angle_resolution Amplification 1..3.
  /// @return True on success.
  bool ConfigureRange(bool multi_turn, uint8_t angle_resolution);

  /// Clears a tripped overload by re-commanding the present position.
  /// @return True when the command was accepted.
  bool ClearFault();

  /// Captures the present position as the servo's centre (2048) without
  /// moving the mechanism. This writes the offset register, so the physical
  /// output does not move; only the numbering changes.
  /// @return True on success.
  bool CentreHere();

 private:
  ServoBus& bus_;
};

}  // namespace servo
#endif  // SERVO_CONTROLLER_H
