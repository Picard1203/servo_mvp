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
            sample (TelemetrySample): The sample to store.
        """

    @abstractmethod
    def count_range(self, ts_from: float, ts_to: float,
                    limit: int) -> tuple[int, float]:
        """Counts samples in range and returns count and base timestamp.

        Args:
            ts_from (float): Range start unix timestamp.
            ts_to (float): Range end unix timestamp.
            limit (int): Maximum rows to count.

        Returns:
            tuple[int, float]: Matching sample count and base timestamp.
        """

    @abstractmethod
    def query(self, ts_from: float, ts_to: float,
              limit: int) -> Iterator[TelemetrySample]:
        """Yields samples inside a time range, oldest first.

        Args:
            ts_from (float): Range start unix timestamp.
            ts_to (float): Range end unix timestamp.
            limit (int): Maximum rows to yield.

        Returns:
            Iterator[TelemetrySample]: Iterator over matching samples.
        """

    @abstractmethod
    def purge_older_than(self, days: int) -> int:
        """Deletes samples older than the retention window.

        Args:
            days (int): Retention window in days.

        Returns:
            int: Number of deleted rows.
        """
