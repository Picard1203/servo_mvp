"""Zero-reference endpoints: list, capture, activate, delete."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_zero_service
from app.schemas.zeros import (ZeroActionResponse, ZeroCaptureRequest,
                               ZeroResponse)
from app.services.zero_service import ZeroService

router = APIRouter(prefix="/api/v1/zeros", tags=["zeros"])

ZeroDep = Annotated[ZeroService, Depends(get_zero_service)]


@router.get("", response_model=list[ZeroResponse])
def list_zeros(zeros: ZeroDep) -> list[ZeroResponse]:
    """Lists all zero references, newest first.

    Args:
        zeros: Injected zero service.

    Returns:
        Stored zeros.
    """
    return [ZeroResponse(id=z.id, name=z.name, raw_counts=z.raw_counts,
                         is_active=z.is_active, is_datum=z.is_datum,
                         created_at=z.created_at)
            for z in zeros.list_all()]


@router.post("/capture", status_code=201, response_model=ZeroResponse)
def capture_zero(request: ZeroCaptureRequest,
                       zeros: ZeroDep) -> ZeroResponse:
    """Captures the current position as a named zero.

    Args:
        request: The zero name.
        zeros: Injected zero service.

    Returns:
        The stored zero.
    """
    zero = zeros.capture(request.name)
    return ZeroResponse(id=zero.id, name=zero.name, raw_counts=zero.raw_counts,
                        is_active=zero.is_active, is_datum=zero.is_datum,
                        created_at=zero.created_at)


@router.post("/{zero_id}/activate", response_model=ZeroActionResponse)
def activate_zero(zero_id: int, zeros: ZeroDep) -> ZeroActionResponse:
    """Sets one zero as the active baseline.

    Args:
        zero_id: Database id.
        zeros: Injected zero service.

    Returns:
        Acknowledgement.
    """
    zeros.activate(zero_id)
    return ZeroActionResponse(zero_id=zero_id, action="activated")


@router.delete("/{zero_id}", response_model=ZeroActionResponse)
def delete_zero(zero_id: int, zeros: ZeroDep) -> ZeroActionResponse:
    """Deletes a non-active zero reference.

    Args:
        zero_id: Database id.
        zeros: Injected zero service.

    Returns:
        Acknowledgement.
    """
    zeros.delete(zero_id)
    return ZeroActionResponse(zero_id=zero_id, action="deleted")
