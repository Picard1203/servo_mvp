"""SQLite connection management and schema initialization."""

import sqlite3
from threading import Lock


class Database:
    """Owns the SQLite connection and serializes all access to it.

    ``write_lock`` guards every statement, not only writes: this class
    holds one ``sqlite3.Connection`` (``check_same_thread=False``) shared
    across the sampler thread and API request threads. SQLite's
    "concurrent readers" guarantee assumes separate connections; two
    threads calling ``execute()`` on the *same* Python connection object
    without a shared lock can hand back a corrupted ``sqlite3.Row`` -
    reproduced under this repo's actual read/write pattern as both a
    silent ``None`` in a ``NOT NULL`` column and an outright
    ``IndexError`` (D10). Every repository built on this class must run
    its statements - reads included - through ``write_lock``.
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

    def close(self) -> None:
        """Closes the connection.

        The process-wide singleton never needs this in production - the
        OS reclaims it at process exit. Tests build a fresh Database per
        case and drop the old one from an lru_cache without ever calling
        this, which left every run's teardown to an unpredictable GC pass
        instead (surfaced as ResourceWarning: unclosed database once
        coverage instrumentation was added and perturbed collection
        timing). conftest.py's _clear_all_caches() calls this before
        clearing the cache.

        Returns:
            None.
        """
        self._connection.close()

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
            # Nullable, no default: NULL means "no move commanded yet",
            # not zero - a fabricated 0.0 would misreport an angle that
            # was never actually requested (same rule as output_deg's
            # own null-on-failed-read handling).
            "ALTER TABLE telemetry ADD COLUMN target_deg REAL",
            # R2, motor isolation: whether the operator's stored intent was
            # in effect for this sample. NOT NULL DEFAULT 0 (not nullable
            # like target_deg above) because this is app-held state, not a
            # servo measurement - there is always a value, the same
            # reasoning ServoStateResponse.locked already rests on.
            "ALTER TABLE telemetry ADD COLUMN isolated INTEGER NOT NULL"
            " DEFAULT 0",
        )
        for statement in migrations:
            try:
                self._connection.execute(statement)
            except sqlite3.OperationalError:
                pass  # column already exists
        self._connection.commit()
