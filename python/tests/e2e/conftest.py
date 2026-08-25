"""E2E fixtures: the backend booted the way main.py boots it.

A real uvicorn server on a real localhost socket (ephemeral port), the
telemetry sampler running, and the relay registered against the Bridge
stub - the closest a dev computer gets to the board deployment.
"""

import socket
import threading
import time
import types

import pytest
import uvicorn


def _bound_socket() -> socket.socket:
    """Binds an ephemeral localhost TCP socket and leaves it open.

    Finding a free port, closing the probe socket, and binding a new one
    later leaves a window where a second process can be handed the same
    port number before this one rebinds it - harmless run serially, a
    real collision under parallel test execution (D26). Handing uvicorn
    the still-open socket removes the window instead of narrowing it.

    Returns:
        The open, bound (but not yet listening) socket.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("127.0.0.1", 0))
    return sock


@pytest.fixture()
def live_backend(backend, monkeypatch):
    """Boots the full backend on a live socket, mirroring main.py.

    Yields:
        Namespace with base_url, port, and the relay instance.
    """
    sock = _bound_socket()
    port = sock.getsockname()[1]
    monkeypatch.setattr(backend.settings, "api_port", port)

    from app.app import create_app
    from app.deps import get_relay, get_telemetry_service

    app = create_app()
    get_telemetry_service().start_sampler()
    relay = get_relay()
    relay.register()

    config = uvicorn.Config(app, host="127.0.0.1", port=port,
                            log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, kwargs={"sockets": [sock]},
                              daemon=True)
    thread.start()
    deadline = time.monotonic() + 5.0
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("uvicorn did not start in time")
        time.sleep(0.02)

    yield types.SimpleNamespace(base_url=f"http://127.0.0.1:{port}",
                                port=port, relay=relay)

    server.should_exit = True
    thread.join(timeout=5.0)
