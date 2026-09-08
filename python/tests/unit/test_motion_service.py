"""MotionService: validation, gating, settle-wait, fine approach, recover."""

import sqlite3
import time
from dataclasses import replace

import pytest

from app.core.exceptions import (CommandNotAcknowledgedError, IsolatedError,
                                 LockedError, MovingError, StepError)
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
        motion.move_to(12.0)
        motion.move_to(12.06)

    def test_move_message_states_full_precision(self, motion, backend):
        """D34: 0.06 deg is the real minimum step; a message rounded to
        1 decimal cannot show it (0.06 and 0.12 both read "0.1")."""
        motion.move_to(12.06)
        accepted = next(e for e in _events(backend)
                        if e.event == "servo.move.accepted")
        assert "12.06" in accepted.message

    def test_from_deg_keeps_full_precision(self, motion, backend, monkeypatch):
        from app.deps import get_state_store
        monkeypatch.setattr(get_state_store(), "current_output_deg",
                            lambda: 6.06)
        motion.move_to(12.0)
        accepted = [e for e in _events(backend)
                   if e.event == "servo.move.accepted"][-1]
        assert accepted.data["from_deg"] == 6.06

    @pytest.mark.parametrize("bad", [10.05, 0.333, 359.99])
    def test_invalid_steps_rejected(self, motion, bad):
        with pytest.raises(StepError):
            motion.move_to(bad)


class TestLockGate:
    """Digital lock gating and settle-wait."""

    def test_locked_rejects_move(self, motion):
        motion.set_lock(True)
        with pytest.raises(LockedError):
            motion.move_to(12.0)

    def test_unlock_then_move_waits_out_settle(self, backend, motion):
        motion.set_lock(True)
        motion.set_lock(False)
        started = time.monotonic()
        motion.move_to(12.0)
        waited = time.monotonic() - started
        assert waited >= backend.settings.settling_seconds * 0.7

    def test_no_settle_wait_when_window_closed(self, backend, motion):
        motion.set_lock(True)
        motion.set_lock(False)
        assert wait_until(
            lambda: not _settling(backend), timeout=2.0)
        started = time.monotonic()
        motion.move_to(12.0)
        assert time.monotonic() - started < 0.1


class TestIsolationGate:
    """Motor isolation gates a move the same way the digital lock does."""

    def test_isolated_rejects_move(self, motion):
        from app.deps import get_isolation_service
        get_isolation_service().set_isolated(True)
        with pytest.raises(IsolatedError):
            motion.move_to(12.0)

    def test_un_isolate_then_move_succeeds(self, motion):
        from app.deps import get_isolation_service
        isolation = get_isolation_service()
        isolation.set_isolated(True)
        isolation.set_isolated(False)
        motion.move_to(12.0)   # must not raise

    def test_isolated_not_guarded_by_motion_state(self, motion, sim):
        """Unlike a lock change, isolating must take effect immediately
        even mid-move - it is meant to double as a future emergency-stop
        mechanism, and refusing it while the servo is misbehaving badly
        enough to need isolating would be exactly backwards."""
        from app.deps import get_isolation_service
        sim.set_deadband(1)
        motion.move_to(60.0)
        assert wait_until(lambda: sim.read_snapshot().moving)
        get_isolation_service().set_isolated(True)   # must not raise
        with pytest.raises(IsolatedError):
            motion.move_to(12.0)

    def test_isolated_and_locked_are_distinct_reasons(self, motion):
        """The two gates must not collapse into one reason code - an
        operator refused for the wrong reason cannot fix the right
        thing."""
        from app.deps import get_isolation_service
        motion.set_lock(True)
        with pytest.raises(LockedError):
            motion.move_to(12.0)
        motion.set_lock(False)
        get_isolation_service().set_isolated(True)
        with pytest.raises(IsolatedError):
            motion.move_to(12.0)

    def test_locked_and_isolated_together_raises_the_combined_error(
            self, motion):
        """Neither single-condition gate may fire alone here - an operator
        who clears one would still be refused a second time for a reason
        they were never told about."""
        from app.core.exceptions import LockedAndIsolatedError
        from app.deps import get_isolation_service
        motion.set_lock(True)
        get_isolation_service().set_isolated(True)
        with pytest.raises(LockedAndIsolatedError):
            motion.move_to(12.0)


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
        motion.move_to(60.0)   # long slow move
        motion.set_lock(True)          # default: allowed

    def test_guard_enabled_refuses_lock_while_moving(self, monkeypatch,
                                                     backend, sim):
        monkeypatch.setattr(backend.settings, "guard_move_to_lock", True)
        from app.deps import get_motion_service
        motion = get_motion_service()
        sim.set_deadband(1)
        motion.move_to(60.0)
        assert wait_until(lambda: sim.read_snapshot().moving)
        with pytest.raises(MovingError):
            motion.set_lock(True)


