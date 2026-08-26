"""Request/response schemas for the system router."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Service health summary.

    Attributes:
        service (str): Application name.
        version (str): Application version.
        uptime_seconds (float): Seconds since process start.
        mcu_status (str): Last status line from the sketch.
        servo_backend (str): Active servo backend name.
        relay_connections_total (int): Total connections accepted since start.
    """

    service: str
    version: str
    uptime_seconds: float
    mcu_status: str
    servo_backend: str
    relay_connections_total: int


class EventResponse(BaseModel):
    """One structured event for the events panel.

    Attributes:
        timestamp (str): ISO timestamp.
        event (str): Dotted event identifier.
        message (str): Human-readable description.
        data (dict): Event-specific fields.
    """

    timestamp: str
    event: str
    message: str
    data: dict


class EventListResponse(BaseModel):
    """Recent events, newest first.

    Attributes:
        events (list[EventResponse]): List of recent structured events.
    """

    events: list[EventResponse]
