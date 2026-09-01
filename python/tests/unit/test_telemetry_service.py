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
    """Binary telemetry export contract.

    XLSX assembly is client-side (app.js) by design - see BACKLOG.md R5 -
    so the server's contract is the compact binary stream only: a header
    (base timestamp, sample count, servo-degrees-per-output-degree ratio)
    followed by one 20-byte packed record per sample. These tests replace
    an earlier version written against a server-side export_xlsx() that
    was never implemented (see D31/R5).
    """

    def test_header_and_stream_length(self, backend, service, sim):
        from app.services.telemetry_service import HEADER_STRUCT, SAMPLE_STRUCT
        service._sample_once()
        service._sample_once()
        chunks = list(service.export_binary_stream(0, time.time() + 1))
        stream = b"".join(chunks)
        base_ts, count, ratio = HEADER_STRUCT.unpack(stream[:HEADER_STRUCT.size])
        assert count == 2
        assert base_ts > 0
        assert ratio == pytest.approx(backend.settings.servo_deg_per_output_deg
                                       * backend.settings.servo_direction)
        assert len(stream) == HEADER_STRUCT.size + count * SAMPLE_STRUCT.size

    def test_target_angle_round_trips(self, backend, service, sim):
        """A sample taken before any move has target_valid=0; one taken
        after an accepted move carries the target angle."""
        from app.deps import get_motion_service
        from app.services.telemetry_service import HEADER_STRUCT, SAMPLE_STRUCT
        service._sample_once()  # no move commanded yet
        get_motion_service().move_to(30.0)
        service._sample_once()
        stream = b"".join(service.export_binary_stream(0, time.time() + 1))
        offset = HEADER_STRUCT.size
        first = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        assert first[8] == 0  # target_valid
        offset += SAMPLE_STRUCT.size
        second = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        assert second[8] == 1
        assert second[9] == pytest.approx(3000, abs=1)  # 30.0 deg * 100

    def test_rows_and_flag_encoding(self, backend, service, sim):
        from app.services.telemetry_service import HEADER_STRUCT, SAMPLE_STRUCT
        sim.simulate_overload()
        service._sample_once()
        sim.command_move(sim.read_raw_counts(), 1000, 50)  # clears fault
        service._sample_once()
        stream = b"".join(service.export_binary_stream(0, time.time() + 1))
        _, count, _ = HEADER_STRUCT.unpack(stream[:HEADER_STRUCT.size])
        assert count == 2
        offset = HEADER_STRUCT.size
        first = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        flags = first[6]
        assert flags & 0b00000100  # bit 2: overload set on the first sample
        offset += SAMPLE_STRUCT.size
        second = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        assert not (second[6] & 0b00000100)  # cleared by the second sample

    def test_isolated_rides_bit1_of_the_target_valid_byte(
            self, backend, service, sim):
        """isolated shares a byte with target_valid rather than widening
        the 20-byte sample - the two bits must be independently
        recoverable, not just both happen to be set together."""
        from app.deps import get_isolation_service, get_motion_service
        from app.services.telemetry_service import HEADER_STRUCT, SAMPLE_STRUCT
        get_motion_service().move_to(30.0)  # target_valid -> 1
        get_isolation_service().set_isolated(True)  # isolated -> 1
        service._sample_once()
        stream = b"".join(service.export_binary_stream(0, time.time() + 1))
        offset = HEADER_STRUCT.size
        sample = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        target_valid_flags = sample[8]
        assert target_valid_flags & 0b01  # bit0: target_valid
        assert target_valid_flags & 0b10  # bit1: isolated

    def test_isolated_bit_is_independent_of_target_valid(
            self, backend, service, sim):
        from app.deps import get_isolation_service
        from app.services.telemetry_service import HEADER_STRUCT, SAMPLE_STRUCT
        get_isolation_service().set_isolated(True)  # isolated, no target yet
        service._sample_once()
        stream = b"".join(service.export_binary_stream(0, time.time() + 1))
        offset = HEADER_STRUCT.size
        sample = SAMPLE_STRUCT.unpack(stream[offset:offset + SAMPLE_STRUCT.size])
        target_valid_flags = sample[8]
        assert not (target_valid_flags & 0b01)  # no move commanded
        assert target_valid_flags & 0b10        # but isolated is set

    def test_range_limits_rows(self, backend, service):
        from app.services.telemetry_service import HEADER_STRUCT
        service._sample_once()
        time.sleep(0.05)
        boundary = time.time()
        time.sleep(0.05)
        service._sample_once()
        stream = b"".join(service.export_binary_stream(0, boundary))
        _, count, _ = HEADER_STRUCT.unpack(stream[:HEADER_STRUCT.size])
        assert count == 1  # only the sample before the boundary


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
        try:
            from tests.conftest import wait_until
            assert wait_until(lambda: calls["n"] >= 3, timeout=3)  # survived
            assert "telemetry.error" in backend.logger.events()
        finally:
            # This service is built directly, not through the cached
            # deps.get_telemetry_service() singleton, so conftest's
            # teardown never sees it - without this the thread's own
            # closure keeps it (and this test's monkeypatched failure)
            # alive and logging into the shared stub for the rest of the
            # suite (backlog D26).
            service.stop_sampler()

    def test_a_sampler_failure_records_what_went_wrong(self, backend,
                                                       monkeypatch):
        """The record must carry the cause, not just the fact.

        A live board run on 7 August 2026 logged 'telemetry sampling
        failed' and nothing else - no exception type, no message, no
        traceback - so the fault could not be identified without
        reproducing it. An ERROR that destroys its own evidence is worse
        than no ERROR: it looks like diagnosis.
        """
        from app.deps import get_state_store, get_telemetry_repository
        from app.services.telemetry_service import TelemetryService
        from tests.conftest import wait_until
        service = TelemetryService(get_telemetry_repository(),
                                   get_state_store(), backend.settings)

        def always_fails():
            raise RuntimeError("the bus fell over")

        monkeypatch.setattr(service, "_sample_once", always_fails)
        service.start_sampler()
        try:
            assert wait_until(lambda: "telemetry.error"
                              in backend.logger.events(), timeout=3)
            failure = next(entry for entry in backend.logger.records
                           if len(entry) == 4
                           and entry[2].get("event") == "telemetry.error")
            extra = failure[3]
            assert extra.get("exception_type") == "RuntimeError"
            assert "the bus fell over" in extra.get("exception", "")
            assert "Traceback" in extra.get("traceback", "")
        finally:
            service.stop_sampler()  # see the sibling test's comment (D26)


