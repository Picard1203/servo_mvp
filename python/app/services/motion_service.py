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
            self._fine_approach_thread = Thread(
                target=self._fine_approach,
                args=(generation, target_deg, target_counts, speed_counts,
                      acceleration),
                daemon=True)
            self._fine_approach_thread.start()
        else:
            acked = self._servo.command_move(target_counts, speed_counts,
                                             acceleration)
            if acked is False:
                self._raise_not_acknowledged(
                    "servo.move.failed",
                    f"move to {target_deg:.2f} deg was not acknowledged",
                    {"target_deg": target_deg})

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
        self._events.record(event, message, metadata)
        logger.error(message, metadata={"event": event}, extra=metadata)
        raise CommandNotAcknowledgedError(message, metadata=metadata)

    def _needs_fine_approach(self, start_deg: Optional[float],
                             target_deg: float) -> bool:
        """Decides whether the anti-backlash approach applies.

        Args:
            start_deg (Optional[float]): Current output angle, or None.
            target_deg (float): Requested output angle.

        Returns:
            bool: True when enabled and target is below start.
        """
        if start_deg is None:
            return False
        return ((self._settings.fine_approach_enabled is True)
                and (target_deg < start_deg))

    def _fine_approach(self, generation: int, target_deg: float,
                       target_counts: int, speed_counts: int,
                       acceleration: int) -> None:
        """Runs the two-leg consistent-direction approach.

        Args:
            generation (int): Move generation this thread was started for.
            target_deg (float): Requested output angle.
            target_counts (int): Final absolute counts target.
            speed_counts (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter.
        """
        try:
            overshoot_deg = (target_deg
                             - self._settings.fine_approach_overshoot_deg)
            overshoot_counts = self._state.counts_from_output_deg(
                overshoot_deg)
            self._servo.command_move(overshoot_counts, speed_counts,
                                     acceleration)
            deadline = (monotonic()
                        + self._settings.fine_approach_timeout_seconds)
            is_moving = True
            while (monotonic() < deadline) and (is_moving is True):
                sleep(0.05)
                is_moving = (self._servo.read_snapshot().moving is True)
            if generation != self._move_generation:
                logger.debug("fine approach: superseded, final leg skipped",
                             metadata={"event": "servo.move.fine_approach"})
                return
            if self._state.is_isolated_intent() is True:
                logger.debug("fine approach: isolated, final leg skipped",
                             metadata={"event": "servo.move.fine_approach"})
                return
            self._servo.command_move(target_counts, speed_counts,
                                     acceleration)
            logger.debug("fine approach: final leg commanded",
                         metadata={"event": "servo.move.fine_approach"},
                         extra={"target_deg": target_deg})
            self._events.record("servo.move.fine_approach",
                                f"fine approach to {target_deg:.2f} deg",
                                {"overshoot_deg": round(overshoot_deg, 2)})
        except (sqlite3.OperationalError, ValueError):
            logger.exception(
                "fine approach failed",
                metadata={"event": "servo.move.fine_approach_error"})

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
