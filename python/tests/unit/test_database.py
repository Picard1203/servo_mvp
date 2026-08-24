"""Database: schema creation, migration of old schemas, row survival."""

import sqlite3

from app.db.database import Database


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
