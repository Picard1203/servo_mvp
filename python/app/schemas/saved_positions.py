"""Request/response schemas for the saved-positions router."""

from pydantic import BaseModel, Field

from app.core.config import get_settings

_settings = get_settings()


class SavedPositionCreateRequest(BaseModel):
    """Request to create a saved position at a given angle.

    Attributes:
        name (str): Unique operator-given name.
        description (str): Operator-given description of the position.
        target_deg (float): Output angle to store.
    """

    name: str = Field(min_length=1, max_length=40)
    description: str = Field(default="", max_length=200)
    target_deg: float = Field(ge=_settings.output_min_deg,
                              le=_settings.output_max_deg)


class SavedPositionUpdateRequest(BaseModel):
    """Request to overwrite a saved position's editable fields.

    Attributes:
        name (str): New name.
        description (str): New description.
        target_deg (float): New output angle to store.
        updated_at (str): The updated_at the caller last saw.
    """

    name: str = Field(min_length=1, max_length=40)
    description: str = Field(default="", max_length=200)
    target_deg: float = Field(ge=_settings.output_min_deg,
                              le=_settings.output_max_deg)
    updated_at: str


class SavedPositionDeleteRequest(BaseModel):
    """Request to delete a saved position.

    Attributes:
        updated_at (str): The updated_at the caller last saw.
    """

    updated_at: str


class SavedPositionResponse(BaseModel):
    """One saved position, enriched with its live angle.

    Attributes:
        id (int): Database identifier.
        name (str): Unique operator-given name.
        description (str): Operator-given description of the position.
        raw_counts (int): Absolute encoder position in raw counts.
        output_deg (float): Live output angle against the current datum.
        stale_reference (bool): True if saved before the current datum.
        created_at (str): ISO timestamp of creation.
        updated_at (str): ISO timestamp of the last edit.
    """

    id: int
    name: str
    description: str
    raw_counts: int
    output_deg: float
    stale_reference: bool
    created_at: str
    updated_at: str


class GoResponse(BaseModel):
    """Acknowledgement of a go-to-position command.

    Attributes:
        accepted (bool): Always True on success.
    """

    accepted: bool


class DeletedResponse(BaseModel):
    """Acknowledgement of a saved-position deletion.

    Attributes:
        deleted (bool): Always True on success.
    """

    deleted: bool
