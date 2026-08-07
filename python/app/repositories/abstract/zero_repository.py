"""Abstract persistence of zero references."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.entities import ZeroReference


class ZeroRepository(ABC):
    """Contract for storing and selecting zero references."""

    @abstractmethod
    def add(self, zero: ZeroReference) -> ZeroReference:
        """Persists a new zero reference.

        Args:
            zero: Entity with id=None.

        Returns:
            The stored entity with its assigned id.
        """

    @abstractmethod
    def list_all(self) -> list[ZeroReference]:
        """Returns all zero references, newest first.

        Returns:
            All stored zeros.
        """

    @abstractmethod
    def get(self, zero_id: int) -> Optional[ZeroReference]:
        """Returns one zero reference by id.

        Args:
            zero_id: Database id.

        Returns:
            The entity, or None when missing.
        """

    @abstractmethod
    def delete(self, zero_id: int) -> bool:
        """Deletes one zero reference.

        Args:
            zero_id: Database id.

        Returns:
            True when a row was deleted.
        """

    @abstractmethod
    def set_active(self, zero_id: int) -> bool:
        """Marks one zero active and clears the previous active flag.

        Args:
            zero_id: Database id.

        Returns:
            True when the zero exists and was activated.
        """

    @abstractmethod
    def get_active(self) -> Optional[ZeroReference]:
        """Returns the active zero reference, if any.

        Returns:
            The active zero, or None.
        """

    @abstractmethod
    def upsert_datum(self, raw_counts: int, created_at: str) -> ZeroReference:
        """Creates or updates THE calibration datum zero.

        At most one datum exists: the first call creates it (named
        'datum'), later calls update its captured counts and timestamp
        (re-homing after a power cycle re-captures the same reference).

        Args:
            raw_counts: Captured raw encoder counts at the reference.
            created_at: ISO timestamp of this capture.

        Returns:
            The stored datum zero.
        """
