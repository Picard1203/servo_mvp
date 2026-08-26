"""Movement orchestration: lock gate, settle-wait, angle math, commands,
consistent-direction fine approach, and fault recovery."""

from threading import Thread
from time import monotonic, sleep

from typing import Optional

from Logger461 import logger

from app.core.config import Settings
from app.core.events import EventService
from app.core.exceptions import (IsolatedError, LockedAndIsolatedError,
                                 LockedError, MovingError, OutOfTravelError,
                                 StepError)
from app.repositories.abstract.servo_repository import ServoRepository
from app.services.servo_state import ServoStateStore


class MotionService:
    """Validates and executes movement commands in output-degree space."""

    def __init__(self, servo: ServoRepository, state: ServoStateStore,
                 events: EventService, settings: Settings) -> None:
        self._servo = servo
        self._state = state
        self._events = events
        self._settings = settings

    def move_to(self, target_deg: float, speed_dps: float,
                acceleration: Optional[int] = None) -> None:
        """Moves to an output angle relative to the active zero.

        Blocks briefly if a lock change is still settling, so the caller
        never has to poll or retry. When fine approach is enabled and the
        target lies below the current position, the move overshoots low
        and arrives moving in the positive direction (anti-backlash).

        Args:
            target_deg: Target output angle in degrees.
            speed_dps: Output speed in degrees per second.
            acceleration: Servo acceleration parameter (0-254); the
                configured default when None.

        Returns:
            None.

        Raises:
            StepError: If the angle violates the configured step size.
            LockedAndIsolatedError: If both the digital lock and motor
                isolation are engaged.
            LockedError: If the digital lock is engaged.
            IsolatedError: If the motor is isolated (R2).
        """
        self._validate_step(target_deg)
        self._validate_reachable(target_deg)
        if acceleration is None:
            acceleration = self._settings.default_acceleration
        # Isolation is gated on INTENT, not the acknowledged hardware state -
        # this must refuse from the very first request the process ever
        # serves, before IsolationService's reconciler has had any chance to
        # run (ADR-0010). See ServoStateStore.is_isolated_intent()'s
        # docstring.
        locked = self._state.is_locked()
        isolated = self._state.is_isolated_intent()
        if locked and isolated:
            self._events.record("servo.move.rejected",
                                "move rejected: locked and isolated",
                                {"target_deg": target_deg})
            logger.warning("move rejected: locked and isolated",
                           metadata={"event": "servo.move.rejected",
                                     "reason": "locked_isolated"},
                           extra={"target_deg": target_deg})
            raise LockedAndIsolatedError("servo is locked and motor is "
                                         "isolated")
        if locked:
            self._events.record("servo.move.rejected",
                                "move rejected: locked",
                                {"target_deg": target_deg})
            logger.warning("move rejected: locked",
                           metadata={"event": "servo.move.rejected",
                                     "reason": "locked"},
                           extra={"target_deg": target_deg})
            raise LockedError("servo is locked")
        if isolated:
            self._events.record("servo.move.rejected",
                                "move rejected: isolated",
                                {"target_deg": target_deg})
            logger.warning("move rejected: isolated",
                           metadata={"event": "servo.move.rejected",
                                     "reason": "isolated"},
                           extra={"target_deg": target_deg})
            raise IsolatedError("motor is isolated")

        self._await_settle()

        start_deg = self._state.current_output_deg()
        target_counts = self._state.counts_from_output_deg(target_deg)
        speed_counts = self._state.counts_speed_from_output_speed(speed_dps)

        # Set once, here, to the angle the OPERATOR asked for - never in
        # _fine_approach, which deliberately commands past this value
        # (anti-backlash overshoot). Recording the overshoot would show
        # the operator a target they never requested (twin-path hazard,
        # same shape as D9/D10).
        self._state.set_target(target_deg)

        if self._needs_fine_approach(start_deg, target_deg):
            Thread(target=self._fine_approach,
                   args=(target_deg, target_counts, speed_counts,
                         acceleration),
                   daemon=True).start()
        else:
            self._servo.command_move(target_counts, speed_counts,
                                     acceleration)

        from_deg = round(start_deg, 2) if start_deg is not None else None
        self._events.record("servo.move.accepted",
                            f"move to {target_deg:.2f} deg",
                            {"from_deg": from_deg,
                             "to_deg": target_deg})
        logger.info("move accepted",
                    metadata={"event": "servo.move.accepted",
                              "from_deg": from_deg},
                    extra={"to_deg": target_deg, "speed_dps": speed_dps,
                           "acceleration": acceleration})

    def stop(self) -> None:
        """Stops the current move at the present position.

        The last target is marked stale, not cleared: "asked for 45,
        stopped at 27" is the supposed-vs-actual reading the target
        display exists for, and it matters most at the moment a move is
        abandoned.

        Returns:
            None.
        """
        self._servo.command_stop()
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
            locked: Desired lock state.

        Returns:
            None.

        Raises:
            MovingError: If configured to guard and a move is in progress.
        """
        if (self._settings.guard_move_to_lock
                and self._servo.read_snapshot().moving):
            raise MovingError("cannot change lock while moving")
        if self._state.set_locked(locked):
            event = "servo.lock.engaged" if locked else "servo.lock.released"
            message = "lock engaged" if locked else "lock released"
            self._events.record(event, message)
            logger.info(message, metadata={"event": event})

    def recover(self) -> None:
        """Clears a tripped overload fault by re-commanding the position.

        Hardware semantics: the overload de-rate is released only by a
        new position command; commanding the current position clears the
        fault without moving.

        That "without moving" depends entirely on the read. A failed
        read reports count 0, so recovering on a stalled bus used to
        command position 0 - driving the mechanism to the bottom of its
        travel in the name of not moving it.

        Raises:
            InvalidReadingError: When the current position is unknown.

        Returns:
            None.
        """
        counts = self._state.read_counts()
        self._servo.command_move(
            counts, self._state.counts_speed_from_output_speed(
                self._settings.default_speed_dps),
            self._settings.default_acceleration)
        self._events.record("servo.fault.recovered",
                            "overload fault cleared by re-command", {})
        logger.info("overload fault cleared by re-command",
                    metadata={"event": "servo.fault.recovered"},
                    extra={"at_counts": counts})

    def _needs_fine_approach(self, start_deg: float,
                             target_deg: float) -> bool:
        """Decides whether the anti-backlash approach applies.

        Args:
            start_deg: Current output angle.
            target_deg: Requested output angle.

        Returns:
            True when fine approach is enabled and the target lies below
            the current position (arrival must come from below).
        """
        return (self._settings.fine_approach_enabled
                and target_deg < start_deg)

    def _fine_approach(self, target_deg: float, target_counts: int,
                       speed_counts: int, acceleration: int) -> None:
        """Runs the two-leg consistent-direction approach.

        Leg 1 overshoots below the target; once the servo settles (or a
        safety timeout elapses), leg 2 arrives moving in the positive
        direction, taking up belt backlash identically on every fine
        move.

        Args:
            target_deg: Requested output angle (for the overshoot math).
            target_counts: Final absolute counts target.
            speed_counts: Speed in counts per second.
            acceleration: Servo acceleration parameter.

        Returns:
            None.
        """
        overshoot_deg = (target_deg
                         - self._settings.fine_approach_overshoot_deg)
        overshoot_counts = self._state.counts_from_output_deg(overshoot_deg)
        self._servo.command_move(overshoot_counts, speed_counts,
                                 acceleration)
        deadline = (monotonic()
                    + self._settings.fine_approach_timeout_seconds)
        while monotonic() < deadline:
            sleep(0.05)
            if not self._servo.read_snapshot().moving:
                break
        self._servo.command_move(target_counts, speed_counts, acceleration)
        logger.debug("fine approach: final leg commanded",
                     metadata={"event": "servo.move.fine_approach"},
                     extra={"target_deg": target_deg})
        self._events.record("servo.move.fine_approach",
                            f"fine approach to {target_deg:.2f} deg",
                            {"overshoot_deg": round(overshoot_deg, 2)})

    def _validate_reachable(self, target_deg: float) -> None:
        """Refuses targets the servo would silently clamp.

        The servo accepts counts 0..4095 and quietly stops at the limit
        rather than reporting a problem, so an unreachable target used to
        look accepted while the mechanism halted early.

        Args:
            target_deg: Requested output angle.

        Returns:
            None.

        Raises:
            OutOfTravelError: If the target maps outside the count range.
        """
        if self._state.is_reachable(target_deg):
            return
        low, high = self._state.reachable_output_range_deg()
        raise OutOfTravelError(
            f"{target_deg:.2f} deg is outside the servo's travel from the "
            f"current reference; reachable range is {low:.2f} to {high:.2f} "
            f"deg. Re-calibrate near the middle of travel to recentre it.")

    def _await_settle(self) -> None:
        """Blocks until any active settle window elapses.

        Returns:
            None.
        """
        remaining = self._state.settle_remaining_seconds()
        if remaining > 0.0:
            logger.debug("waiting for lock settle",
                         metadata={"event": "servo.move.settle_wait"},
                         extra={"wait_seconds": round(remaining, 3)})
            sleep(remaining)

    def _validate_step(self, target_deg: float) -> None:
        """Validates the configured command granularity.

        Args:
            target_deg: Requested output angle.

        Returns:
            None.

        Raises:
            StepError: If the angle is not a multiple of the step size.
        """
        step = self._settings.output_step_deg
        multiples = target_deg / step
        if abs(multiples - round(multiples)) > 1e-6:
            raise StepError(f"angle must be in steps of {step} deg")
