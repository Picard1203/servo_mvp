"""Servo API routes: state, move, stop, lock, calibrate, recover."""

import time

from tests.conftest import wait_until


class TestState:
    """GET /api/v1/servo/state."""

    EXPECTED_KEYS = {"output_deg", "moving", "locked", "settling",
                     "position_verified", "active_zero", "temperature_c",
                     "voltage_v", "current_a", "torque_kgcm", "overload",
                     "overcurrent", "overheat", "voltage_fault",
                     "sensor_fault", "angle_fault"}

    def test_full_shape_and_boot_defaults(self, client):
        body = client.get("/api/v1/servo/state").json()
        assert set(body) == self.EXPECTED_KEYS
        assert body["position_verified"] is False
        assert body["active_zero"] == "factory"
        assert body["locked"] is False


class TestMove:
    """POST /api/v1/servo/move."""

    def test_accepted_202(self, client):
        response = client.post("/api/v1/servo/move",
                               json={"target_deg": 12.0, "speed_dps": 60})
        assert response.status_code == 202
        assert response.json() == {"accepted": True, "target_deg": 12.0}

    def test_locked_409(self, client):
        client.post("/api/v1/servo/lock", json={"locked": True})
        response = client.post("/api/v1/servo/move", json={"target_deg": 12.0})
        assert response.status_code == 409
        assert response.json()["reason"] == "locked"

    def test_settle_wait_blocks_then_accepts(self, backend, client):
        client.post("/api/v1/servo/lock", json={"locked": True})
        client.post("/api/v1/servo/lock", json={"locked": False})
        started = time.monotonic()
        response = client.post("/api/v1/servo/move",
                               json={"target_deg": 12.0, "speed_dps": 60})
        waited = time.monotonic() - started
        assert response.status_code == 202
        assert waited >= backend.settings.settling_seconds * 0.7

    def test_step_violation_422(self, client):
        response = client.post("/api/v1/servo/move",
                               json={"target_deg": 10.07})
        assert response.status_code == 422
        assert response.json()["reason"] == "step"

    def test_out_of_range_angle_422(self, client):
        assert client.post("/api/v1/servo/move",
                           json={"target_deg": 100.0}).status_code == 422

    def test_acceleration_bounds_422(self, client):
        assert client.post(
            "/api/v1/servo/move",
            json={"target_deg": 12.0, "acceleration": 999}).status_code == 422

    def test_movement_reaches_target(self, backend, client):
        client.post("/api/v1/servo/move",
                    json={"target_deg": 18.0, "speed_dps": 60})
        assert wait_until(lambda: abs(
            client.get("/api/v1/servo/state").json()["output_deg"] - 18.0)
            < 0.8, timeout=6)


class TestStopLock:
    """POST /stop and /lock."""

    def test_stop(self, client):
        response = client.post("/api/v1/servo/stop")
        assert response.status_code == 200
        assert response.json() == {"stopped": True}

    def test_lock_roundtrip_reflected_in_state(self, client):
        assert client.post("/api/v1/servo/lock",
                           json={"locked": True}).json() == {"locked": True}
        assert client.get("/api/v1/servo/state").json()["locked"] is True


class TestCalibrate:
    """POST /api/v1/servo/calibrate."""

    def test_calibrate_creates_verified_active_datum(self, client):
        response = client.post("/api/v1/servo/calibrate")
        assert response.status_code == 201
        body = response.json()
        assert body["is_datum"] is True
        assert body["is_active"] is True
        assert body["name"] == "datum"
        state = client.get("/api/v1/servo/state").json()
        assert state["position_verified"] is True
        assert state["active_zero"] == "datum"

    def test_recalibrate_upserts_single_datum(self, client):
        first = client.post("/api/v1/servo/calibrate").json()
        second = client.post("/api/v1/servo/calibrate").json()
        assert second["id"] == first["id"]
        zeros = client.get("/api/v1/zeros").json()
        assert sum(1 for z in zeros if z["is_datum"]) == 1


class TestRecover:
    """POST /api/v1/servo/recover."""

    def test_recover_clears_overload(self, backend, client):
        from app.deps import get_servo_repository
        get_servo_repository().simulate_overload()
        assert client.get("/api/v1/servo/state").json()["overload"] is True
        response = client.post("/api/v1/servo/recover")
        assert response.status_code == 200
        assert response.json() == {"recovered": True}
        assert client.get("/api/v1/servo/state").json()["overload"] is False


class TestMoveGuardOverHttp:
    """guard_move_to_lock surfaces as 409 reason=moving."""

    def test_lock_while_moving_409_moving(self, monkeypatch, backend,
                                          client):
        monkeypatch.setattr(backend.settings, "guard_move_to_lock", True)
        from app.deps import get_servo_repository
        get_servo_repository().set_deadband(1)
        client.post("/api/v1/servo/move",
                    json={"target_deg": 60.0, "speed_dps": 15})
        assert wait_until(lambda: client.get(
            "/api/v1/servo/state").json()["moving"], timeout=3)
        response = client.post("/api/v1/servo/lock", json={"locked": True})
        assert response.status_code == 409
        assert response.json()["reason"] == "moving"


class TestTravelWindow:
    """The +/-90 deg window the operators asked for."""

    def test_negative_angle_accepted(self, client):
        response = client.post("/api/v1/servo/move",
                               json={"target_deg": -60.0, "speed_dps": 30})
        assert response.status_code == 202

    def test_below_minimum_rejected(self, client):
        assert client.post("/api/v1/servo/move",
                           json={"target_deg": -90.06}).status_code == 422

    def test_above_maximum_rejected(self, client):
        assert client.post("/api/v1/servo/move",
                           json={"target_deg": 90.06}).status_code == 422

    def test_limits_are_inclusive(self, client):
        assert client.post("/api/v1/servo/move",
                           json={"target_deg": -90.0}).status_code == 202
        assert client.post("/api/v1/servo/move",
                           json={"target_deg": 90.0}).status_code == 202


class TestOutOfTravelSurfaced:
    """An unreachable target must be refused, not silently clamped."""

    def test_returns_422_with_reason(self, backend, client):
        # Capture the datum at the current position, which for a fresh
        # simulator sits at the bottom of the mechanism's travel.
        zero = client.post("/api/v1/zeros/capture",
                           json={"name": "bottom"}).json()
        client.post(f"/api/v1/zeros/{zero['id']}/activate")
        response = client.post("/api/v1/servo/move",
                               json={"target_deg": -90.0, "speed_dps": 30})
        assert response.status_code == 422
        assert response.json()["reason"] == "out_of_travel"
        assert "reachable range" in response.json()["detail"]


class TestInvalidReadingSurfaced:
    """Calibrating on a dead bus must refuse, not store a zero."""

    def test_returns_409_with_reason(self, backend, client):
        from app.deps import get_servo_repository
        from app.models.entities import TelemetrySnapshot
        get_servo_repository().read_snapshot = lambda: TelemetrySnapshot(
            raw_counts=0, moving=False, temperature_c=0.0, voltage_v=0.0,
            current_a=0.0, torque_kgcm=0.0, overload=False,
            overcurrent=False, overheat=False, voltage_fault=False,
            sensor_fault=False, angle_fault=False, valid=False)
        response = client.post("/api/v1/servo/calibrate")
        assert response.status_code == 409
        assert response.json()["reason"] == "invalid_reading"
