"""Domain exceptions: each carries its own HTTP mapping and log metadata."""

from typing import Optional

from fastapi import status


class ServoAppException(Exception):
    """Base for every domain exception.

    Every subclass declares only its own error-code segment via the
    ``code`` class keyword; ``__init_subclass__`` appends it to the
    parent's already-accumulated code, so no subclass repeats its
    ancestors' path. ``metadata`` is accepted here once and reaches every
    subclass unchanged, since none override ``__init__``.

    Attributes:
        status_code (int): FastAPI status code this exception maps to.
        error_code (str): Dot-separated, all-caps hierarchical error code.
        reason (str): Short snake_case reason the client switches on.
        message (str): Human-readable detail.
        metadata (dict): Structured context for the top-level log line.
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code: str = "SERVO_MVP"
    reason: str = "internal_error"

    def __init_subclass__(cls, code: Optional[str] = None, **kwargs) -> None:
        """Appends this class's error-code segment to its parent's.

        Args:
            code (Optional[str]): This class's own segment, if any.
            **kwargs (object): Forwarded to the next __init_subclass__.
        """
        super().__init_subclass__(**kwargs)
        if code is not None:
            cls.error_code = cls.error_code + "." + code

    def __init__(self, message: str,
                metadata: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.metadata = metadata or {}


class ConflictException(ServoAppException, code="CONFLICT"):
    """Base for 409s: refused given the system's current state."""

    status_code = status.HTTP_409_CONFLICT


class NotFoundException(ServoAppException, code="NOT_FOUND"):
    """Base for 404s: a referenced entity does not exist."""

    status_code = status.HTTP_404_NOT_FOUND


class ValidationException(ServoAppException, code="VALIDATION"):
    """Base for 422s: well-formed but refused on its content."""

    status_code = status.HTTP_422_UNPROCESSABLE_CONTENT


class LockedError(ConflictException, code="LOCKED"):
    """Raised when movement is requested while the digital lock is engaged."""

    reason = "locked"


class MovingError(ConflictException, code="MOVING"):
    """Raised when a lock change is requested while a move is in progress."""

    reason = "moving"


class IsolatedError(ConflictException, code="ISOLATED"):
    """Raised when movement is requested while the motor is isolated."""

    reason = "isolated"


class LockedAndIsolatedError(ConflictException, code="LOCKED_AND_ISOLATED"):
    """Raised when movement is refused for both reasons at once."""

    reason = "locked_isolated"


class DuplicateNameError(ConflictException, code="DUPLICATE_NAME"):
    """Raised when a saved position name is already in use."""

    reason = "duplicate_name"


class StalePositionError(ConflictException, code="STALE_POSITION"):
    """Raised when an edit targets a saved position changed since it was read."""

    reason = "stale_position"


class InvalidReadingError(ConflictException, code="INVALID_READING"):
    """Raised when an operation needs a reading the servo did not supply."""

    reason = "invalid_reading"


class NotFoundError(NotFoundException, code="ENTITY_NOT_FOUND"):
    """Raised when a referenced entity does not exist."""

    reason = "not_found"


class OutOfTravelError(ValidationException, code="OUT_OF_TRAVEL"):
    """Raised when a target lies outside the servo's physical count range."""

    reason = "out_of_travel"


class PositionOutOfRangeError(ValidationException, code="OUT_OF_TRAVEL"):
    """Raised when a saved position's angle falls outside the travel window."""

    reason = "out_of_travel"


class StepError(ValidationException, code="STEP"):
    """Raised when a commanded angle violates the configured step size."""

    reason = "step"
