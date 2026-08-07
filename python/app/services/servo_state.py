"""Single source of truth for live servo state, read atomically.

Owns the digital lock, the active-baseline cache, and the post-lock
settle deadline behind ONE lock, so a state snapshot can never straddle
a concurrent change. Movement commands and telemetry both read through
here, guaranteeing a coherent view.
"""

from threading import Lock
from time import monotonic
from typing import Optional

from app.models.entities import ServoStateView, TelemetrySnapshot
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.zero_repository import ZeroRepository


class ServoStateStore:
    """Coordinates lock state, baseline and settle timing atomically."""

    def __init__(self, servo: ServoRepository, zeros: ZeroRepository,
                 settling_seconds: float, counts_per_turn: int,
                 servo_deg_per_output_deg: float,
                 servo_direction: int = 1) -> None:
        self._servo = servo
        self._zeros = zeros
        self._settling_seconds = settling_seconds
        self._counts_per_turn = counts_per_turn
        self._counts_per_servo_deg = counts_per_turn / 360.0
        self._servo_deg_per_output_deg = servo_deg_per_output_deg
        self._servo_direction = servo_direction
        self._lock = Lock()
        self._locked = False
        self._settle_deadline = 0.0
        self._position_verified = False  # False after every boot

    # ----------------------------------------------------------- locking

    def set_locked(self, locked: bool) -> bool:
        """Sets the lock state and starts a settle window on change.

        Args:
            locked: Desired lock state.

        Returns:
            True when the state actually changed.
        """
        with self._lock:
            changed = locked != self._locked
            self._locked = locked
            if changed:
                self._settle_deadline = monotonic() + self._settling_seconds
            return changed

    def is_locked(self) -> bool:
        """Returns the current lock state.

        Returns:
            True when locked.
        """
        with self._lock:
            return self._locked

    def mark_position_verified(self) -> None:
        """Marks the position reference as verified (after calibration).

        Returns:
            None.
        """
        with self._lock:
            self._position_verified = True

    def is_position_verified(self) -> bool:
        """Returns whether the position reference has been verified.

        Returns:
            True after a successful calibration this power cycle.
        """
        with self._lock:
            return self._position_verified

    def settle_remaining_seconds(self) -> float:
        """Returns seconds left in the settle window (0.0 if none).

        Returns:
            Remaining settle time in seconds.
        """
        with self._lock:
            return max(0.0, self._settle_deadline - monotonic())

    # -------------------------------------------------------- conversions

    def output_deg_from_counts(self, raw_counts: int) -> float:
        """Converts raw counts to output degrees against the active zero.

        Args:
            raw_counts: Absolute encoder counts.

        Returns:
            Output angle in degrees.
        """
        servo_deg = (raw_counts - self._active_counts()) \
            / self._counts_per_servo_deg
        return (servo_deg / self._servo_deg_per_output_deg
                * self._servo_direction)

    def reachable_output_range_deg(self) -> tuple[float, float]:
        """Returns the output angles reachable from the current baseline.

        The servo accepts counts 0..counts_per_turn-1 and clamps silently
        outside that, so the usable angle window depends on where the datum
        was captured. A datum near an end of travel makes half the nominal
        range unreachable, which is worth being able to state plainly.

        Returns:
            Tuple of (minimum, maximum) output degrees.
        """
        baseline = self._active_counts()
        span = self._counts_per_servo_deg * self._servo_deg_per_output_deg
        low = (0 - baseline) / span
        high = ((self._counts_per_turn - 1) - baseline) / span
        if self._servo_direction < 0:
            low, high = -high, -low
        return (low, high)

    def is_reachable(self, output_deg: float) -> bool:
        """Reports whether a target maps inside the servo's count range.

        Args:
            output_deg: Target output angle.

        Returns:
            True when the servo can actually reach it.
        """
        counts = self.counts_from_output_deg(output_deg)
        return 0 <= counts <= self._counts_per_turn - 1

    def counts_from_output_deg(self, output_deg: float) -> int:
        """Converts an output angle to absolute encoder counts.

        Args:
            output_deg: Output angle in degrees.

        Returns:
            Absolute counts target.
        """
        servo_deg = (output_deg * self._servo_deg_per_output_deg
                     * self._servo_direction)
        return self._active_counts() + round(
            servo_deg * self._counts_per_servo_deg)

    def counts_speed_from_output_speed(self, speed_dps: float) -> int:
        """Converts output speed to encoder counts per second.

        Args:
            speed_dps: Output degrees per second.

        Returns:
            Counts per second (minimum 1).
        """
        servo_dps = speed_dps * self._servo_deg_per_output_deg
        return max(1, round(servo_dps * self._counts_per_servo_deg))

    # ------------------------------------------------------------- reads

    def snapshot(self) -> ServoStateView:
        """Returns a coherent snapshot of servo, lock and baseline.

        Returns:
            The atomic state view for the API and telemetry.
        """
        reading = self._servo.read_snapshot()
        active = self._zeros.get_active()
        with self._lock:
            locked = self._locked
            settling = self._settle_deadline > monotonic()
            verified = self._position_verified
        return ServoStateView(
            output_deg=round(self._to_output_deg(reading.raw_counts, active),
                             2),
            moving=reading.moving,
            locked=locked,
            settling=settling,
            position_verified=verified,
            active_zero_name=active.name if active is not None else "factory",
            temperature_c=reading.temperature_c,
            voltage_v=reading.voltage_v,
            current_a=reading.current_a,
            torque_kgcm=reading.torque_kgcm,
            overload=reading.overload,
            overcurrent=reading.overcurrent,
            overheat=reading.overheat,
            voltage_fault=reading.voltage_fault,
            sensor_fault=reading.sensor_fault,
            angle_fault=reading.angle_fault)

    def current_output_deg(self) -> float:
        """Returns the current output angle relative to the active zero.

        Returns:
            Output angle in degrees.
        """
        return self.output_deg_from_counts(self._servo.read_raw_counts())

    def read_raw_counts(self) -> int:
        """Returns the current absolute encoder position in counts.

        Returns:
            Current raw counts.
        """
        return self._servo.read_raw_counts()

    # ---------------------------------------------------------- internals

    def _active_counts(self) -> int:
        """Returns the active baseline in raw counts.

        With no zero captured the baseline is the MIDDLE of the servo's
        travel, not count 0. Zero would be the wrong default: the servo
        clamps below count 0, so a baseline there puts the entire negative
        half of the range out of reach before the operator has done
        anything. The middle makes the nominal window symmetric and
        reachable from a cold start.

        Returns:
            Active zero raw counts, or the centre of travel.
        """
        active = self._zeros.get_active()
        if active is not None:
            return active.raw_counts
        return self._counts_per_turn // 2

    def _to_output_deg(self, raw_counts: int, active) -> float:
        """Converts counts to output degrees using a prefetched baseline.

        Args:
            raw_counts: Absolute encoder counts.
            active: The active ZeroReference, or None.

        Returns:
            Output angle in degrees.
        """
        base = active.raw_counts if active is not None else 0
        servo_deg = (raw_counts - base) / self._counts_per_servo_deg
        return servo_deg / self._servo_deg_per_output_deg
