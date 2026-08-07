"""SQLite connection management and schema initialization."""

import sqlite3
from threading import Lock


class Database:
    """Owns the SQLite connection and serializes write access.

    SQLite permits concurrent readers; writes are serialized through
    ``write_lock`` because the sampler thread and API requests may write
    at the same time.
    """

    def __init__(self, path: str) -> None:
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        self.write_lock = Lock()
        self._init_schema()

    @property
    def connection(self) -> sqlite3.Connection:
        """Returns the shared SQLite connection.

        Returns:
            The open connection.
        """
        return self._connection

    def _init_schema(self) -> None:
        """Creates tables and indexes when missing.

        Returns:
            None.
        """
        with self.write_lock:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS zeros (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    raw_counts INTEGER NOT NULL,
                    is_active INTEGER NOT NULL DEFAULT 0,
                    is_datum INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS telemetry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    raw_counts INTEGER NOT NULL,
                    output_deg REAL NOT NULL,
                    moving INTEGER NOT NULL,
                    locked INTEGER NOT NULL,
                    temperature_c REAL NOT NULL,
                    voltage_v REAL NOT NULL,
                    current_a REAL NOT NULL,
                    torque_kgcm REAL NOT NULL,
                    overload INTEGER NOT NULL DEFAULT 0,
                    overcurrent INTEGER NOT NULL DEFAULT 0,
                    overheat INTEGER NOT NULL DEFAULT 0,
                    voltage_fault INTEGER NOT NULL DEFAULT 0,
                    sensor_fault INTEGER NOT NULL DEFAULT 0,
                    angle_fault INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_ts
                    ON telemetry (timestamp);
                """
            )
            self._connection.commit()
            self._migrate()

    def _migrate(self) -> None:
        """Adds columns introduced after a database was first created.

        Uses the ALTER-and-ignore pattern: adding a column that already
        exists raises OperationalError, which is safely ignored, so this
        is idempotent for both fresh and pre-existing databases.

        Returns:
            None.
        """
        migrations = (
            "ALTER TABLE zeros ADD COLUMN is_datum INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN overload INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN overcurrent INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN overheat INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN voltage_fault INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN sensor_fault INTEGER NOT NULL"
            " DEFAULT 0",
            "ALTER TABLE telemetry ADD COLUMN angle_fault INTEGER NOT NULL"
            " DEFAULT 0",
        )
        for statement in migrations:
            try:
                self._connection.execute(statement)
            except sqlite3.OperationalError:
                pass  # column already exists
        self._connection.commit()
