"""Motor isolation: operator intent and hardware reconciliation."""

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
    """Manages motor isolation intent, reconciliation, and idle timeout.

    Attributes:
        _servo (ServoRepository): Servo repository for hardware commands.
        _state (ServoStateStore): Atomic state store for isolation state.
        _app_state (AppStateRepository): App-state repository for intent.
        _events (EventService): Event service for structured audit logs.
        _settings (Settings): Application configuration settings.
        _lock_engaged_at (Optional[float]): Monotonic lock start timestamp.
    """

    def __init__(self, servo: ServoRepository, state: ServoStateStore,
                 app_state: AppStateRepository, events: EventService,
                 settings: Settings) -> None:
        self._servo: ServoRepository = servo
        self._state: ServoStateStore = state
        self._app_state: AppStateRepository = app_state
        self._events: EventService = events
        self._settings: Settings = settings
        self._lock_engaged_at: Optional[float] = None
        self._reconcile("boot")

    def set_isolated(self, isolated: bool) -> None:
        """Sets operator intent and reconciles it immediately.

        Args:
            isolated (bool): Desired motor isolation state.
        """
        self._persist_intent(isolated)
        self._state.set_isolated_intent(isolated)
        if (isolated is False) and (self._state.is_locked() is True):
            self._lock_engaged_at = monotonic()
        self._reconcile("manual")

    def tick(self) -> None:
        """Advances the idle timer and retries pending reconciliation."""
        self._advance_idle_timer()
        if self._state.is_isolated_intent() != self._state.is_isolated_known():
            self._reconcile("retry")

    def _advance_idle_timer(self) -> None:
        """Auto-engages isolation once the lock has been idle long enough."""
        if self._state.is_locked() is False:
            self._lock_engaged_at = None
            return
        if self._lock_engaged_at is None:
            self._lock_engaged_at = monotonic()
            return
        if self._state.is_isolated_intent() is True:
            return
        idle_for = monotonic() - self._lock_engaged_at
        if idle_for >= self._settings.isolation_idle_timeout_s:
            self._persist_intent(True)
            self._state.set_isolated_intent(True)
            self._reconcile("idle")

    def _reconcile(self, reason: str) -> None:
        """Drives the acknowledged hardware state toward intent once.

        Args:
            reason (str): Cause of reconciliation (boot, manual, idle, retry).
        """
        intent = self._state.is_isolated_intent()
        if intent == self._state.is_isolated_known():
            return
        # set_torque means "restore torque" - negate intent, don't pass it through.
        acked = self._servo.set_torque(intent is False)
        if acked is False:
            logger.warning(
                "motor torque command not acknowledged",
                metadata={"event": "servo.isolation.unconfirmed",
                          "reason": reason},
                extra={"intent_isolated": intent})
            return
        if self._state.set_isolated_known(intent) is False:
            return
        if intent is True:
            self._state.mark_target_stale()
        event = ("servo.isolation.engaged" if intent is True
                 else "servo.isolation.released")
        message = "motor isolated" if intent is True else "motor isolation released"
        self._events.record(event, message, {"reason": reason})
        logger.info(message, metadata={"event": event, "reason": reason})

    def _persist_intent(self, isolated: bool) -> None:
        """Writes intent to the database so it survives a restart.

        Args:
            isolated (bool): Desired motor isolation state.
        """
        self._app_state.set(_ISOLATED_INTENT_KEY, "1" if isolated else "0",
                            datetime.now().isoformat(timespec="seconds"))
