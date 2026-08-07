"""In-memory ring buffer of structured events for the events endpoint.

Kept separate from logging: services log via Logger461 AND record an
event here when it is worth surfacing to the operator UI. No logger
coupling in either direction.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime
from threading import Lock
from typing import Optional


@dataclass(slots=True, frozen=True)
class Event:
    """One operator-facing event.

    Attributes:
        timestamp: ISO timestamp.
        event: Dotted event identifier (e.g. servo.move.accepted).
        message: Human-readable description.
        data: Optional structured fields.
    """

    timestamp: str
    event: str
    message: str
    data: dict


class EventService:
    """Thread-safe fixed-size store of recent events."""

    def __init__(self, capacity: int) -> None:
        self._events: deque[Event] = deque(maxlen=capacity)
        self._lock = Lock()

    def record(self, event: str, message: str,
               data: Optional[dict] = None) -> None:
        """Stores one event.

        Args:
            event: Dotted event identifier.
            message: Human-readable description.
            data: Optional structured fields.

        Returns:
            None.
        """
        entry = Event(timestamp=datetime.now().isoformat(timespec="seconds"),
                      event=event, message=message, data=data or {})
        with self._lock:
            self._events.append(entry)

    def recent(self, limit: int) -> list[Event]:
        """Returns the newest events, newest first.

        Args:
            limit: Maximum number of events to return.

        Returns:
            The most recent events.
        """
        with self._lock:
            items = list(self._events)
        items.reverse()
        return items[:limit]
