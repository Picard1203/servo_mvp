"""SQLite implementation of the zero-reference repository."""

from typing import Optional

from app.db.database import Database
from app.models.entities import ZeroReference


class SqliteZeroRepository:
    """Stores zero references in the zeros table.

    Attributes:
        _db (Database): Database wrapper providing SQLite access.
    """

    def __init__(self, database: Database) -> None:
        self._db: Database = database

    def add(self, zero: ZeroReference) -> ZeroReference:
        """Persists a new zero reference.

        Args:
            zero (ZeroReference): Entity with id=None.

        Returns:
            ZeroReference: The stored entity with assigned id.
        """
        with self._db.write_lock:
            cursor = self._db.connection.execute(
                "INSERT INTO zeros (name, raw_counts, is_active, is_datum,"
                " created_at) VALUES (?, ?, ?, ?, ?)",
                (zero.name, zero.raw_counts, int(zero.is_active),
                 int(zero.is_datum), zero.created_at))
            self._db.connection.commit()
        zero.id = cursor.lastrowid
        return zero

    def list_all(self) -> list[ZeroReference]:
        """Returns all zero references, newest first.

        Returns:
            list[ZeroReference]: All stored zero references.
        """
        with self._db.write_lock:
            rows = self._db.connection.execute(
                "SELECT * FROM zeros ORDER BY id DESC").fetchall()
        result: list[ZeroReference] = []
        for row in rows:
            result.append(self._to_entity(row))
        return result

    def get(self, zero_id: int) -> Optional[ZeroReference]:
        """Returns one zero reference by id.

        Args:
            zero_id (int): Database identifier.

        Returns:
            Optional[ZeroReference]: The entity, or None when missing.
        """
        with self._db.write_lock:
            row = self._db.connection.execute(
                "SELECT * FROM zeros WHERE id = ?", (zero_id,)).fetchone()
        return self._to_entity(row) if row is not None else None

    def delete(self, zero_id: int) -> bool:
        """Deletes one zero reference.

        Args:
            zero_id (int): Database identifier.

        Returns:
            bool: True when a row was deleted.
        """
        with self._db.write_lock:
            cursor = self._db.connection.execute(
                "DELETE FROM zeros WHERE id = ?", (zero_id,))
            self._db.connection.commit()
        return cursor.rowcount > 0

    def set_active(self, zero_id: int) -> bool:
        """Marks one zero active and clears the previous active flag.

        Args:
            zero_id (int): Database identifier.

        Returns:
            bool: True when the zero exists and was activated.
        """
        with self._db.write_lock:
            self._db.connection.execute(
                "UPDATE zeros SET is_active = (id = ?)", (zero_id,))
            self._db.connection.commit()
            row = self._db.connection.execute(
                "SELECT COUNT(*) AS n FROM zeros WHERE id = ? AND is_active = 1",
                (zero_id,)).fetchone()
        return row["n"] > 0

    def get_active(self) -> Optional[ZeroReference]:
        """Returns the active zero reference, if any.

        Returns:
            Optional[ZeroReference]: Active zero reference or None.
        """
        with self._db.write_lock:
            row = self._db.connection.execute(
                "SELECT * FROM zeros WHERE is_active = 1").fetchone()
        return self._to_entity(row) if row is not None else None

    def upsert_datum(self, raw_counts: int, created_at: str) -> ZeroReference:
        """Creates or updates the calibration datum zero.

        Args:
            raw_counts (int): Captured raw encoder counts.
            created_at (str): ISO timestamp of capture.

        Returns:
            ZeroReference: The stored datum zero entity.
        """
        with self._db.write_lock:
            row = self._db.connection.execute(
                "SELECT id FROM zeros WHERE is_datum = 1").fetchone()
            if row is None:
                cursor = self._db.connection.execute(
                    "INSERT INTO zeros (name, raw_counts, is_active,"
                    " is_datum, created_at) VALUES (?, ?, 0, 1, ?)",
                    ("datum", raw_counts, created_at))
                datum_id = cursor.lastrowid
            else:
                datum_id = row["id"]
                self._db.connection.execute(
                    "UPDATE zeros SET raw_counts = ?, created_at = ?"
                    " WHERE id = ?", (raw_counts, created_at, datum_id))
            self._db.connection.commit()
        return self.get(datum_id)

    def _to_entity(self, row: object) -> ZeroReference:
        """Maps a database row to the entity.

        Args:
            row (object): SQLite row.

        Returns:
            ZeroReference: The mapped entity.
        """
        return ZeroReference(
            id=row["id"], name=row["name"], raw_counts=row["raw_counts"],
            is_active=bool(row["is_active"]),
            is_datum=bool(row["is_datum"]), created_at=row["created_at"])
