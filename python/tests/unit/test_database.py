"""Database: schema creation, migration of old schemas, row survival."""

import sqlite3
import threading
import time
from datetime import datetime

from app.db.database import Database
from app.models.entities import SavedPosition, TelemetrySample
from app.repositories.concrete.sqlite_app_state_repository import (
    SqliteAppStateRepository)
from app.repositories.concrete.sqlite_saved_position_repository import (
    SqliteSavedPositionRepository)
from app.repositories.concrete.sqlite_telemetry_repository import (
    SqliteTelemetryRepository)


class TestSchema:
    """Fresh-database schema."""

    def test_tables_and_columns_created(self, tmp_path):
        db = Database(str(tmp_path / "fresh.db"))
        position_cols = [r[1] for r in db.connection.execute(
            "PRAGMA table_info(saved_positions)")]
        assert set(position_cols) == {"id", "name", "description",
                                      "raw_counts", "created_at",
                                      "updated_at"}
        telemetry_cols = [r[1] for r in
                          db.connection.execute("PRAGMA table_info(telemetry)")]
        for col in ("overload", "overcurrent", "overheat", "voltage_fault",
                    "sensor_fault", "target_deg", "isolated"):
            assert col in telemetry_cols
        app_state_cols = [r[1] for r in
                          db.connection.execute(
                              "PRAGMA table_info(app_state)")]
        assert set(app_state_cols) == {"key", "value", "updated_at"}
        zeros_exists = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name = 'zeros'").fetchone()
        assert zeros_exists is None

    def test_init_idempotent(self, tmp_path):
        path = str(tmp_path / "twice.db")
        Database(path)
        Database(path)  # second init must not raise


