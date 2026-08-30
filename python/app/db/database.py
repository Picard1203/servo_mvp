"""SQLite connection management and schema initialization."""

import sqlite3
from threading import Lock


class Database:
    """Owns the SQLite connection and serializes all access to it.

    Attributes:
        _connection (sqlite3.Connection): Active SQLite database connection.
        write_lock (Lock): Mutex serializing all SQLite operations.
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
            sqlite3.Connection: The open connection.
        """
        return self._connection

    def close(self) -> None:
        """Closes the connection."""
        self._connection.close()

    def _init_schema(self) -> None:
        """Creates tables and indexes when missing."""
        with self.write_lock:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS saved_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT NOT NULL DEFAULT '',
                    raw_counts INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
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
                    angle_fault INTEGER NOT NULL DEFAULT 0,
                    target_deg REAL,
                    isolated INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS idx_telemetry_ts
                    ON telemetry (timestamp);
                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                """
            )
            self._connection.commit()
            self._migrate()

    def _migrate(self) -> None:
        """Adds columns introduced after a database was first created."""
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
            "ALTER TABLE telemetry ADD COLUMN target_deg REAL",
            "ALTER TABLE telemetry ADD COLUMN isolated INTEGER NOT NULL"
            " DEFAULT 0",
        )
        for statement in migrations:
            try:
                self._connection.execute(statement)
            except sqlite3.OperationalError:
                pass
        self._connection.commit()
        self._migrate_zeros_to_datum_and_saved_positions()

    def _migrate_zeros_to_datum_and_saved_positions(self) -> None:
        """Carries the old zeros table's rows into app_state and saved_positions."""
        exists = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name = 'zeros'").fetchone()
        if exists is None:
            return
        datum = self._connection.execute(
            "SELECT raw_counts, created_at FROM zeros"
            " WHERE is_datum = 1").fetchone()
        if datum is not None:
            self._connection.execute(
                "INSERT INTO app_state (key, value, updated_at) VALUES"
                " ('datum_raw_counts', ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                " updated_at = excluded.updated_at",
                (str(datum["raw_counts"]), datum["created_at"]))
            self._connection.execute(
                "INSERT INTO app_state (key, value, updated_at) VALUES"
                " ('datum_captured_at', ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                " updated_at = excluded.updated_at",
                (datum["created_at"], datum["created_at"]))
        points = self._connection.execute(
            "SELECT name, raw_counts, created_at FROM zeros"
            " WHERE is_datum = 0").fetchall()
        for point in points:
            self._connection.execute(
                "INSERT INTO saved_positions (name, description, raw_counts,"
                " created_at, updated_at) VALUES (?, '', ?, ?, ?)",
                (point["name"], point["raw_counts"], point["created_at"],
                 point["created_at"]))
        self._connection.execute("DROP TABLE zeros")
        self._connection.commit()
