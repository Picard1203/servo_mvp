"""ServoStateStore: conversions, lock/settle, verified flag, snapshot."""

from tests.conftest import wait_until


class TestConversions:
    """Angle <-> counts math with the 44:30 ratio."""

    def test_roundtrip_output_deg(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        counts = store.counts_from_output_deg(90.0)
        assert abs(store.output_deg_from_counts(counts) - 90.0) < 0.01

    def test_full_output_turn_exceeds_one_servo_turn(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        counts_360 = store.counts_from_output_deg(360.0)
        assert counts_360 > backend.settings.counts_per_turn  # 528 servo deg

    def test_speed_conversion_minimum_one(self, backend):
        from app.deps import get_state_store
        assert get_state_store().counts_speed_from_output_speed(0.001) >= 1


class TestLockAndSettle:
    """Lock state and settle window."""

    def test_lock_change_opens_settle_window(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        assert store.settle_remaining_seconds() == 0.0
        assert store.set_locked(True) is True
        assert store.is_locked() is True
        assert store.settle_remaining_seconds() > 0.0

    def test_same_state_does_not_restart_window(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        store.set_locked(True)
        assert wait_until(lambda: store.settle_remaining_seconds() == 0.0)
        assert store.set_locked(True) is False
        assert store.settle_remaining_seconds() == 0.0


class TestVerifiedFlag:
    """Post-boot position verification."""

    def test_unverified_until_marked(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        assert store.is_position_verified() is False
        store.mark_position_verified()
        assert store.is_position_verified() is True


class TestSnapshot:
    """Coherent snapshot content."""

    def test_snapshot_fields(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        view = store.snapshot()
        assert view.active_zero_name == "factory"
        assert view.position_verified is False
        assert view.locked is False
        assert view.overload is False
        assert isinstance(view.output_deg, float)


class TestDirection:
    """servo_direction inverts commanded and reported motion together.

    Round-trip tolerance is one encoder count (0.06 deg at the output):
    an absolute target is rounded to the nearest achievable count, so a
    residual under one count is the hardware grid, not an error.
    """

    def test_forward_direction_roundtrip(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        counts = store.counts_from_output_deg(30.0)
        assert counts > 0
        assert abs(store.output_deg_from_counts(counts) - 30.0) < 0.06

    def test_reversed_direction_inverts_counts(self, backend):
        from app.services.servo_state import ServoStateStore
        from app.deps import get_servo_repository, get_zero_repository
        reversed_store = ServoStateStore(
            servo=get_servo_repository(), zeros=get_zero_repository(),
            settling_seconds=backend.settings.settling_seconds,
            counts_per_turn=backend.settings.counts_per_turn,
            servo_deg_per_output_deg=backend.settings.servo_deg_per_output_deg,
            servo_direction=-1)
        forward = reversed_store.counts_from_output_deg(30.0)
        # The baseline is the centre of travel, so "mirrored" means the
        # OFFSET from the baseline flips sign, not the absolute count.
        centre = backend.settings.counts_per_turn // 2
        assert forward < centre
        # and it still round-trips: sign applied on both conversions
        assert abs(reversed_store.output_deg_from_counts(forward) - 30.0) < 0.06
        from app.deps import get_state_store
        assert (get_state_store().counts_from_output_deg(30.0) - centre
                == -(forward - centre))

    def test_negative_angles_are_in_range(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        assert backend.settings.output_min_deg == -90.0
        counts = store.counts_from_output_deg(-90.0)
        assert abs(store.output_deg_from_counts(counts) + 90.0) < 0.06


class TestReachableRange:
    """The usable window depends on where the datum sits."""

    def test_reversed_direction_range_is_mirrored(self, backend):
        from app.services.servo_state import ServoStateStore
        from app.deps import get_servo_repository, get_zero_repository
        store = ServoStateStore(
            servo=get_servo_repository(), zeros=get_zero_repository(),
            settling_seconds=backend.settings.settling_seconds,
            counts_per_turn=backend.settings.counts_per_turn,
            servo_deg_per_output_deg=backend.settings.servo_deg_per_output_deg,
            servo_direction=-1)
        low, high = store.reachable_output_range_deg()
        assert low < 0 < high
