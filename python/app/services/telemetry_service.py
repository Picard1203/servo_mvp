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

SAMPLE_STRUCT = struct.Struct("<HhhHHhBIBh")
HEADER_STRUCT = struct.Struct("<dIf")


class TelemetryService:
    """Persists the full sensory input every sampler interval.

    Attributes:
        _telemetry (TelemetryRepository): Repository storing telemetry history.
        _state (ServoStateStore): State store providing coherent snapshots.
        _settings (Settings): Application configuration settings.
        _isolation (Optional[IsolationService]): Optional isolation service.
        _last_purge (float): Monotonic timestamp of last retention purge.
        _stop_event (Event): Threading event signaling sampler stop.
        _thread (Optional[Thread]): Background sampling worker thread.
    """

    def __init__(self, telemetry: TelemetryRepository,
                 state: ServoStateStore, settings: Settings,
                 isolation: Optional[IsolationService] = None) -> None:
        self._telemetry: TelemetryRepository = telemetry
        self._state: ServoStateStore = state
        self._settings: Settings = settings
        self._isolation: Optional[IsolationService] = isolation
        self._last_purge: float = 0.0
        self._stop_event: Event = Event()
        self._thread: Optional[Thread] = None

    def start_sampler(self) -> None:
        """Starts the background sampling thread."""
        self._thread = Thread(target=self._run, daemon=True)
        self._thread.start()
        logger.info("telemetry sampler started",
                    metadata={"event": "telemetry.started"},
                    extra={"interval_s":
                           self._settings.sampler_interval_seconds})

    def stop_sampler(self) -> None:
        """Stops the background sampling thread, if one was started."""
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None

    def export_binary_stream(self, ts_from: float,
                             ts_to: float) -> Iterator[bytes]:
        """Packs telemetry samples in range into a compact binary byte stream.

        Args:
            ts_from (float): Range start unix timestamp.
            ts_to (float): Range end unix timestamp.

        Returns:
            Iterator[bytes]: Iterator over packed binary bytes chunks.
        """
        count, base_ts = self._telemetry.count_range(
            ts_from, ts_to, self._settings.export_max_rows)
        ratio = (self._settings.servo_deg_per_output_deg
                 * self._settings.servo_direction)
        yield HEADER_STRUCT.pack(base_ts, count, ratio)

        _BATCH = 500
        samples = self._telemetry.query(
            ts_from, ts_to, self._settings.export_max_rows)
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
            target_valid = (sample.target_deg is not None)
            target_packed = (max(-32768, min(32767,
                             int(round(sample.target_deg * 100))))
                             if target_valid is True else 0)
            target_valid_flags = ((1 if target_valid is True else 0)
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
        if len(buf) > 0:
            yield bytes(buf)

        logger.info("telemetry binary export served",
                    metadata={"event": "telemetry.exported"},
                    extra={"rows": count, "ts_from": ts_from, "ts_to": ts_to})

    def _run(self) -> None:
        """Samples until stopped, at the configured interval."""
        while self._stop_event.is_set() is False:
            started = monotonic()
            try:
                self._sample_once()
                self._maybe_purge()
                if self._isolation is not None:
                    self._isolation.tick()
            except Exception:
                logger.exception("telemetry sampling failed",
                                 metadata={"event": "telemetry.error"})
            elapsed = monotonic() - started
            self._stop_event.wait(
                max(0.05, self._settings.sampler_interval_seconds - elapsed))

    def _sample_once(self) -> None:
        """Reads one coherent snapshot and persists it."""
        view = self._state.snapshot()
        if view.reading_valid is False:
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
        """Applies retention at the configured interval."""
        now = monotonic()
        if (now - self._last_purge) < self._settings.telemetry_purge_interval_seconds:
            return
        self._last_purge = now
        deleted = self._telemetry.purge_older_than(
            self._settings.telemetry_retention_days)
        if deleted > 0:
            logger.info("purged old telemetry",
                        metadata={"event": "telemetry.purged"},
                        extra={"deleted": deleted})
