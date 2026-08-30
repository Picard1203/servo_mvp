"""Saved positions: named, described points the operator can return to."""

from datetime import datetime

from Logger461 import logger

from app.core.events import EventService
from app.core.exceptions import (
    NotFoundError,
    PositionOutOfRangeError,
    StalePositionError,
)
from app.models.entities import SavedPosition, SavedPositionView
from app.repositories.abstract.saved_position_repository import (
    SavedPositionRepository,
)
from app.services.motion_service import MotionService
from app.services.servo_state import ServoStateStore


class SavedPositionService:
    """Manages saved positions and moves the mechanism to one.

    Attributes:
        _positions (SavedPositionRepository): Saved-position persistence.
        _state (ServoStateStore): Shared servo and datum state.
        _motion (MotionService): Motion service used by go().
        _events (EventService): Event service for recording audit events.
        _revision (int): Bumped on every mutation, for change detection.
    """

    def __init__(self, positions: SavedPositionRepository,
                 state: ServoStateStore, motion: MotionService,
                 events: EventService) -> None:
        self._positions: SavedPositionRepository = positions
        self._state: ServoStateStore = state
        self._motion: MotionService = motion
        self._events: EventService = events
        self._revision: int = 0

    def revision(self) -> int:
        """Returns the current revision, bumped on every mutation.

        Returns:
            int: The revision counter.
        """
        return self._revision

    def list_all(self) -> list[SavedPositionView]:
        """Returns all saved positions with their live angle, newest first.

        Returns:
            list[SavedPositionView]: Saved positions enriched for display.
        """
        result: list[SavedPositionView] = []
        for position in self._positions.list_all():
            result.append(self._to_view(position))
        return result

    def create(self, name: str, description: str,
              target_deg: float) -> SavedPositionView:
        """Creates a saved position at the given angle.

        Args:
            name (str): Unique operator-given name.
            description (str): Operator-given description.
            target_deg (float): Output angle to store.

        Returns:
            SavedPositionView: The stored position, enriched for display.

        Raises:
            PositionOutOfRangeError: If the angle is unreachable.
            DuplicateNameError: If the name is already in use.
        """
        self._validate_reachable(target_deg)
        raw_counts = self._state.counts_from_output_deg(target_deg)
        now = datetime.now().isoformat(timespec="seconds")
        stored = self._positions.add(SavedPosition(
            id=None, name=name, description=description,
            raw_counts=raw_counts, created_at=now, updated_at=now))
        self._revision += 1
        self._events.record("position.saved", f"position '{name}' saved",
                            {"position_id": stored.id,
                             "raw_counts": raw_counts})
        logger.info("position saved",
                    metadata={"event": "position.saved"},
                    extra={"position_id": stored.id, "name": name,
                           "raw_counts": raw_counts})
        return self._to_view(stored)

    def update(self, position_id: int, name: str, description: str,
              target_deg: float,
              expected_updated_at: str) -> SavedPositionView:
        """Overwrites a saved position's name, description and angle.

        Args:
            position_id (int): Database identifier.
            name (str): New name.
            description (str): New description.
            target_deg (float): New output angle to store.
            expected_updated_at (str): The updated_at the caller last saw.

        Returns:
            SavedPositionView: The updated position, enriched for display.

        Raises:
            NotFoundError: If no position has this id.
            StalePositionError: If the position changed since it was read.
            PositionOutOfRangeError: If the angle is unreachable.
            DuplicateNameError: If the name is already in use elsewhere.
        """
        current = self._positions.get(position_id)
        if current is None:
            raise NotFoundError(f"position {position_id} does not exist")
        if current.updated_at != expected_updated_at:
            raise StalePositionError(
                "this position changed since it was last read")
        self._validate_reachable(target_deg)
        raw_counts = self._state.counts_from_output_deg(target_deg)
        now = datetime.now().isoformat(timespec="seconds")
        updated = self._positions.update(position_id, name, description,
                                         raw_counts, now)
        self._revision += 1
        self._events.record("position.updated", f"position '{name}' updated",
                            {"position_id": position_id,
                             "raw_counts": raw_counts})
        logger.info("position updated",
                    metadata={"event": "position.updated"},
                    extra={"position_id": position_id, "name": name,
                           "raw_counts": raw_counts})
        return self._to_view(updated)

    def delete(self, position_id: int, expected_updated_at: str) -> None:
        """Deletes a saved position.

        Args:
            position_id (int): Database identifier.
            expected_updated_at (str): The updated_at the caller last saw.

        Raises:
            NotFoundError: If no position has this id.
            StalePositionError: If the position changed since it was read.
        """
        current = self._positions.get(position_id)
        if current is None:
            raise NotFoundError(f"position {position_id} does not exist")
        if current.updated_at != expected_updated_at:
            raise StalePositionError(
                "this position changed since it was last read")
        self._positions.delete(position_id)
        self._revision += 1
        self._events.record("position.deleted", "position deleted",
                            {"position_id": position_id})
        logger.info("position deleted",
                    metadata={"event": "position.deleted"},
                    extra={"position_id": position_id})

    def go(self, position_id: int) -> None:
        """Moves the mechanism to a saved position.

        Args:
            position_id (int): Database identifier.

        Raises:
            NotFoundError: If no position has this id.
        """
        position = self._positions.get(position_id)
        if position is None:
            raise NotFoundError(f"position {position_id} does not exist")
        self._events.record("position.moved",
                            f"moving to position '{position.name}'",
                            {"position_id": position_id})
        logger.info("moving to saved position",
                    metadata={"event": "position.moved"},
                    extra={"position_id": position_id,
                           "raw_counts": position.raw_counts})
        self._motion.move_to_counts(position.raw_counts)

    def _validate_reachable(self, target_deg: float) -> None:
        """Refuses an angle the servo cannot reach from the current datum.

        Args:
            target_deg (float): Requested output angle.

        Raises:
            PositionOutOfRangeError: If the angle is unreachable.
        """
        if self._state.is_reachable(target_deg) is True:
            return
        low, high = self._state.reachable_output_range_deg()
        raise PositionOutOfRangeError(
            f"{target_deg:.2f} deg is outside the reachable range "
            f"({low:.2f} to {high:.2f} deg).")

    def _to_view(self, position: SavedPosition) -> SavedPositionView:
        """Enriches a saved position with its live angle for display.

        Args:
            position (SavedPosition): The stored entity.

        Returns:
            SavedPositionView: The position enriched for display.
        """
        datum_captured_at = self._state.datum_captured_at()
        stale = ((datum_captured_at is not None)
                 and (position.updated_at < datum_captured_at))
        return SavedPositionView(
            id=position.id, name=position.name,
            description=position.description, raw_counts=position.raw_counts,
            output_deg=round(
                self._state.output_deg_from_counts(position.raw_counts), 2),
            stale_reference=stale, created_at=position.created_at,
            updated_at=position.updated_at)
