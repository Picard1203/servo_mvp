"""Request/response schemas for the zeros router."""

from pydantic import BaseModel, Field


class ZeroCaptureRequest(BaseModel):
    """Request to capture the current position as a named zero.

    Attributes:
        name: Unique display name for the zero.
    """

    name: str = Field(min_length=1, max_length=40)


class ZeroResponse(BaseModel):
    """One stored zero reference.

    Attributes:
        id: Database id.
        name: Display name.
        raw_counts: Captured raw encoder counts.
        is_active: Whether this is the active baseline.
        is_datum: Whether this is the calibration datum (undeletable).
        created_at: ISO capture timestamp.
    """

    id: int
    name: str
    raw_counts: int
    is_active: bool
    is_datum: bool
    created_at: str


class ZeroActionResponse(BaseModel):
    """Acknowledgement of a zero activate/delete action.

    Attributes:
        zero_id: The affected zero id.
        action: The action performed ('activated' or 'deleted').
    """

    zero_id: int
    action: str
