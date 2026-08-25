"""Request/response schemas for the servo router."""

from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.entities import ServoStateView

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
        moving: True while a move is in progress, or null when the servo
            did not answer (D23, amends ADR-0008). The rule stated above
            for output_deg governs this and the six fault flags below
            identically: a failed read states nothing measured, not
            "not moving, no faults" - clients must render null as
            unknown, not as false.
        locked: Digital lock state.
        settling: True while inside the post-lock settle window.
        position_verified: False after boot until calibration; a False
            here means the shown angle may be off by whole turns.
        active_zero: Name of the active baseline.
        temperature_c: Servo temperature in Celsius, or null when the
            servo did not answer. The rule stated above for output_deg
            applies to these four identically - a failed read is not a
            measurement, and 0.00 V shown as one reads to an operator
            as a servo that has lost power.
        voltage_v: Supply voltage in Volts, or null when the servo did
            not answer.
        current_a: Motor current in Amperes, or null when the servo did
            not answer.
        torque_kgcm: Estimated torque in kg*cm, or null when the servo
            did not answer.
        overload: Servo overload protection tripped, or null on a failed
            read (D23) - see moving's docstring above.
        overcurrent: Overcurrent fault flag, or null on a failed read.
        overheat: Overheat fault flag, or null on a failed read.
        voltage_fault: Supply-voltage fault flag, or null on a failed read.
        sensor_fault: Angle-sensor fault flag, or null on a failed read.
        angle_fault: Angle-sensor range fault flag, or null on a failed
            read.
        servo_deg: The servo's own shaft angle before the gear ratio,
            same baseline as output_deg. Follows output_deg's own
            validity.
        target_deg: The last target angle, or null if none since
            boot. Not a measurement - never render it as one.
        target_stale: True after a stop(); the target is kept, not
            cleared, but is no longer being pursued.
        output_min_deg: Lower reachable output angle from the active
            baseline.
        output_max_deg: Upper reachable output angle from the active
            baseline.
    """

    output_deg: Optional[float]
    reading_valid: bool
    moving: Optional[bool]
    locked: bool
    settling: bool
    position_verified: bool
    active_zero: str
    temperature_c: Optional[float]
    voltage_v: Optional[float]
    current_a: Optional[float]
    torque_kgcm: Optional[float]
    overload: Optional[bool]
    overcurrent: Optional[bool]
    overheat: Optional[bool]
    voltage_fault: Optional[bool]
    sensor_fault: Optional[bool]
    angle_fault: Optional[bool]
    servo_deg: Optional[float] = None
    target_deg: Optional[float] = None
    target_stale: bool = False
    output_min_deg: float = 0.0
    output_max_deg: float = 0.0

    @classmethod
    def from_view(cls, view: ServoStateView) -> "ServoStateResponse":
        """Builds the response from one coherent state view.

        The single builder for both call sites (the poller and the SSE
        stream) - two independent field lists here is exactly the twin-
        path shape that has cost this project four defects already.

        Args:
            view: The state store's snapshot.

        Returns:
            The API response.
        """
        return cls(
            output_deg=view.output_deg, reading_valid=view.reading_valid,
            moving=view.moving, locked=view.locked,
            settling=view.settling,
            position_verified=view.position_verified,
            active_zero=view.active_zero_name,
            temperature_c=view.temperature_c, voltage_v=view.voltage_v,
            current_a=view.current_a, torque_kgcm=view.torque_kgcm,
            overload=view.overload, overcurrent=view.overcurrent,
            overheat=view.overheat, voltage_fault=view.voltage_fault,
            sensor_fault=view.sensor_fault, angle_fault=view.angle_fault,
            servo_deg=view.servo_deg, target_deg=view.target_deg,
            target_stale=view.target_stale,
            output_min_deg=view.output_min_deg,
            output_max_deg=view.output_max_deg)
