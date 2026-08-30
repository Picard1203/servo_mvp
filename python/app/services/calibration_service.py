"""Calibration: captures the datum, the one absolute position reference."""

from datetime import datetime

from Logger461 import logger

from app.core.events import EventService
from app.core.exceptions import InvalidReadingError
from app.models.entities import Calibration
from app.repositories.abstract.app_state_repository import AppStateRepository
from app.repositories.abstract.servo_repository import ServoRepository
from app.services.servo_state import ServoStateStore

_DATUM_RAW_COUNTS_KEY = "datum_raw_counts"
_DATUM_CAPTURED_AT_KEY = "datum_captured_at"


class CalibrationService:
    """Captures the current physical position as the datum.

    Attributes:
        _servo (ServoRepository): Servo repository for position reads.
        _app_state (AppStateRepository): Repository storing the datum.
        _events (EventService): Event service for recording audit events.
        _state (ServoStateStore): State store tracking verified status.
        _settings (Settings): Application configuration settings.
    """

    def __init__(self, servo: ServoRepository, app_state: AppStateRepository,
                 events: EventService, state: ServoStateStore,
                 settings=None) -> None:
        self._servo: ServoRepository = servo
        self._app_state: AppStateRepository = app_state
        self._events: EventService = events
        self._state: ServoStateStore = state
        if settings is None:
            from app.core.config import get_settings
            settings = get_settings()
        self._settings = settings

    def calibrate(self) -> Calibration:
        """Captures the current physical position as the datum.

        Returns:
            Calibration: The stored datum.

        Raises:
            InvalidReadingError: If the servo did not supply a reading.
        """
        reading = self._servo.read_snapshot()
        if reading.valid is False:
            raise InvalidReadingError(
                "the servo did not answer, so there is no position to "
                "capture as the reference. Check the servo bus and retry.",
                metadata={"operation": "calibrate"})
        raw_counts = reading.raw_counts

        span_counts = self._settings.counts_per_turn - 1
        half_window = int(
            max(abs(self._settings.output_min_deg),
                abs(self._settings.output_max_deg))
            * self._settings.servo_deg_per_output_deg
            * self._settings.counts_per_turn / 360.0)
        if (raw_counts - half_window < 0) or (raw_counts + half_window > span_counts):
            logger.warning(
                "reference captured near an end of travel; part of the "
                "configured range will be unreachable",
                metadata={"event": "servo.calibrate.off_centre"},
                extra={"raw_counts": raw_counts,
                       "needed_either_side": half_window,
                       "usable_counts": span_counts})

        captured_at = datetime.now().isoformat(timespec="seconds")
        self._app_state.set(_DATUM_RAW_COUNTS_KEY, str(raw_counts), captured_at)
        self._app_state.set(_DATUM_CAPTURED_AT_KEY, captured_at, captured_at)
        self._state.mark_position_verified()
        self._events.record("servo.calibrated", "calibrated: datum captured",
                            {"raw_counts": raw_counts})
        logger.info("calibrated: datum captured",
                    metadata={"event": "servo.calibrated"},
                    extra={"raw_counts": raw_counts})
        return Calibration(raw_counts=raw_counts, captured_at=captured_at)
