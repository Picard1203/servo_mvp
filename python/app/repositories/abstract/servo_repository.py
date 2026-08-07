"""Abstract servo access: the seam between simulation and hardware."""

from abc import ABC, abstractmethod

from app.models.entities import TelemetrySnapshot


class ServoRepository(ABC):
    """Contract for reading and commanding the servo (real or simulated)."""

    @abstractmethod
    def read_raw_counts(self) -> int:
        """Returns the absolute encoder position in counts (multi-turn).

        Contract: the value is ABSOLUTE MULTI-TURN - it may exceed
        0..4095 and may be negative. Hardware implementations must
        compose the within-turn reading with the servo's turn counter
        and decode the sign-magnitude wire format correctly (bit 15 is
        the sign bit for position fields; naive parsing shows ~32700
        when crossing below zero).

        Returns:
            Current raw counts.
        """

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
