"""Abstract persistence of small operator-intent flags that survive a reboot."""

from abc import ABC, abstractmethod
from typing import Optional


class AppStateRepository(ABC):
    """Contract for a small persisted key-value store of operator intent."""

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Returns a stored value.

        Args:
            key (str): State key to retrieve.

        Returns:
            Optional[str]: The stored value, or None when never set.
        """

    @abstractmethod
    def set(self, key: str, value: str, updated_at: str) -> None:
        """Persists a value, replacing any previous one for the same key.

        Args:
            key (str): State key to persist.
            value (str): Value string to store.
            updated_at (str): ISO timestamp of this write.
        """
