"""Motor isolation: operator intent, reconciliation against hardware, and
the idle-timeout auto-isolate backup.

Isolation is a reconciler, not three separate mechanisms. Boot re-apply,
the idle backup, and retrying a failed write are all the same operation:
drive the servo's ACTUAL torque state toward the operator's INTENDED
state, which lives in the database (see ServoStateStore's isolation
methods). Intent is reported to the operator only once the servo has
acknowledged the write - reporting it on intent alone would claim the
motor is powered down when it might not be, which is worse than the
motor staying on.
"""

from datetime import datetime
from time import monotonic
from typing import Optional

from Logger461 import logger

from app.core.config import Settings
from app.core.events import EventService
from app.repositories.abstract.app_state_repository import AppStateRepository
from app.repositories.abstract.servo_repository import ServoRepository
from app.services.servo_state import ServoStateStore

_ISOLATED_INTENT_KEY = "isolated"


class IsolationService:
    """Owns isolation intent, reconciles it against hardware, and runs the
    idle-timeout auto-isolate backup."""

    def __init__(self, servo: ServoRepository, state: ServoStateStore,
                 app_state: AppStateRepository, events: EventService,
                 settings: Settings) -> None:
        self._servo = servo
        self._state = state
        self._app_state = app_state
        self._events = events
        self._settings = settings
        self._lock_engaged_at: Optional[float] = None
        # Converge on the persisted intent immediately, rather than
        # waiting for the first sampler tick - a reboot with isolation
        # intended should not leave the motor energised any longer than
        # one bus round trip has to.
        self._reconcile("boot")

    def set_isolated(self, isolated: bool) -> None:
        """Sets operator intent and reconciles it immediately.

        Never gated on whether a move is in progress - unlike a lock
        change, an isolate command must take effect right away even
        mid-move, since cutting power on demand is the whole point.

        Args:
            isolated: Desired isolation state.

        Returns:
            None.
        """
        self._persist_intent(isolated)
        self._state.set_isolated_intent(isolated)
        if not isolated and self._state.is_locked():
            # Un-isolating while still locked is a deliberate decision to
            # be ready to move again - restart the idle clock from here
            # rather than letting the backup re-fire moments later on
            # however much of the original window happens to remain.
            self._lock_engaged_at = monotonic()
        self._reconcile("manual")

    def tick(self) -> None:
        """Advances the idle timer and retries any pending reconciliation.

        Called once per sampler cycle rather than from its own thread, so
        this adds no new lifecycle that needs its own start/stop
        handling.

        Returns:
            None.
        """
        self._advance_idle_timer()
        if self._state.is_isolated_intent() != self._state.is_isolated_known():
            self._reconcile("retry")

    # ---------------------------------------------------------- internals

    def _advance_idle_timer(self) -> None:
        """Auto-engages isolation once the lock has been idle long enough.

        Fires only while locked: isolating a servo that can still be
        commanded to move risks catching the operator mid-task. Measures
        idleness as time continuously locked, since a locked servo cannot
        be moved at all - every second spent locked is, by definition,
        idle.

        Returns:
            None.
        """
        if not self._state.is_locked():
            self._lock_engaged_at = None
            return
        if self._lock_engaged_at is None:
            self._lock_engaged_at = monotonic()
            return
        if self._state.is_isolated_intent():
            return
        idle_for = monotonic() - self._lock_engaged_at
        if idle_for >= self._settings.isolation_idle_timeout_s:
            self._persist_intent(True)
            self._state.set_isolated_intent(True)
            self._reconcile("idle")

    def _reconcile(self, reason: str) -> None:
        """Drives the acknowledged hardware state toward intent, once.

        Args:
            reason: Why reconciliation is happening now ("boot", "manual",
                "idle" or "retry") - recorded on the event, since an
                unattended change needs to say what caused it.

        Returns:
            None.
        """
        intent = self._state.is_isolated_intent()
        if intent == self._state.is_isolated_known():
            return
        # set_torque's `enabled` means "restore drive torque" - the exact
        # opposite of "isolated" intent - so it must be negated here, not
        # passed straight through.
        acked = self._servo.set_torque(not intent)
        if not acked:
            logger.warning(
                "motor torque command not acknowledged",
                metadata={"event": "servo.isolation.unconfirmed",
                          "reason": reason},
                extra={"intent_isolated": intent})
            return
        if not self._state.set_isolated_known(intent):
            return
        if intent:
            # A target that was being pursued when power was cut is no
            # longer being pursued - the marker and delta on screen must
            # say so rather than keep pointing at a target the motor has
            # stopped moving toward.
            self._state.mark_target_stale()
        event = ("servo.isolation.engaged" if intent
                 else "servo.isolation.released")
        message = "motor isolated" if intent else "motor isolation released"
        self._events.record(event, message, {"reason": reason})
        logger.info(message, metadata={"event": event, "reason": reason})

    def _persist_intent(self, isolated: bool) -> None:
        """Writes intent to the database so it survives a restart.

        Args:
            isolated: Desired isolation state.

        Returns:
            None.
        """
        self._app_state.set(_ISOLATED_INTENT_KEY, "1" if isolated else "0",
                            datetime.now().isoformat(timespec="seconds"))
