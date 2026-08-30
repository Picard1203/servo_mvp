"""Abstract persistence of saved positions."""

from abc import ABC, abstractmethod
from typing import Optional

from app.models.entities import SavedPosition


class SavedPositionRepository(ABC):
    """Contract for storing and editing saved positions."""

    @abstractmethod
    def add(self, position: SavedPosition) -> SavedPosition:
        """Persists a new saved position.

        Args:
            position (SavedPosition): Entity with id=None.

        Returns:
            SavedPosition: The stored entity with its assigned id.

        Raises:
            DuplicateNameError: If the name is already in use.
        """

    @abstractmethod
    def list_all(self) -> list[SavedPosition]:
        """Returns all saved positions, newest first.

        Returns:
            list[SavedPosition]: All stored saved positions.
        """

    @abstractmethod
    def get(self, position_id: int) -> Optional[SavedPosition]:
        """Returns one saved position by id.

        Args:
            position_id (int): Database identifier.

        Returns:
            Optional[SavedPosition]: Matching saved position or None.
        """

    @abstractmethod
    def update(self, position_id: int, name: str, description: str,
              raw_counts: int, updated_at: str) -> Optional[SavedPosition]:
        """Overwrites a saved position's editable fields.

        Args:
            position_id (int): Database identifier.
            name (str): New name.
            description (str): New description.
            raw_counts (int): New absolute encoder position.
            updated_at (str): ISO timestamp of this edit.

        Returns:
            Optional[SavedPosition]: The updated entity, or None if missing.

        Raises:
            DuplicateNameError: If the name is already in use elsewhere.
        """

    @abstractmethod
    def delete(self, position_id: int) -> bool:
        """Deletes one saved position.

        Args:
            position_id (int): Database identifier.

        Returns:
            bool: True when a row was deleted.
        """
