"""Servo access through the Bridge to the MCU.

This is the production counterpart to SimulatedServoRepository. It speaks the
contract defined in sketch/src/BridgeApi.h: plain comma-separated payloads
over Bridge.call, chosen over a binary struct because they are readable in a
log and neither side can silently drift from a field order the other assumes.

Snapshot payload, in order:
    valid,counts,moving,temp_c,volt_v,curr_a,torque_kgcm,load,status_bits

Fault bits in the final field mirror the servo's status register 0x41:
    bit0 voltage, bit1 sensor, bit2 temperature, bit3 current,
    bit4 angle, bit5 overload
"""

import threading
import time
from typing import Optional

from Logger461 import logger

from app.models.entities import TelemetrySnapshot
from app.repositories.abstract.servo_repository import ServoRepository

_SIGN_BIT = 15

# Status register 0x41 bit positions, verified against the Feetech table.
_BIT_VOLTAGE = 1 << 0
_BIT_SENSOR = 1 << 1
_BIT_OVERHEAT = 1 << 2
_BIT_OVERCURRENT = 1 << 3
_BIT_ANGLE = 1 << 4
_BIT_OVERLOAD = 1 << 5

_SNAPSHOT_FIELDS = 9


def decode_sign_magnitude(value: int, sign_bit: int = _SIGN_BIT) -> int:
    """Decodes a sign-magnitude field from the servo wire format.

    STS position fields carry the sign in a dedicated bit rather than two's
    complement, so naive parsing shows roughly 32700 when the position
    crosses below zero. The sketch decodes this before sending, but the
    function stays here because the same rule applies to any raw register a
    caller reads directly.

    Args:
        value: Raw unsigned register value.
        sign_bit: Index of the sign bit (15 for position, 11 for the offset
            register 0x1F).

    Returns:
        The signed magnitude.
    """
    mask = 1 << sign_bit
    if value & mask:
        return -(value & (mask - 1))
    return value


class BridgeServoRepository(ServoRepository):
    """Talks to the servo through the MCU Bridge."""

    def __init__(self, bridge: Optional[object] = None,
                 cache_seconds: float = 0.25) -> None:
        """Creates the repository.

        Args:
            bridge: Object exposing call(name, payload). Defaults to the
                Arduino Bridge; injectable so tests need no board.
            cache_seconds: How long one servo reading may be reused. The
                telemetry sampler and every HTTP request all want the same
                value at roughly the same moment; without this they each pay
                a bus round trip.
        """
        if bridge is None:
            from arduino.app_utils import Bridge
            bridge = Bridge
        self._bridge = bridge
        # ONE Bridge conversation at a time. The RPC multiplexes requests and
        # replies over a single link by message id; two threads calling into
        # it concurrently interleave those ids, and a reply then arrives for
        # a request the caller has already abandoned - which shows up as
        # "Response for unknown msgid" followed by 10 s timeouts. The
        # sampler thread and every HTTP request both read the servo, so this
        # is not a rare race, it is the normal case.
        self._lock = threading.RLock()
        self._cache_seconds = cache_seconds
        self._cached: Optional[TelemetrySnapshot] = None
        self._cached_at = 0.0

    # ------------------------------------------------------------ reading

    def read_snapshot(self) -> TelemetrySnapshot:
        """Reads one coherent snapshot from the servo.

        Returns:
            The snapshot. On a bus failure every reading is zero and the
            fault flags are clear, matching what the sketch reports.
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
        """Performs one real bus read. The caller must hold the lock.

        Returns:
            The snapshot, or an empty one when the read failed.
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
                # The sketch says the bus did not answer. Everything after
                # field 0 is zero padding, not a reading. Treating it as data
                # is how a failed read once became a calibration datum of 0,
                # which silently put half the travel out of reach.
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

    # ------------------------------------------------------------ commands

    def command_move(self, target_counts: int, speed_counts_s: int,
                     acceleration: int) -> None:
        """Starts a move toward an absolute counts target.

        A new position command also clears a tripped overload, which is the
        servo's own rule for releasing the de-rate.

        Args:
            target_counts: Absolute encoder counts target.
            speed_counts_s: Speed in counts per second.
            acceleration: Servo acceleration parameter (0-254).

        Returns:
            None.
        """
        payload = f"{target_counts},{speed_counts_s},{acceleration}"
        self._command("servo_move", payload)

    def command_stop(self) -> None:
        """Stops motion at the current position.

        Returns:
            None.
        """
        self._command("servo_stop", "")

    def set_deadband(self, counts: int) -> None:
        """Configures the servo's dead-zone width.

        Args:
            counts: Dead-zone width in encoder counts (0-32).

        Returns:
            None.
        """
        self._command("servo_set_deadband", str(counts))

    def configure_range(self, multi_turn: bool,
                        angle_resolution: int) -> None:
        """Configures single-turn or multi-turn absolute positioning.

        Args:
            multi_turn: Enable multi-turn absolute positioning.
            angle_resolution: Amplification factor 1..3 (multi-turn only).

        Returns:
            None.
        """
        payload = f"{1 if multi_turn else 0},{angle_resolution}"
        self._command("servo_configure_range", payload)

    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores drive torque while sensors stay powered (R2).

        Uses _call directly, not _command: the ack is load-bearing here,
        unlike every other command in this class (see the abstract
        contract's docstring).

        Args:
            enabled: True to restore drive torque, false to cut it.

        Returns:
            True when the servo acknowledged the command.
        """
        with self._lock:
            reply = self._call("servo_set_torque", "1" if enabled else "0")
            self._cached = None          # state may have changed
        if reply != "ok":
            logger.warning("servo torque command not acknowledged",
                           metadata={"event": "servo.torque.rejected"},
                           extra={"enabled": enabled, "reply": reply})
        return reply == "ok"

    def read_torque_register(self) -> Optional[int]:
        """Reads register 0x28 directly (R2 board verification).

        Diagnostic only - independent of set_torque()'s own write
        acknowledgement, and not part of normal reconciliation.

        Returns:
            0 or 1 as read from the servo, or None when the read failed.
        """
        reply = self._call("servo_read_torque", "")
        if reply not in ("0", "1"):
            return None
        return int(reply)

    # ------------------------------------------------------------ internals

    def _call(self, name: str, payload: str) -> str:
        """Invokes a Bridge function, converting failures into empty results.

        Args:
            name: Bridge function name.
            payload: Request payload.

        Returns:
            The reply string, or an empty string when the call failed.
        """
        try:
            with self._lock:
                return str(self._bridge.call(name, payload))
        except Exception as exc:                      # noqa: BLE001
            logger.error("bridge call failed",
                         metadata={"event": "servo.bridge.error"},
                         extra={"function": name, "error": str(exc)})
            return ""

    def _command(self, name: str, payload: str) -> None:
        """Invokes a Bridge function and logs a non-ok acknowledgement.

        Args:
            name: Bridge function name.
            payload: Request payload.

        Returns:
            None.
        """
        with self._lock:
            reply = self._call(name, payload)
            self._cached = None          # state may have changed
        if reply != "ok":
            logger.warning("servo command not acknowledged",
                           metadata={"event": "servo.command.rejected"},
                           extra={"function": name, "reply": reply})

    @staticmethod
    def _empty_snapshot() -> TelemetrySnapshot:
        """Builds the reading used when the bus did not answer.

        Returns:
            A snapshot with zeroed readings and no faults raised.
        """
        return TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False, overcurrent=False,
            overheat=False, voltage_fault=False, sensor_fault=False,
            angle_fault=False, valid=False)
