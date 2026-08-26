"""Simulated servo: sprint-1 stand-in for the real serial bus.

Models raw encoder counts as an unbounded SIGNED integer, exactly like
the STS multi-turn position after correct sign-magnitude decoding, so
the sprint-2 hardware swap changes nothing above this layer. Honors the
configured dead zone (stops driving within it) and simulates the
overload fault semantics (cleared by the next position command).
"""

import random
from math import copysign
from threading import Lock, Thread
from time import sleep

from app.models.entities import TelemetrySnapshot

_TICK_SECONDS = 0.05
_KT_KGCM_PER_A = 11.0


class SimulatedServoRepository:
    """Thread-driven simulation of one ST3215-class servo."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._counts = 0.0
        self._target = 0.0
        self._speed_counts_s = 0.0
        self._deadband_counts = 10
        self._acceleration = 50
        self._overload = False
        self._multi_turn = False
        self._angle_resolution = 1
        self._torque_enabled = True
        Thread(target=self._run, daemon=True).start()

    def read_raw_counts(self) -> int:
        """Returns the absolute encoder position in counts.

        TEST AFFORDANCE, not part of ServoRepository. The simulator
        cannot fail a read, so a bare int is safe here; production code
        must go through read_snapshot() and honour its `valid` flag.

        Returns:
            Current raw counts.
        """
        with self._lock:
            return round(self._counts)

    def read_snapshot(self) -> TelemetrySnapshot:
        """Returns position, motion flag and mock telemetry.

        Returns:
            The instantaneous readout.
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

        Clears a simulated overload fault, mirroring the hardware rule
        that a new position command releases the overload de-rate.

        Args:
            target_counts: Absolute encoder counts target.
            speed_counts_s: Speed in counts per second.
            acceleration: Accepted and recorded; the simulated motion
                profile stays linear (acceleration shaping is a hardware
                behavior, irrelevant to contract testing).

        Returns:
            None.
        """
        with self._lock:
            self._target = float(target_counts)
            self._speed_counts_s = float(max(1, speed_counts_s))
            self._acceleration = acceleration
            self._overload = False

    def command_stop(self) -> None:
        """Stops motion at the current position.

        Returns:
            None.
        """
        with self._lock:
            self._target = self._counts

    def configure_range(self, multi_turn: bool, angle_resolution: int) -> None:
        """Records the range configuration.

        The simulator already models unbounded signed counts, so nothing
        needs to change in its motion behaviour; the values are recorded so
        tests can assert the startup path passed them through.

        Args:
            multi_turn: Enable multi-turn absolute positioning.
            angle_resolution: Amplification factor 1..3.

        Returns:
            None.
        """
        with self._lock:
            self._multi_turn = multi_turn
            self._angle_resolution = max(1, min(3, angle_resolution))

    def set_deadband(self, counts: int) -> None:
        """Configures the simulated dead-zone width.

        Args:
            counts: Dead-zone width in encoder counts.

        Returns:
            None.
        """
        with self._lock:
            self._deadband_counts = max(1, counts)

    def set_torque(self, enabled: bool) -> bool:
        """Cuts or restores simulated drive torque (R2).

        Mirrors the real controller's un-isolate ordering: restoring
        torque snaps the target to the present position first, so the
        simulator does not resume driving toward a stale goal, matching
        what ServoController/BridgeServoRepository do on real hardware.

        Args:
            enabled: True to restore drive torque, false to cut it.

        Returns:
            Always True - the simulator cannot fail an acknowledgement.
        """
        with self._lock:
            if enabled and not self._torque_enabled:
                self._target = self._counts
            self._torque_enabled = enabled
        return True

    def read_torque_register(self) -> int:
        """Returns the simulated torque state (R2 board verification).

        Returns:
            1 when torque is enabled, 0 when isolated - the simulator
            cannot fail this read.
        """
        with self._lock:
            return 1 if self._torque_enabled else 0

    def simulate_overload(self) -> None:
        """Trips the simulated overload fault (testing/commissioning aid).

        Returns:
            None.
        """
        with self._lock:
            self._overload = True

    def _run(self) -> None:
        """Advances position toward the target until the process ends.

        Returns:
            None.
        """
        while True:
            with self._lock:
                if not self._torque_enabled:
                    pass  # isolated: nothing drives the shaft (R2)
                else:
                    delta = self._target - self._counts
                    if abs(delta) <= self._deadband_counts:
                        pass  # inside the dead zone: servo stops driving
                    else:
                        step = self._speed_counts_s * _TICK_SECONDS
                        if abs(delta) <= step:
                            self._counts = self._target
                        else:
                            self._counts += copysign(step, delta)
            sleep(_TICK_SECONDS)
