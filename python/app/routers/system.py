"""System endpoints: health and recent events."""

from time import monotonic
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.core.events import EventService
from app.deps import get_event_service, get_relay
from app.relay.bridge_relay import BridgeRelay
from app.schemas.system import (EventListResponse, EventResponse,
                                HealthResponse)

router = APIRouter(prefix="/api/v1/system", tags=["system"])

EventDep = Annotated[EventService, Depends(get_event_service)]
RelayDep = Annotated[BridgeRelay, Depends(get_relay)]
SettingsDep = Annotated[Settings, Depends(get_settings)]

_START_TIME = monotonic()


@router.get("/health", response_model=HealthResponse)
def get_health(settings: SettingsDep,
                     relay: RelayDep) -> HealthResponse:
    """Returns service health including the MCU status line.

    Args:
        settings: Injected settings.
        relay: Injected Bridge relay.

    Returns:
        Uptime, version, MCU status and relay statistics.
    """
    try:
        from arduino.app_utils import Bridge
        mcu_status = str(Bridge.call("get_status"))
    except ImportError:
        mcu_status = "no MCU (dev computer)"
    except Exception as exc:
        mcu_status = f"unreachable ({exc})"
    return HealthResponse(
        service=settings.app_name, version=settings.version,
        uptime_seconds=round(monotonic() - _START_TIME, 1),
        mcu_status=mcu_status,
        servo_backend=("hardware" if get_settings().use_hardware_servo
                       else "simulated"),
        relay_connections_total=relay.connections_total)


@router.get("/events", response_model=EventListResponse)
def get_events(events: EventDep,
                     limit: Annotated[int, Query(ge=1, le=200)] = 50
                     ) -> EventListResponse:
    """Returns recent structured events, newest first.

    Args:
        events: Injected event service.
        limit: Maximum number of events.

    Returns:
        The events.
    """
    return EventListResponse(events=[
        EventResponse(timestamp=e.timestamp, event=e.event, message=e.message, data=e.data)
        for e in events.recent(limit)])
