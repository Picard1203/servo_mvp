"""Domain exceptions, mapped to HTTP responses by the application layer."""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class LockedError(DomainError):
    """Raised when movement is requested while the digital lock is engaged."""


class MovingError(DomainError):
    """Raised when a lock change is requested while a move is in progress."""


class IsolatedError(DomainError):
    """Raised when movement is requested while the motor is isolated."""


class LockedAndIsolatedError(DomainError):
    """Raised when movement is refused for both reasons at once."""


class NotFoundError(DomainError):
    """Raised when a referenced entity does not exist."""


class ActiveZeroError(DomainError):
    """Raised when attempting to delete the active zero reference."""


class DatumZeroError(DomainError):
    """Raised when attempting to delete the calibration datum zero."""


class OutOfTravelError(DomainError):
    """Raised when a target lies outside the servo's physical count range."""


class InvalidReadingError(DomainError):
    """Raised when an operation needs a reading the servo did not supply."""


class StepError(DomainError):
    """Raised when a commanded angle violates the configured step size."""
