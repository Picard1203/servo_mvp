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

  /// Applies startup configuration: travel range, dead zone, torque limit,
  /// and minimum start force.
  /// @param multi_turn Enable multi-turn absolute positioning.
  /// @param angle_resolution Amplification 1..3 (multi-turn only).
  /// @param deadband_counts Dead-zone width, 0..32.
  /// @param torque_limit Torque ceiling, 0..1000.
  /// @param min_start_force Minimum PWM force before a move begins, 0..1000.
  /// @return True when the servo answered and every step succeeded.
  bool Begin(bool multi_turn, uint8_t angle_resolution,
             uint8_t deadband_counts, uint16_t torque_limit,
             uint16_t min_start_force);

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

  /// Writes the minimum start force register.
  /// @param force Minimum PWM force before a move begins, 0..1000.
  /// @return True on success.
  bool SetMinStartForce(uint16_t force);

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

  /// Reads the position-loop tuning registers directly (0x15-0x1B).
  /// @return The snapshot; valid is false when any read failed.
  TuningSnapshot ReadTuningRegisters();

  /// Writes any subset of the position-loop tuning registers (0x15-0x1B).
  /// @param p CW/CCW-shared P gain, or -1 to leave it alone.
  /// @param d CW/CCW-shared D gain, or -1 to leave it alone.
  /// @param i CW/CCW-shared I gain, or -1 to leave it alone.
  /// @param min_start_force Minimum start force, or -1 to leave it alone.
  /// @param cw CW dead zone, or -1 to leave it alone.
  /// @param ccw CCW dead zone, or -1 to leave it alone.
  /// @return True when every requested write succeeded.
  bool WriteTuningRegisters(int16_t p, int16_t d, int16_t i,
                            int16_t min_start_force, int16_t cw,
                            int16_t ccw);

  /// Reads register 0x3A directly.
  /// @return Signed counts per second, or 0 on failure.
  int32_t ReadPresentSpeed();

 private:
  ServoBus& bus_;
};

}  // namespace servo
#endif  // SERVO_CONTROLLER_H
