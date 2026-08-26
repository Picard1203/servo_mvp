"""IsolationService: intent, reconciliation against hardware, idle backup."""

import time

import pytest

from tests.conftest import wait_until


class FlakyServo:
    """Wraps the real simulator but can be told to refuse the next
    torque acknowledgement, so reconciliation failure/retry is testable
    without a real bus."""

    def __init__(self, inner):
        self._inner = inner
        self.ack = True
        self.calls = []

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def set_torque(self, enabled):
        self.calls.append(enabled)
        return self.ack


@pytest.fixture()
def flaky(monkeypatch, backend, sim):
    """Swaps the cached servo repository for one whose ack is
    controllable, for the tests that need a failed write. Uses
    monkeypatch (not a raw assignment) so the real provider is restored
    after the test regardless of outcome - a raw reassignment here once
    leaked a fake servo into every unrelated test in the same run.

    Returns:
        The flaky wrapper.
    """
    from app import deps
    wrapper = FlakyServo(sim)
    monkeypatch.setattr(deps, "get_servo_repository", lambda: wrapper)
    return wrapper


class TestReconciliation:
    """Intent -> acknowledged hardware state, and never the reverse."""

    def test_manual_isolate_reconciles_immediately(self, backend, sim):
        from app.deps import get_isolation_service, get_state_store
        get_isolation_service().set_isolated(True)
        assert get_state_store().is_isolated_known() is True
        # The bookkeeping flag is not enough on its own - it can flip
        # cleanly while the actual argument sent to the servo is inverted.
        # Assert the real consequence: torque must actually be cut.
        assert sim.read_torque_register() == 0

    def test_manual_un_isolate_reconciles_immediately(self, backend, sim):
        from app.deps import get_isolation_service, get_state_store
        isolation = get_isolation_service()
        isolation.set_isolated(True)
        isolation.set_isolated(False)
        assert get_state_store().is_isolated_known() is False
        assert sim.read_torque_register() == 1

    def test_isolate_sends_torque_disabled_not_the_raw_intent(
            self, backend, flaky):
        """Regression for the inversion bug: `set_torque`'s argument means
        "restore torque", the opposite of "isolated" intent. FlakyServo
        already recorded every call; nothing ever asserted on it."""
        from app.deps import get_isolation_service
        get_isolation_service().set_isolated(True)
        assert flaky.calls == [False]

    def test_intent_persists_across_a_fresh_service_over_the_same_db(
            self, backend, sim):
        """The whole point of ADR-0010: a rebuilt process (a restart)
        must see the intent the previous process left behind."""
        from app.deps import get_isolation_service, get_state_store
        get_isolation_service().set_isolated(True)

        from app.services.isolation_service import IsolationService
        from app.deps import get_app_state_repository, get_event_service
        rebuilt = IsolationService(
            sim, get_state_store(), get_app_state_repository(),
            get_event_service(), backend.settings)
        assert rebuilt._state.is_isolated_intent() is True

    def test_known_is_never_true_on_an_unacknowledged_write(
            self, backend, flaky):
        """The false-safety-claim case this feature exists to prevent:
        if the servo does not ack, the operator must never be told the
        motor is isolated."""
        flaky.ack = False
        from app.deps import get_isolation_service, get_state_store
        get_isolation_service().set_isolated(True)
        assert get_state_store().is_isolated_known() is False
        assert get_state_store().is_isolated_intent() is True

    def test_tick_retries_a_previously_failed_write(self, backend, flaky):
        flaky.ack = False
        from app.deps import get_isolation_service, get_state_store
        isolation = get_isolation_service()
        isolation.set_isolated(True)
        assert get_state_store().is_isolated_known() is False
        flaky.ack = True
        isolation.tick()
        assert get_state_store().is_isolated_known() is True

    def test_events_recorded_only_on_acknowledged_change(
            self, backend, flaky):
        flaky.ack = False
        from app.deps import get_event_service, get_isolation_service
        get_isolation_service().set_isolated(True)
        events = [e.event for e in get_event_service().recent(50)]
        assert "servo.isolation.engaged" not in events

    def test_engage_records_event_with_manual_reason(self, backend, sim):
        from app.deps import get_event_service, get_isolation_service
        get_isolation_service().set_isolated(True)
        events = get_event_service().recent(50)
        engaged = next(e for e in events
                       if e.event == "servo.isolation.engaged")
        assert engaged.data["reason"] == "manual"

    def test_isolating_marks_the_target_stale(self, backend, sim):
        from app.deps import get_isolation_service, get_state_store
        state = get_state_store()
        state.set_target(30.0)
        get_isolation_service().set_isolated(True)
        _, stale = state.target_state()
        assert stale is True


