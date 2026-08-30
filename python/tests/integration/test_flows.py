"""Cross-service integration flows (no HTTP): components working together."""

import time

from tests.conftest import wait_until


class TestZeroLifecycleAcrossServices:
    """Zeros, state store and motion interacting."""

    def test_activate_zero_shifts_command_targets(self, backend, sim):
        from app.deps import (get_motion_service, get_state_store,
                              get_zero_service)
        motion = get_motion_service()
        store = get_state_store()
        zeros = get_zero_service()

        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        zero = zeros.capture("at30")
        zeros.activate(zero.id)
        # display rebaselined: same physical spot now reads ~0
        assert abs(store.current_output_deg()) < 0.1
        # a move to 10 deg under the new baseline lands 40 deg physical
        motion.move_to(12.0)
        assert wait_until(
            lambda: abs(store.current_output_deg() - 12.0) < 0.8, timeout=6)

    def test_calibrate_then_recalibrate_after_position_change(self, backend,
                                                             sim):
        from app.deps import get_state_store, get_zero_service
        zeros = get_zero_service()
        store = get_state_store()
        first = zeros.calibrate()
        sim.set_deadband(1)
        sim.command_move(2000, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 2000) <= 2)
        second = zeros.calibrate()          # re-home after "power cycle"
        assert second.id == first.id
        assert abs(store.current_output_deg()) < 0.1


class TestSamplerObservesMotion:
    """Telemetry sampler records a real movement profile."""

    def test_samples_capture_moving_transition(self, backend, sim):
        from app.deps import (get_motion_service, get_telemetry_repository,
                              get_telemetry_service)
        service = get_telemetry_service()
        motion = get_motion_service()
        sim.set_deadband(1)
        service.start_sampler()          # 0.2s interval (conftest env)
        motion.move_to(42.0)       # ~1s of motion
        time.sleep(1.6)
        rows = list(get_telemetry_repository().query(0, time.time() + 1, 100))
        assert len(rows) >= 4
        moving_values = {row.moving for row in rows}
        assert moving_values == {True, False}   # saw motion AND rest
        assert rows[-1].output_deg > rows[0].output_deg


class TestFaultVisibleInSampledHistory:
    """Overload flag reaches persisted telemetry."""

    def test_overload_persisted_then_cleared(self, backend, sim):
        from app.deps import (get_motion_service, get_telemetry_repository,
                              get_telemetry_service)
        service = get_telemetry_service()
        sim.simulate_overload()
        service._sample_once()
        get_motion_service().recover()
        service._sample_once()
        rows = list(get_telemetry_repository().query(0, time.time() + 1, 10))
        assert [row.overload for row in rows] == [True, False]
