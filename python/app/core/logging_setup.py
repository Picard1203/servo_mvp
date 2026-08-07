"""Logging configuration built on Logger461 (loguru JSON wrapper).

Logger461 emits one-line JSON entries and takes, on every call:
    logger.<level>(message, event=<dotted.event>, metadata={...},
                   extra={...})
- event: dotted identifier of what happened (e.g. servo.move.accepted)
- metadata: debugging context (ids, reasons, states)
- extra: numeric statistics / metrics (angles, counts, durations)
"""

from Logger461 import logger

from app.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """Initializes Logger461 for the process.

    Args:
        settings: Application settings providing the log file and level.

    Returns:
        None.
    """
    logger.setup(file=settings.log_file, level=settings.log_level,
                 serialize=True)
