"""Servo access through the Bridge to the MCU."""

import threading
import time
from typing import Optional

from Logger461 import logger

from app.models.entities import TelemetrySnapshot, TuningRegisters
from app.repositories.abstract.servo_repository import ServoRepository

_TUNING_FIELDS = 7

_SIGN_BIT = 15

_BIT_VOLTAGE = 1 << 0
_BIT_SENSOR = 1 << 1
_BIT_OVERHEAT = 1 << 2
_BIT_OVERCURRENT = 1 << 3
_BIT_ANGLE = 1 << 4
_BIT_OVERLOAD = 1 << 5

_SNAPSHOT_FIELDS = 9


def decode_sign_magnitude(value: int, sign_bit: int = _SIGN_BIT) -> int:
    """Decodes a sign-magnitude field from the servo wire format.

    Args:
        value (int): Raw unsigned register value.
        sign_bit (int): Index of the sign bit.

    Returns:
        int: The signed magnitude.
    """
    mask = 1 << sign_bit
    if (value & mask) != 0:
        return -(value & (mask - 1))
    return value


class BridgeServoRepository(ServoRepository):
    """Talks to the servo through the MCU Bridge.

    Attributes:
        _bridge (object): Object exposing Bridge RPC call interface.
        _lock (threading.RLock): Reentrant lock serializing Bridge calls.
        _cache_seconds (float): Cache duration for servo snapshots.
        _cached (Optional[TelemetrySnapshot]): Cached snapshot instance.
        _cached_at (float): Monotonic timestamp of last cached read.
    """

    def __init__(self, bridge: Optional[object] = None,
                 cache_seconds: float = 0.25) -> None:
        """Creates the repository.

        Args:
            bridge (Optional[object]): Optional Bridge implementation.
            cache_seconds (float): Lifetime of cached servo readings.
        """
        if bridge is None:
            from arduino.app_utils import Bridge
            bridge = Bridge
        self._bridge = bridge
        self._lock = threading.RLock()
        self._cache_seconds = cache_seconds
        self._cached: Optional[TelemetrySnapshot] = None
        self._cached_at = 0.0

    def read_snapshot(self) -> TelemetrySnapshot:
        """Reads one coherent snapshot from the servo.

        Returns:
            TelemetrySnapshot: The latest snapshot readout.
        """
        with self._lock:
            now = time.monotonic()
            if (self._cached is not None
                    and now - self._cached_at < self._cache_seconds):
                return self._cached
            snapshot = self._read_uncached()
            self._cached = snapshot
            self._cached_at = time.monotonic()
            return snapshot

    def _read_uncached(self) -> TelemetrySnapshot:
        """Performs one real bus read.

        Returns:
            TelemetrySnapshot: The snapshot or empty fallback on failure.
        """
        raw = self._call("servo_read", "")
        parts = raw.split(",") if raw else []
        if len(parts) < _SNAPSHOT_FIELDS:
            logger.warning("servo snapshot malformed",
                           metadata={"event": "servo.read.malformed"},
                           extra={"payload": raw})
            return self._empty_snapshot()
        try:
            status = int(parts[8])
            if parts[0] != "1":
                logger.warning("servo reported an invalid reading",
                               metadata={"event": "servo.read.invalid"},
                               extra={"payload": raw})
                return self._empty_snapshot()
            return TelemetrySnapshot(
                raw_counts=int(parts[1]),
                moving=parts[2] == "1",
                temperature_c=float(parts[3]),
                voltage_v=float(parts[4]),
                current_a=float(parts[5]),
                torque_kgcm=float(parts[6]),
                overload=bool(status & _BIT_OVERLOAD),
                overcurrent=bool(status & _BIT_OVERCURRENT),
                overheat=bool(status & _BIT_OVERHEAT),
                voltage_fault=bool(status & _BIT_VOLTAGE),
                sensor_fault=bool(status & _BIT_SENSOR),
                angle_fault=bool(status & _BIT_ANGLE),
                valid=True)
        except ValueError:
            logger.warning("servo snapshot unparsable",
                           metadata={"event": "servo.read.unparsable"},
                           extra={"payload": raw})
            return self._empty_snapshot()

    def command_move(self, target_counts: int, speed_counts_s: int,
                     acceleration: int) -> bool:
        """Starts a move toward an absolute counts target.

        Args:
            target_counts (int): Absolute encoder counts target.
            speed_counts_s (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter (0-254).

        Returns:
            bool: True when the servo acknowledged the command.
        """
        payload = f"{target_counts},{speed_counts_s},{acceleration}"
        return self._command("servo_move", payload)

    def command_stop(self) -> bool:
        """Stops motion at the current position.

        Returns:
            bool: True when the servo acknowledged the command.
        """
        return self._command("servo_stop", "")

    def set_deadband(self, counts: int) -> None:
        """Configures the servo dead-zone width.

        Args:
            counts (int): Dead-zone width in encoder counts (0-32).
        """
        self._command("servo_set_deadband", str(counts))

    def configure_range(self, multi_turn: bool,
                        angle_resolution: int) -> None:
        """Configures single-turn or multi-turn absolute positioning.

        Args:
            multi_turn (bool): Enable multi-turn absolute positioning.
            angle_resolution (int): Amplification factor 1..3.
        """
        payload = f"{1 if multi_turn else 0},{angle_resolution}"
        self._command("servo_configure_range", payload)

    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores drive torque while sensors stay powered.

        Args:
            enabled (bool): True to restore drive torque, false to cut it.

        Returns:
            bool: True when the servo acknowledged the command.
        """
        with self._lock:
            reply = self._call("servo_set_torque", "1" if enabled else "0")
            self._cached = None
        if reply != "ok":
            logger.warning("servo torque command not acknowledged",
                           metadata={"event": "servo.torque.rejected"},
                           extra={"enabled": enabled, "reply": reply})
        return reply == "ok"

    def read_torque_register(self) -> Optional[int]:
        """Reads register 0x28 directly.

        Returns:
            Optional[int]: Register value (0 or 1), or None if read failed.
        """
        reply = self._call("servo_read_torque", "")
        if reply not in ("0", "1"):
            return None
        return int(reply)

    def read_tuning_registers(self) -> Optional[TuningRegisters]:
        """Reads the position-loop tuning registers directly.

        Returns:
            Optional[TuningRegisters]: The registers, or None if read failed.
        """
        raw = self._call("servo_read_tuning", "")
        parts = raw.split(",") if raw else []
        if len(parts) < _TUNING_FIELDS:
            return None
        try:
            if parts[0] != "1":
                return None
            return TuningRegisters(
                position_p=int(parts[1]),
                position_d=int(parts[2]),
                position_i=int(parts[3]),
                min_start_force=int(parts[4]),
                cw_dead_zone=int(parts[5]),
                ccw_dead_zone=int(parts[6]))
        except ValueError:
            return None

    def write_tuning_registers(
            self, position_p: Optional[int] = None,
            position_d: Optional[int] = None,
            position_i: Optional[int] = None,
            min_start_force: Optional[int] = None,
            cw_dead_zone: Optional[int] = None,
            ccw_dead_zone: Optional[int] = None) -> bool:
        """Writes any subset of the position-loop tuning registers directly.

        Args:
            position_p (Optional[int]): P gain, or None to leave it alone.
            position_d (Optional[int]): D gain, or None to leave it alone.
            position_i (Optional[int]): I gain, or None to leave it alone.
            min_start_force (Optional[int]): Minimum start force, or None.
            cw_dead_zone (Optional[int]): CW dead zone, or None.
            ccw_dead_zone (Optional[int]): CCW dead zone, or None.

        Returns:
            bool: True when every requested write was acknowledged.
        """
        fields = (position_p, position_d, position_i, min_start_force,
                 cw_dead_zone, ccw_dead_zone)
        payload = ",".join(str(-1 if field is None else field)
                           for field in fields)
        return self._command("servo_write_tuning", payload)

    def read_present_speed_counts_s(self) -> Optional[int]:
        """Reads the present-speed register directly.

        Returns:
            Optional[int]: Signed counts per second, or None if read failed.
        """
        reply = self._call("servo_read_speed", "")
        try:
            return int(reply)
        except ValueError:
            return None

    def _call(self, name: str, payload: str) -> str:
        """Invokes a Bridge function, converting failures into empty results.

        Args:
            name (str): Bridge function name.
            payload (str): Request payload string.

        Returns:
            str: The reply string or empty string on failure.
        """
        try:
            with self._lock:
                return str(self._bridge.call(name, payload))
        except Exception as exc:
            logger.error("bridge call failed",
                         metadata={"event": "servo.bridge.error"},
                         extra={"function": name, "error": str(exc)})
            return ""

    def _command(self, name: str, payload: str) -> bool:
        """Invokes a Bridge function and logs a non-ok acknowledgement.

        Args:
            name (str): Bridge function name.
            payload (str): Request payload string.

        Returns:
            bool: True when the Bridge replied "ok".
        """
        with self._lock:
            reply = self._call(name, payload)
            self._cached = None
        if reply != "ok":
            logger.warning("servo command not acknowledged",
                           metadata={"event": "servo.command.rejected"},
                           extra={"function": name, "reply": reply})
            return False
        return True

    @staticmethod
    def _empty_snapshot() -> TelemetrySnapshot:
        """Builds the reading used when the bus did not answer.

        Returns:
            TelemetrySnapshot: Snapshot with zeroed readings.
        """
        return TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False, overcurrent=False,
            overheat=False, voltage_fault=False, sensor_fault=False,
            angle_fault=False, valid=False)
