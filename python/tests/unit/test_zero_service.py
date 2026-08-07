"""ZeroService: capture, activate, delete rules, calibrate."""

import pytest

from app.core.exceptions import ActiveZeroError, DatumZeroError, NotFoundError
from tests.conftest import wait_until


@pytest.fixture()
def service(backend):
    """Fresh zero service.

    Returns:
        The service under test.
    """
    from app.deps import get_zero_service
    return get_zero_service()


class TestCapture:
    """Ordinary zero capture."""

    def test_capture_stores_current_counts(self, service, sim):
        sim.set_deadband(1)
        sim.command_move(400, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 400) <= 2)
        zero = service.capture("here")
        assert abs(zero.raw_counts - 400) <= 2
        assert zero.is_datum is False
        assert zero.is_active is False


class TestActivateDelete:
    """Activation and deletion rules."""

    def test_activate_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.activate(999)

    def test_delete_missing_raises(self, service):
        with pytest.raises(NotFoundError):
            service.delete(999)

    def test_delete_active_refused(self, service):
        zero = service.capture("a")
        service.activate(zero.id)
        with pytest.raises(ActiveZeroError):
            service.delete(zero.id)

    def test_delete_inactive_succeeds(self, service):
        zero = service.capture("a")
        service.delete(zero.id)
        assert all(z.id != zero.id for z in service.list_all())


class TestCalibrate:
    """Datum calibration."""

    def test_calibrate_creates_active_verified_datum(self, backend, service):
        from app.deps import get_state_store
        datum = service.calibrate()
        assert datum.is_datum is True
        assert datum.is_active is True
        assert datum.name == "datum"
        assert get_state_store().is_position_verified() is True

    def test_datum_delete_refused(self, service):
        datum = service.calibrate()
        with pytest.raises(DatumZeroError):
            service.delete(datum.id)

    def test_recalibrate_updates_same_datum(self, service, sim):
        first = service.calibrate()
        sim.set_deadband(1)
        sim.command_move(900, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 900) <= 2)
        second = service.calibrate()
        assert second.id == first.id
        assert abs(second.raw_counts - 900) <= 2
        assert sum(1 for z in service.list_all() if z.is_datum) == 1

    def test_calibrate_rebaselines_display(self, backend, service, sim):
        from app.deps import get_state_store
        store = get_state_store()
        sim.set_deadband(1)
        sim.command_move(600, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 600) <= 2)
        service.calibrate()
        assert abs(store.current_output_deg()) < 0.1


class TestCalibrationRobustness:
    """Calibration must not capture a reading the servo never gave.

    A failed read reports zero. A datum of zero puts the entire negative
    half of the travel out of reach, because the servo clamps at count 0
    and stops early while still reporting the move as accepted. That is
    exactly how a live system ended up unable to go below zero.
    """

    def test_refuses_an_invalid_reading(self, backend, service, sim):
        from app.core.exceptions import InvalidReadingError
        from app.models.entities import TelemetrySnapshot

        def dead_bus():
            return TelemetrySnapshot(
                raw_counts=0, moving=False, temperature_c=0.0,
                voltage_v=0.0, current_a=0.0, torque_kgcm=0.0,
                overload=False, overcurrent=False, overheat=False,
                voltage_fault=False, sensor_fault=False, angle_fault=False,
                valid=False)

        sim.read_snapshot = dead_bus
        with pytest.raises(InvalidReadingError):
            service.calibrate()

    def test_nothing_is_stored_when_the_read_failed(self, backend, service,
                                                    sim):
        from app.core.exceptions import InvalidReadingError
        from app.models.entities import TelemetrySnapshot
        sim.read_snapshot = lambda: TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False,
            overcurrent=False, overheat=False, voltage_fault=False,
            sensor_fault=False, angle_fault=False, valid=False)
        with pytest.raises(InvalidReadingError):
            service.calibrate()
        assert not [z for z in service.list_all() if z.is_datum]
