"""Single source of truth for live servo state, read atomically."""

from threading import Lock
from time import monotonic
from typing import Optional

from Logger461 import logger

from app.core.exceptions import InvalidReadingError
from app.models.entities import (
    ServoStateView,
    ZeroReference,
)
from app.repositories.abstract.app_state_repository import AppStateRepository
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.zero_repository import ZeroRepository

_ISOLATED_INTENT_KEY = "isolated"


class ServoStateStore:
    """Coordinates lock state, baseline, isolation, and settle timing.

    Attributes:
        _servo (ServoRepository): Servo repository for hardware reads.
        _zeros (ZeroRepository): Zero reference repository for active baseline.
        _settling_seconds (float): Lock settle duration in seconds.
        _isolation_idle_timeout_s (float): Idle duration before auto-isolation.
        _counts_per_turn (int): Encoder counts per full servo turn.
        _counts_per_servo_deg (float): Counts per servo degree ratio.
        _servo_deg_per_output_deg (float): Ratio of servo deg to output deg.
        _servo_direction (int): Commanded motion direction multiplier.
        _lock (Lock): Mutex serializing state access and mutations.
        _locked (bool): Current digital lock engagement state.
        _settle_deadline (float): Monotonic timestamp of settle window expiry.
        _position_verified (bool): True if datum calibration verified.
        _target_deg (Optional[float]): Commanded target angle in output deg.
        _target_stale (bool): True if last target is no longer pursued.
        _isolated_intent (bool): Operator intended motor isolation state.
        _isolated_known (bool): Hardware acknowledged motor isolation state.
    """

    def __init__(self, servo: ServoRepository, zeros: ZeroRepository,
                 app_state: AppStateRepository, settling_seconds: float,
                 counts_per_turn: int, servo_deg_per_output_deg: float,
                 servo_direction: int = 1,
                 isolation_idle_timeout_s: float = 0.0) -> None:
        self._servo: ServoRepository = servo
        self._zeros: ZeroRepository = zeros
        self._settling_seconds: float = settling_seconds
        self._isolation_idle_timeout_s: float = isolation_idle_timeout_s
        self._counts_per_turn: int = counts_per_turn
        self._counts_per_servo_deg: float = counts_per_turn / 360.0
        self._servo_deg_per_output_deg: float = servo_deg_per_output_deg
        self._servo_direction: int = servo_direction
        self._lock: Lock = Lock()
        self._locked: bool = False
        self._settle_deadline: float = 0.0
        self._position_verified: bool = False
        self._target_deg: Optional[float] = None
        self._target_stale: bool = False
        self._isolated_intent: bool = (app_state.get(_ISOLATED_INTENT_KEY) == "1")
        self._isolated_known: bool = False

    def set_locked(self, locked: bool) -> bool:
        """Sets the lock state and starts a settle window on change.

        Args:
            locked (bool): Desired lock state.

        Returns:
            bool: True when the state actually changed.
        """
        with self._lock:
            changed = (locked != self._locked)
            self._locked = locked
            if changed is True:
                self._settle_deadline = monotonic() + self._settling_seconds
            return changed

    def is_locked(self) -> bool:
        """Returns the current lock state.

        Returns:
            bool: True when locked.
        """
        with self._lock:
            return self._locked

    def set_isolated_intent(self, isolated: bool) -> None:
        """Sets the operator intent for motor isolation.

        Args:
            isolated (bool): Desired isolation state.
        """
        with self._lock:
            self._isolated_intent = isolated

    def is_isolated_intent(self) -> bool:
        """Returns the operator current isolation intent.

        Returns:
            bool: True when operator intends motor to be isolated.
        """
        with self._lock:
            return self._isolated_intent

    def set_isolated_known(self, isolated: bool) -> bool:
        """Records that the servo acknowledged an isolation write.

        Args:
            isolated (bool): The acknowledged isolation state.

        Returns:
            bool: True when the state actually changed.
        """
        with self._lock:
            changed = (isolated != self._isolated_known)
            self._isolated_known = isolated
            return changed

    def is_isolated_known(self) -> bool:
        """Returns the acknowledged isolation state shown to operator.

        Returns:
            bool: True once servo confirmed drive torque is cut.
        """
        with self._lock:
            return self._isolated_known

    def mark_position_verified(self) -> None:
        """Marks the position reference as verified after calibration."""
        with self._lock:
            self._position_verified = True

    def is_position_verified(self) -> bool:
        """Returns whether the position reference has been verified.

        Returns:
            bool: True after a successful calibration this power cycle.
        """
        with self._lock:
            return self._position_verified

    def settle_remaining_seconds(self) -> float:
        """Returns seconds left in the settle window (0.0 if none).

        Returns:
            float: Remaining settle time in seconds.
        """
        with self._lock:
            return max(0.0, self._settle_deadline - monotonic())

    def set_target(self, target_deg: float) -> None:
        """Records a newly accepted move target and clears staleness.

        Args:
            target_deg (float): Requested target output angle in degrees.
        """
        with self._lock:
            self._target_deg = target_deg
            self._target_stale = False

    def mark_target_stale(self) -> None:
        """Marks current target as no longer being pursued."""
        with self._lock:
            self._target_stale = True

    def target_state(self) -> tuple[Optional[float], bool]:
        """Returns the current target and whether it is stale.

        Returns:
            tuple[Optional[float], bool]: Target angle and stale flag.
        """
        with self._lock:
            return (self._target_deg, self._target_stale)

    def output_deg_from_counts(self, raw_counts: int) -> float:
        """Converts raw counts to output degrees against the active zero.

        Args:
            raw_counts (int): Absolute encoder counts.

        Returns:
            float: Output angle in degrees.
        """
        return self._to_output_deg(raw_counts, self._zeros.get_active())

    def reachable_output_range_deg(self) -> tuple[float, float]:
        """Returns output angles reachable from current baseline.

        Returns:
            tuple[float, float]: Minimum and maximum reachable output degrees.
        """
        baseline = self._active_counts()
        span = self._counts_per_servo_deg * self._servo_deg_per_output_deg
        low = (0 - baseline) / span
        high = ((self._counts_per_turn - 1) - baseline) / span
        if self._servo_direction < 0:
            low, high = -high, -low
        return (low, high)

    def is_reachable(self, output_deg: float) -> bool:
        """Reports whether a target maps inside the servo count range.

        Args:
            output_deg (float): Target output angle in degrees.

        Returns:
            bool: True when the servo can reach the target count.
        """
        counts = self.counts_from_output_deg(output_deg)
        return 0 <= counts <= (self._counts_per_turn - 1)

    def counts_from_output_deg(self, output_deg: float) -> int:
        """Converts an output angle to absolute encoder counts.

        Args:
            output_deg (float): Output angle in degrees.

        Returns:
            int: Absolute counts target.
        """
        servo_deg = (output_deg * self._servo_deg_per_output_deg
                     * self._servo_direction)
        return self._active_counts() + round(
            servo_deg * self._counts_per_servo_deg)

    def counts_speed_from_output_speed(self, speed_dps: float) -> int:
        """Converts output speed to encoder counts per second.

        Args:
            speed_dps (float): Output degrees per second.

        Returns:
            int: Counts per second (minimum 1).
        """
        servo_dps = speed_dps * self._servo_deg_per_output_deg
        return max(1, round(servo_dps * self._counts_per_servo_deg))

    def snapshot(self) -> ServoStateView:
        """Returns a coherent snapshot of servo, lock and baseline.

        Returns:
            ServoStateView: Atomic state view for API and telemetry.
        """
        reading = self._servo.read_snapshot()
        active = self._zeros.get_active()
        with self._lock:
            locked = self._locked
            settling = (self._settle_deadline > monotonic())
            verified = self._position_verified
            target_deg = self._target_deg
            target_stale = self._target_stale
            isolated = self._isolated_known
        if reading.valid is False:
            logger.warning("servo read failed; position is not known",
                           metadata={"event": "servo.read.failed"},
                           extra={"active_zero": active.name
                                  if active is not None else "factory"})
        have_reading = (reading.valid is True) and (reading.raw_counts is not None)
        output_min_deg, output_max_deg = self.reachable_output_range_deg()
        return ServoStateView(
            output_deg=(round(self._to_output_deg(reading.raw_counts, active),
                              2) if have_reading is True else None),
            servo_deg=(round(self._to_servo_deg(reading.raw_counts, active),
                             2) if have_reading is True else None),
            raw_counts=reading.raw_counts if reading.valid is True else None,
            reading_valid=reading.valid,
            moving=reading.moving if reading.valid is True else None,
            locked=locked,
            settling=settling,
            position_verified=verified,
            active_zero_name=active.name if active is not None else "factory",
            temperature_c=reading.temperature_c if reading.valid is True else None,
            voltage_v=reading.voltage_v if reading.valid is True else None,
            current_a=reading.current_a if reading.valid is True else None,
            torque_kgcm=reading.torque_kgcm if reading.valid is True else None,
            overload=reading.overload if reading.valid is True else None,
            overcurrent=reading.overcurrent if reading.valid is True else None,
            overheat=reading.overheat if reading.valid is True else None,
            voltage_fault=reading.voltage_fault if reading.valid is True else None,
            sensor_fault=reading.sensor_fault if reading.valid is True else None,
            angle_fault=reading.angle_fault if reading.valid is True else None,
            target_deg=target_deg,
            target_stale=target_stale,
            output_min_deg=round(output_min_deg, 2),
            output_max_deg=round(output_max_deg, 2),
            isolated=isolated,
            isolation_idle_timeout_s=self._isolation_idle_timeout_s)

    def current_output_deg(self) -> Optional[float]:
        """Returns current output angle relative to the active zero.

        Returns:
            Optional[float]: Output angle or None if read failed.
        """
        return self.snapshot().output_deg

    def read_counts(self) -> int:
        """Returns the current absolute encoder position in counts.

        Returns:
            int: Current raw encoder counts.

        Raises:
            InvalidReadingError: When the servo did not answer.
        """
        reading = self._servo.read_snapshot()
        if reading.valid is False:
            raise InvalidReadingError(
                "the servo did not answer the position read")
        return reading.raw_counts

    def _baseline_counts(self, active: Optional[ZeroReference]) -> int:
        """Returns baseline in raw counts for a prefetched zero.

        Args:
            active (Optional[ZeroReference]): Active zero reference or None.

        Returns:
            int: Active zero raw counts or center of travel.
        """
        if active is not None:
            return active.raw_counts
        return self._counts_per_turn // 2

    def _active_counts(self) -> int:
        """Returns the active baseline in raw counts.

        Returns:
            int: Active zero raw counts or center of travel.
        """
        return self._baseline_counts(self._zeros.get_active())

    def _to_servo_deg(self, raw_counts: int,
                      active: Optional[ZeroReference]) -> float:
        """Converts counts to servo pre-ratio degrees.

        Args:
            raw_counts (int): Absolute encoder counts.
            active (Optional[ZeroReference]): Active zero reference or None.

        Returns:
            float: Servo shaft angle in degrees.
        """
        return ((raw_counts - self._baseline_counts(active))
                / self._counts_per_servo_deg)

    def _to_output_deg(self, raw_counts: int,
                       active: Optional[ZeroReference]) -> float:
        """Converts counts to output degrees using a prefetched baseline.

        Args:
            raw_counts (int): Absolute encoder counts.
            active (Optional[ZeroReference]): Active zero reference or None.

        Returns:
            float: Output angle in degrees.
        """
        servo_deg = self._to_servo_deg(raw_counts, active)
        return (servo_deg / self._servo_deg_per_output_deg
                * self._servo_direction)
