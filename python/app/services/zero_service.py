"""Zero references: capture, selection and the active baseline."""

from datetime import datetime

from Logger461 import logger

from app.core.events import EventService
from app.core.exceptions import (ActiveZeroError, DatumZeroError,
                                 InvalidReadingError, NotFoundError)
from app.models.entities import ZeroReference
from app.repositories.abstract.servo_repository import ServoRepository
from app.repositories.abstract.zero_repository import ZeroRepository
from app.services.servo_state import ServoStateStore


class ZeroService:
    """Manages saved zeros, the active baseline, and calibration."""

    def __init__(self, zeros: ZeroRepository, servo: ServoRepository,
                 events: EventService, state: ServoStateStore,
                 settings=None) -> None:
        self._zeros = zeros
        self._servo = servo
        self._events = events
        self._state = state
        if settings is None:
            from app.core.config import get_settings
            settings = get_settings()
        self._settings = settings

    def capture(self, name: str) -> ZeroReference:
        """Captures the current position as a named zero.

        Args:
            name: Operator-given unique name.

        Raises:
            InvalidReadingError: When the servo did not answer. calibrate()
                has always guarded this; capture() did not, so a bus
                hiccup while an operator saved a named zero stored
                raw_counts=0. Activating that zero later strands the
                whole negative half of travel.

        Returns:
            The stored zero.
        """
        reading = self._servo.read_snapshot()
        if not reading.valid:
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
            Stored zeros.
        """
        return self._zeros.list_all()

    def activate(self, zero_id: int) -> None:
        """Sets one zero as the active baseline.

        Args:
            zero_id: Database id.

        Returns:
            None.

        Raises:
            NotFoundError: If no zero has this id.
        """
        if not self._zeros.set_active(zero_id):
            raise NotFoundError(f"zero {zero_id} does not exist")
        self._events.record("zero.activated", "zero activated",
                            {"zero_id": zero_id})
        logger.info("zero activated",
                    metadata={"event": "zero.activated"},
                    extra={"zero_id": zero_id})

    def delete(self, zero_id: int) -> None:
        """Deletes a zero reference.

        Args:
            zero_id: Database id.

        Returns:
            None.

        Raises:
            NotFoundError: If no zero has this id.
            ActiveZeroError: If the zero is the active baseline.
        """
        zero = self._zeros.get(zero_id)
        if zero is None:
            raise NotFoundError(f"zero {zero_id} does not exist")
        if zero.is_datum:
            raise DatumZeroError("cannot delete the calibration datum")
        if zero.is_active:
            raise ActiveZeroError("cannot delete the active zero")
        self._zeros.delete(zero_id)
        self._events.record("zero.deleted", "zero deleted",
                            {"zero_id": zero_id})
        logger.info("zero deleted",
                    metadata={"event": "zero.deleted"},
                    extra={"zero_id": zero_id})

    def calibrate(self) -> ZeroReference:
        """Captures the current physical position as the datum reference.

        To be called when the mechanism is physically at the documented
        reference position (install, and re-homing after any power-off).
        Creates or updates THE datum zero, makes it the active baseline,
        and marks the position reference verified for this power cycle.

        Returns:
            The stored datum zero.
        """
        reading = self._servo.read_snapshot()
        if not reading.valid:
            # Refusing here is the whole point. A failed read reports zero,
            # and a datum of zero silently puts the entire negative half of
            # the travel out of reach - the servo clamps at count 0 and
            # stops early while still reporting success.
            raise InvalidReadingError(
                "the servo did not answer, so there is no position to "
                "capture as the reference. Check the servo bus and retry.")
        raw_counts = reading.raw_counts

        # Warn if this datum leaves part of the configured window unreachable.
        span_counts = self._settings.counts_per_turn - 1
        half_window = int(
            max(abs(self._settings.output_min_deg),
                abs(self._settings.output_max_deg))
            * self._settings.servo_deg_per_output_deg
            * self._settings.counts_per_turn / 360.0)
        if raw_counts - half_window < 0 or raw_counts + half_window > span_counts:
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