class TestAcceleration:
    """Acceleration pass-through."""

    def test_default_acceleration_used(self, backend, motion, sim):
        motion.move_to(6.0)
        assert sim._acceleration == backend.settings.default_acceleration

    def test_explicit_acceleration_used(self, motion, sim):
        motion.move_to(6.0, acceleration=99)
        assert sim._acceleration == 99


class TestCommandAck:
    """A command the servo never acknowledged is never reported as
    accepted - the write-side twin of ADR-0008's rule for reads."""

    def test_unacknowledged_move_raises(self, motion, sim, monkeypatch):
        monkeypatch.setattr(sim, "command_move", lambda *a, **k: False)
        with pytest.raises(CommandNotAcknowledgedError):
            motion.move_to(12.0)

    def test_unacknowledged_move_does_not_report_accepted(
            self, motion, backend, sim, monkeypatch):
        monkeypatch.setattr(sim, "command_move", lambda *a, **k: False)
        with pytest.raises(CommandNotAcknowledgedError):
            motion.move_to(12.0)
        events = [e.event for e in _events(backend)]
        assert "servo.move.accepted" not in events
        assert "servo.move.failed" in events

    def test_acknowledged_move_still_reports_accepted(self, motion, backend):
        motion.move_to(12.0)
        events = [e.event for e in _events(backend)]
        assert "servo.move.accepted" in events

    def test_unacknowledged_stop_raises(self, motion, sim, monkeypatch):
        monkeypatch.setattr(sim, "command_stop", lambda *a, **k: False)
        with pytest.raises(CommandNotAcknowledgedError):
            motion.stop()

    def test_unacknowledged_recover_raises(self, motion, sim, monkeypatch):
        monkeypatch.setattr(sim, "command_move", lambda *a, **k: False)
        with pytest.raises(CommandNotAcknowledgedError):
            motion.recover()

    def test_fine_approach_overshoot_ack_failure_does_not_report_accepted(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        motion = get_motion_service()
        monkeypatch.setattr(sim, "command_move", lambda *a, **k: False)
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.failed" in
            [e.event for e in _events(backend)], timeout=8)
        events = [e.event for e in _events(backend)]
        assert "servo.move.accepted" not in events
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.failed"]
        assert event.data["leg"] == "overshoot"

    def test_fine_approach_final_leg_ack_failure_is_recorded(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        motion = get_motion_service()

        real_command_move = sim.command_move
        calls = []

        def _fail_second_call(target_counts, speed_counts_s, acceleration):
            calls.append(target_counts)
            if len(calls) == 1:
                return real_command_move(target_counts, speed_counts_s,
                                         acceleration)
            return False

        monkeypatch.setattr(sim, "command_move", _fail_second_call)
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.failed" in
            [e.event for e in _events(backend)], timeout=8)
        events = [e.event for e in _events(backend)]
        assert "servo.move.accepted" in events
        assert "servo.move.fine_approach" not in events
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.failed"]
        assert event.data["leg"] == "final"


