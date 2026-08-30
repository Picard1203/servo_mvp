"""SSE stream for servo state, saved positions and events."""

import asyncio
import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.core.config import Settings, get_settings
from app.core.events import EventService
from app.deps import (
    get_event_service,
    get_saved_position_service,
    get_state_store,
)
from app.schemas.saved_positions import SavedPositionResponse
from app.schemas.servo import ServoStateResponse
from app.schemas.system import EventListResponse, EventResponse
from app.services.saved_position_service import SavedPositionService
from app.services.servo_state import ServoStateStore

router = APIRouter(prefix="/api/v1", tags=["stream"])


async def _stream_generator(
    request: Request,
    state_store: ServoStateStore,
    positions_service: SavedPositionService,
    event_service: EventService,
    settings: Settings,
) -> AsyncGenerator[str, None]:
    """Generates SSE events for state, saved positions and events.

    Args:
        request (Request): The incoming HTTP request.
        state_store (ServoStateStore): Injected servo state store.
        positions_service (SavedPositionService): Injected position service.
        event_service (EventService): Injected event service.
        settings (Settings): Application configuration settings.

    Yields:
        str: Server-sent event formatted text frames.
    """
    count = 0
    active = True
    interval = settings.sampler_interval_seconds
    events_every = max(1, round(15.0 / interval))
    last_positions_revision = -1
    try:
        while active is True:
            disconnected = await request.is_disconnected()
            if disconnected is True:
                active = False
            else:
                view = await asyncio.to_thread(state_store.snapshot)
                state = ServoStateResponse.from_view(view)
                yield f"event: state\ndata: {state.model_dump_json()}\n\n"

                revision = await asyncio.to_thread(
                    positions_service.revision)
                changed = (revision != last_positions_revision)
                due = ((count % events_every) == 0)
                if changed or due:
                    views = await asyncio.to_thread(
                        positions_service.list_all)
                    positions_json = [
                        SavedPositionResponse(
                            id=v.id, name=v.name,
                            description=v.description,
                            raw_counts=v.raw_counts,
                            output_deg=v.output_deg,
                            stale_reference=v.stale_reference,
                            created_at=v.created_at,
                            updated_at=v.updated_at,
                        ).model_dump(mode="json")
                        for v in views
                    ]
                    yield (f"event: positions\ndata: "
                           f"{json.dumps(positions_json)}\n\n")
                    last_positions_revision = revision

                if due:
                    recent_events = await asyncio.to_thread(
                        event_service.recent, 50)
                    events_list: list[EventResponse] = []
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
    positions_service: SavedPositionService = Depends(
        get_saved_position_service),
    event_service: EventService = Depends(get_event_service),
    settings: Settings = Depends(get_settings),
) -> StreamingResponse:
    """Streams servo state, saved positions, and events over SSE.

    Args:
        request (Request): The incoming HTTP request.
        state_store (ServoStateStore): Injected servo state store.
        positions_service (SavedPositionService): Injected position service.
        event_service (EventService): Injected event service.
        settings (Settings): Application configuration settings.

    Returns:
        StreamingResponse: Continuous SSE streaming response.
    """
    return StreamingResponse(
        _stream_generator(request, state_store, positions_service,
                          event_service, settings),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
