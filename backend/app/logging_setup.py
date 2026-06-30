"""Logging configuration with request ID context."""

import json
import logging
import uuid
from contextvars import ContextVar
from typing import Optional

request_id_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

def new_request_id() -> str:
    """Generate a short, unique request ID."""
    return uuid.uuid4().hex[:8]

class RequestIdFilter(logging.Filter):
    """Add request_id to log records."""
    def filter(self, record):
        record.request_id = request_id_var.get() or "-"
        return True

class ExtraFilter(logging.Filter):
    """Add extra fields to log records."""
    def filter(self, record):
        if not hasattr(record, "extra"):
            record.extra = {}
        if not isinstance(record.extra, dict):
            record.extra = {}
        return True

def setup_logging(level: str = "INFO"):
    """Configure logging with JSON format and request IDs."""
    
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Console handler
    handler = logging.StreamHandler()
    handler.setLevel(log_level)
    
    # JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "request_id": getattr(record, "request_id", "-"),
                "name": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, "extra") and record.extra:
                log_obj["extra"] = record.extra
            if record.exc_info:
                log_obj["exception"] = self.formatException(record.exc_info)
            return json.dumps(log_obj)
    
    handler.setFormatter(JSONFormatter())
    handler.addFilter(RequestIdFilter())
    handler.addFilter(ExtraFilter())
    
    # Configure root logger
    root = logging.getLogger()
    root.setLevel(log_level)
    root.addHandler(handler)
    
    # Reduce noise from third-party libs
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)