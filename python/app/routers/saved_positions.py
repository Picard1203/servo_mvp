"""Saved-position endpoints: list, create, update, delete, go."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_saved_position_service
from app.models.entities import SavedPositionView
from app.schemas.saved_positions import (
    DeletedResponse,
    GoResponse,
    SavedPositionCreateRequest,
    SavedPositionDeleteRequest,
    SavedPositionResponse,
    SavedPositionUpdateRequest,
)
from app.services.saved_position_service import SavedPositionService

router = APIRouter(prefix="/api/v1/positions", tags=["positions"])

PositionsDep = Annotated[SavedPositionService,
                         Depends(get_saved_position_service)]


def _to_response(view: SavedPositionView) -> SavedPositionResponse:
    """Builds the API response from a saved-position view.

    Args:
        view (SavedPositionView): The service-layer view.

    Returns:
        SavedPositionResponse: The API response model.
    """
    return SavedPositionResponse(
        id=view.id, name=view.name, description=view.description,
        raw_counts=view.raw_counts, output_deg=view.output_deg,
        stale_reference=view.stale_reference, created_at=view.created_at,
        updated_at=view.updated_at)


@router.get("", response_model=list[SavedPositionResponse])
def list_positions(positions: PositionsDep) -> list[SavedPositionResponse]:
    """Lists all saved positions, newest first.

    Args:
        positions (SavedPositionService): Injected saved-position service.

    Returns:
        list[SavedPositionResponse]: Saved positions enriched for display.
    """
    return [_to_response(view) for view in positions.list_all()]


@router.post("", status_code=201, response_model=SavedPositionResponse)
def create_position(request: SavedPositionCreateRequest,
                    positions: PositionsDep) -> SavedPositionResponse:
    """Creates a saved position at the given angle.

    Args:
        request (SavedPositionCreateRequest): Name, description and angle.
        positions (SavedPositionService): Injected saved-position service.

    Returns:
        SavedPositionResponse: The stored position, enriched for display.
    """
    view = positions.create(request.name, request.description,
                            request.target_deg)
    return _to_response(view)


@router.patch("/{position_id}", response_model=SavedPositionResponse)
def update_position(position_id: int, request: SavedPositionUpdateRequest,
                    positions: PositionsDep) -> SavedPositionResponse:
    """Overwrites a saved position's name, description and angle.

    Args:
        position_id (int): Database identifier.
        request (SavedPositionUpdateRequest): New fields and last-seen state.
        positions (SavedPositionService): Injected saved-position service.

    Returns:
        SavedPositionResponse: The updated position, enriched for display.
    """
    view = positions.update(position_id, request.name, request.description,
                            request.target_deg, request.updated_at)
    return _to_response(view)


@router.delete("/{position_id}", response_model=DeletedResponse)
def delete_position(position_id: int, request: SavedPositionDeleteRequest,
                    positions: PositionsDep) -> DeletedResponse:
    """Deletes a saved position.

    Args:
        position_id (int): Database identifier.
        request (SavedPositionDeleteRequest): Last-seen state.
        positions (SavedPositionService): Injected saved-position service.

    Returns:
        DeletedResponse: Acknowledgement of deletion.
    """
    positions.delete(position_id, request.updated_at)
    return DeletedResponse(deleted=True)


@router.post("/{position_id}/go", response_model=GoResponse)
def go_to_position(position_id: int, positions: PositionsDep) -> GoResponse:
    """Moves the mechanism to a saved position.

    Args:
        position_id (int): Database identifier.
        positions (SavedPositionService): Injected saved-position service.

    Returns:
        GoResponse: Acknowledgement of the move command.
    """
    positions.go(position_id)
    return GoResponse(accepted=True)
