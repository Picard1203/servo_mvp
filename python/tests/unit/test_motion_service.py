"""MotionService: validation, gating, settle-wait, fine approach, recover."""

import time

import pytest

from app.core.exceptions import LockedError, MovingError, StepError
from tests.conftest import wait_until


@pytest.fixture()
def motion(backend):
    """Fresh motion service.

    Returns:
        The service under test.
    """
    from app.deps import get_motion_service
    return get_motion_service()


class TestValidation:
    """Step-size validation."""

    def test_valid_steps_accepted(self, motion):
        motion.move_to(12.0, 60.0)
        motion.move_to(12.06, 60.0)

    @pytest.mark.parametrize("bad", [10.05, 0.333, 359.99])
    def test_invalid_steps_rejected(self, motion, bad):
        with pytest.raises(StepError):
            motion.move_to(bad, 60.0)


class TestLockGate:
    """Digital lock gating and settle-wait."""

    def test_locked_rejects_move(self, motion):
        motion.set_lock(True)
        with pytest.raises(LockedError):
            motion.move_to(12.0, 60.0)

    def test_unlock_then_move_waits_out_settle(self, backend, motion):
        motion.set_lock(True)
        motion.set_lock(False)
        started = time.monotonic()
        motion.move_to(12.0, 60.0)
        waited = time.monotonic() - started
        assert waited >= backend.settings.settling_seconds * 0.7

    def test_no_settle_wait_when_window_closed(self, backend, motion):
        motion.set_lock(True)
        motion.set_lock(False)
        assert wait_until(
            lambda: not _settling(backend), timeout=2.0)
        started = time.monotonic()
        motion.move_to(12.0, 60.0)
        assert time.monotonic() - started < 0.1


def _settling(backend) -> bool:
    """Reads the settle state from the store.

    Args:
        backend: The backend fixture namespace.

    Returns:
        True while the settle window is open.
    """
    from app.deps import get_state_store
    return get_state_store().settle_remaining_seconds() > 0


class TestMoveGuard:
    """Optional move->lock guard."""

    def test_guard_disabled_allows_lock_while_moving(self, motion, sim):
        sim.set_deadband(1)
        motion.move_to(60.0, 20.0)   # long slow move
        motion.set_lock(True)          # default: allowed

    def test_guard_enabled_refuses_lock_while_moving(self, monkeypatch,
                                                     backend, sim):
        monkeypatch.setattr(backend.settings, "guard_move_to_lock", True)
        from app.deps import get_motion_service
        motion = get_motion_service()
        sim.set_deadband(1)
        motion.move_to(60.0, 20.0)
        assert wait_until(lambda: sim.read_snapshot().moving)
        with pytest.raises(MovingError):
            motion.set_lock(True)


class TestAcceleration:
    """Acceleration pass-through."""

    def test_default_acceleration_used(self, backend, motion, sim):
        motion.move_to(6.0, 60.0)
        assert sim._acceleration == backend.settings.default_acceleration

    def test_explicit_acceleration_used(self, motion, sim):
        motion.move_to(6.0, 60.0, acceleration=99)
        assert sim._acceleration == 99


class TestFineApproach:
    """Consistent-direction anti-backlash approach."""

    def test_disabled_by_default_direct_move(self, backend, motion, sim):
        sim.set_deadband(1)
        motion.move_to(30.0, 60.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0, 60.0)   # downward, but feature off
        events = [e.event for e in _events(backend)]
        assert "servo.move.fine_approach" not in events

    def test_enabled_downward_move_overshoots_then_arrives(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        motion = get_motion_service()
        store = get_state_store()
        sim.set_deadband(1)
        motion.move_to(30.0, 60.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0, 60.0)
        # Wait for the fine-approach event FIRST: the overshoot leg travels
        # through the target on its way below it, so a position check alone
        # can succeed mid-transit before the final leg is even commanded.
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        assert wait_until(
            lambda: abs(store.current_output_deg() - 12.0) < 0.3, timeout=8)

    def test_enabled_upward_move_stays_direct(self, monkeypatch, backend,
                                              sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service
        motion = get_motion_service()
        motion.move_to(18.0, 60.0)   # upward from 0: no overshoot leg
        events = [e.event for e in _events(backend)]
        assert "servo.move.fine_approach" not in events


def _events(backend):
    """Returns recorded operator events.

    Args:
        backend: The backend fixture namespace.

    Returns:
        Recent events.
    """
    from app.deps import get_event_service
    return get_event_service().recent(100)


class TestRecover:
    """Overload recovery."""

    def test_recover_clears_overload_without_moving(self, backend, sim):
        from app.deps import get_motion_service, get_state_store
        motion = get_motion_service()
        position = get_state_store().read_counts()
        sim.simulate_overload()
        motion.recover()
        assert sim.read_snapshot().overload is False
        assert abs(get_state_store().read_counts() - position) <= 2
        events = [e.event for e in _events(backend)]
        assert "servo.fault.recovered" in events


class TestTravelLimits:
    """The servo clamps silently outside counts 0..4095; we must not.

    Commanding past the physical range used to be reported as accepted
    while the mechanism stopped early - the failure that made -90 halt
    at 0.
    """

    def test_target_beyond_the_count_range_is_refused(self, backend, motion):
        from app.core.exceptions import OutOfTravelError as OutOfTravel
        from app.deps import get_state_store, get_zero_service
        # Put the datum at the very bottom of travel, as a failed read
        # once did, and the negative half becomes physically unreachable.
        zeros = get_zero_service()
        zero = zeros.capture("bottom")
        zeros.activate(zero.id)
        store = get_state_store()
        low, high = store.reachable_output_range_deg()
        assert low > backend.settings.output_min_deg
        with pytest.raises(OutOfTravel):
            motion.move_to(backend.settings.output_min_deg, 30.0)

    def test_reachable_range_is_symmetric_from_the_centre(self, backend,
                                                          motion):
        from app.deps import get_state_store
        low, high = get_state_store().reachable_output_range_deg()
        assert low < backend.settings.output_min_deg
        assert high > backend.settings.output_max_deg

    def test_full_window_works_from_the_default_baseline(self, motion,
                                                         backend):
        motion.move_to(backend.settings.output_min_deg, 30.0)
        motion.move_to(backend.settings.output_max_deg, 30.0)
