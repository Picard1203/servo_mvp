"""Logging configuration built on Logger461 (loguru JSON wrapper)."""

from Logger461 import logger

from app.core.config import Settings


def setup_logging(settings: Settings) -> None:
    """Initializes Logger461 for the process.

    Args:
        settings (Settings): Application settings providing log file and level.
    """
    logger.setup(file=settings.log_file, level=settings.log_level,
                 serialize=True)
