import logging
import sys
import re
from typing import Optional


class SensitiveDataFilter(logging.Filter):
    """Filter that masks sensitive tokens, passwords, and API keys from logs."""

    PATTERNS = [
        (re.compile(r'(api[_-]?key[\s:=]+)(["\']?[a-zA-Z0-9_\-\.]{8,}["\']?)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(password[\s:=]+)(["\']?[^"\',\s]{3,}["\']?)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(service[_-]?role[\s:=]+)(["\']?[a-zA-Z0-9_\-\.]{8,}["\']?)', re.IGNORECASE), r'\1***MASKED***'),
        (re.compile(r'(postgresql:\/\/[^:]+:)([^@]+)(@)', re.IGNORECASE), r'\1***MASKED***\3'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, repl in self.PATTERNS:
                record.msg = pattern.sub(repl, record.msg)
        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Set up standardized application logging with redaction filter."""
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if setup_logging is called multiple times
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(numeric_level)
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        handler.addFilter(SensitiveDataFilter())
        root_logger.addHandler(handler)
    else:
        for handler in root_logger.handlers:
            handler.setLevel(numeric_level)
            handler.addFilter(SensitiveDataFilter())


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a named logger instance."""
    return logging.getLogger(name or "complaint_assistant")
