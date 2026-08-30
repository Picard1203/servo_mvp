"""E2E through the relay: raw HTTP bytes over the Bridge callbacks.

The closest dev-computer reproduction of the deployed path:
network client -> (sketch, stubbed) -> BridgeRelay -> live uvicorn ->
FastAPI -> services -> simulator, and the reply chunked back through
Bridge net_tx exactly as the sketch would receive it.
"""

import json

from tests.conftest import BridgeStub, wait_until


def _http_request(path: str, method: str = "GET", body: str = "") -> bytes:
    """Builds a raw HTTP/1.1 request as the shield's client would send.

    Args:
        path: Request path.
        method: HTTP method.
        body: Optional JSON body.

    Returns:
        The raw request bytes.
    """
    payload = body.encode()
    head = (f"{method} {path} HTTP/1.1\r\n"
            f"Host: board\r\n"
            f"Connection: close\r\n")
    if payload:
        head += ("Content-Type: application/json\r\n"
                 f"Content-Length: {len(payload)}\r\n")
    return head.encode() + b"\r\n" + payload


def _reply_bytes(slot: int) -> bytes:
    """Joins all net_tx chunks captured for a slot.

    Args:
        slot: Connection slot.

    Returns:
        The concatenated reply bytes.
    """
    return b"".join(args[1] for name, args in BridgeStub.calls
                    if name == "net_tx" and args[0] == slot)


def _parse(reply: bytes) -> tuple:
    """Splits a raw HTTP reply into (status_code, json_body).

    Args:
        reply: Raw HTTP response bytes.

    Returns:
        Tuple of status code and decoded JSON body.
    """
    head, _, body = reply.partition(b"\r\n\r\n")
    status = int(head.split(b" ")[1])
    return status, json.loads(body)


class TestRelayEndToEnd:
    """Requests through net_open/net_rx; replies through net_tx."""

    def test_state_request_roundtrip_chunked(self, backend, live_backend):
        relay = live_backend.relay
        relay._on_open(0, "192.168.10.20")
        request = _http_request("/api/v1/servo/state")
        chunk = backend.settings.relay_chunk_bytes
        for offset in range(0, len(request), chunk):
            relay._on_rx(0, request[offset:offset + chunk])

        assert wait_until(
            lambda: ("net_shutdown", (0,)) in BridgeStub.calls, timeout=5)
        status, body = _parse(_reply_bytes(0))
        assert status == 200
        assert body["position_verified"] is False
        # replies were chunked to the Bridge frame budget
        assert all(len(args[1]) <= chunk for name, args in BridgeStub.calls
                   if name == "net_tx")

    def test_command_through_relay_moves_the_servo(self, backend,
                                                   live_backend):
        relay = live_backend.relay
        relay._on_open(1, "192.168.10.21")
        request = _http_request("/api/v1/servo/move", method="POST",
                                body=json.dumps({"target_deg": 15.0}))
        relay._on_rx(1, request)
        assert wait_until(
            lambda: ("net_shutdown", (1,)) in BridgeStub.calls, timeout=5)
        status, body = _parse(_reply_bytes(1))
        assert status == 202
        assert body == {"accepted": True, "target_deg": 15.0}

        from app.deps import get_state_store
        assert wait_until(lambda: abs(
            get_state_store().current_output_deg() - 15.0) < 0.8, timeout=8)

    def test_two_clients_on_separate_slots(self, backend, live_backend):
        relay = live_backend.relay
        relay._on_open(2, "ip-a")
        relay._on_open(3, "ip-b")
        relay._on_rx(2, _http_request("/api/v1/system/health"))
        relay._on_rx(3, _http_request("/api/v1/positions"))
        assert wait_until(
            lambda: ("net_shutdown", (2,)) in BridgeStub.calls
            and ("net_shutdown", (3,)) in BridgeStub.calls, timeout=5)
        health_status, health = _parse(_reply_bytes(2))
        positions_status, positions = _parse(_reply_bytes(3))
        assert health_status == 200 and "mcu_status" in health
        assert positions_status == 200 and positions == []
        assert live_backend.relay.connections_total >= 2
