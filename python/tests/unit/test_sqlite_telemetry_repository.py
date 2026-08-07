"""SqliteTelemetryRepository: add, ranged query, purge, fault columns."""

import time

import pytest

from app.db.database import Database
from app.models.entities import TelemetrySample
from app.repositories.concrete.sqlite_telemetry_repository import (
    SqliteTelemetryRepository)


@pytest.fixture()
def repo(tmp_path):
    """Telemetry repository over a fresh database.

    Returns:
        The repository under test.
    """
    return SqliteTelemetryRepository(Database(str(tmp_path / "t.db")))


def _sample(timestamp, overload=False):
    """Builds a sample.

    Args:
        timestamp: Unix timestamp.
        overload: Overload flag value.

    Returns:
        The sample.
    """
    return TelemetrySample(timestamp=timestamp, raw_counts=100, output_deg=1.5,
                           moving=False, locked=True, temperature_c=34.0,
                           voltage_v=12.1, current_a=0.2, torque_kgcm=2.2,
                           overload=overload, overcurrent=False,
                           overheat=False, voltage_fault=False,
                           sensor_fault=False, angle_fault=False)


class TestAddQuery:
    """Persistence round-trips."""

    def test_roundtrip_including_fault_flags(self, repo):
        now = time.time()
        repo.add(_sample(now, overload=True))
        rows = list(repo.query(now - 1, now + 1, limit=10))
        assert len(rows) == 1
        assert rows[0].overload is True
        assert rows[0].locked is True
        assert rows[0].output_deg == 1.5

    def test_range_filtering_and_order(self, repo):
        repo.add(_sample(100.0))
        repo.add(_sample(200.0))
        repo.add(_sample(300.0))
        rows = list(repo.query(150.0, 250.0, limit=10))
        assert [r.timestamp for r in rows] == [200.0]
        all_rows = list(repo.query(0.0, 400.0, limit=10))
        assert [r.timestamp for r in all_rows] == [100.0, 200.0, 300.0]

    def test_limit(self, repo):
        for i in range(5):
            repo.add(_sample(float(i)))
        assert len(list(repo.query(0.0, 10.0, limit=3))) == 3


class TestPurge:
    """Retention."""

    def test_purge_older_than(self, repo):
        old = time.time() - 10 * 86_400
        recent = time.time()
        repo.add(_sample(old))
        repo.add(_sample(recent))
        deleted = repo.purge_older_than(days=5)
        assert deleted == 1
        remaining = list(repo.query(0.0, time.time() + 1, limit=10))
        assert len(remaining) == 1
        assert remaining[0].timestamp == recent
