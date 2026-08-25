"""SqliteAppStateRepository: get/set of persisted operator-intent flags."""

import pytest

from app.db.database import Database
from app.repositories.concrete.sqlite_app_state_repository import (
    SqliteAppStateRepository)


@pytest.fixture()
def repo(tmp_path):
    """App-state repository over a fresh database.

    Returns:
        The repository under test.
    """
    return SqliteAppStateRepository(Database(str(tmp_path / "state.db")))


class TestGetSet:
    """A key that was never written reads back as None; a written one
    reads back as written."""

    def test_unknown_key_is_none(self, repo):
        assert repo.get("isolated") is None

    def test_set_then_get_round_trips(self, repo):
        repo.set("isolated", "1", "2026-08-25T00:00:00")
        assert repo.get("isolated") == "1"

    def test_set_replaces_a_previous_value(self, repo):
        repo.set("isolated", "1", "2026-08-25T00:00:00")
        repo.set("isolated", "0", "2026-08-25T00:01:00")
        assert repo.get("isolated") == "0"

    def test_survives_a_fresh_repository_over_the_same_database(
            self, tmp_path):
        """The whole point of this table: a second process (or a
        restart) reading the same file sees what the first one wrote."""
        path = str(tmp_path / "shared.db")
        SqliteAppStateRepository(Database(path)).set(
            "isolated", "1", "2026-08-25T00:00:00")
        reopened = SqliteAppStateRepository(Database(path))
        assert reopened.get("isolated") == "1"

    def test_keys_are_independent(self, repo):
        repo.set("isolated", "1", "2026-08-25T00:00:00")
        assert repo.get("some_other_key") is None
