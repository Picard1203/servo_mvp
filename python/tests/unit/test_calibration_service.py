"""CalibrationService: captures the datum, and only the datum."""

import pytest

from tests.conftest import wait_until


@pytest.fixture()
def service(backend):
    """Fresh calibration service.

    Returns:
        The service under test.
    """
    from app.deps import get_calibration_service
    return get_calibration_service()


class TestCalibrate:
    """Datum calibration."""

    def test_calibrate_verifies_position(self, backend, service):
        from app.deps import get_state_store
        datum = service.calibrate()
        assert isinstance(datum.raw_counts, int)
        assert get_state_store().is_position_verified() is True

    def test_recalibrate_updates_the_stored_datum(self, service, sim):
        from app.deps import get_app_state_repository
        service.calibrate()
        sim.set_deadband(1)
        sim.command_move(900, 20000, 50)
        assert wait_until(lambda: abs(sim.read_raw_counts() - 900) <= 2)
        second = service.calibrate()
        assert second.raw_counts == int(
            get_app_state_repository().get("datum_raw_counts"))
        assert abs(second.raw_counts - 900) <= 2

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
        from app.deps import get_app_state_repository, get_state_store
        from app.models.entities import TelemetrySnapshot
        sim.read_snapshot = lambda: TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False,
            overcurrent=False, overheat=False, voltage_fault=False,
            sensor_fault=False, angle_fault=False, valid=False)
        with pytest.raises(InvalidReadingError):
            service.calibrate()
        assert get_app_state_repository().get("datum_raw_counts") is None
        assert get_state_store().is_position_verified() is False
