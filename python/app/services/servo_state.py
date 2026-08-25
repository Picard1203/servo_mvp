"""Single source of truth for live servo state, read atomically.

Owns the digital lock, the active-baseline cache, and the post-lock
settle deadline behind ONE lock, so a state snapshot can never straddle
a concurrent change. Movement commands and telemetry both read through
here, guaranteeing a coherent view.
"""

from threading import Lock
from time import monotonic
from typing import Optional

from Logger461 import logger

from app.core.exceptions import InvalidReadingError
from app.models.entities import (ServoStateView, TelemetrySnapshot,
                                 ZeroReference)
from app.repositories.abstract.app_state_repository import AppStateRepository
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.zero_repository import ZeroRepository

_ISOLATED_INTENT_KEY = "isolated"


class ServoStateStore:
    """Coordinates lock state, baseline, isolation and settle timing
    atomically."""

    def __init__(self, servo: ServoRepository, zeros: ZeroRepository,
                 app_state: AppStateRepository, settling_seconds: float,
                 counts_per_turn: int, servo_deg_per_output_deg: float,
                 servo_direction: int = 1,
                 isolation_idle_timeout_s: float = 0.0) -> None:
        self._servo = servo
        self._zeros = zeros
        self._settling_seconds = settling_seconds
        self._isolation_idle_timeout_s = isolation_idle_timeout_s
        self._counts_per_turn = counts_per_turn
        self._counts_per_servo_deg = counts_per_turn / 360.0
        self._servo_deg_per_output_deg = servo_deg_per_output_deg
        self._servo_direction = servo_direction
        self._lock = Lock()
        self._locked = False
        self._settle_deadline = 0.0
        self._position_verified = False  # False after every boot
        self._target_deg: Optional[float] = None  # None until a move is
        # commanded this power cycle - never fabricated as 0.0 (D16 shape).
        self._target_stale = False  # True after stop(); cleared by the
        # next accepted move, never inferred from `moving` (a second
        # definition of the same fact is exactly what D9/D10 cost).

        # Loaded synchronously, here, so the very first move request this
        # process ever serves already refuses correctly (ADR-0010) - no
        # ordering dependency on IsolationService having run yet. Never
        # trust the servo's own torque state across a reboot instead: the
        # MCU's own Begin() unconditionally re-enables torque at every
        # boot, so only the database (operator intent) is authoritative.
        self._isolated_intent = app_state.get(_ISOLATED_INTENT_KEY) == "1"
        # Acknowledged hardware state. Always starts False, regardless of
        # intent: reporting isolated=True before the servo has actually
        # confirmed the write would be a false safety claim - the worst
        # failure this feature can produce. IsolationService's reconciler
        # is what advances this once the servo acks.
        self._isolated_known = False

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

    # --------------------------------------------------------- isolation

    def set_isolated_intent(self, isolated: bool) -> None:
        """Sets the operator's intent for motor isolation (R2).

        Called only by IsolationService, which is the sole owner of
        persisting this to the database - this method only updates the
        in-memory value used by the move-refusal gate.

        Args:
            isolated: Desired isolation state.

        Returns:
            None.
        """
        with self._lock:
            self._isolated_intent = isolated

    def is_isolated_intent(self) -> bool:
        """Returns the operator's current isolation intent.

        This is what MotionService.move_to() gates on - intent, not
        acknowledged hardware state - so a move is refused from the very
        first request this process serves, before any reconciler tick has
        had a chance to run.

        Returns:
            True when the operator intends the motor to be isolated.
        """
        with self._lock:
            return self._isolated_intent

    def set_isolated_known(self, isolated: bool) -> bool:
        """Records that the servo has ACKNOWLEDGED an isolation write.

        Called only by IsolationService's reconciler, only after a
        successful command_torque acknowledgement. Never call this on
        intent alone - see the class docstring on _isolated_known.

        Args:
            isolated: The acknowledged isolation state.

        Returns:
            True when the state actually changed.
        """
        with self._lock:
            changed = isolated != self._isolated_known
            self._isolated_known = isolated
            return changed

    def is_isolated_known(self) -> bool:
        """Returns the acknowledged isolation state shown to the operator.

        Returns:
            True only once the servo has confirmed drive torque is cut.
        """
        with self._lock:
            return self._isolated_known

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

    # ------------------------------------------------------------- target

    def set_target(self, target_deg: float) -> None:
        """Records a newly accepted move's target and clears staleness.

        Called once, from an accepted move_to() - never from the fine-
        approach overshoot, which commands past the requested angle and
        must not be mistaken for a new target (twin-path hazard: the same
        shape as D9's two baselines and D10's two loggers).

        Args:
            target_deg: The angle the operator asked for.

        Returns:
            None.
        """
        with self._lock:
            self._target_deg = target_deg
            self._target_stale = False

    def mark_target_stale(self) -> None:
        """Marks the current target as no longer being pursued.

        Called on stop(). The target is kept, not cleared - "asked for
        45, stopped at 27" is the supposed-vs-actual reading this feature
        exists for, and it matters most at the moment a move is abandoned.

        Returns:
            None.
        """
        with self._lock:
            self._target_stale = True

    def target_state(self) -> tuple[Optional[float], bool]:
        """Returns the current target and whether it is stale.

        Returns:
            Tuple of (target_deg or None if never commanded, is_stale).
        """
        with self._lock:
            return (self._target_deg, self._target_stale)

    # -------------------------------------------------------- conversions

    def output_deg_from_counts(self, raw_counts: int) -> float:
        """Converts raw counts to output degrees against the active zero.

        Args:
            raw_counts: Absolute encoder counts.

        Returns:
            Output angle in degrees.
        """
        return self._to_output_deg(raw_counts, self._zeros.get_active())

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
            target_deg = self._target_deg
            target_stale = self._target_stale
            isolated = self._isolated_known
        if not reading.valid:
            logger.warning("servo read failed; position is not known",
                           metadata={"event": "servo.read.failed"},
                           extra={"active_zero": active.name
                                  if active is not None else "factory"})
        have_reading = reading.valid is True and reading.raw_counts is not None
        output_min_deg, output_max_deg = self.reachable_output_range_deg()
        return ServoStateView(
            output_deg=(round(self._to_output_deg(reading.raw_counts, active),
                              2) if have_reading else None),
            servo_deg=(round(self._to_servo_deg(reading.raw_counts, active),
                             2) if have_reading else None),
            raw_counts=reading.raw_counts if reading.valid else None,
            reading_valid=reading.valid,
            moving=reading.moving if reading.valid else None,
            locked=locked,
            settling=settling,
            position_verified=verified,
            active_zero_name=active.name if active is not None else "factory",
            temperature_c=reading.temperature_c if reading.valid else None,
            voltage_v=reading.voltage_v if reading.valid else None,
            current_a=reading.current_a if reading.valid else None,
            torque_kgcm=reading.torque_kgcm if reading.valid else None,
            overload=reading.overload if reading.valid else None,
            overcurrent=reading.overcurrent if reading.valid else None,
            overheat=reading.overheat if reading.valid else None,
            voltage_fault=reading.voltage_fault if reading.valid else None,
            sensor_fault=reading.sensor_fault if reading.valid else None,
            angle_fault=reading.angle_fault if reading.valid else None,
            target_deg=target_deg,
            target_stale=target_stale,
            output_min_deg=round(output_min_deg, 2),
            output_max_deg=round(output_max_deg, 2),
            isolated=isolated,
            isolation_idle_timeout_s=self._isolation_idle_timeout_s)

    def current_output_deg(self) -> Optional[float]:
        """Returns the current output angle relative to the active zero.

        Returns:
            Output angle in degrees, or None when the read failed.
        """
        return self.snapshot().output_deg

    def read_counts(self) -> int:
        """Returns the current absolute encoder position in counts.

        Raises:
            InvalidReadingError: When the servo did not answer. Callers
                get no number rather than a fabricated zero.

        Returns:
            Current raw counts.
        """
        reading = self._servo.read_snapshot()
        if not reading.valid:
            raise InvalidReadingError(
                "the servo did not answer the position read")
        return reading.raw_counts

    # ---------------------------------------------------------- internals

    def _baseline_counts(self, active: Optional[ZeroReference]) -> int:
        """Returns the baseline in raw counts for a prefetched zero.

        With no zero captured the baseline is the MIDDLE of the servo's
        travel, not count 0. Zero would be the wrong default: the servo
        clamps below count 0, so a baseline there puts the entire negative
        half of the range out of reach before the operator has done
        anything. The middle makes the nominal window symmetric and
        reachable from a cold start.

        This is the ONLY definition of the baseline. It used to be stated
        twice - correctly here, and as a bare 0 in the conversion the
        snapshot used - so the display and the motion path disagreed by
        half a turn. On 7 August 2026 that sent the mechanism 212.7 deg
        on a command of 90.

        Args:
            active: The active ZeroReference, or None.

        Returns:
            Active zero raw counts, or the centre of travel.
        """
        if active is not None:
            return active.raw_counts
        return self._counts_per_turn // 2

    def _active_counts(self) -> int:
        """Returns the active baseline in raw counts.

        Returns:
            Active zero raw counts, or the centre of travel.
        """
        return self._baseline_counts(self._zeros.get_active())

    def _to_servo_deg(self, raw_counts: int,
                      active: Optional[ZeroReference]) -> float:
        """Converts counts to the servo's own (pre-ratio) degrees.

        Baseline-relative, same zero point as output degrees, just before
        the 44:30 belt division - this is the ONLY place that division
        happens. output_deg is derived from this, not computed a second
        way (see _to_output_deg): a second definition of one conversion
        is what sent the mechanism 212.7 deg on a command of 90 (D9).

        Args:
            raw_counts: Absolute encoder counts.
            active: The active ZeroReference, or None.

        Returns:
            Servo shaft angle in degrees, relative to the active baseline.
        """
        return ((raw_counts - self._baseline_counts(active))
                / self._counts_per_servo_deg)

    def _to_output_deg(self, raw_counts: int,
                       active: Optional[ZeroReference]) -> float:
        """Converts counts to output degrees using a prefetched baseline.

        Args:
            raw_counts: Absolute encoder counts.
            active: The active ZeroReference, or None.

        Returns:
            Output angle in degrees.
        """
        servo_deg = self._to_servo_deg(raw_counts, active)
        return (servo_deg / self._servo_deg_per_output_deg
                * self._servo_direction)
