"""SqliteSavedPositionRepository: CRUD, ordering, name uniqueness."""

from datetime import datetime

import pytest

from app.core.exceptions import DuplicateNameError
from app.db.database import Database
from app.models.entities import SavedPosition
from app.repositories.concrete.sqlite_saved_position_repository import (
    SqliteSavedPositionRepository)


@pytest.fixture()
def repo(tmp_path):
    """Saved-position repository over a fresh database.

    Returns:
        The repository under test.
    """
    return SqliteSavedPositionRepository(
        Database(str(tmp_path / "positions.db")))


def _position(name="p1", counts=100, description=""):
    """Builds an unsaved saved-position entity.

    Args:
        name: Position name.
        counts: Raw counts.
        description: Position description.

    Returns:
        The entity.
    """
    now = datetime.now().isoformat()
    return SavedPosition(id=None, name=name, description=description,
                        raw_counts=counts, created_at=now, updated_at=now)


class TestCrud:
    """Create, read, update, delete."""

    def test_add_assigns_id_and_get_roundtrips(self, repo):
        stored = repo.add(_position())
        assert stored.id is not None
        fetched = repo.get(stored.id)
        assert fetched.name == "p1"
        assert fetched.raw_counts == 100
        assert fetched.description == ""

    def test_list_newest_first(self, repo):
        first = repo.add(_position("a"))
        second = repo.add(_position("b"))
        listed = repo.list_all()
        assert [p.id for p in listed] == [second.id, first.id]

    def test_get_missing_returns_none(self, repo):
        assert repo.get(999) is None

    def test_update_overwrites_editable_fields(self, repo):
        stored = repo.add(_position())
        updated = repo.update(stored.id, "renamed", "a note", 999, "t2")
        assert updated.name == "renamed"
        assert updated.description == "a note"
        assert updated.raw_counts == 999
        assert updated.updated_at == "t2"

    def test_update_missing_returns_none(self, repo):
        assert repo.update(999, "x", "", 1, "t") is None

    def test_delete(self, repo):
        stored = repo.add(_position())
        assert repo.delete(stored.id) is True
        assert repo.get(stored.id) is None
        assert repo.delete(stored.id) is False


class TestNameUniqueness:
    """The UNIQUE constraint surfaces as a domain exception, not a 500."""

    def test_add_duplicate_name_raises(self, repo):
        repo.add(_position("taken"))
        with pytest.raises(DuplicateNameError):
            repo.add(_position("taken"))

    def test_update_to_a_name_in_use_raises(self, repo):
        repo.add(_position("a"))
        b = repo.add(_position("b"))
        with pytest.raises(DuplicateNameError):
            repo.update(b.id, "a", "", b.raw_counts, "t")
