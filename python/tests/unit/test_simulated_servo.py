"""SimulatedServoRepository: motion, deadband, faults, signed multi-turn."""

from tests.conftest import wait_until


class TestMotion:
    """Basic motion profile."""

    def test_moves_toward_target(self, sim):
        sim.set_deadband(1)
        sim.command_move(2000, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 2000) <= 2)

    def test_stop_holds_position(self, sim):
        sim.set_deadband(1)
        sim.command_move(4000, 2000, 50)
        assert wait_until(lambda: sim.read_raw_counts() > 200)
        sim.command_stop()
        held = sim.read_raw_counts()
        import time
        time.sleep(0.2)
        assert abs(sim.read_raw_counts() - held) <= 1


class TestDeadband:
    """Dead-zone behavior."""

    def test_stops_inside_deadband(self, sim):
        sim.set_deadband(50)
        sim.command_move(1000, 20000, 50)
        assert wait_until(
            lambda: not sim.read_snapshot().moving, timeout=3.0)
        assert abs(sim.read_raw_counts() - 1000) <= 50

    def test_tighter_deadband_lands_closer(self, sim):
        sim.set_deadband(2)
        sim.command_move(1000, 20000, 50)
        assert wait_until(lambda: not sim.read_snapshot().moving)
        assert abs(sim.read_raw_counts() - 1000) <= 2

    def test_minimum_deadband_is_one(self, sim):
        sim.set_deadband(0)
        assert sim._deadband_counts == 1


class TestSignedMultiTurn:
    """Absolute counts beyond one turn and below zero (contract)."""

    def test_negative_counts_no_wrap(self, sim):
        sim.set_deadband(1)
        sim.command_move(-300, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() + 300) <= 2)
        assert sim.read_raw_counts() < 0

    def test_counts_beyond_one_turn(self, sim):
        sim.set_deadband(1)
        sim.command_move(10000, 40000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 10000) <= 2)


class TestFaults:
    """Overload semantics."""

    def test_overload_visible_in_snapshot(self, sim):
        sim.simulate_overload()
        assert sim.read_snapshot().overload is True

    def test_new_position_command_clears_overload(self, sim):
        sim.simulate_overload()
        sim.command_move(sim.read_raw_counts(), 1000, 50)
        assert sim.read_snapshot().overload is False

    def test_other_flags_false(self, sim):
        snapshot = sim.read_snapshot()
        assert not any((snapshot.overcurrent, snapshot.overheat,
                        snapshot.voltage_fault, snapshot.sensor_fault))


class TestTorque:
    """Motor isolation: cutting torque must stop the shaft actually moving,
    not just report False - a twin that only lied about moving while still
    driving would be worse than the thing it is meant to fix."""

    def test_set_torque_returns_true(self, sim):
        assert sim.set_torque(False) is True
        assert sim.set_torque(True) is True

    def test_isolated_servo_does_not_reach_its_target(self, sim):
        sim.set_deadband(1)
        sim.set_torque(False)
        sim.command_move(4000, 20000, 50)
        import time
        time.sleep(0.2)
        assert abs(sim.read_raw_counts() - 4000) > 100

    def test_moving_is_false_while_isolated_even_with_a_live_target(self, sim):
        sim.set_deadband(1)
        sim.command_move(4000, 20000, 50)
        assert wait_until(lambda: sim.read_snapshot().moving)
        sim.set_torque(False)
        assert sim.read_snapshot().moving is False

    def test_restoring_torque_does_not_resume_a_stale_target(self, sim):
        """Mirrors the real controller's un-isolate ordering: the target
        snaps to wherever the shaft actually is before torque returns, so
        it does not lurch toward a goal set before isolation."""
        sim.set_deadband(1)
        sim.command_move(4000, 20000, 50)
        assert wait_until(lambda: sim.read_snapshot().moving)
        sim.set_torque(False)
        held = sim.read_raw_counts()
        sim.set_torque(True)
        import time
        time.sleep(0.2)
        assert abs(sim.read_raw_counts() - held) <= 2

    def test_read_torque_register_reflects_current_state(self, sim):
        assert sim.read_torque_register() == 1
        sim.set_torque(False)
        assert sim.read_torque_register() == 0
        sim.set_torque(True)
        assert sim.read_torque_register() == 1

    def test_read_tuning_registers_reports_factory_defaults(self, sim):
        """Nothing in this repository writes these registers - it must
        report what an untouched servo actually ships with, not zeros."""
        registers = sim.read_tuning_registers()
        assert registers.position_p == 32
        assert registers.position_d == 32
        assert registers.position_i == 0
        assert registers.min_start_force == 0
        assert registers.cw_dead_zone == 1
        assert registers.ccw_dead_zone == 1

    def test_write_tuning_registers_updates_the_written_fields(self, sim):
        assert sim.write_tuning_registers(position_p=16, min_start_force=50) \
            is True
        registers = sim.read_tuning_registers()
        assert registers.position_p == 16
        assert registers.min_start_force == 50

    def test_write_tuning_registers_leaves_unset_fields_alone(self, sim):
        sim.write_tuning_registers(position_p=16)
        registers = sim.read_tuning_registers()
        assert registers.position_d == 32
        assert registers.position_i == 0
        assert registers.cw_dead_zone == 1
        assert registers.ccw_dead_zone == 1

    def test_read_present_speed_is_zero_when_settled(self, sim):
        assert sim.read_present_speed_counts_s() == 0

    def test_read_present_speed_is_signed_toward_the_target(self, sim):
        sim.set_deadband(1)
        sim.command_move(4000, 2000, 50)
        assert wait_until(lambda: sim.read_present_speed_counts_s() > 0)
        sim.command_move(-4000, 2000, 50)
        assert wait_until(lambda: sim.read_present_speed_counts_s() < 0)


class TestRangeConfiguration:
    """configure_range records the travel-range mode."""

    def test_single_turn_default(self, sim):
        sim.configure_range(False, 1)
        assert sim._multi_turn is False
        assert sim._angle_resolution == 1

    def test_multi_turn_with_amplification(self, sim):
        sim.configure_range(True, 2)
        assert sim._multi_turn is True
        assert sim._angle_resolution == 2

    def test_amplification_clamped_to_1_3(self, sim):
        sim.configure_range(True, 9)
        assert sim._angle_resolution == 3
        sim.configure_range(True, 0)
        assert sim._angle_resolution == 1
