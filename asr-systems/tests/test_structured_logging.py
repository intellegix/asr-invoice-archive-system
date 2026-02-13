"""
P77: Structured logging tests.
Validates text/JSON format configuration, field presence, extra merging,
contextvars, log level filtering, and idempotent reconfiguration.
"""

import json
import logging
import os
import sys
from io import StringIO
from pathlib import Path

import pytest
import structlog

_asr = Path(__file__).parent.parent
sys.path.insert(0, str(_asr / "shared"))
sys.path.insert(0, str(_asr / "production-server"))

os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")


def _capture_log(log_format: str, log_level: str = "INFO"):
    """Reconfigure logging with a StringIO capture, return (logger, stream)."""
    from config.logging_config import configure_logging

    configure_logging(log_level=log_level, log_format=log_format)

    stream = StringIO()
    handler = logging.StreamHandler(stream)

    # Apply structlog ProcessorFormatter from the root handler
    root = logging.getLogger()
    if root.handlers:
        handler.setFormatter(root.handlers[0].formatter)

    # Replace root handler with our capture stream
    root.handlers.clear()
    root.addHandler(handler)

    test_logger = logging.getLogger("test.structured")
    return test_logger, stream


def test_text_format_outputs_readable_string():
    """Text format produces human-readable non-JSON output."""
    lgr, stream = _capture_log("text")
    lgr.info("hello world")
    output = stream.getvalue()
    assert "hello world" in output
    # Text format should NOT be valid JSON
    with pytest.raises(json.JSONDecodeError):
        json.loads(output.strip().split("\n")[-1])


def test_json_format_outputs_valid_json():
    """JSON format produces parseable JSON with required fields."""
    lgr, stream = _capture_log("json")
    lgr.info("test event")
    output = stream.getvalue().strip()
    line = output.split("\n")[-1]
    data = json.loads(line)
    assert data["event"] == "test event"
    assert "level" in data
    assert "timestamp" in data
    assert "logger" in data


def test_json_extra_dict_merged():
    """Extra dict passed to logger.info() is merged into JSON output."""
    lgr, stream = _capture_log("json")
    lgr.info("with_extra", extra={"request_id": "abc-123", "method": "GET"})
    output = stream.getvalue().strip()
    line = output.split("\n")[-1]
    data = json.loads(line)
    assert data["request_id"] == "abc-123"
    assert data["method"] == "GET"


def test_contextvars_merged_into_output():
    """Bound contextvars appear in JSON log output."""
    lgr, stream = _capture_log("json")
    structlog.contextvars.bind_contextvars(request_id="ctx-456")
    try:
        lgr.info("ctx test")
    finally:
        structlog.contextvars.clear_contextvars()

    output = stream.getvalue().strip()
    line = output.split("\n")[-1]
    data = json.loads(line)
    assert data.get("request_id") == "ctx-456"


def test_log_level_filtering():
    """DEBUG messages are suppressed when level is INFO."""
    lgr, stream = _capture_log("json", log_level="INFO")
    lgr.debug("this should be suppressed")
    lgr.info("this should appear")
    output = stream.getvalue().strip()
    lines = [l for l in output.split("\n") if l.strip()]
    assert len(lines) == 1
    assert "this should appear" in lines[0]


def test_warning_level_passes_through():
    """WARNING level messages pass through at INFO level."""
    lgr, stream = _capture_log("json", log_level="INFO")
    lgr.warning("warn msg")
    output = stream.getvalue().strip()
    data = json.loads(output.split("\n")[-1])
    assert data["level"] == "warning"


def test_error_level_includes_event():
    """ERROR logs include the event text."""
    lgr, stream = _capture_log("json", log_level="INFO")
    lgr.error("something broke")
    output = stream.getvalue().strip()
    data = json.loads(output.split("\n")[-1])
    assert data["event"] == "something broke"
    assert data["level"] == "error"


def test_idempotent_configuration():
    """Calling configure_logging() twice does not produce duplicate handlers."""
    from config.logging_config import configure_logging

    configure_logging("INFO", "text")
    configure_logging("INFO", "text")
    root = logging.getLogger()
    assert len(root.handlers) == 1


def test_uvicorn_access_quieted():
    """uvicorn.access logger should be at WARNING level after configuration."""
    from config.logging_config import configure_logging

    configure_logging("INFO", "text")
    access_logger = logging.getLogger("uvicorn.access")
    assert access_logger.level >= logging.WARNING


def test_request_logging_middleware_binds_contextvars():
    """RequestLoggingMiddleware binds and clears request_id in contextvars."""
    from fastapi.testclient import TestClient

    from api.main import app

    with TestClient(app, raise_server_exceptions=False) as client:
        resp = client.get("/api/status")
        assert resp.status_code == 200
        # After request completes, contextvars should be cleared
        ctx = structlog.contextvars.get_contextvars()
        assert "request_id" not in ctx
