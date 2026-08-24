"""E2E: a full operator session against the live server over real HTTP."""

import time

import httpx

from tests.conftest import wait_until


class TestOperatorSession:
    """Boot -> calibrate -> move -> lock -> zeros -> telemetry -> fault."""

    def test_full_session(self, backend, live_backend):
        with httpx.Client(base_url=live_backend.base_url,
                          timeout=5.0) as http:
            # 1. boot: unverified, factory baseline
            state = http.get("/api/v1/servo/state").json()
            assert state["position_verified"] is False
            assert state["active_zero"] == "factory"

            # 2. install calibration at the physical reference
            datum = http.post("/api/v1/servo/calibrate").json()
            assert datum["is_datum"] and datum["is_active"]
            assert http.get(
                "/api/v1/servo/state").json()["position_verified"] is True

            # 3. commanded move is observable while in flight, then lands
            response = http.post("/api/v1/servo/move",
                                 json={"target_deg": 24.0, "speed_dps": 60})
            assert response.status_code == 202
            assert wait_until(lambda: http.get(
                "/api/v1/servo/state").json()["moving"], timeout=2)
            assert wait_until(lambda: (
                lambda s: not s["moving"]
                and abs(s["output_deg"] - 24.0) < 0.8)(
                    http.get("/api/v1/servo/state").json()), timeout=8)

            # 4. lock gates movement; unlock triggers settle-wait
            http.post("/api/v1/servo/lock", json={"locked": True})
            refused = http.post("/api/v1/servo/move",
                                json={"target_deg": 30.0})
            assert refused.status_code == 409
            assert refused.json()["reason"] == "locked"
            http.post("/api/v1/servo/lock", json={"locked": False})
            started = time.monotonic()
            accepted = http.post("/api/v1/servo/move",
                                 json={"target_deg": 30.0,
                                       "speed_dps": 60})
            assert accepted.status_code == 202
            assert time.monotonic() - started >= \
                backend.settings.settling_seconds * 0.7

            # 5. operational zero on top of the datum
            assert wait_until(lambda: not http.get(
                "/api/v1/servo/state").json()["moving"], timeout=8)
            zero = http.post("/api/v1/zeros/capture",
                             json={"name": "work-point"}).json()
            http.post(f"/api/v1/zeros/{zero['id']}/activate")
            assert abs(http.get(
                "/api/v1/servo/state").json()["output_deg"]) < 0.8
            assert http.delete(
                f"/api/v1/zeros/{zero['id']}").status_code == 409

            # 6. overload -> visible -> recovered
            from app.deps import get_servo_repository
            get_servo_repository().simulate_overload()
            assert http.get("/api/v1/servo/state").json()["overload"]
            assert http.post("/api/v1/servo/recover").json()["recovered"]
            assert not http.get("/api/v1/servo/state").json()["overload"]

            # 7. sampler produced history; export honors the contract
            # (XLSX assembly is client-side, app.js - this checks the
            # binary stream the server actually serves, see BACKLOG.md R5)
            from app.services.telemetry_service import HEADER_STRUCT
            time.sleep(0.5)
            export = http.get("/api/v1/telemetry/binary",
                              params={"from": 0, "to": time.time() + 1})
            assert export.status_code == 200
            assert export.headers["content-type"] == "application/octet-stream"
            _, count, _ = HEADER_STRUCT.unpack(export.content[:HEADER_STRUCT.size])
            assert count >= 1

            # 8. the session's story is in the events feed
            names = {event["event"] for event in http.get(
                "/api/v1/system/events").json()["events"]}
            assert {"servo.calibrated", "servo.move.accepted",
                    "servo.lock.engaged", "servo.lock.released",
                    "zero.captured", "zero.activated",
                    "servo.fault.recovered"} <= names

            # 9. health reports the (stub) MCU and service identity
            health = http.get("/api/v1/system/health").json()
            assert health["service"] == backend.settings.app_name
            assert health["mcu_status"] == "stub-mcu-ok"
