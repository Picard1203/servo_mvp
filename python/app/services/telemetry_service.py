"""Telemetry: periodic sampling, retention, and CSV export."""

import csv
import io
from threading import Thread
from time import monotonic, sleep, time
from typing import Iterator

from Logger461 import logger

from app.core.config import Settings
from app.models.entities import TelemetrySample
from app.repositories.abstract.telemetry_repository import TelemetryRepository
from app.services.servo_state import ServoStateStore

_CSV_COLUMNS = ("timestamp", "raw_counts", "output_deg", "moving", "locked",
                "temperature_c", "voltage_v", "current_a", "torque_kgcm",
                "overload", "overcurrent", "overheat", "voltage_fault",
                "sensor_fault", "angle_fault")


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

    def export_csv(self, ts_from: float, ts_to: float) -> Iterator[str]:
        """Streams a CSV of samples in the range, capped for the relay.

        Args:
            ts_from: Range start, unix timestamp.
            ts_to: Range end, unix timestamp.

        Returns:
            An iterator of CSV text chunks, header first.
        """
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(_CSV_COLUMNS)
        yield buffer.getvalue()

        rows = 0
        for sample in self._telemetry.query(ts_from, ts_to,
                                            self._settings.export_max_rows):
            buffer.seek(0)
            buffer.truncate()
            writer.writerow((sample.timestamp, sample.raw_counts, sample.output_deg,
                             int(sample.moving), int(sample.locked),
                             sample.temperature_c, sample.voltage_v,
                             sample.current_a, sample.torque_kgcm,
                             int(sample.overload), int(sample.overcurrent),
                             int(sample.overheat), int(sample.voltage_fault),
                             int(sample.sensor_fault),
                             int(sample.angle_fault)))
            rows += 1
            yield buffer.getvalue()

        logger.info("telemetry export served",
                    metadata={"event": "telemetry.exported"},
                    extra={"rows": rows, "ts_from": ts_from, "ts_to": ts_to})

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

        Returns:
            None.
        """
        view = self._state.snapshot()
        self._telemetry.add(TelemetrySample(
            timestamp=time(),
            raw_counts=self._state.read_raw_counts(),
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
