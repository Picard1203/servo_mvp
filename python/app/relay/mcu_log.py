"""Receives diagnostic events forwarded from the MCU side (backlog D3).

`Bridge.notify("mcu_log", level, message, event, arg1, arg2, uptime_s)`
lands here. Written to its own file, not through Logger461: the two sources
are sized and rotated independently on purpose, so a volume spike on either
side cannot evict the other's history (see Settings.mcu_log_file).
"""

import json
import os
import time
from threading import Lock

from Logger461 import logger

from app.core.config import Settings

_LEVEL_NAMES = {0: "DEBUG", 1: "INFO", 2: "WARNING", 3: "ERROR"}


def _now_iso() -> str:
    """Returns the current UTC time as an ISO-8601 string, millisecond precision.

    Returns:
        Timestamp string, e.g. "2026-08-08T12:00:00.000".
    """
    millis = int(time.time() * 1000) % 1000
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + f".{millis:03d}"


class McuLog:
    """Bridge receiver that writes MCU-originated events to their own file."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._write_lock = Lock()

    def register(self) -> None:
        """Registers the Bridge callback. Call once at startup.

        On a machine without the board runtime (dev computer) the Bridge is
        unavailable; registration is skipped with a warning instead of
        crashing - matches BridgeRelay.register().

        Returns:
            None.
        """
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
            level: 0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR.
            message: Human-readable text.
            event: Dotted machine identifier, e.g. "mcu.relay.rejected".
            arg1: First numeric argument; meaning is event-specific.
            arg2: Second numeric argument; meaning is event-specific.
            uptime_s: MCU uptime in whole seconds at the time of the event.

        Returns:
            None.
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
        """Appends one JSON line, rotating the file past the size threshold.

        Args:
            line: The record to serialize and append.

        Returns:
            None.
        """
        path = self._settings.mcu_log_file
        with self._write_lock:
            directory = os.path.dirname(path)
            if directory:
                os.makedirs(directory, exist_ok=True)
            self._rotate_if_needed(path)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(line) + "\n")

    def _rotate_if_needed(self, path: str) -> None:
        """Renames path to path + ".1" once it has grown past the threshold.

        A single backup - matching what T9's budget was measured against,
        see BACKLOG.md D3. Any existing ".1" is overwritten.

        Args:
            path: The log file path.

        Returns:
            None.
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
