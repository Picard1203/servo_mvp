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
                "settling", "position_verified", "active_zero",
                "temperature_c", "voltage_v", "current_a", "torque_kgcm",
                "overload", "overcurrent", "overheat", "voltage_fault",
                "sensor_fault", "angle_fault", "servo_deg", "target_deg",
                "target_stale", "output_min_deg", "output_max_deg"
            }
            assert set(state_data) == expected_keys

    def test_emits_zeros_event(self, client: TestClient,
                               monkeypatch: pytest.MonkeyPatch) -> None:
        async def mock_sleep(*args: Any, **kwargs: Any) -> None:
            raise StopStream()
        
        monkeypatch.setattr("app.routers.stream.asyncio.sleep", mock_sleep)

        with client.stream("GET", "/api/v1/stream") as response:
            lines = _read_sse_lines(response, 9)
            events = _parse_sse_events(lines)

            zeros_events = []
            for e in events:
                if e["event"] == "zeros":
                    zeros_events.append(e)

            assert len(zeros_events) > 0

            zeros_data = json.loads(zeros_events[0]["data"])
            assert isinstance(zeros_data, list)

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
