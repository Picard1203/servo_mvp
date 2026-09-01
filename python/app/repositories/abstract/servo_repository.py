"""Abstract servo access: the seam between simulation and hardware."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.entities import TelemetrySnapshot, TuningRegisters


class ServoRepository(ABC):
    """Contract for reading and commanding the servo (real or simulated)."""

    # No read_raw_counts() here on purpose - see docs/DESIGN_NOTES.md (D2/D9).

    @abstractmethod
    def read_snapshot(self) -> TelemetrySnapshot:
        """Returns the full instantaneous sensory readout.

        Returns:
            TelemetrySnapshot: Position, motion flag, and telemetry.
        """

    @abstractmethod
    def command_move(self, target_counts: int, speed_counts_s: int,
                     acceleration: int) -> bool:
        """Starts a move toward an absolute counts target.

        Args:
            target_counts (int): Absolute encoder counts target.
            speed_counts_s (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter (0-254).

        Returns:
            bool: True when the servo acknowledged the command.
        """

    @abstractmethod
    def command_stop(self) -> bool:
        """Stops motion at the current position.

        Returns:
            bool: True when the servo acknowledged the command.
        """

    @abstractmethod
    def configure_range(self, multi_turn: bool, angle_resolution: int) -> None:
        """Configures the travel-range mode before normal operation.

        Args:
            multi_turn (bool): Enable multi-turn absolute positioning.
            angle_resolution (int): Amplification factor 1..3.
        """

    @abstractmethod
    def set_deadband(self, counts: int) -> None:
        """Configures the servo dead-zone width.

        Args:
            counts (int): Dead-zone width in encoder counts.
        """

    @abstractmethod
    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores drive torque while sensors stay powered.

        Args:
            enabled (bool): True to restore drive torque, false to cut it.

        Returns:
            bool: True when the servo acknowledged the command.
        """

    @abstractmethod
    def read_torque_register(self) -> Optional[int]:
        """Reads the torque-enable register directly.

        Returns:
            Optional[int]: Register value (0 or 1), or None if read failed.
        """

    @abstractmethod
    def read_tuning_registers(self) -> Optional[TuningRegisters]:
        """Reads the position-loop tuning registers directly.

        Returns:
            Optional[TuningRegisters]: The registers, or None if read failed.
        """

    @abstractmethod
    def write_tuning_registers(
            self, position_p: Optional[int] = None,
            position_d: Optional[int] = None,
            position_i: Optional[int] = None,
            min_start_force: Optional[int] = None,
            cw_dead_zone: Optional[int] = None,
            ccw_dead_zone: Optional[int] = None) -> bool:
        """Writes any subset of the position-loop tuning registers directly.

        Args:
            position_p (Optional[int]): P gain, or None to leave it alone.
            position_d (Optional[int]): D gain, or None to leave it alone.
            position_i (Optional[int]): I gain, or None to leave it alone.
            min_start_force (Optional[int]): Minimum start force, or None.
            cw_dead_zone (Optional[int]): CW dead zone, or None.
            ccw_dead_zone (Optional[int]): CCW dead zone, or None.

        Returns:
            bool: True when every requested write was acknowledged.
        """

    @abstractmethod
    def read_present_speed_counts_s(self) -> Optional[int]:
        """Reads the present-speed register directly.

        Returns:
            Optional[int]: Signed counts per second, or None if read failed.
        """