class TestFineApproach:
    """Consistent-direction anti-backlash approach."""

    def test_disabled_by_default_direct_move(self, backend, motion, sim):
        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0)   # downward, but feature off
        events = [e.event for e in _events(backend)]
        assert "servo.move.fine_approach" not in events

    def test_enabled_downward_move_overshoots_then_arrives(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        motion = get_motion_service()
        store = get_state_store()
        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0)
        # Wait for the fine-approach event FIRST: the overshoot leg travels
        # through the target on its way below it, so a position check alone
        # can succeed mid-transit before the final leg is even commanded.
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        assert wait_until(
            lambda: abs(store.current_output_deg() - 12.0) < 0.3, timeout=8)

    def test_enabled_upward_move_also_overshoots_then_arrives(
            self, monkeypatch, backend, sim):
        """An upward move gets the same correction as a downward one - a
        plain direct upward move measured a real 0.61 deg shortfall on the
        rig (1 September 2026); "arrives from a consistent direction
        already" turned out not to be true protection on its own."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        # Fixed below the target - real, not the ambient default, so the
        # move's direction does not depend on whatever SERVO_DIRECTION this
        # machine's .env happens to carry.
        monkeypatch.setattr(store, "current_output_deg", lambda: 0.0)
        motion = get_motion_service()
        motion.move_to(18.0)   # upward from 0: overshoots above, then back
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.fine_approach"]
        assert event.data["overshoot_deg"] == (
            18.0 + backend.settings.fine_approach_overshoot_deg)
        assert wait_until(
            lambda: abs(sim.read_snapshot().raw_counts
                       - store.counts_from_output_deg(18.0)) <= 1, timeout=8)

    def test_unknown_start_position_skips_fine_approach(
            self, monkeypatch, backend, sim):
        """A failed read must not crash the backlash decision - it has no
        information to decide with, so it declines rather than guesses
        (ADR-0008's rule, applied to a decision instead of a display)."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        monkeypatch.setattr(get_state_store(), "current_output_deg",
                            lambda: None)
        motion = get_motion_service()
        motion.move_to(12.0)   # must not raise TypeError
        events = [e.event for e in _events(backend)]
        assert "servo.move.fine_approach" not in events
        assert "servo.move.accepted" in events

    def test_second_move_during_approach_supersedes_the_stale_thread(
            self, monkeypatch, backend, sim):
        """The thread must never override a more recent command once it
        finally wakes up - the exact "second press does nothing, and the
        old target comes back anyway" shape from the operator's report."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        monkeypatch.setattr(backend.settings,
                            "fine_approach_timeout_seconds", 0.2)
        from app.deps import get_motion_service, get_state_store
        motion = get_motion_service()
        store = get_state_store()
        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0)   # downward: spawns the fine-approach thread
        motion.move_to(18.0)   # supersedes it before the thread's deadline
        assert wait_until(
            lambda: abs(store.current_output_deg() - 18.0) < 0.3, timeout=8)
        time.sleep(0.5)   # let the stale thread's deadline pass and fire
        assert abs(store.current_output_deg() - 18.0) < 0.3

    def test_isolating_during_approach_aborts_the_final_leg(
            self, monkeypatch, backend, sim):
        """A guard that fails open on a state change mid-flight: isolating
        must stop the stale thread from writing a goal position that
        torque is about to be restored into. Forces the thread to stay in
        its wait loop for a fixed, generous window instead of racing real
        servo settle timing against the main thread's isolate call."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        monkeypatch.setattr(backend.settings,
                            "fine_approach_timeout_seconds", 0.5)
        from app.deps import (get_isolation_service, get_motion_service,
                              get_state_store)
        monkeypatch.setattr(get_state_store(), "current_output_deg",
                            lambda: 30.0)
        motion = get_motion_service()

        calls = []
        real_command_move = sim.command_move
        real_read_snapshot = sim.read_snapshot

        def _recording(target_counts, speed_counts_s, acceleration):
            calls.append(target_counts)
            return real_command_move(target_counts, speed_counts_s,
                                     acceleration)

        monkeypatch.setattr(sim, "command_move", _recording)
        monkeypatch.setattr(
            sim, "read_snapshot",
            lambda: replace(real_read_snapshot(), moving=True))

        motion.move_to(12.0)   # downward: spawns the fine-approach thread
        get_isolation_service().set_isolated(True)   # well inside the window
        time.sleep(0.8)   # let the thread's deadline pass and try to fire

        assert len(calls) == 1   # only the overshoot leg, never the final one

    def test_locked_datum_read_inside_the_thread_is_logged_not_swallowed(
            self, monkeypatch, backend, sim):
        """The documented real risk on this filesystem (CLAUDE.md 6):
        SQLite cannot take its own lock on the CIFS mount. Only the
        overshoot leg's own conversion sees it, so the synchronous
        dispatch path (already exercised, unaffected) must still work -
        this proves the failure surfaces from inside the thread."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        target_deg = 12.0
        # Above the target: the overshoot leg is placed by the target's own
        # sign now, not by the direction of travel.
        overshoot_deg = (target_deg
                        + backend.settings.fine_approach_overshoot_deg)
        real_counts_from_output_deg = store.counts_from_output_deg

        def _flaky(output_deg):
            if output_deg == overshoot_deg:
                raise sqlite3.OperationalError("database is locked")
            return real_counts_from_output_deg(output_deg)

        monkeypatch.setattr(store, "counts_from_output_deg", _flaky)
        logged = []
        monkeypatch.setattr("app.services.motion_service.logger.exception",
                            lambda *a, **k: logged.append(a))
        motion = get_motion_service()
        motion.move_to(target_deg)   # spawns the thread
        assert wait_until(lambda: len(logged) > 0, timeout=4)

    def test_overshoot_is_clamped_to_the_reachable_range(
            self, monkeypatch, backend, sim):
        """The overshoot leg must never command a count outside the servo's
        single-turn range - it was unchecked before this delivery, latent
        only because D40b's testing never approached a travel edge."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        requested_overshoot_deg = (
            6.0 + backend.settings.fine_approach_overshoot_deg)
        clamp_high = requested_overshoot_deg - 0.5   # forces clamping
        monkeypatch.setattr(store, "reachable_output_range_deg",
                            lambda: (-100.0, clamp_high))
        motion = get_motion_service()

        calls = []
        real_command_move = sim.command_move
        monkeypatch.setattr(
            sim, "command_move",
            lambda counts, speed, accel: (calls.append(counts),
                                          real_command_move(counts, speed,
                                                            accel))[1])

        motion.move_to(6.0)   # overshoot wants above clamp_high
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.fine_approach"]
        assert event.data["overshoot_deg"] == clamp_high
        assert event.data["overshoot_clamped"] is True
        assert calls[0] == store.counts_from_output_deg(clamp_high)

    def test_overshoot_within_range_is_not_reported_as_clamped(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        sim.set_deadband(1)
        motion = get_motion_service()
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.fine_approach"]
        assert event.data["overshoot_clamped"] is False
        assert event.data["overshoot_deg"] == (
            12.0 + backend.settings.fine_approach_overshoot_deg)

    def test_event_carries_diagnostic_metadata_for_the_board_run(
            self, monkeypatch, backend, sim):
        """Fields needed to tell 'the mechanism didn't help' apart from 'the
        mechanism never actually ran' - the wait loop can exit before the
        overshoot leg has moved, collapsing both legs into roughly one
        ordinary move with no visible sign in the log otherwise."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        sim.set_deadband(1)
        motion = get_motion_service()
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        [event] = [e for e in _events(backend)
                  if e.event == "servo.move.fine_approach"]
        assert "wait_elapsed_s" in event.data
        assert event.data["wait_elapsed_s"] >= 0.0
        assert "position_at_final_leg_deg" in event.data
        assert "current_a_at_overshoot" in event.data
        assert "torque_kgcm_at_overshoot" in event.data
        assert "current_a_at_final" in event.data
        assert "torque_kgcm_at_final" in event.data

    def test_final_leg_speed_override_applies_only_to_the_final_leg(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        monkeypatch.setattr(backend.settings,
                            "fine_approach_final_speed_dps", 6.0)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        motion = get_motion_service()

        calls = []
        real_command_move = sim.command_move
        monkeypatch.setattr(
            sim, "command_move",
            lambda counts, speed, accel: (calls.append(speed),
                                          real_command_move(counts, speed,
                                                            accel))[1])
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        expected_final_speed = store.counts_speed_from_output_speed(6.0)
        assert calls[0] == store.counts_speed_from_output_speed(
            backend.settings.default_speed_dps)
        assert calls[1] == expected_final_speed

    def test_final_leg_speed_unset_keeps_the_move_speed(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: 30.0)
        motion = get_motion_service()

        calls = []
        real_command_move = sim.command_move
        monkeypatch.setattr(
            sim, "command_move",
            lambda counts, speed, accel: (calls.append(speed),
                                          real_command_move(counts, speed,
                                                            accel))[1])
        motion.move_to(12.0)
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        move_speed = store.counts_speed_from_output_speed(
            backend.settings.default_speed_dps)
        assert calls[0] == move_speed
        assert calls[1] == move_speed

    def test_join_fine_approach_is_a_no_op_with_no_thread(self, motion):
        motion.join_fine_approach(timeout=0.1)   # must not raise

    def test_join_fine_approach_actually_stops_the_thread(
            self, monkeypatch, backend, sim):
        """Forces the wait loop to stay alive for a fixed window, the same
        way the isolation-abort test does, so observing the thread alive
        before joining it is deterministic rather than a timing race."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        monkeypatch.setattr(backend.settings,
                            "fine_approach_timeout_seconds", 0.5)
        from app.deps import get_motion_service, get_state_store
        monkeypatch.setattr(get_state_store(), "current_output_deg",
                            lambda: 30.0)
        real_read_snapshot = sim.read_snapshot
        monkeypatch.setattr(
            sim, "read_snapshot",
            lambda: replace(real_read_snapshot(), moving=True))
        motion = get_motion_service()
        motion.move_to(12.0)   # downward: spawns the fine-approach thread
        assert wait_until(lambda: motion._fine_approach_thread is not None
                          and motion._fine_approach_thread.is_alive(),
                          timeout=1.0)
        motion.join_fine_approach()
        assert motion._fine_approach_thread is None


