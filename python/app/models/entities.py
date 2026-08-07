"""Immutable domain entities shared across layers."""

from dataclasses import dataclass
from typing import Optional


@dataclass(slots=True)
class ZeroReference:
    """A saved baseline position.

    Attributes:
        id: Database id; None before persistence.
        name: Operator-given unique name.
        raw_counts: Servo raw encoder counts captured.
        is_active: Whether this zero is the current baseline.
        is_datum: Whether this zero is the install calibration datum
            (protected from deletion; at most one exists).
        created_at: ISO timestamp of capture.
    """

    id: Optional[int]
    name: str
    raw_counts: int
    is_active: bool
    is_datum: bool
    created_at: str


@dataclass(slots=True, frozen=True)
class TelemetrySnapshot:
    """Instantaneous sensory readout from the servo layer.

    Attributes:
        raw_counts: Absolute encoder counts (multi-turn; may exceed
            0..4095 and be negative - see ServoRepository contract).
        moving: True while a move is in progress.
        temperature_c: Servo temperature, Celsius.
        voltage_v: Supply voltage, Volts.
        current_a: Motor current, Amperes.
        torque_kgcm: Estimated output torque, kg*cm.
        overload: Servo overload protection tripped.
        overcurrent: Overcurrent fault flag.
        overheat: Overheat fault flag.
        voltage_fault: Supply-voltage fault flag.
        sensor_fault: Angle-sensor fault flag.
        angle_fault: Angle error flag (status bit 4).
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
class ServoStateView:
    """Coherent snapshot of servo + lock + baseline, read atomically.

    Attributes:
        output_deg: Output angle relative to the active zero, or None
            when the read failed. None means "not measured" and must
            never be substituted with a number: a failed read reports
            count 0, and 0 is indistinguishable from a genuine reading
            at the bottom of travel.
        raw_counts: Absolute encoder counts, or None when the read
            failed.
        reading_valid: False when the servo did not answer this read.
        moving: True while a move is in progress.
        locked: Digital lock state.
        settling: True while inside the post-lock settle window.
        position_verified: False after boot until calibration confirms
            the position reference (multi-turn context can be lost on
            power-off); True after a successful calibrate.
        active_zero_name: Name of the active baseline, or 'factory'.
        temperature_c: Servo temperature, Celsius.
        voltage_v: Supply voltage, Volts.
        current_a: Motor current, Amperes.
        torque_kgcm: Estimated output torque, kg*cm.
        overload: Servo overload protection tripped.
        overcurrent: Overcurrent fault flag.
        overheat: Overheat fault flag.
        voltage_fault: Supply-voltage fault flag.
        sensor_fault: Angle-sensor fault flag.
    """

    output_deg: Optional[float]
    raw_counts: Optional[int]
    reading_valid: bool
    moving: bool
    locked: bool
    settling: bool
    position_verified: bool
    active_zero_name: str
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


@dataclass(slots=True, frozen=True)
class TelemetrySample:
    """One persisted telemetry row.

    Attributes:
        timestamp: Unix timestamp of the sample.
        raw_counts: Encoder counts at sample time.
        output_deg: Output angle relative to the active zero.
        moving: Movement flag.
        locked: Digital lock state.
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
