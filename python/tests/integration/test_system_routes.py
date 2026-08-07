"""System API routes: health and events."""

from tests.conftest import BridgeStub


class TestHealth:
    """GET /api/v1/system/health."""

    def test_health_shape_and_mcu_status(self, backend, client):
        body = client.get("/api/v1/system/health").json()
        assert set(body) == {"service", "version", "uptime_seconds",
                             "mcu_status", "servo_backend",
                             "relay_connections_total"}
        assert body["mcu_status"] == "stub-mcu-ok"
        assert body["service"] == backend.settings.app_name
        # Defaults to the simulator; a silent simulator is exactly the
        # failure this field exists to make visible.
        assert body["servo_backend"] == "simulated"

    def test_health_mcu_unreachable_path(self, backend, client):
        BridgeStub.raise_on_call = RuntimeError("bridge down")
        body = client.get("/api/v1/system/health").json()
        assert body["mcu_status"].startswith("unreachable")


class TestEvents:
    """GET /api/v1/system/events."""

    def test_events_recorded_and_limited(self, backend, client):
        client.post("/api/v1/servo/lock", json={"locked": True})
        client.post("/api/v1/servo/lock", json={"locked": False})
        client.post("/api/v1/servo/calibrate")
        body = client.get("/api/v1/system/events",
                          params={"limit": 2}).json()
        assert len(body["events"]) == 2
        names = {e["event"] for e in
                 client.get("/api/v1/system/events").json()["events"]}
        assert {"servo.lock.engaged", "servo.lock.released",
                "servo.calibrated"} <= names

    def test_limit_bounds_422(self, client):
        assert client.get("/api/v1/system/events",
                          params={"limit": 0}).status_code == 422
        assert client.get("/api/v1/system/events",
                          params={"limit": 500}).status_code == 422



class TestHealthDevComputer:
    """Health reporting when the board runtime is absent."""

    def test_health_names_missing_mcu(self, monkeypatch, client):
        import sys
        monkeypatch.setitem(sys.modules, "arduino.app_utils", None)
        body = client.get("/api/v1/system/health").json()
        assert body["mcu_status"] == "no MCU (dev computer)"


class TestServoBackendReported:
    """The health endpoint names the servo backend in use."""

    def test_simulated_by_default(self, client):
        assert client.get(
            "/api/v1/system/health").json()["servo_backend"] == "simulated"

    def test_hardware_when_enabled(self, monkeypatch, backend, client):
        monkeypatch.setattr(backend.settings, "use_hardware_servo", True)
        assert client.get(
            "/api/v1/system/health").json()["servo_backend"] == "hardware"
