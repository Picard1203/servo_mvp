"""Request/response schemas for the zeros router."""

from pydantic import BaseModel, Field


class ZeroCaptureRequest(BaseModel):
    """Request to capture the current position as a named zero.

    Attributes:
        name (str): Unique display name for the zero reference.
    """

    name: str = Field(min_length=1, max_length=40)


class ZeroResponse(BaseModel):
    """One stored zero reference.

    Attributes:
        id (int): Database identifier.
        name (str): Display name for the zero reference.
        raw_counts (int): Captured raw encoder counts.
        is_active (bool): True if this is the active baseline.
        is_datum (bool): True if this is the calibration datum.
        created_at (str): ISO timestamp of capture.
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
        zero_id (int): Affected zero reference identifier.
        action (str): Action performed ('activated' or 'deleted').
    """

    zero_id: int
    action: str
