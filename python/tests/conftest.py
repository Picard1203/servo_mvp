"""Shared test configuration: stubs, environment, and fixtures.

Runs entirely on a dev computer: the board-only modules (arduino,
Logger461) are replaced with recording stubs BEFORE any app import, and
every test gets a fresh database, fresh settings, and fresh singletons.
"""

import os
import sys
import tempfile
import traceback
import types
from typing import Optional

import pytest

# ---------------------------------------------------------------- stubs
# Installed before any app import so `from arduino.app_utils import ...`
# and `from Logger461 import logger` resolve on the dev computer.


class BridgeStub:
    """Recording stub of the Arduino Bridge."""

    provided: dict = {}
    calls: list = []
    call_result: object = "stub-mcu-ok"
    raise_on_call: Optional[Exception] = None

    @classmethod
    def reset(cls) -> None:
        """Clears recorded state between tests.

        Returns:
            None.
        """
        cls.provided = {}
        cls.calls = []
        cls.call_result = "stub-mcu-ok"
        cls.raise_on_call = None

    @classmethod
    def provide(cls, name, fn) -> None:
        """Records a provided callback.

        Args:
            name: Bridge function name.
            fn: The callback.

        Returns:
            None.
        """
        cls.provided[name] = fn

    @classmethod
    def call(cls, name, *args):
        """Records a call and returns the configured result.

        Args:
            name: Bridge function name.
            *args: Call arguments.

        Returns:
            The configured call result.
        """
        cls.calls.append((name, args))
        if cls.raise_on_call is not None:
            raise cls.raise_on_call
        return cls.call_result


class AppStub:
    """Stub of the App loop runner."""

    @staticmethod
    def run(*args, **kwargs) -> None:
        """Does nothing.

        Returns:
            None.
        """


class LoggerStub:
    """Recording stub of Logger461's logger object."""

    def __init__(self) -> None:
        self.records: list = []

    def setup(self, **kwargs) -> None:
        """Records setup configuration.

        Args:
            **kwargs: Configuration values.

        Returns:
            None.
        """
        self.records.append(("setup", kwargs))

    def _record(self, level, message, metadata, extra) -> None:
        self.records.append((level, message, metadata or {}, extra or {}))

    def info(self, message, metadata=None, extra=None) -> None:
        self._record("INFO", message, metadata, extra)

    def debug(self, message, metadata=None, extra=None) -> None:
        self._record("DEBUG", message, metadata, extra)

    def warning(self, message, metadata=None, extra=None) -> None:
        self._record("WARNING", message, metadata, extra)

    def error(self, message, metadata=None, extra=None) -> None:
        self._record("ERROR", message, metadata, extra)

    def critical(self, message, metadata=None, extra=None) -> None:
        self._record("CRITICAL", message, metadata, extra)

    def exception(self, message, metadata=None, extra=None) -> None:
        """Mirrors the real logger: the exception rides with the record.

        Must attach it, or a test asserting on the cause passes against a
        stub that drops it just as the production logger once did.

        Args:
            message: Message.
            metadata: Event metadata.
            extra: Structured fields; the exception is added to them.

        Returns:
            None.
        """
        kind, value, _ = sys.exc_info()
        enriched = dict(extra or {})
        if kind is not None:
            enriched["exception_type"] = kind.__name__
            enriched["exception"] = str(value)
            enriched["traceback"] = traceback.format_exc().rstrip()
        self._record("ERROR", message, metadata, enriched)

    def log(self, level, message, metadata=None, extra=None) -> None:
        self._record(level, message, metadata, extra)

    def events(self) -> list:
        """Returns the dotted event names recorded so far.

        Returns:
            Event names from metadata, in order.
        """
        return [entry[2].get("event") for entry in self.records
                if len(entry) == 4 and isinstance(entry[2], dict)]


_arduino = types.ModuleType("arduino")
_arduino_app_utils = types.ModuleType("arduino.app_utils")
_arduino_app_utils.App = AppStub
_arduino_app_utils.Bridge = BridgeStub
_arduino.app_utils = _arduino_app_utils
sys.modules.setdefault("arduino", _arduino)
sys.modules.setdefault("arduino.app_utils", _arduino_app_utils)

_logger_stub = LoggerStub()
_logger461 = types.ModuleType("Logger461")
_logger461.logger = _logger_stub
sys.modules.setdefault("Logger461", _logger461)

# Baseline environment BEFORE first app import (schema Field bounds are
# read once at import time from these values).
os.environ.setdefault("SETTLING_SECONDS", "0.2")
os.environ.setdefault("SAMPLER_INTERVAL_SECONDS", "0.2")
os.environ.setdefault("FINE_APPROACH_ENABLED", "false")
# Never touch real hardware from a test, even when a board .env is present.
# Environment variables win over .env, so this keeps the suite hermetic
# wherever it runs - including on the board itself.
os.environ.setdefault("USE_HARDWARE_SERVO", "false")
os.environ.setdefault("FINE_APPROACH_OVERSHOOT_DEG", "1.0")
os.environ.setdefault("FINE_APPROACH_TIMEOUT_SECONDS", "5.0")
os.environ.setdefault("LOG_FILE", os.path.join(tempfile.gettempdir(),
                                               "test_app.jsonl"))

# ------------------------------------------------------------- fixtures


def _clear_all_caches() -> None:
    """Clears every cached provider so each test builds fresh singletons.

    Returns:
        None.
    """
    from app import deps
    from app.core.config import get_settings
    # Sampler first, then the database it reads through - stopping the
    # thread before closing the connection it may still be mid-read on
    # is what makes closing the connection safe at all (see
    # TelemetryService.stop_sampler and Database.close).
    if deps.get_telemetry_service.cache_info().currsize > 0:
        deps.get_telemetry_service().stop_sampler()
    if deps.get_database.cache_info().currsize > 0:
        deps.get_database().close()
    get_settings.cache_clear()
    for name in dir(deps):
        provider = getattr(deps, name)
        if callable(provider) and hasattr(provider, "cache_clear"):
            provider.cache_clear()


@pytest.fixture()
def backend(monkeypatch, tmp_path):
    """Fresh backend context: new DB, cleared caches, recording stubs.

    Yields:
        A namespace with settings and the stub handles.
    """
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("LOG_FILE", str(tmp_path / "test.jsonl"))
    BridgeStub.reset()
    _logger_stub.records.clear()
    _clear_all_caches()

    from app.core.config import get_settings
    yield types.SimpleNamespace(settings=get_settings(),
                                bridge=BridgeStub, logger=_logger_stub)
    _clear_all_caches()


@pytest.fixture()
def client(backend):
    """FastAPI TestClient over a fresh app (sampler NOT started).

    Yields:
        The test client.
    """
    from fastapi.testclient import TestClient
    from app.app import create_app
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture()
def sim(backend):
    """The fresh simulated servo repository singleton.

    Returns:
        The simulator instance.
    """
    from app.deps import get_servo_repository
    return get_servo_repository()


def wait_until(predicate, timeout=3.0, interval=0.02) -> bool:
    """Polls a predicate until true or timeout.

    Args:
        predicate: Zero-argument callable returning bool.
        timeout: Maximum seconds to wait.
        interval: Poll period in seconds.

    Returns:
        True when the predicate became true within the timeout.
    """
    import time
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(interval)
    return False
