"""Telemetry API route: compact binary export.

XLSX assembly happens client-side (app.js), not on this route - see
BACKLOG.md R5/D31. This route's contract is the compact binary stream
only, which app.js parses and turns into the workbook in the browser.
"""

import time


class TestExport:
    """GET /api/v1/telemetry/binary."""

    def test_binary_headers_and_content(self, backend, client):
        from app.deps import get_telemetry_service
        from app.services.telemetry_service import HEADER_STRUCT
        get_telemetry_service()._sample_once()
        response = client.get(
            "/api/v1/telemetry/binary",
            params={"from": 0, "to": time.time() + 1})
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/octet-stream"
        _, count, _ = HEADER_STRUCT.unpack(response.content[:HEADER_STRUCT.size])
        assert count == 1

    def test_missing_params_422(self, client):
        assert client.get("/api/v1/telemetry/binary").status_code == 422

    def test_empty_range_valid_header_only(self, client):
        from app.services.telemetry_service import HEADER_STRUCT
        response = client.get("/api/v1/telemetry/binary",
                              params={"from": 1, "to": 2})
        assert response.status_code == 200
        _, count, _ = HEADER_STRUCT.unpack(response.content[:HEADER_STRUCT.size])
        assert count == 0
