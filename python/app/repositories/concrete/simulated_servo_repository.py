"""Simulated servo: sprint-1 stand-in for the real serial bus."""

import random
from math import copysign
from threading import Lock, Thread
from time import sleep

from app.models.entities import TelemetrySnapshot, TuningRegisters

_TICK_SECONDS = 0.05
_KT_KGCM_PER_A = 11.0

# STS3215 factory defaults - this simulator never writes these registers,
# so it reports what an untouched servo actually ships with (bench-sourced,
# see skills/uno-q-st3215/SKILL.md), not zeros.
_FACTORY_POSITION_P = 32
_FACTORY_POSITION_D = 32
_FACTORY_POSITION_I = 0
_FACTORY_MIN_START_FORCE = 0
_FACTORY_CW_DEAD_ZONE = 1
_FACTORY_CCW_DEAD_ZONE = 1


class SimulatedServoRepository:
    """Thread-driven simulation of one ST3215-class servo.

    Attributes:
        _lock (Lock): Mutex protecting simulated servo state.
        _counts (float): Current simulated shaft position in encoder counts.
        _target (float): Commanded target position in encoder counts.
        _speed_counts_s (float): Commanded motion speed in counts per second.
        _deadband_counts (int): Dead-zone threshold in encoder counts.
        _acceleration (int): Commanded acceleration parameter.
        _overload (bool): Simulated overload protection fault state.
        _multi_turn (bool): Multi-turn positioning mode flag.
        _angle_resolution (int): Multi-turn resolution amplification factor.
        _torque_enabled (bool): Simulated drive torque engagement state.
        _running (bool): Background simulation loop execution flag.
        _position_p (int): Simulated position-loop P gain register.
        _position_d (int): Simulated position-loop D gain register.
        _position_i (int): Simulated position-loop I gain register.
        _min_start_force (int): Simulated minimum start force register.
        _cw_dead_zone (int): Simulated CW dead-zone register.
        _ccw_dead_zone (int): Simulated CCW dead-zone register.
    """

    def __init__(self) -> None:
        self._lock: Lock = Lock()
        self._counts: float = 0.0
        self._target: float = 0.0
        self._speed_counts_s: float = 0.0
        self._deadband_counts: int = 10
        self._acceleration: int = 50
        self._overload: bool = False
        self._multi_turn: bool = False
        self._angle_resolution: int = 1
        self._torque_enabled: bool = True
        self._running: bool = True
        self._position_p: int = _FACTORY_POSITION_P
        self._position_d: int = _FACTORY_POSITION_D
        self._position_i: int = _FACTORY_POSITION_I
        self._min_start_force: int = _FACTORY_MIN_START_FORCE
        self._cw_dead_zone: int = _FACTORY_CW_DEAD_ZONE
        self._ccw_dead_zone: int = _FACTORY_CCW_DEAD_ZONE
        Thread(target=self._run, daemon=True).start()

    # Test-only affordance, not part of ServoRepository - see docs/DESIGN_NOTES.md.
    def read_raw_counts(self) -> int:
        """Returns the absolute encoder position in counts.

        Returns:
            int: Current raw encoder counts.
        """
        with self._lock:
            return round(self._counts)

    def read_snapshot(self) -> TelemetrySnapshot:
        """Returns position, motion flag, and mock telemetry.

        Returns:
            TelemetrySnapshot: The instantaneous readout.
        """
        with self._lock:
            moving = (self._torque_enabled
                      and abs(self._target - self._counts)
                      > self._deadband_counts)
            counts = round(self._counts)
            overload = self._overload
        base_current = 0.9 if moving else 0.18
        current = max(0.05, base_current + random.uniform(-0.05, 0.05))
        return TelemetrySnapshot(
            raw_counts=counts,
            moving=moving,
            temperature_c=round(34.0 + (4.0 if moving else 0.0)
                                + random.uniform(-0.5, 0.5), 1),
            voltage_v=round(12.1 + random.uniform(-0.15, 0.05), 2),
            current_a=round(current, 2),
            torque_kgcm=round(current * _KT_KGCM_PER_A, 1),
            overload=overload,
            overcurrent=False,
            overheat=False,
            voltage_fault=False,
            sensor_fault=False,
            angle_fault=False,
        )

    def command_move(self, target_counts: int, speed_counts_s: int,
                     acceleration: int) -> bool:
        """Starts a move toward an absolute counts target.

        Args:
            target_counts (int): Absolute encoder counts target.
            speed_counts_s (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter (0-254).

        Returns:
            bool: Always True on simulated hardware.
        """
        with self._lock:
            self._target = float(target_counts)
            self._speed_counts_s = float(max(1, speed_counts_s))
            self._acceleration = acceleration
            self._overload = False
        return True

    def command_stop(self) -> bool:
        """Stops motion at the current position.

        Returns:
            bool: Always True on simulated hardware.
        """
        with self._lock:
            self._target = self._counts
        return True

    def configure_range(self, multi_turn: bool, angle_resolution: int) -> None:
        """Records the range configuration.

        Args:
            multi_turn (bool): Enable multi-turn absolute positioning.
            angle_resolution (int): Amplification factor 1..3.
        """
        with self._lock:
            self._multi_turn = multi_turn
            self._angle_resolution = max(1, min(3, angle_resolution))

    def set_deadband(self, counts: int) -> None:
        """Configures the simulated dead-zone width.

        Args:
            counts (int): Dead-zone width in encoder counts.
        """
        with self._lock:
            self._deadband_counts = max(1, counts)

    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores simulated drive torque.

        Args:
            enabled (bool): True to restore drive torque, false to cut it.

        Returns:
            bool: Always True on simulated hardware.
        """
        with self._lock:
            if (enabled is True) and (self._torque_enabled is False):
                self._target = self._counts
            self._torque_enabled = enabled
        return True

    def read_torque_register(self) -> int:
        """Returns the simulated torque state.

        Returns:
            int: 1 when torque is enabled, 0 when isolated.
        """
        with self._lock:
            return 1 if self._torque_enabled else 0

    def read_tuning_registers(self) -> TuningRegisters:
        """Returns the tuning registers as last written, or factory default.

        Returns:
            TuningRegisters: Simulated position-loop tuning registers.
        """
        with self._lock:
            return TuningRegisters(
                position_p=self._position_p,
                position_d=self._position_d,
                position_i=self._position_i,
                min_start_force=self._min_start_force,
                cw_dead_zone=self._cw_dead_zone,
                ccw_dead_zone=self._ccw_dead_zone)

    def write_tuning_registers(
            self, position_p=None, position_d=None, position_i=None,
            min_start_force=None, cw_dead_zone=None,
            ccw_dead_zone=None) -> bool:
        """Records any subset of the position-loop tuning registers.

        Args:
            position_p (Optional[int]): P gain, or None to leave it alone.
            position_d (Optional[int]): D gain, or None to leave it alone.
            position_i (Optional[int]): I gain, or None to leave it alone.
            min_start_force (Optional[int]): Minimum start force, or None.
            cw_dead_zone (Optional[int]): CW dead zone, or None.
            ccw_dead_zone (Optional[int]): CCW dead zone, or None.

        Returns:
            bool: Always True on simulated hardware.
        """
        with self._lock:
            if position_p is not None:
                self._position_p = position_p
            if position_d is not None:
                self._position_d = position_d
            if position_i is not None:
                self._position_i = position_i
            if min_start_force is not None:
                self._min_start_force = min_start_force
            if cw_dead_zone is not None:
                self._cw_dead_zone = cw_dead_zone
            if ccw_dead_zone is not None:
                self._ccw_dead_zone = ccw_dead_zone
        return True

    def read_present_speed_counts_s(self) -> int:
        """Returns the simulated present speed, signed toward the target.

        Returns:
            int: Signed counts per second, 0 when settled.
        """
        with self._lock:
            delta = self._target - self._counts
            if abs(delta) <= self._deadband_counts:
                return 0
            signed = copysign(self._speed_counts_s, delta)
            return round(signed)

    def simulate_overload(self) -> None:
        """Trips the simulated overload fault."""
        with self._lock:
            self._overload = True

    def _run(self) -> None:
        """Advances position toward target until process termination."""
        while self._running is True:
            with self._lock:
                if self._torque_enabled is False:
                    pass
                else:
                    delta = self._target - self._counts
                    if abs(delta) <= self._deadband_counts:
                        pass
                    else:
                        step = self._speed_counts_s * _TICK_SECONDS
                        if abs(delta) <= step:
                            self._counts = self._target
                        else:
                            self._counts += copysign(step, delta)
            sleep(_TICK_SECONDS)