class TestIdleBackup:
    """The idle timer only ever catches 'locked but forgot to isolate'."""

    def test_never_fires_while_unlocked(self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "isolation_idle_timeout_s",
                            0.05)
        from app.deps import get_isolation_service, get_state_store
        isolation = get_isolation_service()
        time.sleep(0.2)
        for _ in range(5):
            isolation.tick()
        assert get_state_store().is_isolated_known() is False

    def test_fires_after_being_locked_and_idle(self, monkeypatch, backend,
                                               sim):
        monkeypatch.setattr(backend.settings, "isolation_idle_timeout_s",
                            0.05)
        from app.deps import (get_isolation_service, get_motion_service,
                              get_state_store)
        get_motion_service().set_lock(True)
        isolation = get_isolation_service()
        state = get_state_store()

        def _idled_and_isolated() -> bool:
            isolation.tick()
            return state.is_isolated_known()

        assert wait_until(_idled_and_isolated, timeout=2.0)

    def test_auto_engage_records_event_with_idle_reason(
            self, monkeypatch, backend, sim):
        monkeypatch.setattr(backend.settings, "isolation_idle_timeout_s",
                            0.05)
        from app.deps import (get_event_service, get_isolation_service,
                              get_motion_service)
        get_motion_service().set_lock(True)
        isolation = get_isolation_service()
        events = get_event_service()

        def _idled_with_reason() -> bool:
            isolation.tick()
            return any(e.event == "servo.isolation.engaged"
                      and e.data.get("reason") == "idle"
                      for e in events.recent(50))

        assert wait_until(_idled_with_reason, timeout=2.0)

    def test_does_not_re_fire_once_already_isolated(self, monkeypatch,
                                                     backend, sim):
        monkeypatch.setattr(backend.settings, "isolation_idle_timeout_s",
                            0.05)
        from app.deps import (get_event_service, get_isolation_service,
                              get_motion_service)
        get_motion_service().set_lock(True)
        isolation = get_isolation_service()
        isolation.set_isolated(True)   # manual, ahead of the timer
        time.sleep(0.2)
        for _ in range(5):
            isolation.tick()
        engagements = [e for e in get_event_service().recent(50)
                      if e.event == "servo.isolation.engaged"]
        assert len(engagements) == 1   # the manual one only

    def test_un_isolating_while_locked_restarts_the_idle_clock(
            self, monkeypatch, backend, sim):
        """A deliberate un-isolate while still locked must not be
        immediately re-isolated with whatever time happened to remain
        on the original window."""
        monkeypatch.setattr(backend.settings, "isolation_idle_timeout_s",
                            0.3)
        from app.deps import (get_isolation_service, get_motion_service,
                              get_state_store)
        get_motion_service().set_lock(True)
        isolation = get_isolation_service()
        time.sleep(0.25)          # most of the way through the window
        isolation.set_isolated(False)
        isolation.tick()
        assert get_state_store().is_isolated_known() is False
        time.sleep(0.1)            # would have fired under the OLD clock
        isolation.tick()
        assert get_state_store().is_isolated_known() is False
