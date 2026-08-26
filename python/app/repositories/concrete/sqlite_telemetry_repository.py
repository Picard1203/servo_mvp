"""SQLite implementation of the telemetry repository."""

from time import time
from typing import Iterator

from app.db.database import Database
from app.models.entities import TelemetrySample


class SqliteTelemetryRepository:
    """Stores telemetry samples in the telemetry table.

    Attributes:
        _db (Database): Database wrapper providing SQLite access.
    """

    def __init__(self, database: Database) -> None:
        self._db: Database = database

    def add(self, sample: TelemetrySample) -> None:
        """Persists one sample.

        Args:
            sample (TelemetrySample): The sample to store.
        """
        with self._db.write_lock:
            self._db.connection.execute(
                "INSERT INTO telemetry (timestamp, raw_counts, output_deg, moving,"
                " locked, temperature_c, voltage_v, current_a, torque_kgcm,"
                " overload, overcurrent, overheat, voltage_fault,"
                " sensor_fault, angle_fault, target_deg, isolated)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (sample.timestamp, sample.raw_counts, sample.output_deg,
                 int(sample.moving), int(sample.locked), sample.temperature_c,
                 sample.voltage_v, sample.current_a, sample.torque_kgcm,
                 int(sample.overload), int(sample.overcurrent),
                 int(sample.overheat), int(sample.voltage_fault),
                 int(sample.sensor_fault), int(sample.angle_fault),
                 sample.target_deg, int(sample.isolated)))
            self._db.connection.commit()

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
        with self._db.write_lock:
            cursor = self._db.connection.execute(
                "SELECT COUNT(*), MIN(timestamp) FROM telemetry "
                "WHERE timestamp BETWEEN ? AND ?", (ts_from, ts_to))
            row = cursor.fetchone()
        c = row[0] if (row is not None) and (row[0] is not None) else 0
        c = min(c, limit)
        m = row[1] if (row is not None) and (row[1] is not None) else ts_from
        return c, m

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
        with self._db.write_lock:
            rows = self._db.connection.execute(
                "SELECT * FROM telemetry WHERE timestamp BETWEEN ? AND ?"
                " ORDER BY timestamp ASC LIMIT ?",
                (ts_from, ts_to, limit)).fetchall()
        for row in rows:
            yield TelemetrySample(
                timestamp=row["timestamp"], raw_counts=row["raw_counts"],
                output_deg=row["output_deg"], moving=bool(row["moving"]),
                locked=bool(row["locked"]), temperature_c=row["temperature_c"],
                voltage_v=row["voltage_v"], current_a=row["current_a"],
                torque_kgcm=row["torque_kgcm"],
                overload=bool(row["overload"]),
                overcurrent=bool(row["overcurrent"]),
                overheat=bool(row["overheat"]),
                voltage_fault=bool(row["voltage_fault"]),
                sensor_fault=bool(row["sensor_fault"]),
                angle_fault=bool(row["angle_fault"]),
                target_deg=row["target_deg"],
                isolated=bool(row["isolated"]))

    def purge_older_than(self, days: int) -> int:
        """Deletes samples older than the retention window.

        Args:
            days (int): Retention window in days.

        Returns:
            int: Number of deleted rows.
        """
        threshold = time() - days * 86_400
        with self._db.write_lock:
            cursor = self._db.connection.execute(
                "DELETE FROM telemetry WHERE timestamp < ?", (threshold,))
            self._db.connection.commit()
        return cursor.rowcount
