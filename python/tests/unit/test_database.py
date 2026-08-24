"""Database: schema creation, migration of old schemas, row survival."""

import sqlite3
import threading
import time
from datetime import datetime

from app.db.database import Database
from app.models.entities import TelemetrySample, ZeroReference
from app.repositories.concrete.sqlite_telemetry_repository import (
    SqliteTelemetryRepository)
from app.repositories.concrete.sqlite_zero_repository import (
    SqliteZeroRepository)


class TestSchema:
    """Fresh-database schema."""

    def test_tables_and_columns_created(self, tmp_path):
        db = Database(str(tmp_path / "fresh.db"))
        zero_cols = [r[1] for r in
                     db.connection.execute("PRAGMA table_info(zeros)")]
        telemetry_cols = [r[1] for r in
                          db.connection.execute("PRAGMA table_info(telemetry)")]
        assert "is_datum" in zero_cols
        for col in ("overload", "overcurrent", "overheat", "voltage_fault",
                    "sensor_fault", "target_deg"):
            assert col in telemetry_cols

    def test_init_idempotent(self, tmp_path):
        path = str(tmp_path / "twice.db")
        Database(path)
        Database(path)  # second init must not raise


class TestMigration:
    """Upgrading a database created before this change pack."""

    def test_old_schema_upgraded_with_rows_intact(self, tmp_path):
        path = str(tmp_path / "old.db")
        conn = sqlite3.connect(path)
        conn.executescript(
            "CREATE TABLE zeros (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " name TEXT NOT NULL UNIQUE, raw_counts INTEGER NOT NULL,"
            " is_active INTEGER NOT NULL DEFAULT 0, created_at TEXT NOT NULL);"
            "CREATE TABLE telemetry (id INTEGER PRIMARY KEY AUTOINCREMENT,"
            " timestamp REAL NOT NULL, raw_counts INTEGER NOT NULL, output_deg REAL"
            " NOT NULL, moving INTEGER NOT NULL, locked INTEGER NOT NULL,"
            " temperature_c REAL NOT NULL, voltage_v REAL NOT NULL,"
            " current_a REAL NOT NULL, torque_kgcm REAL NOT NULL);"
            "INSERT INTO zeros (name, raw_counts, is_active, created_at)"
            " VALUES ('legacy', 123, 1, '2026-01-01');")
        conn.commit()
        conn.close()

        db = Database(path)
        row = db.connection.execute(
            "SELECT * FROM zeros WHERE name = 'legacy'").fetchone()
        assert row["raw_counts"] == 123
        assert row["is_datum"] == 0
        telemetry_cols = [r[1] for r in
                          db.connection.execute("PRAGMA table_info(telemetry)")]
        assert "sensor_fault" in telemetry_cols
        assert "target_deg" in telemetry_cols

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
        zeros = SqliteZeroRepository(db)
        telemetry = SqliteTelemetryRepository(db)
        active = zeros.add(ZeroReference(
            id=None, name="datum", raw_counts=2046, is_active=True,
            is_datum=True, created_at=datetime.now().isoformat()))

        stop = threading.Event()
        failures = []

        def read_active_zero():
            while not stop.is_set():
                try:
                    zero = zeros.get_active()
                except Exception as exc:  # the corrupted-row failure mode
                    failures.append(exc)
                    return
                if zero is not None and zero.raw_counts is None:
                    failures.append(AssertionError(
                        "get_active() returned a NOT NULL column as None"))
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

        def write_zero():
            while not stop.is_set():
                zeros.set_active(active.id)

        threads = ([threading.Thread(target=read_active_zero)
                    for _ in range(4)]
                   + [threading.Thread(target=write_telemetry)
                      for _ in range(2)]
                   + [threading.Thread(target=write_zero) for _ in range(2)])
        for t in threads:
            t.start()
        time.sleep(2.0)
        stop.set()
        for t in threads:
            t.join(timeout=5)

        assert failures == []
