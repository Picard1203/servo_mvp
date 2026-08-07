"""TelemetryService: sampling, CSV export, retention timing."""

import time

import pytest


@pytest.fixture()
def service(backend):
    """Fresh telemetry service (sampler NOT started).

    Returns:
        The service under test.
    """
    from app.deps import get_telemetry_service
    return get_telemetry_service()


class TestFailedReadsAreNotStored:
    """A stalled bus must leave a gap, not a row claiming position 0.

    Seven such rows reached the board's database on 7 August 2026, six
    of them count 0 and one count -1, each written while the Bridge was
    timing out. A gap is honest; a fabricated zero is not, and it is
    indistinguishable from a genuine reading at the bottom of travel.
    """

    def test_an_invalid_reading_is_not_persisted(self, backend, service, sim):
        from app.models.entities import TelemetrySnapshot
        from app.deps import get_telemetry_repository

        def dead_bus():
            return TelemetrySnapshot(
                raw_counts=0, moving=False, temperature_c=0.0,
                voltage_v=0.0, current_a=0.0, torque_kgcm=0.0,
                overload=False, overcurrent=False, overheat=False,
                voltage_fault=False, sensor_fault=False, angle_fault=False,
                valid=False)

        sim.read_snapshot = dead_bus
        service._sample_once()
        rows = list(get_telemetry_repository().query(0, time.time() + 1, 10))
        assert rows == []

    def test_one_sample_costs_exactly_one_bus_read(self, backend, service,
                                                   sim):
        """The stored row must come from a single coherent read.

        The row used to be stitched from snapshot() plus a second,
        independent read_raw_counts(), so raw_counts and output_deg
        could describe different instants - and it doubled the sampler's
        Bridge traffic, which is what starves the thread that then times
        out.
        """
        reads = {"snapshot": 0, "raw": 0}
        original = sim.read_snapshot

        def counted_snapshot():
            reads["snapshot"] += 1
            return original()

        def counted_raw():
            reads["raw"] += 1
            return 0

        sim.read_snapshot = counted_snapshot
        sim.read_raw_counts = counted_raw
        service._sample_once()
        assert reads == {"snapshot": 1, "raw": 0}


class TestSampling:
    """Single-sample persistence."""

    def test_sample_once_persists_full_row(self, backend, service, sim):
        sim.simulate_overload()
        service._sample_once()
        from app.deps import get_telemetry_repository
        rows = list(get_telemetry_repository().query(0, time.time() + 1, 10))
        assert len(rows) == 1
        row = rows[0]
        assert row.overload is True
        assert row.locked is False
        assert isinstance(row.output_deg, float)

    def test_sampler_thread_produces_rows(self, backend, service):
        service.start_sampler()
        time.sleep(0.7)   # interval 0.2s -> expect >= 2 rows
        from app.deps import get_telemetry_repository
        rows = list(get_telemetry_repository().query(0, time.time() + 1, 100))
        assert len(rows) >= 2


class TestExport:
    """CSV export contract."""

    EXPECTED_HEADER = ("timestamp,raw_counts,output_deg,moving,locked,"
                      "temperature_c,voltage_v,current_a,torque_kgcm,"
                      "overload,overcurrent,overheat,voltage_fault,"
                      "sensor_fault,angle_fault")

    def test_header_contract(self, service):
        chunks = list(service.export_csv(0, time.time()))
        assert chunks[0].strip() == self.EXPECTED_HEADER

    def test_rows_and_flag_encoding(self, backend, service, sim):
        sim.simulate_overload()
        service._sample_once()
        sim.command_move(sim.read_raw_counts(), 1000, 50)  # clears fault
        service._sample_once()
        chunks = list(service.export_csv(0, time.time() + 1))
        rows = [c.strip() for c in chunks[1:]]
        assert len(rows) == 2
        assert rows[0].endswith(",1,0,0,0,0,0")   # overload=1
        assert rows[1].endswith(",0,0,0,0,0,0")

    def test_range_limits_rows(self, backend, service):
        service._sample_once()
        time.sleep(0.05)
        boundary = time.time()
        time.sleep(0.05)
        service._sample_once()
        chunks = list(service.export_csv(0, boundary))
        assert len(chunks) == 2   # header + first row only


class TestRetention:
    """Purge scheduling."""

    def test_purge_applies_retention(self, monkeypatch, backend, service):
        from app.deps import get_telemetry_repository
        from app.models.entities import TelemetrySample
        repository = get_telemetry_repository()
        old_ts = time.time() - 365 * 86_400
        repository.add(TelemetrySample(
            timestamp=old_ts, raw_counts=0, output_deg=0.0, moving=False,
            locked=False, temperature_c=30.0, voltage_v=12.0, current_a=0.1,
            torque_kgcm=1.0, overload=False, overcurrent=False,
            overheat=False, voltage_fault=False, sensor_fault=False, angle_fault=False))
        monkeypatch.setattr(backend.settings,
                            "telemetry_purge_interval_seconds", 0.0)
        service._last_purge = -10_000.0
        service._maybe_purge()
        assert list(repository.query(0, old_ts + 1, 10)) == []


class TestSamplerResilience:
    """The sampler thread survives sampling failures."""

    def test_sampler_logs_and_continues_after_exception(self, backend,
                                                        monkeypatch):
        from app.deps import (get_state_store, get_telemetry_repository)
        from app.services.telemetry_service import TelemetryService
        service = TelemetryService(get_telemetry_repository(),
                                   get_state_store(), backend.settings)
        calls = {"n": 0}

        def flaky():
            calls["n"] += 1
            if calls["n"] == 1:
                raise RuntimeError("sensor glitch")

        monkeypatch.setattr(service, "_sample_once", flaky)
        service.start_sampler()
        from tests.conftest import wait_until
        assert wait_until(lambda: calls["n"] >= 3, timeout=3)   # survived
        assert "telemetry.error" in backend.logger.events()