def _events(backend):
    """Returns recorded operator events.

    Args:
        backend: The backend fixture namespace.

    Returns:
        Recent events.
    """
    from app.deps import get_event_service
    return get_event_service().recent(100)


class TestTarget:
    """Target angle capture: set once on accept, stale (not cleared) on
    stop, never overwritten by the fine-approach overshoot."""

    def test_accepted_move_sets_target(self, motion):
        from app.deps import get_state_store
        motion.move_to(30.0)
        target_deg, stale = get_state_store().target_state()
        assert target_deg == 30.0
        assert stale is False

    def test_rejected_move_does_not_set_target(self, motion):
        from app.deps import get_state_store
        motion.set_lock(True)
        with pytest.raises(LockedError):
            motion.move_to(30.0)
        target_deg, _ = get_state_store().target_state()
        assert target_deg is None

    def test_stop_marks_target_stale_without_clearing_it(self, motion):
        from app.deps import get_state_store
        motion.move_to(30.0)
        motion.stop()
        target_deg, stale = get_state_store().target_state()
        assert target_deg == 30.0
        assert stale is True

    def test_next_move_clears_staleness(self, motion):
        from app.deps import get_state_store
        motion.move_to(30.0)
        motion.stop()
        motion.move_to(12.0)
        target_deg, stale = get_state_store().target_state()
        assert target_deg == 12.0
        assert stale is False

    def test_fine_approach_overshoot_does_not_overwrite_target(
            self, monkeypatch, backend, sim):
        """The overshoot leg commands PAST the requested angle - the
        operator must see what they asked for (12.0), never the
        overshoot value, or the target display would show a number they
        never requested (same twin-path shape as D9/D10)."""
        monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
        from app.deps import get_motion_service, get_state_store
        motion = get_motion_service()
        store = get_state_store()
        sim.set_deadband(1)
        motion.move_to(30.0)
        assert wait_until(lambda: not sim.read_snapshot().moving, timeout=6)
        motion.move_to(12.0)   # downward: triggers the overshoot leg
        assert wait_until(
            lambda: "servo.move.fine_approach" in
            [e.event for e in _events(backend)], timeout=8)
        target_deg, _ = store.target_state()
        assert target_deg == 12.0


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
        from app.deps import get_calibration_service, get_state_store
        # Calibrate at the very bottom of travel, as a failed read once
        # did, and one half becomes physically unreachable - which half
        # depends on servo_direction, so pick by sign rather than assume.
        get_calibration_service().calibrate()
        store = get_state_store()
        low, high = store.reachable_output_range_deg()
        unreachable = (backend.settings.output_min_deg if low > backend.settings.output_min_deg
                      else backend.settings.output_max_deg)
        assert low > backend.settings.output_min_deg or high < backend.settings.output_max_deg
        with pytest.raises(OutOfTravel):
            motion.move_to(unreachable)

    def test_reachable_range_is_symmetric_from_the_centre(self, backend,
                                                          motion):
        from app.deps import get_state_store
        low, high = get_state_store().reachable_output_range_deg()
        assert low < backend.settings.output_min_deg
        assert high > backend.settings.output_max_deg

    def test_full_window_works_from_the_default_baseline(self, motion,
                                                         backend):
        motion.move_to(backend.settings.output_min_deg)
        motion.move_to(backend.settings.output_max_deg)


