"""BridgeServoRepository: the CSV contract with the sketch.

No board and no Bridge are needed - a fake bridge records the calls and
returns canned payloads, which is exactly the seam the repository was given
a constructor argument for.
"""

import pytest

from app.repositories.concrete.bridge_servo_repository import (
    BridgeServoRepository, decode_sign_magnitude)


class FakeBridge:
    """Records Bridge calls and replies with a scripted payload."""

    def __init__(self, reply="ok"):
        self.calls = []
        self.reply = reply
        self.raise_on_call = None

    def call(self, name, payload):
        """Records one call.

        Args:
            name: Bridge function name.
            payload: Request payload.

        Returns:
            The scripted reply.
        """
        self.calls.append((name, payload))
        if self.raise_on_call is not None:
            raise self.raise_on_call
        return self.reply


# valid,counts,moving,temp,volt,curr,torque,load,status
GOOD = "1,1234,1,36.2,12.08,0.19,2.09,240,0"


@pytest.fixture()
def bridge():
    """A fake bridge returning a healthy snapshot.

    Returns:
        The fake.
    """
    return FakeBridge(GOOD)


@pytest.fixture()
def repo(bridge):
    """Repository wired to the fake bridge.

    Returns:
        The repository under test.
    """
    return BridgeServoRepository(bridge=bridge)


class TestSnapshotDecoding:
    """The snapshot payload maps onto TelemetrySnapshot."""

    def test_all_fields_decoded(self, repo):
        snapshot = repo.read_snapshot()
        assert snapshot.raw_counts == 1234
        assert snapshot.moving is True
        assert snapshot.temperature_c == 36.2
        assert snapshot.voltage_v == 12.08
        assert snapshot.current_a == 0.19
        assert snapshot.torque_kgcm == 2.09
        assert not snapshot.overload

    def test_negative_multi_turn_counts(self, bridge, repo):
        bridge.reply = "1,-2500,0,30.0,12.0,0.1,1.1,0,0"
        assert repo.read_snapshot().raw_counts == -2500

    def test_counts_beyond_one_turn(self, bridge, repo):
        bridge.reply = "1,9000,0,30.0,12.0,0.1,1.1,0,0"
        assert repo.read_snapshot().raw_counts == 9000


class TestFaultBits:
    """Every documented status bit maps to its own flag."""

    @pytest.mark.parametrize("bits,attribute", [
        (1, "voltage_fault"),
        (2, "sensor_fault"),
        (4, "overheat"),
        (8, "overcurrent"),
        (16, "angle_fault"),
        (32, "overload"),
    ])
    def test_single_bit(self, bridge, repo, bits, attribute):
        bridge.reply = f"1,0,0,30.0,12.0,0.1,1.1,0,{bits}"
        assert getattr(repo.read_snapshot(), attribute) is True

    def test_bit4_is_the_flag_the_backend_used_to_miss(self, bridge, repo):
        bridge.reply = "1,0,0,30.0,12.0,0.1,1.1,0,16"
        snapshot = repo.read_snapshot()
        assert snapshot.angle_fault is True
        assert snapshot.overload is False

    def test_combined_bits_decode_independently(self, bridge, repo):
        bridge.reply = "1,0,0,30.0,12.0,0.1,1.1,0,36"   # 32 overload + 4 heat
        snapshot = repo.read_snapshot()
        assert snapshot.overload and snapshot.overheat
        assert not snapshot.overcurrent
        assert not snapshot.angle_fault