class TestMigration:
    """Upgrading a database created before this change pack."""

    def test_datum_carried_into_app_state(self, tmp_path):
        path = str(tmp_path / "old.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            "CREATE TABLE zeros (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL UNIQUE, raw_counts INTEGER NOT NULL,"
            " is_active INTEGER NOT NULL DEFAULT 0,"
            " is_datum INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);"
            "CREATE TABLE telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " timestamp REAL NOT NULL, raw_counts INTEGER NOT NULL, output_deg REAL"
            " NOT NULL, moving INTEGER NOT NULL, locked INTEGER NOT NULL,"
            " temperature_c REAL NOT NULL, voltage_v REAL NOT NULL,"
            " current_a REAL NOT NULL, torque_kgcm REAL NOT NULL);"
            "INSERT INTO zeros (name, raw_counts, is_active, is_datum,"
            " created_at) VALUES ('datum', 2046, 1, 1, '2026-01-01');"
            "INSERT INTO zeros (name, raw_counts, is_active, is_datum,"
            " created_at) VALUES ('gate open', 3000, 0, 0, '2026-01-02');")
        conn.commit()
        conn.close()

        db = Database(path)
        app_state = SqliteAppStateRepository(db)
        assert app_state.get("datum_raw_counts") == "2046"
        assert app_state.get("datum_captured_at") == "2026-01-01"
        positions = SqliteSavedPositionRepository(db).list_all()
        assert len(positions) == 1
        assert positions[0].name == "gate open"
        assert positions[0].raw_counts == 3000
        zeros_exists = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
            " AND name = 'zeros'").fetchone()
        assert zeros_exists is None

    def test_migration_idempotent_when_run_twice(self, tmp_path):
        path = str(tmp_path / "old2.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            "CREATE TABLE zeros (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL UNIQUE, raw_counts INTEGER NOT NULL,"
            " is_active INTEGER NOT NULL DEFAULT 0,"
            " is_datum INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);"
            "CREATE TABLE telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " timestamp REAL NOT NULL, raw_counts INTEGER NOT NULL, output_deg REAL"
            " NOT NULL, moving INTEGER NOT NULL, locked INTEGER NOT NULL,"
            " temperature_c REAL NOT NULL, voltage_v REAL NOT NULL,"
            " current_a REAL NOT NULL, torque_kgcm REAL NOT NULL);"
            "INSERT INTO zeros (name, raw_counts, is_active, is_datum,"
            " created_at) VALUES ('datum', 2046, 1, 1, '2026-01-01');")
        conn.commit()
        conn.close()

        Database(path)
        db2 = Database(path)  # zeros already dropped: must not raise
        app_state = SqliteAppStateRepository(db2)
        assert app_state.get("datum_raw_counts") == "2046"

    def test_old_telemetry_columns_upgraded(self, tmp_path):
        path = str(tmp_path / "old_telemetry.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            "CREATE TABLE telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " timestamp REAL NOT NULL, raw_counts INTEGER NOT NULL, output_deg REAL"
            " NOT NULL, moving INTEGER NOT NULL, locked INTEGER NOT NULL,"
            " temperature_c REAL NOT NULL, voltage_v REAL NOT NULL,"
            " current_a REAL NOT NULL, torque_kgcm REAL NOT NULL);")
        conn.commit()
        conn.close()

        db = Database(path)
        telemetry_cols = [r[1] for r in
                          db.connection.execute("PRAGMA table_info(telemetry)")]
        assert "sensor_fault" in telemetry_cols
        assert "target_deg" in telemetry_cols
        assert "isolated" in telemetry_cols
        # A database old enough to predate target_deg predates app_state
        # and saved_positions too - both must be created fresh.
        app_state_cols = [r[1] for r in
                          db.connection.execute(
                              "PRAGMA table_info(app_state)")]
        assert set(app_state_cols) == {"key", "value", "updated_at"}
        position_cols = [r[1] for r in db.connection.execute(
            "PRAGMA table_info(saved_positions)")]
        assert "raw_counts" in position_cols

    def test_migration_idempotent_on_a_populated_database(self, tmp_path):
        """The ALTER-and-ignore pattern must not raise or lose rows on a
        database that already has target_deg AND existing telemetry
        rows - the second init this session's own column goes through."""
        path = str(tmp_path / "populated.db")
        db = Database(path)
        db.connection.execute(
            "INSERT INTO telemetry (timestamp, raw_counts, output_deg,"
            " moving, locked, temperature_c, voltage_v, current_a,"
            " torque_kgcm, target_deg) VALUES"
            " (1.0, 100, 5.0, 0, 0, 30.0, 12.0, 0.1, 1.0, 45.0)")
        db.connection.commit()

        db2 = Database(path)  # re-init: migration runs again, must not raise
        row = db2.connection.execute(
            "SELECT * FROM telemetry WHERE timestamp = 1.0").fetchone()
        assert row["target_deg"] == 45.0
        # isolated is NOT NULL DEFAULT 0 - a row written before the
        # column existed must read back as 0, not NULL or an error.
        assert row["isolated"] == 0


class TestConcurrentAccess:
    """D10: one shared connection, read under a lock or corrupt.

    ``check_same_thread=False`` lets multiple threads share one
    ``sqlite3.Connection``. Serializing writes alone (the pre-fix shape)
    still lets a read's ``execute()``/``fetchone()`` interleave with a
    write on another thread, on the *same* connection object - not a
    stored-data race, a connection-sharing one. Reproduced two failure
    modes this way: a ``NOT NULL`` column reading back as ``None``, and
    an outright ``IndexError`` from a torn ``sqlite3.Row``. This drives
    every statement (read and write) through ``write_lock``.
    """

    def test_reads_survive_concurrent_writes(self, tmp_path):
        db = Database(str(tmp_path / "concurrent.db"))
        positions = SqliteSavedPositionRepository(db)
        telemetry = SqliteTelemetryRepository(db)
        saved = positions.add(SavedPosition(
            id=None, name="gate open", description="", raw_counts=2046,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()))

        stop = threading.Event()
        failures = []

        def read_position():
            while not stop.is_set():
                try:
                    position = positions.get(saved.id)
                except Exception as exc:  # the corrupted-row failure mode
                    failures.append(exc)
                    return
                if position is not None and position.raw_counts is None:
                    failures.append(AssertionError(
                        "get() returned a NOT NULL column as None"))
                    return

        def write_telemetry():
            while not stop.is_set():
                telemetry.add(TelemetrySample(
                    timestamp=time.time(), raw_counts=2046, output_deg=0.0,
                    moving=False, locked=False, temperature_c=25.0,
                    voltage_v=7.4, current_a=0.1, torque_kgcm=1.0,
                    overload=False, overcurrent=False, overheat=False,
                    voltage_fault=False, sensor_fault=False,
                    angle_fault=False, target_deg=None))

        def write_position():
            while not stop.is_set():
                positions.update(saved.id, saved.name, "moved",
                                 saved.raw_counts,
                                 datetime.now().isoformat())

        threads = ([threading.Thread(target=read_position)
                    for _ in range(4)]
                   + [threading.Thread(target=write_telemetry)
                      for _ in range(2)]
                   + [threading.Thread(target=write_position) for _ in range(2)])
        for t in threads:
            t.start()
        time.sleep(2.0)
        stop.set()
        for t in threads:
            t.join(timeout=5)

        assert failures == []
