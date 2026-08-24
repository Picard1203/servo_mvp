"""Telemetry endpoints: binary telemetry stream export."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import StreamingResponse

from app.deps import get_telemetry_service
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])

TelemetryDep = Annotated[TelemetryService, Depends(get_telemetry_service)]


@router.get("/binary")
def export_binary(telemetry: TelemetryDep,
                  ts_from: Annotated[float, Query(alias="from")],
                  ts_to: Annotated[float, Query(alias="to")]) -> StreamingResponse:
    """Exports compact packed binary telemetry data for client-side rendering.

    Args:
        telemetry: Injected telemetry service.
        ts_from: Range start, unix timestamp.
        ts_to: Range end, unix timestamp.

    Returns:
        Binary stream response (compressed via GZipMiddleware).
    """
    stream = telemetry.export_binary_stream(ts_from, ts_to)
    return StreamingResponse(stream, media_type="application/octet-stream")