class TestCommands:
    """Commands become the payloads the sketch parses."""

    def test_move_payload(self, bridge, repo):
        bridge.reply = "ok"
        repo.command_move(1500, 900, 50)
        assert bridge.calls[-1] == ("servo_move", "1500,900,50")

    def test_negative_target_is_sent_verbatim(self, bridge, repo):
        bridge.reply = "ok"
        repo.command_move(-400, 100, 20)
        assert bridge.calls[-1] == ("servo_move", "-400,100,20")

    def test_stop(self, bridge, repo):
        bridge.reply = "ok"
        repo.command_stop()
        assert bridge.calls[-1] == ("servo_stop", "")

    def test_move_returns_true_on_ack(self, bridge, repo):
        bridge.reply = "ok"
        assert repo.command_move(1500, 900, 50) is True

    def test_move_returns_false_when_not_acknowledged(self, bridge, repo):
        """The ack is load-bearing here too: a caller must never believe
        a move was dispatched on an unconfirmed write."""
        bridge.reply = "err"
        assert repo.command_move(1500, 900, 50) is False

    def test_move_returns_false_on_bridge_exception(self, bridge, repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.command_move(1500, 900, 50) is False

    def test_stop_returns_true_on_ack(self, bridge, repo):
        bridge.reply = "ok"
        assert repo.command_stop() is True

    def test_stop_returns_false_when_not_acknowledged(self, bridge, repo):
        bridge.reply = "err"
        assert repo.command_stop() is False

    def test_set_deadband(self, bridge, repo):
        bridge.reply = "ok"
        repo.set_deadband(0)
        assert bridge.calls[-1] == ("servo_set_deadband", "0")

    def test_configure_range_single_turn(self, bridge, repo):
        bridge.reply = "ok"
        repo.configure_range(False, 1)
        assert bridge.calls[-1] == ("servo_configure_range", "0,1")

    def test_configure_range_multi_turn(self, bridge, repo):
        bridge.reply = "ok"
        repo.configure_range(True, 2)
        assert bridge.calls[-1] == ("servo_configure_range", "1,2")

    def test_set_torque_off_payload(self, bridge, repo):
        bridge.reply = "ok"
        repo.set_torque(False)
        assert bridge.calls[-1] == ("servo_set_torque", "0")

    def test_set_torque_on_payload(self, bridge, repo):
        bridge.reply = "ok"
        repo.set_torque(True)
        assert bridge.calls[-1] == ("servo_set_torque", "1")

    def test_set_torque_returns_true_on_ack(self, bridge, repo):
        bridge.reply = "ok"
        assert repo.set_torque(False) is True

    def test_set_torque_returns_false_when_not_acknowledged(self, bridge, repo):
        """The ack is load-bearing for this one command: callers must
        never believe isolation took effect on an unconfirmed write."""
        bridge.reply = "err"
        assert repo.set_torque(False) is False

    def test_set_torque_returns_false_on_bridge_exception(self, bridge, repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.set_torque(True) is False

    def test_read_torque_register_payload(self, bridge, repo):
        bridge.reply = "0"
        repo.read_torque_register()
        assert bridge.calls[-1] == ("servo_read_torque", "")

    def test_read_torque_register_parses_zero(self, bridge, repo):
        bridge.reply = "0"
        assert repo.read_torque_register() == 0

    def test_read_torque_register_parses_one(self, bridge, repo):
        bridge.reply = "1"
        assert repo.read_torque_register() == 1

    def test_read_torque_register_none_when_not_acknowledged(self, bridge,
                                                              repo):
        bridge.reply = "err"
        assert repo.read_torque_register() is None

    def test_read_torque_register_none_on_bridge_exception(self, bridge,
                                                            repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.read_torque_register() is None

    def test_read_tuning_registers_payload(self, bridge, repo):
        bridge.reply = "1,32,32,0,0,1,1"
        repo.read_tuning_registers()
        assert bridge.calls[-1] == ("servo_read_tuning", "")

    def test_read_tuning_registers_parses_all_fields(self, bridge, repo):
        bridge.reply = "1,16,32,8,50,0,0"
        registers = repo.read_tuning_registers()
        assert registers.position_p == 16
        assert registers.position_d == 32
        assert registers.position_i == 8
        assert registers.min_start_force == 50
        assert registers.cw_dead_zone == 0
        assert registers.ccw_dead_zone == 0

    def test_read_tuning_registers_none_when_not_acknowledged(self, bridge,
                                                               repo):
        bridge.reply = "0,32,32,0,0,1,1"
        assert repo.read_tuning_registers() is None

    def test_read_tuning_registers_none_on_malformed_payload(self, bridge,
                                                              repo):
        bridge.reply = "1,32,32"
        assert repo.read_tuning_registers() is None

    def test_read_tuning_registers_none_on_unparsable_payload(self, bridge,
                                                               repo):
        bridge.reply = "1,x,32,0,0,1,1"
        assert repo.read_tuning_registers() is None

    def test_read_tuning_registers_none_on_bridge_exception(self, bridge,
                                                             repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.read_tuning_registers() is None

    def test_write_tuning_registers_all_unset_sends_all_sentinels(
            self, bridge, repo):
        bridge.reply = "ok"
        repo.write_tuning_registers()
        assert bridge.calls[-1] == ("servo_write_tuning", "-1,-1,-1,-1,-1,-1")

    def test_write_tuning_registers_payload_leaves_unset_fields_at_sentinel(
            self, bridge, repo):
        bridge.reply = "ok"
        repo.write_tuning_registers(position_p=16, min_start_force=50)
        assert bridge.calls[-1] == (
            "servo_write_tuning", "16,-1,-1,50,-1,-1")

    def test_write_tuning_registers_returns_true_on_ack(self, bridge, repo):
        bridge.reply = "ok"
        assert repo.write_tuning_registers(position_p=16) is True

    def test_write_tuning_registers_returns_false_when_not_acknowledged(
            self, bridge, repo):
        bridge.reply = "err"
        assert repo.write_tuning_registers(position_p=16) is False

    def test_write_tuning_registers_returns_false_on_bridge_exception(
            self, bridge, repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.write_tuning_registers(position_p=16) is False

    def test_read_present_speed_payload(self, bridge, repo):
        bridge.reply = "120"
        repo.read_present_speed_counts_s()
        assert bridge.calls[-1] == ("servo_read_speed", "")

    def test_read_present_speed_parses_positive(self, bridge, repo):
        bridge.reply = "120"
        assert repo.read_present_speed_counts_s() == 120

    def test_read_present_speed_parses_negative(self, bridge, repo):
        bridge.reply = "-120"
        assert repo.read_present_speed_counts_s() == -120

    def test_read_present_speed_none_on_unparsable_payload(self, bridge,
                                                            repo):
        bridge.reply = "err"
        assert repo.read_present_speed_counts_s() is None

    def test_read_present_speed_none_on_bridge_exception(self, bridge, repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        assert repo.read_present_speed_counts_s() is None


class TestResilience:
    """A misbehaving bus must not take the backend down."""

    def test_malformed_payload_yields_empty_snapshot(self, bridge, repo):
        bridge.reply = "garbage"
        snapshot = repo.read_snapshot()
        assert snapshot.raw_counts == 0
        assert not snapshot.overload

    def test_unparsable_numbers_yield_empty_snapshot(self, bridge, repo):
        bridge.reply = "1,abc,0,x,y,z,q,0,0"
        assert repo.read_snapshot().raw_counts == 0

    def test_bridge_exception_is_contained(self, bridge, repo):
        bridge.raise_on_call = RuntimeError("bridge down")
        snapshot = repo.read_snapshot()
        assert snapshot.raw_counts == 0
        assert snapshot.valid is False if hasattr(snapshot, "valid") else True

    def test_rejected_command_does_not_raise(self, bridge, repo):
        bridge.reply = "err"
        repo.command_stop()          # logged, not raised


class TestSignMagnitude:
    """The wire-format decoder stays available to callers."""

    @pytest.mark.parametrize("raw,expected", [
        (0, 0), (2048, 2048), (32773, -5), (32768, 0),
    ])
    def test_decode(self, raw, expected):
        assert decode_sign_magnitude(raw) == expected

    def test_offset_register_uses_bit11(self):
        assert decode_sign_magnitude((1 << 11) | 7, sign_bit=11) == -7


class TestDefaultBridge:
    """With no bridge injected it falls back to the Arduino Bridge."""

    def test_defaults_to_the_arduino_bridge(self, backend):
        from tests.conftest import BridgeStub
        repository = BridgeServoRepository()
        BridgeStub.call_result = "ok"
        repository.command_stop()
        assert ("servo_stop", ("",)) in BridgeStub.calls


class TestBackendSelection:
    """deps honours use_hardware_servo."""

    def test_simulated_by_default(self, backend):
        from app.deps import get_servo_repository
        assert type(get_servo_repository()).__name__ == \
            "SimulatedServoRepository"

    def test_hardware_when_enabled(self, monkeypatch, backend):
        from app.core.config import get_settings
        from app import deps
        monkeypatch.setenv("USE_HARDWARE_SERVO", "true")
        get_settings.cache_clear()
        deps.get_servo_repository.cache_clear()
        assert type(deps.get_servo_repository()).__name__ == \
            "BridgeServoRepository"
        get_settings.cache_clear()
        deps.get_servo_repository.cache_clear()


class TestConcurrencySafety:
    """The Bridge is a single multiplexed link; only one call at a time."""

    def test_calls_are_serialised(self):
        """Two threads reading at once must not overlap on the wire.

        Overlapping RPC interleaves message ids, and a reply then arrives
        for a request the caller has abandoned - the "Response for unknown
        msgid" failure seen on the board.
        """
        import threading
        import time

        overlaps = []
        active = []

        class SlowBridge:
            def call(self, name, payload):
                active.append(name)
                if len(active) > 1:
                    overlaps.append(len(active))
                time.sleep(0.05)
                active.pop()
                return GOOD

        repo = BridgeServoRepository(bridge=SlowBridge(), cache_seconds=0.0)
        threads = [threading.Thread(target=repo.read_snapshot)
                   for _ in range(6)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        assert overlaps == [], f"bridge calls overlapped: {overlaps}"

    def test_reads_within_the_window_share_one_bus_trip(self, bridge):
        repo = BridgeServoRepository(bridge=bridge, cache_seconds=5.0)
        for _ in range(10):
            repo.read_snapshot()
        assert len(bridge.calls) == 1

    def test_cache_expires(self, bridge):
        repo = BridgeServoRepository(bridge=bridge, cache_seconds=0.0)
        repo.read_snapshot()
        repo.read_snapshot()
        assert len(bridge.calls) == 2

    def test_command_invalidates_the_cache(self, bridge):
        repo = BridgeServoRepository(bridge=bridge, cache_seconds=5.0)
        repo.read_snapshot()
        bridge.reply = "ok"
        repo.command_stop()
        bridge.reply = GOOD
        repo.read_snapshot()
        names = [name for name, _ in bridge.calls]
        assert names.count("servo_read") == 2


class TestInvalidFlagHonoured:
    """Field 0 of the snapshot payload is the sketch saying 'no answer'."""

    def test_valid_zero_yields_an_invalid_snapshot(self, bridge, repo):
        bridge.reply = "0,0,0,0,0,0,0,0,0"
        snapshot = repo.read_snapshot()
        assert snapshot.valid is False

    def test_valid_one_yields_a_usable_snapshot(self, repo):
        assert repo.read_snapshot().valid is True
