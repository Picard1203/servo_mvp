"""Request/response schemas for the servo router."""

from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings

_settings = get_settings()


class MoveRequest(BaseModel):
    """Command to move to an output angle relative to the active zero.

    Attributes:
        target_deg: Target output angle in degrees.
        speed_dps: Output speed in degrees per second.
        acceleration: Servo acceleration parameter (native units, 0-254).
    """

    target_deg: float = Field(ge=_settings.output_min_deg,
                              le=_settings.output_max_deg)
    speed_dps: float = Field(default=_settings.default_speed_dps, gt=0.0,
                             le=_settings.max_speed_dps)
    acceleration: int = Field(default=_settings.default_acceleration, ge=0,
                              le=_settings.max_acceleration)


class LockRequest(BaseModel):
    """Command to engage or release the digital lock.

    Attributes:
        locked: Desired lock state.
    """

    locked: bool


class MoveAcceptedResponse(BaseModel):
    """Acknowledgement of an accepted move.

    Attributes:
        accepted: Always True on success.
        target_deg: The accepted output angle.
    """

    accepted: bool
    target_deg: float


class StopResponse(BaseModel):
    """Acknowledgement of a stop command.

    Attributes:
        stopped: Always True on success.
    """

    stopped: bool


class LockResponse(BaseModel):
    """Result of a lock-state change.

    Attributes:
        locked: The applied lock state.
    """

    locked: bool


class RecoverResponse(BaseModel):
    """Acknowledgement of an overload recovery action.

    Attributes:
        recovered: Always True on success.
    """

    recovered: bool


class ServoStateResponse(BaseModel):
    """Full state snapshot for the client poller.

    Attributes:
        output_deg: Current output angle vs. the active zero, or null
            when the servo did not answer. Clients must render null as
            "unknown" and never as 0 - a failed read is not a position.
        reading_valid: False when this snapshot has no position in it.
        moving: True while a move is in progress.
        locked: Digital lock state.
        settling: True while inside the post-lock settle window.
        position_verified: False after boot until calibration; a False
            here means the shown angle may be off by whole turns.
        active_zero: Name of the active baseline.
        temperature_c: Servo temperature, Celsius.
        voltage_v: Supply voltage, Volts.
        current_a: Motor current, Amperes.
        torque_kgcm: Estimated torque, kg*cm.
        overload: Servo overload protection tripped.
        overcurrent: Overcurrent fault flag.
        overheat: Overheat fault flag.
        voltage_fault: Supply-voltage fault flag.
        sensor_fault: Angle-sensor fault flag.
    """

    output_deg: Optional[float]
    reading_valid: bool
    moving: bool
    locked: bool
    settling: bool
    position_verified: bool
    active_zero: str
    temperature_c: float
    voltage_v: float
    current_a: float
    torque_kgcm: float
    overload: bool
    overcurrent: bool
    overheat: bool
    voltage_fault: bool
    sensor_fault: bool
    angle_fault: bool
