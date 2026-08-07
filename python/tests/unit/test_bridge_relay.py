"""BridgeRelay: connection mirroring, byte pumping, teardown paths."""

import socket
import threading

import pytest

from tests.conftest import BridgeStub, wait_until


@pytest.fixture()
def echo_server(backend, monkeypatch):
    """Local TCP server standing in for FastAPI; echoes received bytes
    back prefixed with b'ok:'.

    Yields:
        (host, port, received: list[bytes])
    """
    received = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", 0))
    server.listen(4)
    port = server.getsockname()[1]
    monkeypatch.setattr(backend.settings, "api_port", port)
    stop = threading.Event()

    def serve():
        server.settimeout(0.2)
        while not stop.is_set():
            try:
                conn, _ = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break   # server socket closed during teardown
            def handle(c):
                try:
                    while True:
                        data = c.recv(1024)
                        if not data:
                            break
                        received.append(data)
                        c.sendall(b"ok:" + data)
                except OSError:
                    pass
            threading.Thread(target=handle, args=(conn,), daemon=True).start()

    threading.Thread(target=serve, daemon=True).start()
    yield ("127.0.0.1", port, received)
    stop.set()
    server.close()


@pytest.fixture()
def relay(backend):
    """Fresh registered relay.

    Returns:
        The relay under test.
    """
    from app.deps import get_relay
    instance = get_relay()
    instance.register()
    return instance


class TestRegistration:
    """Bridge callback registration."""

    def test_registers_expected_callbacks(self, relay):
        assert set(BridgeStub.provided) == {"net_open", "net_rx", "net_close"}


class TestPumping:
    """Bytes both directions."""

    def test_open_rx_reply_roundtrip(self, relay, echo_server):
        _, _, received = echo_server
        relay._on_open(0, "192.168.10.20")
        relay._on_rx(0, b"GET /x")
        assert wait_until(lambda: received == [b"GET /x"])
        assert wait_until(lambda: any(
            name == "net_tx" and args[0] == 0 and b"ok:GET /x" in args[1]
            for name, args in BridgeStub.calls))
        assert relay.connections_total == 1

    def test_rx_for_unknown_slot_ignored(self, relay, echo_server):
        relay._on_rx(7, b"data")   # no such slot: must not raise

    def test_close_drops_socket(self, relay, echo_server):
        relay._on_open(0, "ip")
        relay._on_close(0)
        assert 0 not in relay._sockets


class TestFailurePaths:
    """Backend unreachable and server-side close."""

    def test_open_with_no_server_tells_mcu_shutdown(self, backend, relay,
                                                    monkeypatch):
        monkeypatch.setattr(backend.settings, "api_port", 9)  # nothing there
        relay._on_open(3, "ip")
        assert ("net_shutdown", (3,)) in BridgeStub.calls
        assert 3 not in relay._sockets

    def test_server_close_ends_pump_with_shutdown(self, relay, echo_server,
                                                  backend):
        relay._on_open(1, "ip")
        with relay._map_lock:
            sock = relay._sockets[1]
        sock_peer_close_via_server = sock  # server side closes on stop
        relay._on_rx(1, b"ping")
        # force server-side close by shutting our socket read end:
        sock_peer_close_via_server.shutdown(socket.SHUT_RD)
        assert wait_until(
            lambda: ("net_shutdown", (1,)) in BridgeStub.calls, timeout=3)


class TestErrorPaths:
    """Remaining failure branches."""

    def test_rx_on_dead_socket_drops_and_tells_mcu(self, relay, echo_server):
        relay._on_open(5, "ip")
        with relay._map_lock:
            sock = relay._sockets[5]
        sock.close()   # kill the local socket under the relay
        relay._on_rx(5, b"data")   # sendall -> OSError branch
        assert wait_until(
            lambda: ("net_shutdown", (5,)) in BridgeStub.calls, timeout=3)
        assert 5 not in relay._sockets

    def test_drop_swallows_close_oserror(self, relay):
        class BrokenSocket:
            def close(self):
                raise OSError("already dead")

        with relay._map_lock:
            relay._sockets[6] = BrokenSocket()
            relay._client_ips[6] = "ip"
        relay._drop(6, tell_mcu=False)   # must not raise
        assert 6 not in relay._sockets

    def test_drop_swallows_bridge_call_failure(self, relay, echo_server):
        relay._on_open(7, "ip")
        BridgeStub.raise_on_call = RuntimeError("bridge gone")
        relay._drop(7, tell_mcu=True)    # net_shutdown raises -> swallowed
        assert 7 not in relay._sockets
        BridgeStub.raise_on_call = None

    def test_pump_recv_oserror_branch(self, relay):
        class ExplodingSocket:
            """recv raises immediately, close is silent."""

            def recv(self, n):
                raise OSError("torn down")

            def close(self):
                pass

        with relay._map_lock:
            relay._sockets[8] = ExplodingSocket()
            relay._client_ips[8] = "ip"
        relay._pump_replies(8, ExplodingSocket())   # direct, synchronous
        assert ("net_shutdown", (8,)) in BridgeStub.calls
        assert 8 not in relay._sockets



class TestDevComputerPath:
    """Behavior when the board runtime is absent (dev PC)."""

    def test_register_skips_cleanly_without_bridge(self, backend,
                                                   monkeypatch):
        import sys
        # None entry makes `from arduino.app_utils import ...` raise
        # ImportError - simulating a machine without the board runtime.
        monkeypatch.setitem(sys.modules, "arduino.app_utils", None)
        from app.deps import get_relay
        relay = get_relay()
        relay.register()          # must not raise
        assert relay._bridge is None
        assert "relay.register.skipped" in backend.logger.events()
