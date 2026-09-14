"""Structured JSON logging (§105, §125).

Every log record carries a UTC ISO-8601 timestamp. JSON is the default format so logs
are machine-parseable for the research/audit workflows the spec depends on.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import UTC, datetime


class _UtcJsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Attach structured extras (anything passed via logger.info(..., extra={...})).
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


_RESERVED = set(
    logging.makeLogRecord({}).__dict__
) | {"message", "asctime", "taskName"}


def configure_logging(level: str = "INFO", *, json_format: bool = True) -> None:
    """Configure root logging. Idempotent."""
    root = logging.getLogger()
    root.setLevel(level.upper())
    for h in list(root.handlers):
        root.removeHandler(h)
    handler = logging.StreamHandler(stream=sys.stderr)
    handler.setFormatter(
        _UtcJsonFormatter() if json_format else logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s"
        )
    )
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
