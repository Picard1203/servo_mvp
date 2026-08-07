"""Dev-PC runner: the full backend + web UI, no board required.

The app modules import cleanly without the board runtime (the relay and
the health endpoint handle a missing `arduino` package themselves), so
this runner has no stubbing to do. It only:

  * points DB_PATH / LOG_FILE at local files (the .env defaults are
    board paths like /home/arduino/... which do not exist on Windows) -
    your own environment variables or .env still win if set,
  * boots the backend the way main.py does, minus the Bridge relay
    (there is no MCU to relay for),
  * gives a tiny console to exercise the fault path.

Run from the python/ folder:

    python run_dev.py

then open  http://127.0.0.1:8000  in Chrome.

Console commands while it runs:

    overload   trip the simulated overload (watch the UI go red)
    state      print the current state snapshot
    quit       stop the server

Requires on the dev PC: fastapi, uvicorn, pydantic-settings, Logger461.
"""

import os
import pathlib
import sys
import threading
import time

# Make `app` importable no matter which directory this is launched from,
# and stop an IDE from "helpfully" rewriting the imports to python.app.*
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

# Dev-friendly paths BEFORE the app (and its Settings) are imported.
# setdefault: your .env / environment variables still take precedence.
os.environ.setdefault("DB_PATH", "servo_dev.db")
os.environ.setdefault("LOG_FILE", "servo_dev.jsonl")

def _ensure_logger461() -> None:
    """Provides Logger461 when the real wheel is not installed.

    Logger461 is our own logging wrapper and ships only as a wheel inside the
    air-gapped network. Off that network the import fails, so this installs a
    stand-in that mirrors its API: readable lines on the console AND one JSON
    object per line to LOG_FILE, so the file format matches what the real
    library writes and the same tooling can read either.

    Fallback only: if the real Logger461 imports, nothing here runs, and
    nothing is written to disk that could shadow it on the board.

    Returns:
        None.
    """
    try:
        import Logger461  # noqa: F401
        return
    except ImportError:
        pass

    import datetime
    import json
    import os
    import pathlib
    import threading
    import types

    log_path = os.environ.get("LOG_FILE", "servo_dev.jsonl")
    try:
        parent = pathlib.Path(log_path).parent
        if str(parent) not in ("", "."):
            parent.mkdir(parents=True, exist_ok=True)
    except OSError:
        log_path = "servo_dev.jsonl"          # unwritable directory

    class _DevLogger:
        """Console + JSONL stand-in for the real Logger461 logger object."""

        def __init__(self, path: str) -> None:
            self._path = path
            self._lock = threading.Lock()

        def setup(self, **kwargs) -> None:
            """Accepts the real library's configuration and honours file.

            Args:
                **kwargs: Configuration values; only `file` is used.

            Returns:
                None.
            """
            target = kwargs.get("file")
            if target:
                self._path = str(target)

        def _emit(self, level, message, metadata, extra) -> None:
            now = datetime.datetime.now()
            record = {
                "timestamp": now.isoformat(timespec="milliseconds"),
                "level": level,
                "message": message,
                "metadata": metadata or {},
                "extra": extra or {},
            }
            event = (metadata or {}).get("event", "")
            tail = ""
            if extra:
                tail = "  " + " ".join(f"{k}={v}" for k, v in extra.items())
            print(f"{now:%H:%M:%S} {level:<8} {event:<26} {message}{tail}",
                  flush=True)
            try:
                with self._lock, open(self._path, "a",
                                      encoding="utf-8") as handle:
                    handle.write(json.dumps(record) + "\n")
            except OSError:
                pass                          # never let logging kill the app

        def info(self, m, metadata=None, extra=None) -> None:
            self._emit("INFO", m, metadata, extra)

        def debug(self, m, metadata=None, extra=None) -> None:
            self._emit("DEBUG", m, metadata, extra)

        def warning(self, m, metadata=None, extra=None) -> None:
            self._emit("WARNING", m, metadata, extra)

        def error(self, m, metadata=None, extra=None) -> None:
            self._emit("ERROR", m, metadata, extra)

        def critical(self, m, metadata=None, extra=None) -> None:
            self._emit("CRITICAL", m, metadata, extra)

        def exception(self, m, metadata=None, extra=None) -> None:
            self._emit("ERROR", m, metadata, extra)

        def log(self, level, m, metadata=None, extra=None) -> None:
            self._emit(str(level).upper(), m, metadata, extra)

    module = types.ModuleType("Logger461")
    module.logger = _DevLogger(log_path)
    sys.modules["Logger461"] = module
    print(f"[logger] Logger461 not installed -> stand-in active, "
          f"writing {log_path}", flush=True)


_ensure_logger461()


import uvicorn

from app.app import create_app
from app.core.config import get_settings
from app.core.logging_setup import setup_logging
from app.deps import (get_servo_repository, get_state_store,
                      get_telemetry_service)


def main() -> None:
    """Boots the backend + web UI and runs the dev console.

    Returns:
        None.
    """
    settings = get_settings()
    setup_logging(settings)
    app = create_app()
    get_telemetry_service().start_sampler()
    # No relay.register(): there is no MCU on the dev PC. (Even if it
    # were called, register() now skips cleanly when Bridge is absent.)

    config = uvicorn.Config(app, host=settings.api_host,
                            port=settings.api_port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    while not server.started:
        time.sleep(0.05)

    host_shown = ("127.0.0.1" if settings.api_host in ("0.0.0.0", "")
                  else settings.api_host)
    print(f"\n[run_dev] Servo Control is up:"
          f"  http://{host_shown}:{settings.api_port}")
    print("[run_dev] commands: overload | state | quit\n")

    try:
        while True:
            try:
                command = input("> ").strip().lower()
            except EOFError:
                time.sleep(3600)
                continue
            if command == "overload":
                get_servo_repository().simulate_overload()
                print("[run_dev] overload tripped - watch the UI go red;"
                      " clear it with the UI's recover button")
            elif command == "state":
                print(get_state_store().snapshot())
            elif command in ("quit", "exit", "q"):
                break
            elif command:
                print("[run_dev] commands: overload | state | quit")
    except KeyboardInterrupt:
        pass

    server.should_exit = True
    thread.join(timeout=5)
    print("[run_dev] stopped")


if __name__ == "__main__":
    main()
