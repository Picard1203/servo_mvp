"""Abstract servo access: the seam between simulation and hardware."""

from abc import ABC, abstractmethod

from app.models.entities import TelemetrySnapshot


class ServoRepository(ABC):
    """Contract for reading and commanding the servo (real or simulated)."""

    # There is deliberately NO read_raw_counts() on this contract.
    #
    # It returned a bare int, so a failed read arrived as 0 - identical
    # to a genuine reading at the bottom of travel, and the snapshot's
    # `valid` flag was thrown away to produce it. Every caller must take
    # a snapshot and decide what to do when it is invalid. Guarding one
    # call site fixes today; removing the method fixes every call site
    # that will ever exist.

    @abstractmethod
    def read_snapshot(self) -> TelemetrySnapshot:
        """Returns the full instantaneous sensory readout.

        Returns:
            Position, motion flag and telemetry.
        """

    @abstractmethod
    def command_move(self, target_counts: int, speed_counts_s: int,
                     acceleration: int) -> None:
        """Starts a move toward an absolute counts target.

        A new position command also clears a tripped overload fault
        (hardware semantics: overload de-rate is released by the next
        position command).

        Args:
            target_counts: Absolute encoder counts target.
            speed_counts_s: Speed in counts per second.
            acceleration: Servo acceleration parameter (native WritePosEx
                units, 0-254; 0 = maximum).

        Returns:
            None.
        """

    @abstractmethod
    def command_stop(self) -> None:
        """Stops motion at the current position.

        Returns:
            None.
        """

    @abstractmethod
    def configure_range(self, multi_turn: bool, angle_resolution: int) -> None:
        """Configures the travel-range mode before normal operation.

        With multi_turn False the servo stays in its factory single-turn
        window (0..4095), which is all that is needed while the configured
        travel fits inside one servo turn - the case for a +/-90 deg output
        window (264 servo deg = 3004 counts).

        With multi_turn True the hardware path applies the multi-turn
        absolute sequence: unlock EEPROM, both angle limits to 0, angle
        resolution to the amplification factor, phase BIT4 set, mode left
        at 0, re-lock. Note that amplification coarsens every step by the
        same factor, so it is only worth enabling when the window genuinely
        exceeds one servo turn.

        Args:
            multi_turn: Enable multi-turn absolute positioning.
            angle_resolution: Amplification factor 1..3 (multi-turn only).

        Returns:
            None.
        """

    @abstractmethod
    def set_deadband(self, counts: int) -> None:
        """Configures the servo's dead-zone width.

        The dead zone is how close to the exact target the servo
        considers itself arrived. Hardware implementations write the
        servo's CW/CCW dead-zone registers in sprint 2.

        Args:
            counts: Dead-zone width in encoder counts.

        Returns:
            None.
        """

    @abstractmethod
    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores drive torque while sensors stay powered (R2).

        The return value is load-bearing, unlike every other command here:
        callers must never report isolation engaged or cleared on a write
        the servo did not actually acknowledge, since that would claim the
        motor is safe (or free to move) when it may not be.

        Args:
            enabled: True to restore drive torque, false to cut it.

        Returns:
            True when the servo acknowledged the command.
        """
