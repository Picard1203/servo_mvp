"""Simulated servo: sprint-1 stand-in for the real serial bus."""

import random
from math import copysign
from threading import Lock, Thread
from time import sleep

from app.models.entities import TelemetrySnapshot

_TICK_SECONDS = 0.05
_KT_KGCM_PER_A = 11.0


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
                     acceleration: int) -> None:
        """Starts a move toward an absolute counts target.

        Args:
            target_counts (int): Absolute encoder counts target.
            speed_counts_s (int): Speed in counts per second.
            acceleration (int): Servo acceleration parameter (0-254).
        """
        with self._lock:
            self._target = float(target_counts)
            self._speed_counts_s = float(max(1, speed_counts_s))
            self._acceleration = acceleration
            self._overload = False

    def command_stop(self) -> None:
        """Stops motion at the current position."""
        with self._lock:
            self._target = self._counts

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
