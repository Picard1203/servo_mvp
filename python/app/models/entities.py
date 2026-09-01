"""Immutable domain entities shared across layers."""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True, frozen=True)
class Calibration:
    """The calibration datum.

    Attributes:
        raw_counts (int): Absolute encoder position of the datum.
        captured_at (str): ISO timestamp of capture.
    """

    raw_counts: int
    captured_at: str


@dataclass(slots=True)
class SavedPosition:
    """A named, described position an operator can return to.

    Attributes:
        id (Optional[int]): Database identifier or None before saving.
        name (str): Unique operator-given name.
        description (str): Operator-given description of the position.
        raw_counts (int): Absolute encoder position in raw counts.
        created_at (str): ISO timestamp of creation.
        updated_at (str): ISO timestamp of the last edit.
    """

    id: Optional[int]
    name: str
    description: str
    raw_counts: int
    created_at: str
    updated_at: str


@dataclass(slots=True, frozen=True)
class SavedPositionView:
    """A saved position enriched with its live angle, for display.

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


@dataclass(slots=True, frozen=True)
class TelemetrySnapshot:
    """Instantaneous sensory readout from the servo layer.

    Attributes:
        raw_counts (int): Absolute multi-turn encoder count.
        moving (bool): True while a move is in progress.
        temperature_c (float): Servo temperature in Celsius.
        voltage_v (float): Supply voltage in Volts.
        current_a (float): Motor current in Amperes.
        torque_kgcm (float): Estimated output torque in kg*cm.
        overload (bool): True if overload protection tripped.
        overcurrent (bool): True if overcurrent fault flag set.
        overheat (bool): True if overheat fault flag set.
        voltage_fault (bool): True if supply voltage fault set.
        sensor_fault (bool): True if angle sensor fault set.
        angle_fault (bool): True if angle error flag set.
        valid (bool): True if readout was successfully received.
    """

    raw_counts: int
    moving: bool
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
    valid: bool = True


@dataclass(slots=True, frozen=True)
class TuningRegisters:
    """Diagnostic read of the servo's position-loop tuning registers.

    Attributes:
        position_p (int): Proportional gain register (0x15).
        position_d (int): Derivative gain register (0x16).
        position_i (int): Integral gain register (0x17).
        min_start_force (int): Minimum start-force register (0x18).
        cw_dead_zone (int): Clockwise dead-zone register (0x1A).
        ccw_dead_zone (int): Counter-clockwise dead-zone register (0x1B).
    """

    position_p: int
    position_d: int
    position_i: int
    min_start_force: int
    cw_dead_zone: int
    ccw_dead_zone: int


@dataclass(slots=True, frozen=True)
class ServoStateView:
    """Coherent snapshot of servo, lock, and baseline state.

    Attributes:
        output_deg (Optional[float]): Output angle or None if read failed.
        raw_counts (Optional[int]): Encoder counts or None if read failed.
        reading_valid (bool): False when servo did not answer read.
        moving (Optional[bool]): True if moving or None if read failed.
        locked (bool): Digital lock engagement state.
        settling (bool): True during post-lock settle delay window.
        position_verified (bool): True once datum calibration confirmed.
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
    raw_counts: Optional[int]
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


@dataclass(slots=True, frozen=True)
class TelemetrySample:
    """One persisted telemetry row.

    Attributes:
        timestamp (float): Unix timestamp of the sample.
        raw_counts (int): Encoder counts at sample time.
        output_deg (float): Output angle relative to the datum.
        moving (bool): True if motion was in progress.
        locked (bool): Digital lock engagement state.
        temperature_c (float): Servo temperature in Celsius.
        voltage_v (float): Supply voltage in Volts.
        current_a (float): Motor current in Amperes.
        torque_kgcm (float): Estimated torque in kg*cm.
        overload (bool): True if overload protection tripped.
        overcurrent (bool): True if overcurrent fault flag set.
        overheat (bool): True if overheat fault flag set.
        voltage_fault (bool): True if supply voltage fault set.
        sensor_fault (bool): True if angle sensor fault set.
        angle_fault (bool): True if angle error flag set.
        target_deg (Optional[float]): Target angle in effect or None.
        isolated (bool): True if motor isolation was in effect.
    """

    timestamp: float
    raw_counts: int
    output_deg: float
    moving: bool
    locked: bool
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
    target_deg: Optional[float] = None
    isolated: bool = False
