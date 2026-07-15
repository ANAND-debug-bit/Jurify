import json

from app.core.config import Settings
from app.core.logging import (
    REDACTED,
    _redact_sensitive,
    clear_log_context,
    configure_logging,
    current_log_context,
    get_logger,
    log_context,
    new_correlation_id,
    new_request_id,
)


def test_redact_sensitive_strips_blocklisted_keys() -> None:
    event = {"password": "hunter2", "case_id": "abc", "token": "xyz"}

    result = _redact_sensitive(None, "info", event)

    assert result["password"] == REDACTED
    assert result["token"] == REDACTED
    assert result["case_id"] == "abc"


def test_redact_sensitive_is_case_insensitive() -> None:
    event = {"PASSWORD": "hunter2"}

    result = _redact_sensitive(None, "info", event)

    assert result["PASSWORD"] == REDACTED


def test_redact_sensitive_leaves_safe_keys_untouched() -> None:
    event = {"model": "gemma3n", "latency": 0.42, "input_tokens": 100}

    result = _redact_sensitive(None, "info", event)

    assert result == event


def test_new_request_id_and_correlation_id_are_unique_hex() -> None:
    a, b = new_request_id(), new_correlation_id()

    assert a != b
    assert len(a) == 32
    int(a, 16)  # raises if not valid hex


def test_log_context_binds_and_restores(monkeypatch) -> None:
    clear_log_context()
    assert current_log_context() == {}

    with log_context(request_id="r1", case_id="c1"):
        ctx = current_log_context()
        assert ctx["request_id"] == "r1"
        assert ctx["case_id"] == "c1"

        with log_context(case_id="c2", agent_name="risk_assessment"):
            nested = current_log_context()
            assert nested["case_id"] == "c2"
            assert nested["request_id"] == "r1"
            assert nested["agent_name"] == "risk_assessment"

        restored = current_log_context()
        assert restored["case_id"] == "c1"
        assert "agent_name" not in restored

    assert current_log_context() == {}


def test_log_context_drops_none_values() -> None:
    clear_log_context()
    with log_context(request_id="r1", user_id=None):
        ctx = current_log_context()
        assert "user_id" not in ctx
        assert ctx["request_id"] == "r1"
    clear_log_context()


def test_configure_logging_prod_renders_json(capsys) -> None:
    settings = Settings(environment="prod")
    configure_logging(settings)
    clear_log_context()

    logger = get_logger("test.prod")
    logger.info("hello_world", case_id="c1")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)  # raises if not valid JSON

    assert payload["event"] == "hello_world"
    assert payload["case_id"] == "c1"
    assert payload["level"] == "info"


def test_configure_logging_dev_renders_non_json_console_output(capsys) -> None:
    settings = Settings(environment="dev")
    configure_logging(settings)
    clear_log_context()

    logger = get_logger("test.dev")
    logger.info("hello_console", case_id="c1")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]

    assert "hello_console" in line
    try:
        json.loads(line)
    except json.JSONDecodeError:
        pass
    else:
        raise AssertionError("dev console output should not be raw JSON")


def test_exception_logging_includes_traceback(capsys) -> None:
    settings = Settings(environment="prod")
    configure_logging(settings)
    clear_log_context()

    logger = get_logger("test.exc")
    try:
        raise ValueError("boom")
    except ValueError:
        logger.exception("operation_failed", node_name="legal_research")

    captured = capsys.readouterr()
    line = captured.out.strip().splitlines()[-1]
    payload = json.loads(line)

    assert payload["event"] == "operation_failed"
    assert "ValueError" in payload["exception"]
    assert "boom" in payload["exception"]