class TestSamplerLifecycleIsolation:
    """D26: a sampler thread that outlived its test used to log into a

    later test's own results, unreproducibly. The Python suite failed
    once in ten runs (8 August 2026) with the failing test never
    identified. Root cause, found 25 August 2026 while chasing an
    unrelated ResourceWarning: start_sampler() had no stop mechanism at
    all, so a thread started by one test kept running against that
    test's own (soon closed) Database for the rest of the whole suite -
    reading state and logging errors into the shared test logger stub
    at whatever moment the scheduler happened to run it. That is exactly
    the shape of an intermittent, unreproducible failure: which test it
    corrupts, and when, depends on thread timing, not on anything either
    test does wrong on its own.

    These tests induce the mechanism directly and deterministically,
    rather than relooping the whole suite and hoping to get unlucky
    again: the first proves stop_sampler() actually stops the thread;
    the second proves what used to happen when nothing did.
    """

    def test_stop_sampler_actually_stops_the_thread(self, backend, sim):
        from app.deps import get_state_store, get_telemetry_repository
        from app.services.telemetry_service import TelemetryService
        from tests.conftest import wait_until
        service = TelemetryService(get_telemetry_repository(),
                                   get_state_store(), backend.settings)
        service.start_sampler()
        assert wait_until(lambda: service._thread is not None
                          and service._thread.is_alive(), timeout=1.0)
        service.stop_sampler()
        assert service._thread is None

    def test_teardown_stops_the_sampler_before_closing_the_database(self):
        """The ordering itself is the fix - proven directly, not risked.

        An earlier version of this test induced the actual race (started
        a sampler, closed its database out from under the live thread,
        asserted a clean ProgrammingError got logged). That reliably
        reproduced the mechanism - and, once, segfaulted the whole
        interpreter instead: sqlite3's C extension is not safe against a
        connection being closed while another thread is mid-statement on
        it, `check_same_thread=False` notwithstanding. A test that can
        crash the process it runs in is worse than the bug it documents,
        so this asserts the invariant that prevents the race - stop
        happens before close - rather than ever triggering it for real.
        """
        import unittest.mock as mock
        from tests.conftest import _clear_all_caches
        calls = []
        with mock.patch("app.deps.get_telemetry_service") as get_svc, \
             mock.patch("app.deps.get_database") as get_db, \
             mock.patch("app.core.config.get_settings"):
            get_svc.cache_info.return_value = mock.Mock(currsize=1)
            get_svc.return_value.stop_sampler.side_effect = \
                lambda: calls.append("stop_sampler")
            get_db.cache_info.return_value = mock.Mock(currsize=1)
            get_db.return_value.close.side_effect = \
                lambda: calls.append("close")
            _clear_all_caches()
        assert calls == ["stop_sampler", "close"], (
            "closing before the sampler is confirmed stopped is exactly "
            "the segfault this test used to risk")

    def test_teardown_joins_the_fine_approach_thread_before_closing(self):
        """The same mechanism, for MotionService's own background thread -
        added once that thread also started segfaulting the suite the same
        way the sampler once did."""
        import unittest.mock as mock
        from tests.conftest import _clear_all_caches
        calls = []
        with mock.patch("app.deps.get_telemetry_service") as get_telemetry, \
             mock.patch("app.deps.get_motion_service") as get_motion, \
             mock.patch("app.deps.get_database") as get_db, \
             mock.patch("app.core.config.get_settings"):
            get_telemetry.cache_info.return_value = mock.Mock(currsize=0)
            get_motion.cache_info.return_value = mock.Mock(currsize=1)
            get_motion.return_value.join_fine_approach.side_effect = \
                lambda: calls.append("join_fine_approach")
            get_db.cache_info.return_value = mock.Mock(currsize=1)
            get_db.return_value.close.side_effect = \
                lambda: calls.append("close")
            _clear_all_caches()
        assert calls == ["join_fine_approach", "close"], (
            "closing before the fine-approach thread is confirmed joined "
            "risks the same segfault the sampler ordering test guards")
