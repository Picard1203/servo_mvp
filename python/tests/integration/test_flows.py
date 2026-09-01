"""Cross-service integration flows (no HTTP): components working together."""

import time

from tests.conftest import wait_until


class TestCalibrationAndSavedPositionsAcrossServices:
    """Calibration, saved positions, state store and motion interacting."""

    def test_go_to_saved_position_does_not_shift_the_datum(self, backend,
                                                            sim):
        from app.deps import (get_motion_service, get_saved_position_service,
                              get_state_store)
        motion = get_motion_service()
        store = get_state_store()
        positions = get_saved_position_service()

        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        saved = positions.create("at30", "", 30.0)
        positions.go(saved.id)
        # unlike the old activate-a-zero model, going to a saved position
        # never rebaselines the display - the datum is unaffected.
        assert wait_until(
            lambda: abs(store.current_output_deg() - 30.0) < 0.8, timeout=6)
        motion.move_to(12.0)
        assert wait_until(
            lambda: abs(store.current_output_deg() - 12.0) < 0.8, timeout=6)

    def test_calibrate_then_recalibrate_after_position_change(self, backend,
                                                             sim):
        from app.deps import get_calibration_service, get_state_store
        calibration = get_calibration_service()
        store = get_state_store()
        calibration.calibrate()
        sim.set_deadband(1)
        sim.command_move(2000, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 2000) <= 2)
        calibration.calibrate()          # re-home after "power cycle"
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
        # closer to the target at the end than at the start - direction-
        # agnostic, since which sign is "increasing" depends on config
        assert abs(rows[-1].output_deg - 42.0) < abs(rows[0].output_deg - 42.0)


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
