"""Telemetry: periodic sampling, retention, and binary export."""

import io
import struct
from threading import Event, Thread
from time import monotonic, time
from typing import Iterator, Optional

from Logger461 import logger

from app.core.config import Settings
from app.models.entities import TelemetrySample
from app.repositories.abstract.telemetry_repository import TelemetryRepository
from app.services.isolation_service import IsolationService
from app.services.servo_state import ServoStateStore

# Binary telemetry payload struct format. This is a twin path with
# parseBinaryTelemetry() in static/app.js - the two must be changed
# together, and this comment is the third statement of the same format,
# so all three must agree (a stale comment here once disagreed with both
# the struct string and the client - see BACKLOG.md).
#
# Base Header (16 bytes): <dIf
# d: base timestamp (unix seconds, float64)
# I: sample count (uint32)
# f: servo_deg per output_deg, signed by direction (float32) - the ONE
#    authoritative gear-ratio constant, sent as data so the client
#    derives servo angle rather than declaring a second copy of it
#    (ANGLE_STEP in app.js is the same class of duplication D9 cost).
#
# Per Sample (20 bytes): <HhhHHhBIBh
# H: raw_counts (uint16)
# h: output_deg * 100 (int16)
# h: temperature_c * 100 (int16)
# H: voltage_v * 100 (uint16) - never negative; was mis-typed 'h'
#    (signed) here while the comment and the client already agreed on
#    'H'. Fixed to match all three; no behaviour change at real values.
# H: current_a * 100 (uint16) - same fix, same reason.
# h: torque_kgcm * 100 (int16)
# B: flags bitmask
# I: dt_ms (uint32)
# B: target_valid_flags - bit0: target_valid (was a plain 0/1, an unused
#    pad byte before that). bit1: isolated (motor isolation, an app-held
#    state that is never null the way a servo reading can be, so it rides
#    a spare bit here rather than widening the sample - the flags byte
#    above has none left).
# h: target_deg * 100 (int16) - meaningless when bit0 is unset;
#    the client must render that as unknown, never as 0.0 deg (the
#    same rule output_deg's own null-on-failed-read already follows)
SAMPLE_STRUCT = struct.Struct("<HhhHHhBIBh")
HEADER_STRUCT = struct.Struct("<dIf")


