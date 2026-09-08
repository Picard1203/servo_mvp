"""Saved-positions API routes: list, create, update, delete, go."""


class TestCreateList:
    """POST and GET /api/v1/positions."""

    def test_create_201_and_listed(self, client):
        response = client.post(
            "/api/v1/positions",
            json={"name": "gate open", "description": "clears the frame",
                  "target_deg": 30.0})
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "gate open"
        assert abs(body["output_deg"] - 30.0) < 0.06
        listed = client.get("/api/v1/positions").json()
        assert [p["id"] for p in listed] == [body["id"]]

    def test_create_empty_name_422(self, client):
        assert client.post(
            "/api/v1/positions",
            json={"name": "", "target_deg": 0.0}).status_code == 422

    def test_create_out_of_range_422(self, client):
        assert client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 200.0}).status_code == 422

    def test_create_duplicate_name_409(self, client):
        client.post("/api/v1/positions",
                    json={"name": "p", "target_deg": 10.0})
        response = client.post("/api/v1/positions",
                               json={"name": "p", "target_deg": 20.0})
        assert response.status_code == 409
        assert response.json()["reason"] == "duplicate_name"


class TestUpdate:
    """PATCH /api/v1/positions/{id}."""

    def test_update_reflected_in_list(self, client):
        created = client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 10.0}).json()
        response = client.patch(
            f"/api/v1/positions/{created['id']}",
            json={"name": "renamed", "description": "note",
                  "target_deg": 20.0, "updated_at": created["updated_at"]})
        assert response.status_code == 200
        assert response.json()["name"] == "renamed"

    def test_update_missing_404(self, client):
        assert client.patch(
            "/api/v1/positions/999",
            json={"name": "x", "target_deg": 0.0,
                  "updated_at": "t"}).status_code == 404

    def test_update_stale_409(self, client):
        created = client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 10.0}).json()
        response = client.patch(
            f"/api/v1/positions/{created['id']}",
            json={"name": "p", "target_deg": 20.0,
                  "updated_at": "not-the-real-timestamp"})
        assert response.status_code == 409
        assert response.json()["reason"] == "stale_position"


class TestDelete:
    """DELETE /api/v1/positions/{id}."""

    def test_delete_ok(self, client):
        created = client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 10.0}).json()
        response = client.request(
            "DELETE", f"/api/v1/positions/{created['id']}",
            json={"updated_at": created["updated_at"]})
        assert response.status_code == 200
        assert client.get("/api/v1/positions").json() == []

    def test_delete_missing_404(self, client):
        response = client.request(
            "DELETE", "/api/v1/positions/999", json={"updated_at": "t"})
        assert response.status_code == 404

    def test_delete_stale_409(self, client):
        created = client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 10.0}).json()
        response = client.request(
            "DELETE", f"/api/v1/positions/{created['id']}",
            json={"updated_at": "not-the-real-timestamp"})
        assert response.status_code == 409
        assert response.json()["reason"] == "stale_position"


class TestGo:
    """POST /api/v1/positions/{id}/go."""

    def test_go_accepted(self, backend, client):
        from app.deps import get_servo_repository
        get_servo_repository().set_deadband(1)
        created = client.post(
            "/api/v1/positions",
            json={"name": "p", "target_deg": 12.0}).json()
        response = client.post(f"/api/v1/positions/{created['id']}/go")
        assert response.status_code == 200
        assert response.json() == {"accepted": True}

    def test_go_missing_404(self, client):
        assert client.post(
            "/api/v1/positions/999/go").status_code == 404


class TestDismiss:
    """POST /api/v1/positions/{id}/dismiss-reference and the batch route."""

    def _make_stale(self, client):
        # Seeded in the past and against a past datum literal, not a real
        # calibrate call - a dismissal always lands at real "now", so the
        # position and its datum both need to sit safely before that
        # moment for the fixture to be deterministic (see the unit-test
        # service fixture's own _make_stale for the same reasoning).
        from app.deps import (get_app_state_repository,
                              get_saved_position_repository)
        from app.models.entities import SavedPosition
        get_saved_position_repository().add(SavedPosition(
            id=None, name="p", description="", raw_counts=1000,
            created_at="2000-01-01T00:00:00",
            updated_at="2000-01-01T00:00:00"))
        get_app_state_repository().set(
            "datum_captured_at", "2010-01-01T00:00:00",
            "2010-01-01T00:00:00")
        listed = client.get("/api/v1/positions").json()[0]
        assert listed["stale_reference"] is True
        return listed

    def test_dismiss_clears_the_flag(self, backend, client):
        created = self._make_stale(client)
        response = client.post(
            f"/api/v1/positions/{created['id']}/dismiss-reference",
            json={"updated_at": created["updated_at"]})
        assert response.status_code == 200
        assert response.json()["stale_reference"] is False

    def test_dismiss_missing_404(self, client):
        response = client.post(
            "/api/v1/positions/999/dismiss-reference",
            json={"updated_at": "t"})
        assert response.status_code == 404

    def test_dismiss_stale_409(self, backend, client):
        created = self._make_stale(client)
        response = client.post(
            f"/api/v1/positions/{created['id']}/dismiss-reference",
            json={"updated_at": "not-the-real-timestamp"})
        assert response.status_code == 409
        assert response.json()["reason"] == "stale_position"

    def test_dismiss_all_clears_and_reports_the_count(self, backend, client):
        self._make_stale(client)
        response = client.post("/api/v1/positions/dismiss-references")
        assert response.status_code == 200
        assert response.json() == {"dismissed_count": 1}
        assert client.get("/api/v1/positions").json()[0][
            "stale_reference"] is False

    def test_dismiss_all_zero_when_nothing_tagged(self, client):
        client.post("/api/v1/positions",
                    json={"name": "p", "target_deg": 10.0})
        response = client.post("/api/v1/positions/dismiss-references")
        assert response.json() == {"dismissed_count": 0}
