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
            zero (ZeroReference): Entity with id=None.

        Returns:
            ZeroReference: The stored entity with its assigned id.
        """

    @abstractmethod
    def list_all(self) -> list[ZeroReference]:
        """Returns all zero references, newest first.

        Returns:
            list[ZeroReference]: All stored zero references.
        """

    @abstractmethod
    def get(self, zero_id: int) -> Optional[ZeroReference]:
        """Returns one zero reference by id.

        Args:
            zero_id (int): Database identifier.

        Returns:
            Optional[ZeroReference]: Matching zero reference or None.
        """

    @abstractmethod
    def delete(self, zero_id: int) -> bool:
        """Deletes one zero reference.

        Args:
            zero_id (int): Database identifier.

        Returns:
            bool: True when a row was deleted.
        """

    @abstractmethod
    def set_active(self, zero_id: int) -> bool:
        """Marks one zero active and clears previous active flag.

        Args:
            zero_id (int): Database identifier.

        Returns:
            bool: True when the zero exists and was activated.
        """

    @abstractmethod
    def get_active(self) -> Optional[ZeroReference]:
        """Returns the active zero reference, if any.

        Returns:
            Optional[ZeroReference]: Active zero reference or None.
        """

    @abstractmethod
    def upsert_datum(self, raw_counts: int, created_at: str) -> ZeroReference:
        """Creates or updates the calibration datum zero.

        Args:
            raw_counts (int): Captured raw encoder counts.
            created_at (str): ISO timestamp of capture.

        Returns:
            ZeroReference: The stored datum zero entity.
        """
