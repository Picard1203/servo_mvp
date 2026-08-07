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


def _free_port() -> int:
    """Finds a free localhost TCP port.

    Returns:
        An ephemeral port number currently free.
    """
    probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    probe.bind(("127.0.0.1", 0))
    port = probe.getsockname()[1]
    probe.close()
    return port


@pytest.fixture()
def live_backend(backend, monkeypatch):
    """Boots the full backend on a live socket, mirroring main.py.

    Yields:
        Namespace with base_url, port, and the relay instance.
    """
    port = _free_port()
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
    thread = threading.Thread(target=server.run, daemon=True)
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