class TelemetryService:
    """Persists the full sensory input every sampler interval."""

    def __init__(self, telemetry: TelemetryRepository,
                 state: ServoStateStore, settings: Settings,
                 isolation: Optional[IsolationService] = None) -> None:
        self._telemetry = telemetry
        self._state = state
        self._settings = settings
        self._isolation = isolation
        self._last_purge = 0.0
        self._stop_event = Event()
        self._thread: Optional[Thread] = None

    def start_sampler(self) -> None:
        """Starts the background sampling thread.

        Returns:
            None.
        """
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("telemetry sampler started",
                    metadata={"event": "telemetry.started"},
                    extra={"interval_s":
                           self._settings.sampler_interval_seconds})

    def stop_sampler(self) -> None:
        """Stops the background sampling thread, if one was started.

        Production never needs this - the process just exits. Tests
        build a fresh TelemetryService per case; without this, a thread
        started by one test kept running against that test's own (now
        stale) objects for the rest of the whole suite, silently reading
        state and logging into the shared test logger stub at any later
        moment - the exact shape of an unreproducible, timing-dependent
        failure (backlog D26). conftest.py's _clear_all_caches() calls
        this before dropping the cached instance.

        Returns:
            None.
        """
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def export_binary_stream(self, ts_from: float, ts_to: float) -> Iterator[bytes]:
        """Packs telemetry samples in range into a compact binary byte stream.

        Args:
            ts_from: Range start, unix timestamp.
            ts_to: Range end, unix timestamp.

        Returns:
            An iterator over the packed binary bytes.
        """
        count, base_ts = self._telemetry.count_range(ts_from, ts_to, self._settings.export_max_rows)
        ratio = (self._settings.servo_deg_per_output_deg
                 * self._settings.servo_direction)
        yield HEADER_STRUCT.pack(base_ts, count, ratio)

        # Batch samples into one relay write instead of one per sample - board-
        # validated 2026-08-23 (see BACKLOG.md D6): real gain, but the Bridge's
        # 224-byte-per-message ceiling (RELAY_NOTES.md S5) still dominates.
        _BATCH = 500
        samples = self._telemetry.query(ts_from, ts_to, self._settings.export_max_rows)
        buf = bytearray()
        for sample in samples:
            dt_ms = int(max(0.0, sample.timestamp - base_ts) * 1000)
            flags = (
                (1 if sample.moving else 0) |
                ((1 if sample.locked else 0) << 1) |
                ((1 if sample.overload else 0) << 2) |
                ((1 if sample.overcurrent else 0) << 3) |
                ((1 if sample.overheat else 0) << 4) |
                ((1 if sample.voltage_fault else 0) << 5) |
                ((1 if sample.sensor_fault else 0) << 6) |
                ((1 if sample.angle_fault else 0) << 7)
            )
            target_valid = sample.target_deg is not None
            target_packed = (max(-32768, min(32767,
                             int(round(sample.target_deg * 100))))
                             if target_valid else 0)
            target_valid_flags = ((1 if target_valid else 0)
                                  | ((1 if sample.isolated else 0) << 1))
            buf += SAMPLE_STRUCT.pack(
                max(0, min(65535, int(sample.raw_counts))),
                max(-32768, min(32767, int(round(sample.output_deg * 100)))),
                max(-32768, min(32767, int(round(sample.temperature_c * 100)))),
                max(0, min(65535, int(round(sample.voltage_v * 100)))),
                max(0, min(65535, int(round(sample.current_a * 100)))),
                max(-32768, min(32767, int(round(sample.torque_kgcm * 100)))),
                flags,
                dt_ms,
                target_valid_flags,
                target_packed
            )
            if len(buf) >= _BATCH * SAMPLE_STRUCT.size:
                yield bytes(buf)
                buf.clear()
        if buf:
            yield bytes(buf)

        logger.info("telemetry binary export served",
                    metadata={"event": "telemetry.exported"},
                    extra={"rows": count, "ts_from": ts_from, "ts_to": ts_to})

    def _run(self) -> None:
        """Samples until stopped, at the configured interval.

        Returns:
            None.
        """
        while not self._stop_event.is_set():
            started = monotonic()
            try:
                self._sample_once()
                self._maybe_purge()
                # Reuses this loop's own lifecycle rather than starting a
                # second thread for the isolation idle timer and retry -
                # one more thread with no stop mechanism is exactly the
                # shape of bug this loop's own stop_sampler() exists to
                # prevent.
                if self._isolation is not None:
                    self._isolation.tick()
            except Exception:
                logger.exception("telemetry sampling failed",
                                 metadata={"event": "telemetry.error"})
            elapsed = monotonic() - started
            self._stop_event.wait(
                max(0.05, self._settings.sampler_interval_seconds - elapsed))

    def _sample_once(self) -> None:
        """Reads one coherent snapshot and persists it.

        A failed read is skipped, not stored. It would land as position
        0, which reads exactly like a genuine sample at the bottom of
        travel; a gap in the series is honest and visible. The row is
        built from this one snapshot only - it used to take a second,
        independent read for raw_counts, so a single row could describe
        two different instants and every sample cost two Bridge calls.

        Returns:
            None.
        """
        view = self._state.snapshot()
        if not view.reading_valid:
            return
        self._telemetry.add(TelemetrySample(
            timestamp=time(),
            raw_counts=view.raw_counts,
            output_deg=view.output_deg,
            moving=view.moving,
            locked=view.locked,
            temperature_c=view.temperature_c,
            voltage_v=view.voltage_v,
            current_a=view.current_a,
            torque_kgcm=view.torque_kgcm,
            overload=view.overload,
            overcurrent=view.overcurrent,
            overheat=view.overheat,
            voltage_fault=view.voltage_fault,
            sensor_fault=view.sensor_fault,
            angle_fault=view.angle_fault,
            target_deg=view.target_deg,
            isolated=view.isolated))

    def _maybe_purge(self) -> None:
        """Applies retention at the configured interval.

        Returns:
            None.
        """
        now = monotonic()
        if now - self._last_purge < self._settings.telemetry_purge_interval_seconds:
            return
        self._last_purge = now
        deleted = self._telemetry.purge_older_than(
            self._settings.telemetry_retention_days)
        if deleted > 0:
            logger.info("purged old telemetry",
                        metadata={"event": "telemetry.purged"},
                        extra={"deleted": deleted})
