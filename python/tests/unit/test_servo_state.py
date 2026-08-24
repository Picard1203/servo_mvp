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


class TestFailedReadIsNeverAPosition:
    """A read the servo never answered must not become a position.

    Observed on the board on 7 August 2026: three consecutive Bridge
    stalls, each 10.99 s (the servo_read timeout plus one sampler
    interval), returned an empty snapshot with valid=False. snapshot()
    used its raw_counts anyway, so the UI displayed -212.74 deg and the
    database stored it. One sample stored count -1, which no 0..4095
    servo can report. Nothing was logged.

    This is the same defect class as the calibrate() guard in
    TestCalibrationRobustness, applied to the path that feeds every
    operator decision.
    """

    @staticmethod
    def _dead_bus():
        from app.models.entities import TelemetrySnapshot
        return TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False,
            overcurrent=False, overheat=False, voltage_fault=False,
            sensor_fault=False, angle_fault=False, valid=False)

    def test_invalid_reading_reports_no_position(self, backend, sim):
        from app.deps import get_state_store
        sim.read_snapshot = self._dead_bus
        view = get_state_store().snapshot()
        assert view.reading_valid is False
        assert view.output_deg is None
        assert view.raw_counts is None

    def test_invalid_reading_is_logged(self, backend, sim):
        from app.deps import get_state_store
        sim.read_snapshot = self._dead_bus
        get_state_store().snapshot()
        assert "servo.read.failed" in backend.logger.events()

    def test_invalid_reading_reports_no_telemetry(self, backend, sim):
        """The rule that nulls the position governs the readings beside it.

        The docstring on output_deg stated the rule correctly and it was
        applied to one field of five: temperature, voltage, current and
        torque stayed plain floats, so a dead bus delivered 0.0 for each
        from _empty_snapshot(). An operator saw 0.00 V next to a position
        that honestly said unknown, which reads as lost power (D16).
        """
        from app.deps import get_state_store
        sim.read_snapshot = self._dead_bus
        view = get_state_store().snapshot()
        assert view.temperature_c is None
        assert view.voltage_v is None
        assert view.current_a is None
        assert view.torque_kgcm is None

    def test_valid_reading_still_reports_telemetry(self, backend, sim):
        """Nulling on failure must not null on success."""
        from app.deps import get_state_store
        view = get_state_store().snapshot()
        assert view.reading_valid is True
        assert isinstance(view.temperature_c, float)
        assert isinstance(view.voltage_v, float)
        assert isinstance(view.current_a, float)
        assert isinstance(view.torque_kgcm, float)


class TestOneBaseline:
    """The display and the motion path must share one baseline.

    Observed on the board: with no datum captured and the servo parked
    at count 0, an operator pressed "move to 90". The motion path used
    the mid-travel baseline and correctly logged from_deg -122.7, so the
    servo swept 3550 counts - 212.7 output degrees. The display used a
    baseline of 0 and read "0.0 deg" throughout. The operator commanded
    90 from a screen showing 0 and the mechanism moved 212.7.
    """

    def test_snapshot_agrees_with_the_motion_conversion(self, backend, sim):
        from app.deps import get_state_store
        store = get_state_store()
        counts = store.snapshot().raw_counts
        assert store.snapshot().output_deg == round(
            store.output_deg_from_counts(counts), 2)

    def test_no_datum_baselines_on_mid_travel_not_zero(self, backend):
        from app.deps import get_state_store
        store = get_state_store()
        centre = backend.settings.counts_per_turn // 2
        assert store.output_deg_from_counts(centre) == 0.0
        assert store.output_deg_from_counts(0) < -100.0


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