class _ScriptedArm:
    """Reproduces how this servo actually lands, so the correction loop can
    be tested without hardware.

    Two behaviours were measured on the rig and the loop has to converge
    against both. With a *bias*, the arm lands a fixed distance past
    whatever it is aimed at - at -90 deg it overshot by 0.43 deg on every
    single attempt. With `lands_at_aim`, it instead stops exactly where it
    was told, after one initial miss; that is the case that made the
    original loop ping-pong forever between 45.18 and 44.82.
    """

    def __init__(self, store, bias_deg: float = 0.0,
                 first_miss_deg: float = 0.0):
        self._store = store
        self._bias_deg = bias_deg
        self._first_miss_deg = first_miss_deg
        self.aims_deg: list[float] = []
        self._landed: float = 0.0
        self._moves = 0

    def command_move(self, counts: int, speed: int, accel: int) -> bool:
        """Records the commanded angle and lands the arm.

        Args:
            counts (int): Absolute encoder counts commanded.
            speed (int): Speed in counts per second.
            accel (int): Acceleration parameter.

        Returns:
            bool: Always True; refusal is covered by its own tests.
        """
        aim_deg = self._store.output_deg_from_counts(counts)
        self.aims_deg.append(round(aim_deg, 3))
        self._moves += 1
        if self._moves == 1 and self._first_miss_deg:
            self._landed = aim_deg + self._first_miss_deg
        else:
            self._landed = aim_deg + self._bias_deg
        return True

    def current_output_deg(self):
        """Returns where the arm came to rest.

        Returns:
            float: The landed output angle.
        """
        return round(self._landed, 2)


