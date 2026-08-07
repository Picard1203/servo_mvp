"""Telemetry endpoints: CSV export by time range."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse

from app.deps import get_telemetry_service
from app.services.telemetry_service import TelemetryService

router = APIRouter(prefix="/api/v1/telemetry", tags=["telemetry"])

TelemetryDep = Annotated[TelemetryService, Depends(get_telemetry_service)]


@router.get("/export")
async def export_csv(telemetry: TelemetryDep,
                     ts_from: Annotated[float, Query(alias="from")],
                     ts_to: Annotated[float, Query(alias="to")]
                     ) -> StreamingResponse:
    """Streams telemetry samples in a time range as CSV.

    Args:
        telemetry: Injected telemetry service.
        ts_from: Range start, unix timestamp.
        ts_to: Range end, unix timestamp.

    Returns:
        A streaming CSV response (row cap applies, see settings).
    """
    return StreamingResponse(
        telemetry.export_csv(ts_from, ts_to), media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=telemetry.csv"})
