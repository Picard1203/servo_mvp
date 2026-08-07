"""SqliteZeroRepository: CRUD, active selection, datum upsert."""

from datetime import datetime

import pytest

from app.db.database import Database
from app.models.entities import ZeroReference
from app.repositories.concrete.sqlite_zero_repository import (
    SqliteZeroRepository)


@pytest.fixture()
def repo(tmp_path):
    """Zero repository over a fresh database.

    Returns:
        The repository under test.
    """
    return SqliteZeroRepository(Database(str(tmp_path / "zeros.db")))


def _zero(name="z1", counts=100):
    """Builds an unsaved zero entity.

    Args:
        name: Zero name.
        counts: Raw counts.

    Returns:
        The entity.
    """
    return ZeroReference(id=None, name=name, raw_counts=counts,
                         is_active=False, is_datum=False,
                         created_at=datetime.now().isoformat())


class TestCrud:
    """Create, read, delete."""

    def test_add_assigns_id_and_get_roundtrips(self, repo):
        stored = repo.add(_zero())
        assert stored.id is not None
        fetched = repo.get(stored.id)
        assert fetched.name == "z1"
        assert fetched.raw_counts == 100
        assert fetched.is_datum is False

    def test_list_newest_first(self, repo):
        first = repo.add(_zero("a"))
        second = repo.add(_zero("b"))
        listed = repo.list_all()
        assert [z.id for z in listed] == [second.id, first.id]

    def test_get_missing_returns_none(self, repo):
        assert repo.get(999) is None

    def test_delete(self, repo):
        stored = repo.add(_zero())
        assert repo.delete(stored.id) is True
        assert repo.get(stored.id) is None
        assert repo.delete(stored.id) is False


class TestActive:
    """Active-baseline selection."""

    def test_set_active_exclusive(self, repo):
        a = repo.add(_zero("a"))
        b = repo.add(_zero("b"))
        assert repo.set_active(a.id) is True
        assert repo.set_active(b.id) is True
        assert repo.get_active().id == b.id
        assert repo.get(a.id).is_active is False

    def test_set_active_missing_returns_false(self, repo):
        assert repo.set_active(999) is False

    def test_get_active_none_initially(self, repo):
        assert repo.get_active() is None


class TestDatum:
    """Upsert of THE calibration datum."""

    def test_first_upsert_creates_named_datum(self, repo):
        datum = repo.upsert_datum(500, "2026-01-01T00:00:00")
        assert datum.name == "datum"
        assert datum.is_datum is True

    def test_second_upsert_updates_same_row(self, repo):
        first = repo.upsert_datum(500, "t1")
        second = repo.upsert_datum(777, "t2")
        assert second.id == first.id
        assert second.raw_counts == 777
        datums = [z for z in repo.list_all() if z.is_datum]
        assert len(datums) == 1

    def test_datum_coexists_with_ordinary_zeros(self, repo):
        repo.add(_zero("ops"))
        repo.upsert_datum(1, "t")
        assert len(repo.list_all()) == 2
