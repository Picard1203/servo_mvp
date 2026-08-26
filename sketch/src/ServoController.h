#ifndef SERVO_CONTROLLER_H
#define SERVO_CONTROLLER_H

#include <stdint.h>

#include "ServoBus.h"
#include "ServoTypes.h"

namespace servo {

class ServoController {
 public:
  /// Constructs a servo controller bound to the given bus.
  /// @param bus Bus wrapper for the servo.
  explicit ServoController(ServoBus& bus);

  /// Applies startup configuration: travel range, dead zone, and torque limit.
  /// @param multi_turn Enable multi-turn absolute positioning.
  /// @param angle_resolution Amplification 1..3 (multi-turn only).
  /// @param deadband_counts Dead-zone width, 0..32.
  /// @param torque_limit Torque ceiling, 0..1000.
  /// @return True when the servo answered and every step succeeded.
  bool Begin(bool multi_turn, uint8_t angle_resolution,
             uint8_t deadband_counts, uint16_t torque_limit);

  /// Reads one coherent snapshot in a single bus round trip.
  /// @return The snapshot; valid is false when the bus did not answer.
  ServoSnapshot ReadSnapshot();

  /// Reads only the absolute position.
  /// @return Signed multi-turn counts, or 0 when the read failed.
  int32_t ReadRawCounts();

  /// Starts a move toward an absolute counts target.
  /// @param command Target, speed and acceleration in servo units.
  /// @return True when the command was accepted by the bus.
  bool Move(const MoveCommand& command);

  /// Stops motion by commanding the present position.
  /// @return True when the command was accepted.
  bool Stop();

  /// Writes the dead-zone registers.
  /// @param counts Dead-zone width, clamped to 0..32.
  /// @return True on success.
  bool SetDeadband(uint8_t counts);

  /// Selects single-turn or multi-turn absolute positioning.
  /// @param multi_turn Enable multi-turn absolute positioning.
  /// @param angle_resolution Amplification 1..3.
  /// @return True on success.
  bool ConfigureRange(bool multi_turn, uint8_t angle_resolution);

  /// Clears a tripped overload by re-commanding the present position.
  /// @return True when the command was accepted.
  bool ClearFault();

  /// Captures the present position as the servo's centre (2048).
  /// @return True on success.
  bool CentreHere();

  /// Cuts or restores drive torque while electronics stay powered.
  /// @param enabled True to restore drive torque, false to cut it.
  /// @return True when every step the servo answered to succeeded.
  bool SetTorque(bool enabled);

  /// Reads register 0x28 directly.
  /// @return The raw register value (0 or 1), or -1 on failure.
  int ReadTorqueRegister();

 private:
  ServoBus& bus_;
};

}  // namespace servo
#endif  // SERVO_CONTROLLER_H
