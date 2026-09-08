"""Movement orchestration: lock gate, settle-wait, and fault recovery."""

import sqlite3
from threading import Thread
from time import monotonic, sleep
from typing import Optional

from Logger461 import logger

from app.core.config import Settings
from app.core.events import EventService
from app.core.exceptions import (
    CommandNotAcknowledgedError,
    IsolatedError,
    LockedAndIsolatedError,
    LockedError,
    MovingError,
    OutOfTravelError,
    StepError,
)
from app.repositories.abstract.servo_repository import ServoRepository
from app.services.servo_state import ServoStateStore

# One encoder count in output degrees. Two readings closer together than
# this are the same position as far as the servo can express it.
_COUNT_EPSILON_DEG = 0.061


class MotionService:
    """Validates and executes movement commands in output-degree space.

    Attributes:
        _servo (ServoRepository): Servo repository for movement commands.
        _state (ServoStateStore): Shared servo state store.
        _events (EventService): Event service for recording audit events.
        _settings (Settings): Application configuration settings.
        _move_generation (int): Counter bumped on each dispatched move.
        _fine_approach_thread (Optional[Thread]): Most recently spawned
            fine-approach worker thread.
    """

    def __init__(self, servo: ServoRepository, state: ServoStateStore,
                 events: EventService, settings: Settings) -> None:
        self._servo: ServoRepository = servo
        self._state: ServoStateStore = state
        self._events: EventService = events
        self._settings: Settings = settings
        self._move_generation: int = 0
        self._fine_approach_thread: Optional[Thread] = None

    def join_fine_approach(self, timeout: float = 2.0) -> None:
        """Waits for the most recent fine-approach thread to finish.

        Args:
            timeout (float): Maximum seconds to wait.
        """
        if self._fine_approach_thread is not None:
            self._fine_approach_thread.join(timeout=timeout)
            self._fine_approach_thread = None

    def move_to(self, target_deg: float,
                acceleration: Optional[int] = None) -> None:
        """Moves to an output angle relative to the datum.

        Args:
            target_deg (float): Target output angle in degrees.
            acceleration (Optional[int]): Acceleration parameter (0-254).

        Raises:
            StepError: If angle violates configured step size.
            LockedAndIsolatedError: If lock and isolation are both active.
            LockedError: If the digital lock is engaged.
            IsolatedError: If the motor is isolated.
        """
        self._validate_step(target_deg)
        self._validate_reachable(target_deg)
        target_counts = self._state.counts_from_output_deg(target_deg)
        self._command(target_deg, target_counts, acceleration)

    def move_to_counts(self, target_counts: int,
                       acceleration: Optional[int] = None) -> None:
        """Moves directly to an absolute encoder position.

        Args:
            target_counts (int): Absolute encoder counts to move to.
            acceleration (Optional[int]): Acceleration parameter (0-254).

        Raises:
            LockedAndIsolatedError: If lock and isolation are both active.
            LockedError: If the digital lock is engaged.
            IsolatedError: If the motor is isolated.
        """
        target_deg = self._state.output_deg_from_counts(target_counts)
        self._command(target_deg, target_counts, acceleration)

    def _command(self, target_deg: float, target_counts: int,
                acceleration: Optional[int]) -> None:
        """Gates, settle-waits, and dispatches a move shared by both entry points.

        Args:
            target_deg (float): Output angle for gating and display.
            target_counts (int): Absolute encoder counts to command.
            acceleration (Optional[int]): Acceleration parameter (0-254).

        Raises:
            LockedAndIsolatedError: If lock and isolation are both active.
            LockedError: If the digital lock is engaged.
            IsolatedError: If the motor is isolated.
        """
        if acceleration is None:
            acceleration = self._settings.default_acceleration
        locked = self._state.is_locked()
        isolated = self._state.is_isolated_intent()
        if (locked is True) and (isolated is True):
            self._events.record("servo.move.rejected",
                                "move rejected: locked and isolated",
                                {"target_deg": target_deg})
            raise LockedAndIsolatedError(
                "servo is locked and motor is isolated",
                metadata={"target_deg": target_deg})
        if locked is True:
            self._events.record("servo.move.rejected",
                                "move rejected: locked",
                                {"target_deg": target_deg})
            raise LockedError("servo is locked",
                              metadata={"target_deg": target_deg})
        if isolated is True:
            self._events.record("servo.move.rejected",
                                "move rejected: isolated",
                                {"target_deg": target_deg})
            raise IsolatedError("motor is isolated",
                               metadata={"target_deg": target_deg})

        self._await_settle()

        start_deg = self._state.current_output_deg()
        speed_counts = self._state.counts_speed_from_output_speed(
            self._settings.default_speed_dps)

        self._state.set_target(target_deg)

        from_deg = round(start_deg, 2) if start_deg is not None else None

        self._move_generation += 1
        generation = self._move_generation

        if self._needs_fine_approach(start_deg, target_deg) is True:
            # The side the arm arrives from decides where it lands: the
            # wrong side misses by 0.45-0.67 deg, the right side by
            # 0.03-0.16 (60 trials, p<=0.005 for each sign). Deriving it
            # from the direction of travel - which is what this did - let
            # the starting position decide the arrival side, so the same
            # commanded angle landed somewhere different depending on
            # where the move began. Anchoring it to the target's own sign
            # instead means the overshoot always sits away from the datum
            # and the final leg always travels toward it, whatever the
            # move's own direction was.
            direction = 1 if target_deg > 0 else -1
            # Marked here, not inside the thread: between accepting the
            # move and the thread starting there would otherwise be a
            # window where the arm still reads as finished.
            self._state.set_positioning(True)
            self._fine_approach_thread = Thread(
                target=self._fine_approach,
                args=(generation, target_deg, target_counts, speed_counts,
                      acceleration, direction, from_deg),
                daemon=True)
            self._fine_approach_thread.start()
            return

        acked = self._servo.command_move(target_counts, speed_counts,
                                         acceleration)
        if acked is False:
            self._raise_not_acknowledged(
                "servo.move.failed",
                f"move to {target_deg:.2f} deg was not acknowledged",
                {"target_deg": target_deg})
        self._record_accepted(target_deg, from_deg, acceleration)

    def _record_accepted(self, target_deg: float, from_deg: Optional[float],
                         acceleration: int) -> None:
        """Records the single 'move accepted' event and its log line.

        Args:
            target_deg (float): Output angle the move was accepted for.
            from_deg (Optional[float]): Output angle the move started from.
            acceleration (int): Acceleration parameter used.
        """
        self._events.record("servo.move.accepted",
                            f"move to {target_deg:.2f} deg",
                            {"from_deg": from_deg,
                             "to_deg": target_deg})
        logger.info("move accepted",
                    metadata={"event": "servo.move.accepted",
                              "from_deg": from_deg},
                    extra={"to_deg": target_deg,
                           "speed_dps": self._settings.default_speed_dps,
                           "acceleration": acceleration})

    def stop(self) -> None:
        """Stops the current move at the present position.

        Raises:
            CommandNotAcknowledgedError: If the servo did not acknowledge.
        """
        acked = self._servo.command_stop()
        if acked is False:
            self._raise_not_acknowledged(
                "servo.stop.failed", "stop was not acknowledged", {})
        self._state.mark_target_stale()
        deg = self._state.current_output_deg()
        at_deg = round(deg, 2) if deg is not None else None
        self._events.record("servo.stop", "stop commanded",
                            {"at_deg": at_deg})
        logger.info("stop commanded",
                    metadata={"event": "servo.stop"},
                    extra={"at_deg": at_deg})

    def set_lock(self, locked: bool) -> None:
        """Changes the digital lock, honoring the optional move guard.

        Args:
            locked (bool): Desired digital lock state.

        Raises:
            MovingError: If configured to guard and move is in progress.
        """
        if ((self._settings.guard_move_to_lock is True)
                and (self._servo.read_snapshot().moving is True)):
            raise MovingError("cannot change lock while moving")
        if self._state.set_locked(locked) is True:
            event = "servo.lock.engaged" if locked is True else "servo.lock.released"
            message = "lock engaged" if locked is True else "lock released"
            self._events.record(event, message)
            logger.info(message, metadata={"event": event})

    def recover(self) -> None:
        """Clears a tripped overload fault by re-commanding the position.

        Raises:
            InvalidReadingError: When current position is unknown.
            CommandNotAcknowledgedError: If the servo did not acknowledge.
        """
        counts = self._state.read_counts()
        acked = self._servo.command_move(
            counts, self._state.counts_speed_from_output_speed(
                self._settings.default_speed_dps),
            self._settings.default_acceleration)
        if acked is False:
            self._raise_not_acknowledged(
                "servo.recover.failed", "recover was not acknowledged",
                {"at_counts": counts})
        self._events.record("servo.fault.recovered",
                            "overload fault cleared by re-command", {})
        logger.info("overload fault cleared by re-command",
                    metadata={"event": "servo.fault.recovered"},
                    extra={"at_counts": counts})

    def _raise_not_acknowledged(self, event: str, message: str,
                                metadata: dict) -> None:
        """Records and raises a non-acknowledgement, never a false success.

        Args:
            event (str): Event name for the audit log and event stream.
            message (str): Human-readable failure message.
            metadata (dict): Structured context for both.

        Raises:
            CommandNotAcknowledgedError: Always.
        """
        self._record_failure(event, message, metadata)
        raise CommandNotAcknowledgedError(message, metadata=metadata)

    def _record_failure(self, event: str, message: str,
                        metadata: dict) -> None:
        """Records a failure event and logs it at error level.

        Args:
            event (str): Event name for the audit log and event stream.
            message (str): Human-readable failure message.
            metadata (dict): Structured context for both.
        """
        self._events.record(event, message, metadata)
        logger.error(message, metadata={"event": event}, extra=metadata)

    def _needs_fine_approach(self, start_deg: Optional[float],
                             target_deg: float) -> bool:
        """Decides whether the anti-backlash approach applies.

        Args:
            start_deg (Optional[float]): Current output angle, or None.
            target_deg (float): Requested output angle.

        Returns:
            bool: True when enabled and the target differs from the start.
        """
        if start_deg is None:
            return False
        return ((self._settings.fine_approach_enabled is True)
                and (target_deg != start_deg))

    def _fine_approach(self, generation: int, target_deg: float,
                       target_counts: int, speed_counts: int,
                       acceleration: int, direction: int,
                       from_deg: Optional[float]) -> None:
        """Runs the consistent-direction approach, then verifies it arrived.

        The approach itself is two legs - overshoot away from the datum,
        then a final leg back toward it. What follows is the part that was
        missing: reading the position back and correcting it. Without that,
        this reported a move as done once the servo acknowledged the
        command, whether or not the arm ever got there, and it routinely
        stops three counts short.

        Args:
            generation (int): Move generation this thread was started for.
            target_deg (float): Requested output angle.
            target_counts (int): Final absolute counts target.
            speed_counts (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter.
            direction (int): +1 when the target is above the datum, -1 below.
            from_deg (Optional[float]): Output angle the move started from.
        """
        try:
            aim_deg = target_deg
            aim_counts = target_counts
            corrections = 0
            while True:
                arrived = self._approach_once(
                    generation, target_deg, aim_deg, aim_counts,
                    speed_counts, acceleration, direction, from_deg,
                    is_first_leg=(corrections == 0))
                if arrived is False:
                    return
                landed_deg = self._wait_until_landed()
                if landed_deg is None:
                    # ADR-0008: a failed read is unknown, never a number.
                    # Correcting against an invented position is how a bad
                    # read becomes a real, commanded 61 deg swing.
                    self._record_failure(
                        "servo.move.failed",
                        f"could not confirm arrival at {target_deg:.2f} deg: "
                        "the servo did not answer a position read",
                        {"target_deg": target_deg, "leg": "verify"})
                    return
                residual = landed_deg - target_deg
                if abs(residual) <= self._settings.fine_approach_gate_deg:
                    self._events.record(
                        "servo.move.arrived",
                        f"arrived at {target_deg:.2f} deg",
                        {"landed_deg": round(landed_deg, 2),
                         "residual_deg": round(residual, 2),
                         "corrections": corrections})
                    return
                if abs(residual) > (
                        self._settings.fine_approach_max_correction_deg):
                    # Too far out to be a miss. Report it; never drive it.
                    self._record_failure(
                        "servo.move.failed",
                        f"stopped {abs(residual):.2f} deg from "
                        f"{target_deg:.2f} deg, too far to correct safely",
                        {"target_deg": target_deg,
                         "landed_deg": round(landed_deg, 2),
                         "residual_deg": round(residual, 2),
                         "leg": "verify"})
                    return
                if corrections >= self._settings.fine_approach_max_corrections:
                    self._record_failure(
                        "servo.move.failed",
                        f"stopped {abs(residual):.2f} deg short of "
                        f"{target_deg:.2f} deg after {corrections} "
                        "corrections",
                        {"target_deg": target_deg,
                         "landed_deg": round(landed_deg, 2),
                         "residual_deg": round(residual, 2),
                         "corrections": corrections, "leg": "verify"})
                    return
                # Correct the aim, not the target. Re-deriving the aim from
                # the target each round discards where it last aimed, and
                # against a servo that lands where it is aimed that just
                # flips the error's sign forever (measured: 45.18, 44.82,
                # 45.18, 44.82). Carrying the aim forward converges against
                # that and against a fixed offset alike.
                aim_deg = aim_deg - residual
                aim_counts = self._state.counts_from_output_deg(aim_deg)
                corrections += 1
        except (sqlite3.OperationalError, ValueError):
            logger.exception(
                "fine approach failed",
                metadata={"event": "servo.move.fine_approach_error"})
        finally:
            self._state.set_positioning(False)

    def _approach_once(self, generation: int, target_deg: float,
                       aim_deg: float, aim_counts: int, speed_counts: int,
                       acceleration: int, direction: int,
                       from_deg: Optional[float],
                       is_first_leg: bool) -> bool:
        """Runs one overshoot-then-final-leg approach at a given aim.

        Args:
            generation (int): Move generation this thread was started for.
            target_deg (float): The angle the operator asked for, for events.
            aim_deg (float): Angle to aim at, which is the target on the
                first pass and a corrected value afterwards.
            aim_counts (int): `aim_deg` in absolute counts.
            speed_counts (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter.
            direction (int): +1 when the target is above the datum, -1 below.
            from_deg (Optional[float]): Angle the move started from.
            is_first_leg (bool): True on the operator's own move, False on a
                correction - only the first one is recorded as accepted.

        Returns:
            bool: True when both legs were acknowledged and the approach was
                neither superseded nor aborted.
        """
        requested_overshoot_deg = (
            aim_deg + direction * self._settings.fine_approach_overshoot_deg)
        low_deg, high_deg = self._state.reachable_output_range_deg()
        overshoot_deg = min(max(requested_overshoot_deg, low_deg), high_deg)
        overshoot_clamped = overshoot_deg != requested_overshoot_deg
        overshoot_counts = self._state.counts_from_output_deg(overshoot_deg)
        overshoot_acked = self._servo.command_move(
            overshoot_counts, speed_counts, acceleration)
        if overshoot_acked is False:
            self._record_failure(
                "servo.move.failed",
                f"fine approach overshoot leg to {overshoot_deg:.2f} deg "
                "was not acknowledged",
                {"target_deg": target_deg, "leg": "overshoot"})
            return False
        if is_first_leg is True:
            self._record_accepted(target_deg, from_deg, acceleration)
        start_snapshot = self._servo.read_snapshot()
        wait_start = monotonic()
        deadline = wait_start + self._settings.fine_approach_timeout_seconds
        is_moving = True
        while (monotonic() < deadline) and (is_moving is True):
            sleep(0.05)
            is_moving = (self._servo.read_snapshot().moving is True)
        wait_elapsed_s = monotonic() - wait_start
        if generation != self._move_generation:
            logger.debug("fine approach: superseded, final leg skipped",
                         metadata={"event": "servo.move.fine_approach"})
            return False
        if self._state.is_isolated_intent() is True:
            logger.debug("fine approach: isolated, final leg skipped",
                         metadata={"event": "servo.move.fine_approach"})
            return False
        position_at_final_leg_deg = self._state.current_output_deg()
        final_speed_counts = speed_counts
        if self._settings.fine_approach_final_speed_dps is not None:
            final_speed_counts = (
                self._state.counts_speed_from_output_speed(
                    self._settings.fine_approach_final_speed_dps))
        final_acceleration = acceleration
        if self._settings.fine_approach_final_acceleration is not None:
            final_acceleration = (
                self._settings.fine_approach_final_acceleration)
        final_acked = self._servo.command_move(
            aim_counts, final_speed_counts, final_acceleration)
        if final_acked is False:
            self._record_failure(
                "servo.move.failed",
                f"fine approach final leg to {aim_deg:.2f} deg was "
                "not acknowledged",
                {"target_deg": target_deg, "leg": "final"})
            return False
        end_snapshot = self._servo.read_snapshot()
        logger.debug("fine approach: final leg commanded",
                     metadata={"event": "servo.move.fine_approach"},
                     extra={"target_deg": target_deg, "aim_deg": aim_deg})
        self._events.record(
            "servo.move.fine_approach",
            f"fine approach to {aim_deg:.2f} deg",
            {"overshoot_deg": round(overshoot_deg, 2),
             "overshoot_clamped": overshoot_clamped,
             "aim_deg": round(aim_deg, 2),
             "wait_elapsed_s": round(wait_elapsed_s, 3),
             "position_at_final_leg_deg": (
                 round(position_at_final_leg_deg, 2)
                 if position_at_final_leg_deg is not None else None),
             "current_a_at_overshoot": start_snapshot.current_a,
             "torque_kgcm_at_overshoot": start_snapshot.torque_kgcm,
             "current_a_at_final": end_snapshot.current_a,
             "torque_kgcm_at_final": end_snapshot.torque_kgcm})
        return True

    def _wait_until_landed(self) -> Optional[float]:
        """Waits for the position to hold still, then returns it.

        Movement decides this, and current does not gate it at any level:
        an arm holding a position against gravity draws a current that
        never goes quiet, so requiring it to would mean never detecting a
        landing at all. Measured on the diagnostic tool, that mistake cost
        a full 25s timeout on every correction; on movement alone the same
        correction takes 5s.

        The window is five times the 0.277s limit-cycle period this servo
        shows, so an arm still hunting cannot pass as landed: across 245
        archived traces the median gap between movements while hunting is
        0.27s, and 98% of arms still for 2s never moved again.

        Returns:
            Optional[float]: The settled output angle, or None if the servo
                never answered a read - which means unknown, not a number.
        """
        required = self._settings.fine_approach_settle_quiet_seconds
        deadline = (monotonic()
                    + self._settings.fine_approach_timeout_seconds)
        last: Optional[float] = None
        quiet_since: Optional[float] = None
        while monotonic() < deadline:
            current_deg = self._state.current_output_deg()
            now = monotonic()
            if current_deg is not None:
                if (last is not None
                        and abs(current_deg - last) < _COUNT_EPSILON_DEG):
                    if quiet_since is None:
                        quiet_since = now
                    elif (now - quiet_since) >= required:
                        return current_deg
                else:
                    quiet_since = None
                last = current_deg
            sleep(0.05)
        return last

    def _validate_reachable(self, target_deg: float) -> None:
        """Refuses targets the servo would silently clamp.

        Args:
            target_deg (float): Requested output angle.

        Raises:
            OutOfTravelError: If target maps outside reachable count range.
        """
        if self._state.is_reachable(target_deg) is True:
            return
        low, high = self._state.reachable_output_range_deg()
        raise OutOfTravelError(
            f"{target_deg:.2f} deg is outside the reachable range "
            f"({low:.2f} to {high:.2f} deg). Re-calibrate to recentre it.",
            metadata={"target_deg": target_deg, "low_deg": low,
                     "high_deg": high})

    def _await_settle(self) -> None:
        """Blocks until any active settle window elapses."""
        remaining = self._state.settle_remaining_seconds()
        if remaining > 0.0:
            logger.debug("waiting for lock settle",
                         metadata={"event": "servo.move.settle_wait"},
                         extra={"wait_seconds": round(remaining, 3)})
            sleep(remaining)

    def _validate_step(self, target_deg: float) -> None:
        """Validates the configured command granularity.

        Args:
            target_deg (float): Requested output angle.

        Raises:
            StepError: If angle is not a multiple of step size.
        """
        step = self._settings.output_step_deg
        multiples = target_deg / step
        if abs(multiples - round(multiples)) > 1e-6:
            raise StepError(f"angle must be in steps of {step} deg",
                            metadata={"target_deg": target_deg,
                                      "step": step})
