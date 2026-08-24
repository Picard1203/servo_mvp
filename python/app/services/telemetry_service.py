"""Telemetry: periodic sampling, retention, and binary export."""

import io
import struct
from threading import Thread
from time import monotonic, sleep, time
from typing import Iterator

from Logger461 import logger

from app.core.config import Settings
from app.models.entities import TelemetrySample
from app.repositories.abstract.telemetry_repository import TelemetryRepository
from app.services.servo_state import ServoStateStore

# Binary telemetry payload struct format:
# Base Header: <dI (8-byte base timestamp, 4-byte sample count)
# Per Sample (18 bytes):
# H: raw_counts (uint16)
# h: output_deg * 100 (int16)
# h: temperature_c * 100 (int16)
# H: voltage_v * 100 (uint16)
# H: current_a * 100 (uint16)
# h: torque_kgcm * 100 (int16)
# B: flags bitmask
# I: dt_ms (uint32)
# B: pad
SAMPLE_STRUCT = struct.Struct("<HhhhhhBIB")
HEADER_STRUCT = struct.Struct("<dI")


class TelemetryService:
    """Persists the full sensory input every sampler interval."""

    def __init__(self, telemetry: TelemetryRepository,
                 state: ServoStateStore, settings: Settings) -> None:
        self._telemetry = telemetry
        self._state = state
        self._settings = settings
        self._last_purge = 0.0

    def start_sampler(self) -> None:
        """Starts the background sampling thread.

        Returns:
            None.
        """
        Thread(target=self._run, daemon=True).start()
        logger.info("telemetry sampler started",
                    metadata={"event": "telemetry.started"},
                    extra={"interval_s":
                           self._settings.sampler_interval_seconds})

    def export_binary_stream(self, ts_from: float, ts_to: float) -> Iterator[bytes]:
        """Packs telemetry samples in range into a compact binary byte stream.

        Args:
            ts_from: Range start, unix timestamp.
            ts_to: Range end, unix timestamp.

        Returns:
            An iterator over the packed binary bytes.
        """
        count, base_ts = self._telemetry.count_range(ts_from, ts_to, self._settings.export_max_rows)
        yield HEADER_STRUCT.pack(base_ts, count)

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
            buf += SAMPLE_STRUCT.pack(
                max(0, min(65535, int(sample.raw_counts))),
                max(-32768, min(32767, int(round(sample.output_deg * 100)))),
                max(-32768, min(32767, int(round(sample.temperature_c * 100)))),
                max(0, min(65535, int(round(sample.voltage_v * 100)))),
                max(0, min(65535, int(round(sample.current_a * 100)))),
                max(-32768, min(32767, int(round(sample.torque_kgcm * 100)))),
                flags,
                dt_ms,
                0
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
        """Samples until the process ends, at the configured interval.

        Returns:
            None.
        """
        while True:
            started = monotonic()
            try:
                self._sample_once()
                self._maybe_purge()
            except Exception:
                logger.exception("telemetry sampling failed",
                                 metadata={"event": "telemetry.error"})
            elapsed = monotonic() - started
            sleep(max(0.05,
                      self._settings.sampler_interval_seconds - elapsed))

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
            angle_fault=view.angle_fault))

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
