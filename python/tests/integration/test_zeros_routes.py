"""Zeros API routes: list, capture, activate, delete + error mapping."""


class TestCaptureList:
    """POST /capture and GET list."""

    def test_capture_201_and_listed(self, client):
        response = client.post("/api/v1/zeros/capture", json={"name": "home"})
        assert response.status_code == 201
        body = response.json()
        assert body["name"] == "home"
        assert body["is_datum"] is False
        zeros = client.get("/api/v1/zeros").json()
        assert [z["id"] for z in zeros] == [body["id"]]

    def test_capture_empty_name_422(self, client):
        assert client.post("/api/v1/zeros/capture",
                           json={"name": ""}).status_code == 422


class TestActivate:
    """POST /{id}/activate."""

    def test_activate_reflected_in_state(self, client):
        zero_id = client.post("/api/v1/zeros/capture",
                              json={"name": "base"}).json()["id"]
        assert client.post(
            f"/api/v1/zeros/{zero_id}/activate").status_code == 200
        assert client.get(
            "/api/v1/servo/state").json()["active_zero"] == "base"

    def test_activate_missing_404(self, client):
        assert client.post("/api/v1/zeros/999/activate").status_code == 404


class TestDelete:
    """DELETE /{id} and its protections."""

    def test_delete_ok(self, client):
        zero_id = client.post("/api/v1/zeros/capture",
                              json={"name": "tmp"}).json()["id"]
        assert client.delete(f"/api/v1/zeros/{zero_id}").status_code == 200
        assert client.get("/api/v1/zeros").json() == []

    def test_delete_missing_404(self, client):
        assert client.delete("/api/v1/zeros/999").status_code == 404

    def test_delete_active_409(self, client):
        zero_id = client.post("/api/v1/zeros/capture",
                              json={"name": "act"}).json()["id"]
        client.post(f"/api/v1/zeros/{zero_id}/activate")
        response = client.delete(f"/api/v1/zeros/{zero_id}")
        assert response.status_code == 409
        assert response.json()["reason"] == "active_zero"

    def test_delete_datum_409(self, client):
        datum_id = client.post("/api/v1/servo/calibrate").json()["id"]
        response = client.delete(f"/api/v1/zeros/{datum_id}")
        assert response.status_code == 409
        assert response.json()["reason"] == "datum_zero"
