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
        moving: True while a move is in progress, or None when the read
            failed. The rule stated for output_deg governs this and the
            six fault flags below identically (D23, amends ADR-0008): a
            failed read states nothing measured, not "not moving, no
            faults" - false statements about hardware nothing was heard
            from.
        locked: Digital lock state.
        settling: True while inside the post-lock settle window.
        position_verified: False after boot until calibration confirms
            the position reference (multi-turn context can be lost on
            power-off); True after a successful calibrate.
        active_zero_name: Name of the active baseline, or 'factory'.
        temperature_c: Servo temperature in Celsius, or None when the
            read failed. The rule stated for output_deg governs these
            four readings identically: a failed read reports 0.0 for
            each, and 0.0 V is indistinguishable from a genuine
            measurement of a servo that has lost power.
        voltage_v: Supply voltage in Volts, or None when the read
            failed.
        current_a: Motor current in Amperes, or None when the read
            failed.
        torque_kgcm: Estimated output torque in kg*cm, or None when the
            read failed.
        overload: Servo overload protection tripped, or None on a failed
            read (D23) - see moving's docstring above.
        overcurrent: Overcurrent fault flag, or None on a failed read.
        overheat: Overheat fault flag, or None on a failed read.
        voltage_fault: Supply-voltage fault flag, or None on a failed read.
        sensor_fault: Angle-sensor fault flag, or None on a failed read.
        angle_fault: Angle-sensor range fault flag, or None on a failed
            read.
        servo_deg: The servo's own shaft angle, before the gear ratio -
            same baseline as output_deg (zero at the datum), just
            un-geared. Follows output_deg's own validity: None exactly
            when output_deg is None.
        target_deg: The last target angle, or None if no move has
            been commanded since boot. Independent of reading_valid - a
            target is still known when the servo goes silent. Never a
            measurement; never substituted with 0.0.
        target_stale: True after stop() until the next accepted move -
            the target is kept (not cleared) but is no longer being
            pursued.
        output_min_deg: Lower reachable output angle from the active
            baseline (see ServoStateStore.reachable_output_range_deg).
        output_max_deg: Upper reachable output angle from the active
            baseline. Sent so the client can scale a travel display
            against the real range instead of a second, hardcoded copy
            of it - the config already lives in exactly one place.
    """

    output_deg: Optional[float]
    raw_counts: Optional[int]
    reading_valid: bool
    moving: Optional[bool]
    locked: bool
    settling: bool
    position_verified: bool
    active_zero_name: str
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
        target_deg: The target angle in effect at sample time, or None
            when no move had been commanded since boot. Servo-side degree
            (pre-ratio) is NOT stored - it is a pure function of
            output_deg and the (fixed) gear ratio, so storing it would
            duplicate data across a 30-day export for nothing.
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
