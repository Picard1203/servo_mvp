"""SQLite implementation of the saved-position repository."""

import sqlite3
from typing import Optional

from app.core.exceptions import DuplicateNameError
from app.db.database import Database
from app.models.entities import SavedPosition


class SqliteSavedPositionRepository:
    """Stores saved positions in the saved_positions table.

    Attributes:
        _db (Database): Database wrapper providing SQLite access.
    """

    def __init__(self, database: Database) -> None:
        self._db: Database = database

    def add(self, position: SavedPosition) -> SavedPosition:
        """Persists a new saved position.

        Args:
            position (SavedPosition): Entity with id=None.

        Returns:
            SavedPosition: The stored entity with its assigned id.

        Raises:
            DuplicateNameError: If the name is already in use.
        """
        with self._db.write_lock:
            try:
                cursor = self._db.connection.execute(
                    "INSERT INTO saved_positions (name, description,"
                    " raw_counts, created_at, updated_at) VALUES"
                    " (?, ?, ?, ?, ?)",
                    (position.name, position.description,
                     position.raw_counts, position.created_at,
                     position.updated_at))
                self._db.connection.commit()
            except sqlite3.IntegrityError as exc:
                raise DuplicateNameError(
                    f"a saved position is already called '{position.name}'"
                ) from exc
        position.id = cursor.lastrowid
        return position

    def list_all(self) -> list[SavedPosition]:
        """Returns all saved positions, newest first.

        Returns:
            list[SavedPosition]: All stored saved positions.
        """
        with self._db.write_lock:
            rows = self._db.connection.execute(
                "SELECT * FROM saved_positions ORDER BY id DESC").fetchall()
        result: list[SavedPosition] = []
        for row in rows:
            result.append(self._to_entity(row))
        return result

    def get(self, position_id: int) -> Optional[SavedPosition]:
        """Returns one saved position by id.

        Args:
            position_id (int): Database identifier.

        Returns:
            Optional[SavedPosition]: Matching saved position or None.
        """
        with self._db.write_lock:
            row = self._db.connection.execute(
                "SELECT * FROM saved_positions WHERE id = ?",
                (position_id,)).fetchone()
        return self._to_entity(row) if row is not None else None

    def update(self, position_id: int, name: str, description: str,
              raw_counts: int, updated_at: str) -> Optional[SavedPosition]:
        """Overwrites a saved position's editable fields.

        Args:
            position_id (int): Database identifier.
            name (str): New name.
            description (str): New description.
            raw_counts (int): New absolute encoder position.
            updated_at (str): ISO timestamp of this edit.

        Returns:
            Optional[SavedPosition]: The updated entity, or None if missing.

        Raises:
            DuplicateNameError: If the name is already in use elsewhere.
        """
        with self._db.write_lock:
            try:
                cursor = self._db.connection.execute(
                    "UPDATE saved_positions SET name = ?, description = ?,"
                    " raw_counts = ?, updated_at = ? WHERE id = ?",
                    (name, description, raw_counts, updated_at, position_id))
                self._db.connection.commit()
            except sqlite3.IntegrityError as exc:
                raise DuplicateNameError(
                    f"a saved position is already called '{name}'") from exc
            if cursor.rowcount == 0:
                return None
            row = self._db.connection.execute(
                "SELECT * FROM saved_positions WHERE id = ?",
                (position_id,)).fetchone()
        return self._to_entity(row)

    def delete(self, position_id: int) -> bool:
        """Deletes one saved position.

        Args:
            position_id (int): Database identifier.

        Returns:
            bool: True when a row was deleted.
        """
        with self._db.write_lock:
            cursor = self._db.connection.execute(
                "DELETE FROM saved_positions WHERE id = ?", (position_id,))
            self._db.connection.commit()
        return cursor.rowcount > 0

    def _to_entity(self, row: object) -> SavedPosition:
        """Maps a database row to the entity.

        Args:
            row (object): SQLite row.

        Returns:
            SavedPosition: The mapped entity.
        """
        return SavedPosition(
            id=row["id"], name=row["name"], description=row["description"],
            raw_counts=row["raw_counts"], created_at=row["created_at"],
            updated_at=row["updated_at"])
