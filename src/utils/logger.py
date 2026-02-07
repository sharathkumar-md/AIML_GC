"""
Logging configuration for the Kelp Automated Deal Flow pipeline.
Provides colored console output and file logging.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Try to import colorlog for colored output
try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


# Global logger instances
_loggers = {}


def setup_logger(
    name: str = "kelp",
    level: int = logging.INFO,
    log_dir: Optional[str] = None,
    console_output: bool = True,
    file_output: bool = True
) -> logging.Logger:
    """
    Set up a logger with console and file handlers.

    Args:
        name: Logger name
        level: Logging level (default: INFO)
        log_dir: Directory for log files (default: logs/)
        console_output: Enable console output
        file_output: Enable file output

    Returns:
        Configured logger instance
    """
    # Check if logger already exists
    if name in _loggers:
        return _loggers[name]

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.handlers = []  # Clear any existing handlers

    # Format strings
    console_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    file_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Console handler with colors
    if console_output:
        # On Windows, wrap stdout with UTF-8 encoding to handle special characters
        if sys.platform == 'win32':
            import io
            stream = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        else:
            stream = sys.stdout
        console_handler = logging.StreamHandler(stream)
        console_handler.setLevel(level)

        if COLORLOG_AVAILABLE:
            # Colored formatter
            color_formatter = colorlog.ColoredFormatter(
                "%(log_color)s%(asctime)s | %(levelname)-8s | %(name)s | %(message)s%(reset)s",
                datefmt=date_format,
                log_colors={
                    'DEBUG': 'cyan',
                    'INFO': 'green',
                    'WARNING': 'yellow',
                    'ERROR': 'red',
                    'CRITICAL': 'red,bg_white',
                }
            )
            console_handler.setFormatter(color_formatter)
        else:
            # Plain formatter
            console_handler.setFormatter(
                logging.Formatter(console_format, datefmt=date_format)
            )

        logger.addHandler(console_handler)

    # File handler
    if file_output:
        # Create log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{name}_{timestamp}.log"

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(
            logging.Formatter(file_format, datefmt=date_format)
        )

        logger.addHandler(file_handler)

        # Also create a latest.log symlink/copy
        latest_log = log_dir / f"{name}_latest.log"
        try:
            if latest_log.exists():
                latest_log.unlink()
            # On Windows, create a copy instead of symlink
            import shutil
            # We'll update this file as we log
        except Exception:
            pass

    # Store logger
    _loggers[name] = logger

    return logger


def get_logger(name: str = "kelp") -> logging.Logger:
    """
    Get an existing logger or create a new one.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]
    return setup_logger(name)


class LoggerMixin:
    """
    Mixin class to add logging capabilities to any class.

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Doing something")
    """

    @property
    def logger(self) -> logging.Logger:
        """Get logger for this class."""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


# Convenience functions for quick logging
def log_info(message: str, logger_name: str = "kelp"):
    """Log an info message."""
    get_logger(logger_name).info(message)


def log_warning(message: str, logger_name: str = "kelp"):
    """Log a warning message."""
    get_logger(logger_name).warning(message)


def log_error(message: str, logger_name: str = "kelp"):
    """Log an error message."""
    get_logger(logger_name).error(message)


def log_debug(message: str, logger_name: str = "kelp"):
    """Log a debug message."""
    get_logger(logger_name).debug(message)


# Performance logging context manager
class LogTimer:
    """
    Context manager for timing operations.

    Usage:
        with LogTimer("Processing data"):
            process_data()
    """

    def __init__(self, operation: str, logger_name: str = "kelp"):
        self.operation = operation
        self.logger = get_logger(logger_name)
        self.start_time = None

    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"Starting: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        if exc_type is None:
            self.logger.info(f"Completed: {self.operation} ({elapsed:.2f}s)")
        else:
            self.logger.error(f"Failed: {self.operation} ({elapsed:.2f}s) - {exc_val}")
        return False
