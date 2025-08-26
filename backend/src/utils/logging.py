import logging
import sys
from typing import Optional


class _RequestIdFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        # Inject request_id into message when available without failing when absent
        base = super().format(record)
        req_id = getattr(record, "request_id", None)
        if req_id:
            return f"{base} request_id={req_id}"
        return base


def configure_logging(level: str = "INFO") -> None:
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        _RequestIdFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    )
    root = logging.getLogger()
    root.setLevel(numeric_level)
    # Clear any existing handlers to avoid duplicates in reload scenarios
    root.handlers = [handler]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    return logging.getLogger(name or __name__)
