"""Request/response schemas for the servo router."""

from typing import Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.models.entities import ServoStateView

_settings = get_settings()


class MoveRequest(BaseModel):
    """Command to move to an output angle relative to the datum.

    Attributes:
        target_deg (float): Target output angle in degrees.
        acceleration (int): Servo acceleration parameter (0-254).
    """

    target_deg: float = Field(ge=_settings.output_min_deg,
                              le=_settings.output_max_deg)
    acceleration: int = Field(default=_settings.default_acceleration, ge=0,
                              le=_settings.max_acceleration)


class LockRequest(BaseModel):
    """Command to engage or release the digital lock.

    Attributes:
        locked (bool): Desired lock state.
    """

    locked: bool


class MoveAcceptedResponse(BaseModel):
    """Acknowledgement of an accepted move.

    Attributes:
        accepted (bool): Always True on success.
        target_deg (float): The accepted output angle.
    """

    accepted: bool
    target_deg: float


class StopResponse(BaseModel):
    """Acknowledgement of a stop command.

    Attributes:
        stopped (bool): Always True on success.
    """

    stopped: bool


class LockResponse(BaseModel):
    """Result of a lock-state change.

    Attributes:
        locked (bool): The applied lock state.
    """

    locked: bool


class IsolateRequest(BaseModel):
    """Command to engage or release motor isolation.

    Attributes:
        isolated (bool): Desired isolation state.
    """

    isolated: bool


class IsolateResponse(BaseModel):
    """Acknowledgement of an isolation-state change request.

    Attributes:
        isolated (bool): The operator isolation intent that was set.
    """

    isolated: bool


class TorqueRegisterResponse(BaseModel):
    """Diagnostic read of the servo torque-enable register.

    Attributes:
        torque_register (Optional[int]): Register value (0 or 1), or None.
    """

    torque_register: Optional[int]


class CalibrationResponse(BaseModel):
    """Result of capturing the datum.

    Attributes:
        raw_counts (int): Absolute encoder position of the datum.
        captured_at (str): ISO timestamp of capture.
    """

    raw_counts: int
    captured_at: str


class RecoverResponse(BaseModel):
    """Acknowledgement of an overload recovery action.

    Attributes:
        recovered (bool): Always True on success.
    """

    recovered: bool


class ServoStateResponse(BaseModel):
    """Full state snapshot for the client poller.

    Attributes:
        output_deg (Optional[float]): Output angle or None if read failed.
        reading_valid (bool): False when snapshot has no valid position.
        moving (Optional[bool]): True if moving or None if read failed.
        locked (bool): Digital lock state.
        settling (bool): True during post-lock settle delay window.
        position_verified (bool): True once position reference confirmed.
        temperature_c (Optional[float]): Temperature or None if read failed.
        voltage_v (Optional[float]): Voltage or None if read failed.
        current_a (Optional[float]): Current or None if read failed.
        torque_kgcm (Optional[float]): Torque or None if read failed.
        overload (Optional[bool]): Overload flag or None if read failed.
        overcurrent (Optional[bool]): Overcurrent or None if read failed.
        overheat (Optional[bool]): Overheat flag or None if read failed.
        voltage_fault (Optional[bool]): Voltage fault or None if read failed.
        sensor_fault (Optional[bool]): Sensor fault or None if read failed.
        angle_fault (Optional[bool]): Angle fault or None if read failed.
        servo_deg (Optional[float]): Pre-ratio servo angle or None.
        target_deg (Optional[float]): Commanded target angle or None.
        target_stale (bool): True after stop until next commanded move.
        output_min_deg (float): Minimum reachable output angle limit.
        output_max_deg (float): Maximum reachable output angle limit.
        isolated (bool): True if motor isolation was acknowledged.
        isolation_idle_timeout_s (float): Idle timeout before auto-isolation.
    """

    output_deg: Optional[float]
    reading_valid: bool
    moving: Optional[bool]
    locked: bool
    settling: bool
    position_verified: bool
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
    isolated: bool = False
    isolation_idle_timeout_s: float = 0.0

    @classmethod
    def from_view(cls, view: ServoStateView) -> "ServoStateResponse":
        """Builds the response from one coherent state view.

        Args:
            view (ServoStateView): The state store snapshot.

        Returns:
            ServoStateResponse: The API response model.
        """
        return cls(
            output_deg=view.output_deg, reading_valid=view.reading_valid,
            moving=view.moving, locked=view.locked,
            settling=view.settling,
            position_verified=view.position_verified,
            temperature_c=view.temperature_c, voltage_v=view.voltage_v,
            current_a=view.current_a, torque_kgcm=view.torque_kgcm,
            overload=view.overload, overcurrent=view.overcurrent,
            overheat=view.overheat, voltage_fault=view.voltage_fault,
            sensor_fault=view.sensor_fault, angle_fault=view.angle_fault,
            servo_deg=view.servo_deg, target_deg=view.target_deg,
            target_stale=view.target_stale,
            output_min_deg=view.output_min_deg,
            output_max_deg=view.output_max_deg,
            isolated=view.isolated,
            isolation_idle_timeout_s=view.isolation_idle_timeout_s)
