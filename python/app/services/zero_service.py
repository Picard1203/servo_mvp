"""Zero references: capture, selection and the active baseline."""

from datetime import datetime

from Logger461 import logger

from app.core.events import EventService
from app.core.exceptions import (
    ActiveZeroError,
    DatumZeroError,
    InvalidReadingError,
    NotFoundError,
)
from app.models.entities import ZeroReference
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.zero_repository import ZeroRepository
from app.services.servo_state import ServoStateStore


class ZeroService:
    """Manages saved zeros, the active baseline, and calibration.

    Attributes:
        _zeros (ZeroRepository): Repository managing zero persistence.
        _servo (ServoRepository): Servo repository for position reads.
        _events (EventService): Event service for recording audit events.
        _state (ServoStateStore): State store tracking verified status.
        _settings (Settings): Application configuration settings.
    """

    def __init__(self, zeros: ZeroRepository, servo: ServoRepository,
                 events: EventService, state: ServoStateStore,
                 settings=None) -> None:
        self._zeros: ZeroRepository = zeros
        self._servo: ServoRepository = servo
        self._events: EventService = events
        self._state: ServoStateStore = state
        if settings is None:
            from app.core.config import get_settings
            settings = get_settings()
        self._settings = settings

    def capture(self, name: str) -> ZeroReference:
        """Captures the current position as a named zero.

        Args:
            name (str): Operator-given unique name.

        Returns:
            ZeroReference: The stored zero reference entity.

        Raises:
            InvalidReadingError: When the servo did not answer.
        """
        reading = self._servo.read_snapshot()
        if reading.valid is False:
            raise InvalidReadingError(
                "the servo did not answer; no zero was captured")
        zero = ZeroReference(
            id=None, name=name, raw_counts=reading.raw_counts,
            is_active=False, is_datum=False,
            created_at=datetime.now().isoformat(timespec="seconds"))
        stored = self._zeros.add(zero)
        self._events.record("zero.captured", f"zero '{name}' captured",
                            {"zero_id": stored.id,
                             "raw_counts": stored.raw_counts})
        logger.info("zero captured",
                    metadata={"event": "zero.captured", "name": name},
                    extra={"zero_id": stored.id,
                           "raw_counts": stored.raw_counts})
        return stored

    def list_all(self) -> list[ZeroReference]:
        """Returns all zeros, newest first.

        Returns:
            list[ZeroReference]: All stored zero references.
        """
        return self._zeros.list_all()

    def activate(self, zero_id: int) -> None:
        """Sets one zero as the active baseline.

        Args:
            zero_id (int): Database identifier.

        Raises:
            NotFoundError: If no zero has this id.
        """
        if self._zeros.set_active(zero_id) is False:
            raise NotFoundError(f"zero {zero_id} does not exist")
        self._events.record("zero.activated", "zero activated",
                            {"zero_id": zero_id})
        logger.info("zero activated",
                    metadata={"event": "zero.activated"},
                    extra={"zero_id": zero_id})

    def delete(self, zero_id: int) -> None:
        """Deletes a zero reference.

        Args:
            zero_id (int): Database identifier.

        Raises:
            NotFoundError: If no zero has this id.
            DatumZeroError: If the zero is the calibration datum.
            ActiveZeroError: If the zero is the active baseline.
        """
        zero = self._zeros.get(zero_id)
        if zero is None:
            raise NotFoundError(f"zero {zero_id} does not exist")
        if zero.is_datum is True:
            raise DatumZeroError("cannot delete the calibration datum")
        if zero.is_active is True:
            raise ActiveZeroError("cannot delete the active zero")
        self._zeros.delete(zero_id)
        self._events.record("zero.deleted", "zero deleted",
                            {"zero_id": zero_id})
        logger.info("zero deleted",
                    metadata={"event": "zero.deleted"},
                    extra={"zero_id": zero_id})

    def calibrate(self) -> ZeroReference:
        """Captures the current physical position as the datum reference.

        Returns:
            ZeroReference: The stored datum zero reference.

        Raises:
            InvalidReadingError: If the servo did not supply a reading.
        """
        reading = self._servo.read_snapshot()
        if reading.valid is False:
            raise InvalidReadingError(
                "the servo did not answer, so there is no position to "
                "capture as the reference. Check the servo bus and retry.")
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

        datum = self._zeros.upsert_datum(
            raw_counts, datetime.now().isoformat(timespec="seconds"))
        self._zeros.set_active(datum.id)
        self._state.mark_position_verified()
        self._events.record("servo.calibrated",
                            "calibrated: datum captured and activated",
                            {"zero_id": datum.id, "raw_counts": raw_counts})
        logger.info("calibrated: datum captured and activated",
                    metadata={"event": "servo.calibrated"},
                    extra={"zero_id": datum.id, "raw_counts": raw_counts})
        return self._zeros.get(datum.id)
