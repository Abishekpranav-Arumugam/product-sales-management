import logging
import json
import sys
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
        }

        standard_attrs = {
            'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
            'funcName', 'levelname', 'levelno', 'lineno', 'module',
            'msecs', 'message', 'msg', 'name', 'pathname', 'process',
            'processName', 'relativeCreated', 'stack_info', 'thread',
            'threadName'
        }

        for key, val in record.__dict__.items():
            if key not in standard_attrs:
                log_data[key] = val

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # 1. Console Handler (Streams JSON to stdout for local terminal)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(JsonFormatter())
        logger.addHandler(console_handler)

        # Ensure the logs directory is created dynamically if it doesn't exist
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        file_path = os.path.join(log_dir, "app.log")

        # - maxBytes=5 * 1024 * 1024 (5 Megabytes)
        # - backupCount=5 (Keep up to 5 historical log backups)
        file_handler = RotatingFileHandler(
            file_path,
            maxBytes=5 * 1024 * 1024,
            backupCount=5
        )
        file_handler.setFormatter(JsonFormatter())
        logger.addHandler(file_handler)

    return logger