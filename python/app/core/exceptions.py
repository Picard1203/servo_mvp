"""Domain exceptions, mapped to HTTP responses by the application layer."""


class DomainError(Exception):
    """Base class for all domain-level errors."""


class LockedError(DomainError):
    """Raised when movement is requested while the digital lock is engaged."""


class MovingError(DomainError):
    """Raised when a lock change is requested while a move is in progress."""


class NotFoundError(DomainError):
    """Raised when a referenced entity does not exist."""


class ActiveZeroError(DomainError):
    """Raised when attempting to delete the active zero reference."""


class DatumZeroError(DomainError):
    """Raised when attempting to delete the calibration datum zero."""


class OutOfTravelError(DomainError):
    """Raised when a target lies outside the servo's physical count range.

    The servo is configured with angle limits 0..4095 and silently CLAMPS
    anything beyond them - it does not refuse, it just stops early and
    reports success. Commanding -90 deg from a datum captured near count 0
    therefore looked accepted while the mechanism halted at zero. This turns
    that silent clamp into an explicit refusal.
    """


class InvalidReadingError(DomainError):
    """Raised when an operation needs a reading the servo did not supply."""


class StepError(DomainError):
    """Raised when a commanded angle violates the configured step size."""
