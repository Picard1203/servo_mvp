"""SQLite implementation of the app-state key/value repository."""

from typing import Optional

from app.db.database import Database


class SqliteAppStateRepository:
    """Stores small operator-intent flags in the app_state table.

    Attributes:
        _db (Database): Database wrapper providing SQLite access.
    """

    def __init__(self, database: Database) -> None:
        self._db: Database = database

    def get(self, key: str) -> Optional[str]:
        """Returns a stored value.

        Args:
            key (str): State key to retrieve.

        Returns:
            Optional[str]: The stored value, or None when never set.
        """
        with self._db.write_lock:
            row = self._db.connection.execute(
                "SELECT value FROM app_state WHERE key = ?",
                (key,)).fetchone()
        return row["value"] if row is not None else None

    def set(self, key: str, value: str, updated_at: str) -> None:
        """Persists a value, replacing any previous one for the same key.

        Args:
            key (str): State key to persist.
            value (str): Value string to store.
            updated_at (str): ISO timestamp of this write.
        """
        with self._db.write_lock:
            self._db.connection.execute(
                "INSERT INTO app_state (key, value, updated_at) VALUES"
                " (?, ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                " updated_at = excluded.updated_at",
                (key, value, updated_at))
            self._db.connection.commit()
