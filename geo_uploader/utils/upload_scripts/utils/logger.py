import logging
import os
import sys


def setup_logger(
    name: str,
    log_file: str | None = None,
    level: int = logging.INFO,
    console: bool = True,
) -> logging.Logger:
    """Set up and configure a logger instance."""
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create formatters
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Add console handler if requested
    if console or log_file is None:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Add file handler if log file is specified
    if log_file:
        # Ensure directory exists
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
