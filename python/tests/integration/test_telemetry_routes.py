"""Telemetry API route: CSV export."""

import time


class TestExport:
    """GET /api/v1/telemetry/export."""

    HEADER = ("timestamp,raw_counts,output_deg,moving,locked,temperature_c,"
              "voltage_v,current_a,torque_kgcm,overload,overcurrent,"
              "overheat,voltage_fault,sensor_fault,angle_fault")

    def test_csv_headers_and_disposition(self, backend, client):
        from app.deps import get_telemetry_service
        get_telemetry_service()._sample_once()
        response = client.get(
            "/api/v1/telemetry/export",
            params={"from": 0, "to": time.time() + 1})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        assert "telemetry.csv" in response.headers["content-disposition"]
        lines = response.text.strip().splitlines()
        assert lines[0] == self.HEADER
        assert len(lines) == 2

    def test_missing_params_422(self, client):
        assert client.get("/api/v1/telemetry/export").status_code == 422

    def test_empty_range_header_only(self, client):
        response = client.get("/api/v1/telemetry/export",
                              params={"from": 1, "to": 2})
        assert response.text.strip() == self.HEADER
