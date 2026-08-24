"""Entry point: initialize, serve FastAPI, run the App loop.

App Lab runs this file on the board. Initialization is explicit here:
logging, then the FastAPI server in a background thread, then background
work (telemetry sampler, Bridge relay), then App.run() holds the main
thread for the Bridge.
"""

import sys
from threading import Thread

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
    import traceback
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
            # The traceback is multi-line, so it goes under the record
            # rather than into the single-line tail. It stays whole in
            # the JSON either way.
            trace = (extra or {}).get("traceback")
            tail = ""
            if extra:
                tail = "  " + " ".join(f"{k}={v}" for k, v in extra.items()
                                       if k != "traceback")
            print(f"{now:%H:%M:%S} {level:<8} {event:<26} {message}{tail}",
                  flush=True)
            if trace:
                print(trace, flush=True)
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
            """Records an ERROR with the exception being handled.

            Attaching the exception is the whole difference between this
            and error(). Without it the record says something failed and
            nothing about what, which is worse than silence: it looks
            like diagnosis. A live sampler failure was lost this way.

            Args:
                m: Message.
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
            self._emit("ERROR", m, metadata, enriched)

        def log(self, level, m, metadata=None, extra=None) -> None:
            self._emit(str(level).upper(), m, metadata, extra)

    module = types.ModuleType("Logger461")
    module.logger = _DevLogger(log_path)
    sys.modules["Logger461"] = module
    print(f"[logger] Logger461 not installed -> stand-in active, "
          f"writing {log_path}", flush=True)


_ensure_logger461()


import uvicorn
from Logger461 import logger

from app.app import create_app
from app.core.config import get_settings
from app.core.logging_setup import setup_logging
from app.deps import get_mcu_log, get_relay, get_telemetry_service


def _serve(app) -> None:
    """Runs uvicorn on localhost; relay and adb-forward are the doors.

    Args:
        app: The FastAPI application.

    Returns:
        None.
    """
    settings = get_settings()
    # Short keep-alive: an idle connection holds one of the relay's limited
    # W5500 slots, so they are recycled rather than parked.
    uvicorn.run(app, host=settings.api_host, port=settings.api_port,
                timeout_keep_alive=5, log_level="warning")


def _start_background() -> None:
    """Starts the telemetry sampler and registers the Bridge relay.

    Returns:
        None.
    """
    get_telemetry_service().start_sampler()
    try:
        get_relay().register()
    except Exception as exc:  # off-board: no arduino module
        logger.warning("relay not registered (off-board?)",
                       metadata={"event": "app.relay.skipped",
                                 "error": str(exc)})
    try:
        get_mcu_log().register()
    except Exception as exc:  # off-board: no arduino module
        logger.warning("mcu_log not registered (off-board?)",
                       metadata={"event": "app.mcu_log.skipped",
                                 "error": str(exc)})


def main() -> None:
    """Boots the backend and hands the main thread to the App loop.

    Returns:
        None.
    """
    settings = get_settings()
    setup_logging(settings)
    # Name the config file that was actually read. A .env in the wrong
    # place is indistinguishable from no .env at all, and every setting
    # silently falls back to its default when that happens.
    from app.core.config import _ENV_FILE
    logger.info("configuration source",
                metadata={"event": "config.source"},
                extra={"env_file": str(_ENV_FILE),
                       "found": _ENV_FILE.is_file()})

    # State the servo backend explicitly. Defaulting to the simulator is
    # right for a laptop, but it is silent, and a silent simulator looks
    # exactly like working hardware on screen while the servo never moves.
    if settings.use_hardware_servo:
        logger.info("driving the REAL servo through the MCU bridge",
                    metadata={"event": "servo.backend"},
                    extra={"backend": "hardware"})
    else:
        logger.warning("SIMULATED servo - the real servo will NOT move. "
                       "Set USE_HARDWARE_SERVO=true in .env "
                       "(cp .env.board .env) to drive hardware.",
                       metadata={"event": "servo.backend"},
                       extra={"backend": "simulated"})

    logger.info("backend starting",
                metadata={"event": "app.boot", "version": settings.version},
                extra={"api_port": settings.api_port})

    app = create_app()
    Thread(target=_serve, args=(app,), daemon=True).start()
    _start_background()

    from arduino.app_utils import App
    App.run()


if __name__ == "__main__":
    main()
