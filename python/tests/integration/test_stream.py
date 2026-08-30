"""SSE stream API integration tests."""

import asyncio
import json
from typing import Any, Optional

import httpx
import pytest
from fastapi.testclient import TestClient


def _read_sse_lines(response: httpx.Response, count: int) -> list[str]:
    """Reads exactly count lines from the response iterator.

    Args:
        response: The streaming response.
        count: Number of lines to read.

    Returns:
        The read lines as a list of strings.
    """
    lines = []
    iterator = response.iter_lines()
    for _ in range(count):
        try:
            lines.append(next(iterator))
        except StopIteration:
            break
    return lines


def _parse_sse_events(lines: list[str]) -> list[dict]:
    """Parses SSE lines into a list of event dictionaries.

    Args:
        lines: Raw SSE lines.

    Returns:
        List of parsed events with 'event' and 'data' keys.
    """
    events = []
    current_event: Optional[str] = None
    current_data: Optional[str] = None
    for line in lines:
        if line.startswith("event: "):
            current_event = line[7:]
        elif line.startswith("data: "):
            current_data = line[6:]
        elif line == "":
            if (current_event is not None) and (current_data is not None):
                events.append({"event": current_event, "data": current_data})
                current_event = None
                current_data = None
    return events


class StopStream(Exception):
    """Custom exception to terminate stream generator during tests."""
    pass


class TestStream:
    """GET /api/v1/stream."""

    def test_content_type(self, client: TestClient,
                            monkeypatch: pytest.MonkeyPatch) -> None:
        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            raise StopStream()
        
        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
            assert response.headers["cache-control"] == "no-cache"
            assert response.headers["x-accel-buffering"] == "no"
            _read_sse_lines(response, 1)

    def test_emits_state_event(self, client: TestClient,
                               monkeypatch: pytest.MonkeyPatch) -> None:
        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            raise StopStream()
        
        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            lines = _read_sse_lines(response, 9)
            events = _parse_sse_events(lines)

            state_events = []
            for e in events:
                if e["event"] == "state":
                    state_events.append(e)

            assert len(state_events) > 0

            state_data = json.loads(state_events[0]["data"])
            expected_keys = {
                "output_deg", "reading_valid", "moving", "locked",
                "settling", "position_verified",
                "temperature_c", "voltage_v", "current_a", "torque_kgcm",
                "overload", "overcurrent", "overheat", "voltage_fault",
                "sensor_fault", "angle_fault", "servo_deg", "target_deg",
                "target_stale", "output_min_deg", "output_max_deg",
                "isolated", "isolation_idle_timeout_s"
            }
            assert set(state_data) == expected_keys

    def test_emits_positions_event(self, client: TestClient,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            raise StopStream()

        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            lines = _read_sse_lines(response, 9)
            events = _parse_sse_events(lines)

            positions_events = []
            for e in events:
                if e["event"] == "positions":
                    positions_events.append(e)

            assert len(positions_events) > 0

            positions_data = json.loads(positions_events[0]["data"])
            assert isinstance(positions_data, list)

    def test_positions_pushed_immediately_on_change(
            self, client: TestClient,
            monkeypatch: pytest.MonkeyPatch) -> None:
        from app.deps import get_saved_position_service
        calls = {"n": 0}

        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            calls["n"] += 1
            if calls["n"] == 1:
                get_saved_position_service().create("p", "", 10.0)
            if calls["n"] >= 3:
                raise StopStream()

        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            lines = _read_sse_lines(response, 20)
            events = _parse_sse_events(lines)
            payloads = [json.loads(e["data"]) for e in events
                       if e["event"] == "positions"]
            # the created position reaches the stream well before the
            # ~15s periodic floor, on the very next tick after it exists.
            assert any(len(p) == 1 for p in payloads)

    def test_emits_events_event(self, client: TestClient,
                                monkeypatch: pytest.MonkeyPatch) -> None:
        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            raise StopStream()
        
        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            lines = _read_sse_lines(response, 9)
            events = _parse_sse_events(lines)

            events_events = []
            for e in events:
                if e["event"] == "events":
                    events_events.append(e)

            assert len(events_events) > 0

            events_data = json.loads(events_events[0]["data"])
            assert "events" in events_data
            assert isinstance(events_data["events"], list)
