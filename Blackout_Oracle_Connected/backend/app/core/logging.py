"""
Blackout Oracle - Logging Configuration.

Centralized logging configuration for the Blackout Oracle backend.
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path


# ============================================================
# CONSTANTS
# ============================================================

DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_DIRECTORY = "./logs"
DEFAULT_LOG_FILE = "blackout_oracle.log"

MAX_LOG_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
LOG_BACKUP_COUNT = 5


# ============================================================
# LOG FORMAT
# ============================================================

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%dT%H:%M:%S%z"


# ============================================================
# SENSITIVE FIELDS
# ============================================================

SENSITIVE_FIELD_NAMES = {
    "api_key",
    "apikey",
    "access_token",
    "authorization",
    "password",
    "passwd",
    "secret",
    "secret_key",
    "token",
    "refresh_token",
    "database_url",
    "gemini_api_key",
    "weather_api_key",
}


# ============================================================
# GET LOG LEVEL
# ============================================================

def get_log_level(default=DEFAULT_LOG_LEVEL):
    """
    Get the logging level from the LOG_LEVEL environment variable.
    """

    configured_level = os.getenv(
        "LOG_LEVEL",
        default,
    ).upper()

    level = getattr(
        logging,
        configured_level,
        None,
    )

    if not isinstance(level, int):
        return logging.INFO

    return level


# ============================================================
# SANITIZE VALUES
# ============================================================

def sanitize_value(value):
    """
    Recursively remove sensitive values before logging.
    """

    if isinstance(value, dict):

        sanitized = {}

        for key, item in value.items():

            key_lower = str(key).lower()

            if any(
                sensitive_name in key_lower
                for sensitive_name in SENSITIVE_FIELD_NAMES
            ):
                sanitized[key] = "***REDACTED***"

            else:
                sanitized[key] = sanitize_value(item)

        return sanitized

    if isinstance(value, list):

        return [
            sanitize_value(item)
            for item in value
        ]

    if isinstance(value, tuple):

        return tuple(
            sanitize_value(item)
            for item in value
        )

    if isinstance(value, set):

        return {
            sanitize_value(item)
            for item in value
        }

    return value


# ============================================================
# SENSITIVE DATA FILTER
# ============================================================

class SensitiveDataFilter(logging.Filter):
    """
    Prevent common secret patterns from appearing in logs.
    """

    REDACTED = "***REDACTED***"

    SECRET_PATTERNS = (
        "GEMINI_API_KEY=",
        "WEATHER_API_KEY=",
        "DATABASE_URL=",
        "Authorization: Bearer ",
        "authorization: bearer ",
    )

    def filter(self, record):
        """
        Sanitize sensitive information in log messages.
        """

        message = record.getMessage()

        for pattern in self.SECRET_PATTERNS:

            if pattern in message:

                prefix, _, _ = message.partition(
                    pattern
                )

                record.msg = (
                    prefix
                    + pattern
                    + self.REDACTED
                )

                record.args = ()

        return True


# ============================================================
# FORMATTER
# ============================================================

class BlackoutOracleFormatter(logging.Formatter):
    """
    Formatter used by Blackout Oracle.
    """

    def format(self, record):
        return super().format(record)


# ============================================================
# LOG DIRECTORY
# ============================================================

def get_log_directory():
    """
    Return the configured log directory.
    """

    return Path(
        os.getenv(
            "LOG_DIRECTORY",
            DEFAULT_LOG_DIRECTORY,
        )
    )


def ensure_log_directory():
    """
    Create the log directory if necessary.
    """

    directory = get_log_directory()

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    return directory


# ============================================================
# CONSOLE HANDLER
# ============================================================

def create_console_handler(level):
    """
    Create the console logging handler.
    """

    handler = logging.StreamHandler(
        sys.stdout
    )

    handler.setLevel(level)

    handler.setFormatter(
        BlackoutOracleFormatter(
            fmt=LOG_FORMAT,
            datefmt=DATE_FORMAT,
        )
    )

    handler.addFilter(
        SensitiveDataFilter()
    )

    return handler


# ============================================================
# FILE HANDLER
# ============================================================

def create_file_handler(level):
    """
    Create the rotating file logging handler.
    """

    log_directory = ensure_log_directory()

    log_file = (
        log_directory
        / DEFAULT_LOG_FILE
    )

    handler = (
        logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=MAX_LOG_FILE_SIZE,
            backupCount=LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
    )

    handler.setLevel(level)

    handler.setFormatter(
        BlackoutOracleFormatter(
            fmt=LOG_FORMAT,
            datefmt=DATE_FORMAT,
        )
    )

    handler.addFilter(
        SensitiveDataFilter()
    )

    return handler


# ============================================================
# CONFIGURE LOGGING
# ============================================================

def configure_logging():
    """
    Configure the Blackout Oracle logging system.

    Safe to call multiple times.
    """

    level = get_log_level()

    root_logger = logging.getLogger()

    root_logger.setLevel(level)

    # Prevent duplicate handlers.
    if getattr(
        root_logger,
        "_blackout_oracle_configured",
        False,
    ):
        return root_logger

    # Console logging.
    console_handler = create_console_handler(
        level
    )

    root_logger.addHandler(
        console_handler
    )

    # File logging.
    file_logging_enabled = (
        os.getenv(
            "LOG_FILE_ENABLED",
            "true",
        ).lower()
        in {
            "1",
            "true",
            "yes",
            "on",
        }
    )

    if file_logging_enabled:

        file_handler = create_file_handler(
            level
        )

        root_logger.addHandler(
            file_handler
        )

    root_logger._blackout_oracle_configured = True

    return root_logger


# ============================================================
# LOGGER FACTORY
# ============================================================

def get_logger(name=None):
    """
    Return a logger for a Blackout Oracle module.

    Example:

        logger = get_logger(__name__)
    """

    configure_logging()

    return logging.getLogger(
        name or "blackout_oracle"
    )


# ============================================================
# EVENT LOGGING
# ============================================================

def log_event(
    logger,
    message,
    level=logging.INFO,
    **context
):
    """
    Log an event with sanitized contextual information.
    """

    safe_context = sanitize_value(
        context
    )

    if safe_context:

        logger.log(
            level,
            "%s | context=%s",
            message,
            safe_context,
        )

    else:

        logger.log(
            level,
            message,
        )


# ============================================================
# EXCEPTION LOGGING
# ============================================================

def log_exception(
    logger,
    message,
    **context
):
    """
    Log an exception with sanitized contextual information.

    Call this function from inside an exception handler.
    """

    safe_context = sanitize_value(
        context
    )

    if safe_context:

        logger.exception(
            "%s | context=%s",
            message,
            safe_context,
        )

    else:

        logger.exception(
            message
        )


# ============================================================
# SPECIALIZED LOGGERS
# ============================================================

def get_agent_logger():
    """
    Logger for the AI-agent subsystem.
    """

    return get_logger(
        "blackout_oracle.agent"
    )


def get_telemetry_logger():
    """
    Logger for telemetry ingestion.
    """

    return get_logger(
        "blackout_oracle.telemetry"
    )


def get_weather_logger():
    """
    Logger for weather ingestion.
    """

    return get_logger(
        "blackout_oracle.weather"
    )


def get_risk_logger():
    """
    Logger for risk calculations.
    """

    return get_logger(
        "blackout_oracle.risk"
    )


def get_simulation_logger():
    """
    Logger for digital-twin simulations.
    """

    return get_logger(
        "blackout_oracle.simulation"
    )


def get_database_logger():
    """
    Logger for database operations.
    """

    return get_logger(
        "blackout_oracle.database"
    )


def get_security_logger():
    """
    Logger for security-related events.
    """

    return get_logger(
        "blackout_oracle.security"
    )


# ============================================================
# INITIALIZE LOGGING
# ============================================================

configure_logging()


# ============================================================
# PUBLIC EXPORTS
# ============================================================

__all__ = [
    "configure_logging",
    "get_logger",
    "log_event",
    "log_exception",
    "sanitize_value",
    "get_agent_logger",
    "get_telemetry_logger",
    "get_weather_logger",
    "get_risk_logger",
    "get_simulation_logger",
    "get_database_logger",
    "get_security_logger",
]