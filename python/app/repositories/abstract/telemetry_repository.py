"""Abstract persistence of telemetry samples."""

from abc import ABC, abstractmethod
from typing import Iterator

from app.models.entities import TelemetrySample


class TelemetryRepository(ABC):
    """Contract for storing and querying telemetry history."""

    @abstractmethod
    def add(self, sample: TelemetrySample) -> None:
        """Persists one sample.

        Args:
            sample: The sample to store.

        Returns:
            None.
        """

    @abstractmethod
    def query(self, ts_from: float, ts_to: float,
              limit: int) -> Iterator[TelemetrySample]:
        """Yields samples inside a time range, oldest first.

        Args:
            ts_from: Range start, unix timestamp.
            ts_to: Range end, unix timestamp.
            limit: Maximum rows to yield.

        Returns:
            An iterator over matching samples.
        """

    @abstractmethod
    def purge_older_than(self, days: int) -> int:
        """Deletes samples older than the retention window.

        Args:
            days: Retention in days.

        Returns:
            Number of deleted rows.
        """
