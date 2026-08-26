"""Receives diagnostic events forwarded from the MCU side."""

import json
import os
import time
from threading import Lock

from Logger461 import logger

from app.core.config import Settings

_LEVEL_NAMES = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR"}


def _now_iso() -> str:
    """Returns current UTC time as an ISO-8601 string with milliseconds.

    Returns:
        str: Formatted ISO-8601 timestamp string.
    """
    millis = int(time.time() * 1000) % 1000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{millis:03d}"


class McuLog:
    """Bridge receiver that writes MCU-originated events to their own file.

    Attributes:
        _settings (Settings): Application settings providing file path.
        _write_lock (Lock): Mutex serializing log file writes.
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._write_lock = Lock()

    def register(self) -> None:
        """Registers the Bridge callback for MCU logs."""
        try:
            from arduino.app_utils import Bridge
        except ImportError:
            logger.warning(
                "Bridge unavailable - mcu_log not registered (dev computer)",
                metadata={"event": "mcu_log.register.skipped"})
            return
        Bridge.provide("mcu_log", self._on_log)

    def _on_log(self, level: int, message: str, event: str, arg1: int,
                arg2: int, uptime_s: int) -> None:
        """Handles one diagnostic record forwarded from the MCU.

        Args:
            level (int): Numeric severity level (0=DEBUG, 1=INFO, etc.).
            message (str): Human-readable log description.
            event (str): Dotted machine event identifier.
            arg1 (int): First numeric event argument.
            arg2 (int): Second numeric event argument.
            uptime_s (int): MCU uptime in seconds at event time.
        """
        self._write({
            "timestamp": _now_iso(),
            "level": _LEVEL_NAMES.get(level, "INFO"),
            "message": message,
            "event": event,
            "arg1": arg1,
            "arg2": arg2,
            "mcu_uptime_s": uptime_s,
        })

    def _write(self, line: dict) -> None:
        """Appends one JSON line, rotating the file past size threshold.

        Args:
            line (dict): Record to serialize and append.
        """
        path = self._settings.mcu_log_file
        with self._write_lock:
            directory = os.path.dirname(path)
            if len(directory) > 0:
                os.makedirs(directory, exist_ok=True)
            self._rotate_if_needed(path)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(line) + "\n")

    def _rotate_if_needed(self, path: str) -> None:
        """Renames path to path.1 once grown past threshold.

        Args:
            path (str): The log file path to evaluate.
        """
        try:
            size = os.path.getsize(path)
        except OSError:
            return
        if size < self._settings.mcu_log_max_bytes:
            return
        try:
            os.replace(path, path + ".1")
        except OSError:
            pass