def _fast_settle(monkeypatch, backend):
    """Shrinks the landing-quiet window so tests do not wait on real time.

    Args:
        monkeypatch: Pytest monkeypatch fixture.
        backend: The backend fixture carrying settings.
    """
    monkeypatch.setattr(backend.settings, "fine_approach_enabled", True)
    monkeypatch.setattr(backend.settings,
                        "fine_approach_settle_quiet_seconds", 0.05)
    monkeypatch.setattr(backend.settings,
                        "fine_approach_timeout_seconds", 3.0)


class TestArrivalDirection:
    """The overshoot is placed by the target's sign, not by where the move
    started.

    Arriving from the wrong side missed by 0.45-0.67 deg against 0.03-0.16
    from the right side (60 trials). Deriving the side from the direction
    of travel let the starting position decide it, so one commanded angle
    had two different resting places.
    """

    def _overshoot_of(self, monkeypatch, backend, sim, start_deg, target_deg):
        """Runs one move and returns the angle of its overshoot leg.

        Args:
            monkeypatch: Pytest monkeypatch fixture.
            backend: Backend fixture.
            sim: Simulated servo fixture.
            start_deg (float): Angle the move starts from.
            target_deg (float): Angle to command.

        Returns:
            float: The overshoot leg's output angle.
        """
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        monkeypatch.setattr(store, "current_output_deg", lambda: start_deg)
        arm = _ScriptedArm(store)
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        get_motion_service().move_to(target_deg)
        assert wait_until(lambda: len(arm.aims_deg) >= 1, timeout=8)
        return arm.aims_deg[0]

    def test_negative_target_overshoots_below_from_either_side(
            self, monkeypatch, backend, sim):
        overshoot = backend.settings.fine_approach_overshoot_deg
        from_above = self._overshoot_of(monkeypatch, backend, sim, 30.0, -30.0)
        assert from_above == pytest.approx(-30.0 - overshoot, abs=0.06)

    def test_positive_target_overshoots_above_from_either_side(
            self, monkeypatch, backend, sim):
        overshoot = backend.settings.fine_approach_overshoot_deg
        from_below = self._overshoot_of(monkeypatch, backend, sim, -30.0, 30.0)
        assert from_below == pytest.approx(30.0 + overshoot, abs=0.06)

    def test_the_same_target_gets_the_same_overshoot_from_both_sides(
            self, monkeypatch, backend, sim):
        # The defect in one line: this pair used to differ, which is why
        # the same command landed in two different places.
        below = self._overshoot_of(monkeypatch, backend, sim, -80.0, -30.0)
        above = self._overshoot_of(monkeypatch, backend, sim, 30.0, -30.0)
        assert below == above


