"""Abstract persistence of small operator-intent flags that survive a reboot."""

from abc import ABC, abstractmethod
from typing import Optional


class AppStateRepository(ABC):
    """Contract for a small persisted key/value store of operator intent.

    Not a general settings store - this exists specifically for latched
    operator decisions that must survive a restart (ADR-0010), starting
    with motor isolation and shaped to carry R8's emergency-stop latch
    later without a new mechanism.
    """

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Returns a stored value.

        Args:
            key: State key.

        Returns:
            The stored value, or None when never set.
        """

    @abstractmethod
    def set(self, key: str, value: str, updated_at: str) -> None:
        """Persists a value, replacing any previous one for the same key.

        Args:
            key: State key.
            value: Value to store.
            updated_at: ISO timestamp of this write.

        Returns:
            None.
        """
