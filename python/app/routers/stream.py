"""SSE stream for servo state, zeros and events."""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.core.events import EventService
from app.deps import get_event_service, get_state_store, get_zero_service
from app.schemas.servo import ServoStateResponse
from app.schemas.system import EventListResponse, EventResponse
from app.schemas.zeros import ZeroResponse
from app.services.servo_state import ServoStateStore
from app.services.zero_service import ZeroService

router = APIRouter(prefix="/api/v1", tags=["stream"])


async def _stream_generator(
    request: Request,
    state_store: ServoStateStore,
    zero_service: ZeroService,
    event_service: EventService,
    settings: Settings,
) -> AsyncGenerator[str, None]:
    """Generates SSE events for state, zeros and events.

    Args:
        request: The incoming request.
        state_store: The servo state store.
        zero_service: The zero service.
        event_service: The event service.
        settings: Application settings.

    Yields:
        SSE formatted strings.
    """
    count = 0
    active = True
    interval = settings.sampler_interval_seconds
    # Zeros/events push roughly every 15s of wall clock, regardless of the
    # state-push interval - the two are unrelated cadences that share a loop.
    zeros_events_every = max(1, round(15.0 / interval))
    try:
        while active is True:
            disconnected = await request.is_disconnected()
            if disconnected is True:
                active = False
            else:
                view = await asyncio.to_thread(state_store.snapshot)
                state = ServoStateResponse(
                    output_deg=view.output_deg,
                    reading_valid=view.reading_valid,
                    moving=view.moving,
                    locked=view.locked,
                    settling=view.settling,
                    position_verified=view.position_verified,
                    active_zero=view.active_zero_name,
                    temperature_c=view.temperature_c,
                    voltage_v=view.voltage_v,
                    current_a=view.current_a,
                    torque_kgcm=view.torque_kgcm,
                    overload=view.overload,
                    overcurrent=view.overcurrent,
                    overheat=view.overheat,
                    voltage_fault=view.voltage_fault,
                    sensor_fault=view.sensor_fault,
                    angle_fault=view.angle_fault,
                )
                yield f"event: state\ndata: {state.model_dump_json()}\n\n"

                if ((count % zeros_events_every) == 0):
                    zeros_list = await asyncio.to_thread(zero_service.list_all)
                    
                    zeros_resp = []
                    for z in zeros_list:
                        zeros_resp.append(
                            ZeroResponse(
                                id=z.id,
                                name=z.name,
                                raw_counts=z.raw_counts,
                                is_active=z.is_active,
                                is_datum=z.is_datum,
                                created_at=z.created_at,
                            )
                        )
                    
                    zeros_json_list = []
                    for z in zeros_resp:
                        zeros_json_list.append(z.model_dump(mode="json"))
                    yield f"event: zeros\ndata: {json.dumps(zeros_json_list)}\n\n"

                    recent_events = await asyncio.to_thread(event_service.recent, 50)
                    events_list = []
                    for e in recent_events:
                        events_list.append(
                            EventResponse(
                                timestamp=e.timestamp,
                                event=e.event,
                                message=e.message,
                                data=e.data,
                            )
                        )
                    events_resp = EventListResponse(events=events_list)
                    yield f"event: events\ndata: {events_resp.model_dump_json()}\n\n"

                count += 1
                await asyncio.sleep(interval)
    except (asyncio.CancelledError, Exception):
        pass


@router.get("/stream")
async def stream(
    request: Request,
    state_store: ServoStateStore = Depends(get_state_store),
    zero_service: ZeroService = Depends(get_zero_service),
    event_service: EventService = Depends(get_event_service),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Streams servo state, zeros and events.

    Args:
        request: The incoming request.
        state_store: The servo state store.
        zero_service: The zero service.
        event_service: The event service.
        settings: Application settings.

    Returns:
        The streaming response.
    """
    return StreamingResponse(
        _stream_generator(request, state_store, zero_service, event_service,
                           settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