class TestVerifyAndCorrect:
    """The move is not done when the servo acknowledges it, but when the
    arm is measured to have arrived."""

    def test_a_fixed_bias_is_corrected_away(self, monkeypatch, backend, sim):
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store, bias_deg=-0.43)   # the measured -90 case
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        monkeypatch.setattr(store, "current_output_deg",
                            arm.current_output_deg)
        get_motion_service().move_to(-90.0)
        assert wait_until(
            lambda: "servo.move.arrived" in
            [e.event for e in _events(backend)], timeout=8)
        [arrived] = [e for e in _events(backend)
                     if e.event == "servo.move.arrived"]
        assert abs(arrived.data["residual_deg"]) <= (
            backend.settings.fine_approach_gate_deg)
        assert arrived.data["corrections"] >= 1

    def test_an_arm_that_lands_on_its_aim_does_not_ping_pong(
            self, monkeypatch, backend, sim):
        # Measured at +45: 45.18, 44.82, 45.18, 44.82 - forever, because
        # the aim was re-derived from the target every round.
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store, bias_deg=0.0, first_miss_deg=0.18)
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        monkeypatch.setattr(store, "current_output_deg",
                            arm.current_output_deg)
        get_motion_service().move_to(45.0)
        assert wait_until(
            lambda: "servo.move.arrived" in
            [e.event for e in _events(backend)], timeout=8)
        [arrived] = [e for e in _events(backend)
                     if e.event == "servo.move.arrived"]
        assert abs(arrived.data["residual_deg"]) <= (
            backend.settings.fine_approach_gate_deg)

    def test_an_unreadable_position_is_reported_and_never_corrected(
            self, monkeypatch, backend, sim):
        # ADR-0008: a failed read is unknown, never a number. Correcting
        # against an invented position is how a bad read becomes a real,
        # commanded 61 deg swing - which happened on the rig.
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store)
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        reads = {"n": 0}

        def _first_read_then_silence():
            # The move itself needs a starting position; the readback that
            # follows is the one the servo fails to answer.
            reads["n"] += 1
            return 0.0 if reads["n"] == 1 else None

        monkeypatch.setattr(store, "current_output_deg",
                            _first_read_then_silence)
        get_motion_service().move_to(30.0)
        assert wait_until(
            lambda: "servo.move.failed" in
            [e.event for e in _events(backend)], timeout=8)
        assert len(arm.aims_deg) == 2   # overshoot and final leg only

    def test_an_implausible_residual_is_reported_never_driven(
            self, monkeypatch, backend, sim):
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store, bias_deg=-61.0)   # a mid-travel reading
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        monkeypatch.setattr(store, "current_output_deg",
                            arm.current_output_deg)
        get_motion_service().move_to(30.0)
        assert wait_until(
            lambda: "servo.move.failed" in
            [e.event for e in _events(backend)], timeout=8)
        [failure] = [e for e in _events(backend)
                     if e.event == "servo.move.failed"]
        assert "too far to correct safely" in failure.message
        assert len(arm.aims_deg) == 2   # nothing was driven at 61 deg

    def test_a_miss_it_cannot_close_is_reported_not_called_success(
            self, monkeypatch, backend, sim):
        _fast_settle(monkeypatch, backend)
        monkeypatch.setattr(backend.settings,
                            "fine_approach_max_corrections", 2)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        # Lands 0.5 deg out wherever it aims: inside the clamp, so it is a
        # real miss, but no correction can remove it.
        arm = _ScriptedArm(store, bias_deg=-0.5)
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        monkeypatch.setattr(store, "current_output_deg",
                            lambda: round(-30.0 - 0.5, 2))
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        get_motion_service().move_to(-30.0)
        assert wait_until(
            lambda: "servo.move.failed" in
            [e.event for e in _events(backend)], timeout=8)
        [failure] = [e for e in _events(backend)
                     if e.event == "servo.move.failed"]
        assert "short of" in failure.message
        assert failure.data["corrections"] == 2
        assert "servo.move.arrived" not in [e.event for e in _events(backend)]


