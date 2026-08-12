"""Structured (JSON) application logging. Mirrors
backend/mirage_backend/logging_config.py exactly — see its docstring."""

from __future__ import annotations

import json
import logging
import sys

from .request_context import RequestIdLogFilter

_JSON_HANDLER_MARK = "_mirage_json_handler"


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "requestId": getattr(record, "request_id", "-"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(level: int = logging.INFO) -> None:
    root = logging.getLogger()
    if any(getattr(h, _JSON_HANDLER_MARK, False) for h in root.handlers):
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RequestIdLogFilter())
    setattr(handler, _JSON_HANDLER_MARK, True)
    root.addHandler(handler)
    root.setLevel(level)
