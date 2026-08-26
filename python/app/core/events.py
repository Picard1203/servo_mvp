"""In-memory ring buffer of structured events for the events endpoint."""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Optional


@dataclass(slots=True, frozen=True)
class Event:
    """One operator-facing event.

    Attributes:
        timestamp (str): ISO timestamp.
        event (str): Dotted event identifier.
        message (str): Human-readable description.
        data (dict): Structured event fields.
    """

    timestamp: str
    event: str
    message: str
    data: dict


class EventService:
    """Thread-safe fixed-size store of recent events.

    Attributes:
        _events (deque[Event]): Fixed-capacity ring buffer of events.
        _lock (Lock): Mutex protecting event buffer access.
    """

    def __init__(self, capacity: int) -> None:
        self._events: deque[Event] = deque(maxlen=capacity)
        self._lock: Lock = Lock()

    def record(self, event: str, message: str,
               data: Optional[dict] = None) -> None:
        """Stores one event.

        Args:
            event (str): Dotted event identifier.
            message (str): Human-readable description.
            data (Optional[dict]): Optional structured fields.
        """
        entry = Event(timestamp=datetime.now(timezone.utc)
                      .isoformat(timespec="seconds"),
                      event=event, message=message, data=data or {})
        with self._lock:
            self._events.append(entry)

    def recent(self, limit: int) -> list[Event]:
        """Returns the newest events, newest first.

        Args:
            limit (int): Maximum number of events to return.

        Returns:
            list[Event]: The most recent events.
        """
        with self._lock:
            items = list(self._events)
        items.reverse()
        return items[:limit]