class TestPositioningIsVisibleAsSettling:
    """Several operators watch the same arm. If it reads HOLDING between
    its own legs it appears finished and then moves again with nobody
    having commanded it."""

    def test_settling_stays_true_across_the_whole_sequence(
            self, monkeypatch, backend, sim):
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store, bias_deg=-0.43)
        seen = []

        def _record_then_move(counts, speed, accel):
            # Sampled from inside the sequence, at each leg it commands, so
            # this cannot race the sequence ending the way sampling from
            # outside does.
            seen.append(store.snapshot().settling)
            return arm.command_move(counts, speed, accel)

        monkeypatch.setattr(sim, "command_move", _record_then_move)
        monkeypatch.setattr(store, "current_output_deg",
                            arm.current_output_deg)
        motion = get_motion_service()
        motion.move_to(-90.0)
        motion.join_fine_approach(timeout=8.0)
        assert wait_until(
            lambda: "servo.move.arrived" in
            [e.event for e in _events(backend)], timeout=8)
        # overshoot, final leg, and at least one corrective re-approach
        assert len(seen) >= 3
        assert all(seen), "the arm read as finished between its own legs"

    def test_settling_clears_once_the_sequence_ends(
            self, monkeypatch, backend, sim):
        _fast_settle(monkeypatch, backend)
        from app.deps import get_motion_service, get_state_store
        store = get_state_store()
        arm = _ScriptedArm(store, bias_deg=-0.43)
        monkeypatch.setattr(sim, "command_move", arm.command_move)
        monkeypatch.setattr(store, "current_output_deg",
                            arm.current_output_deg)
        motion = get_motion_service()
        motion.move_to(-90.0)
        motion.join_fine_approach(timeout=8.0)
        assert wait_until(lambda: store.snapshot().settling is False,
                          timeout=8)
