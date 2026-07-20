import logging

from router.adapters.http.logging_config import LOGGER_NAME, configure_logging


def test_configure_logging_creates_log_file_and_parent_dirs(tmp_path):
    log_path = tmp_path / "logs" / "router.log"

    logger = configure_logging(log_path=log_path, level="INFO")
    logger.info("hello")
    for handler in logger.handlers:
        handler.flush()

    assert log_path.exists()
    assert "hello" in log_path.read_text()


def test_configure_logging_applies_configured_level(tmp_path):
    logger = configure_logging(log_path=tmp_path / "router.log", level="DEBUG")

    assert logger.level == logging.DEBUG


def test_configure_logging_returns_the_named_logger(tmp_path):
    logger = configure_logging(log_path=tmp_path / "router.log", level="INFO")

    assert logger.name == LOGGER_NAME
