"""Full-content request/response logging (resolved decision: log everything by
default, configurable level, to ~/Library/Logs/ai-provider-router/router.log —
prioritizes debuggability over minimizing local persistence)."""

import logging
from pathlib import Path

LOGGER_NAME = "ai_provider_router"
DEFAULT_LOG_PATH = Path.home() / "Library" / "Logs" / "ai-provider-router" / "router.log"


def configure_logging(log_path: Path = DEFAULT_LOG_PATH, level: str = "INFO") -> logging.Logger:
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(level)

    handler = logging.FileHandler(log_path)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    return logger
