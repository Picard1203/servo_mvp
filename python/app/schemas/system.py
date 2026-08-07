"""Request/response schemas for the system router."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Service health summary.

    Attributes:
        service: Application name.
        version: Application version.
        uptime_seconds: Seconds since process start.
        mcu_status: Last status line from the sketch.
        relay_connections_total: Connections accepted since start.
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
        timestamp: ISO timestamp.
        event: Dotted event identifier.
        message: Human-readable description.
        data: Event-specific fields.
    """

    timestamp: str
    event: str
    message: str
    data: dict


class EventListResponse(BaseModel):
    """Recent events, newest first.

    Attributes:
        events: The events.
    """

    events: list[EventResponse]
