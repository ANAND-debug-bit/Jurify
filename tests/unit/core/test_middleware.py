import json

import pytest
from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.routing import Route
from starlette.testclient import TestClient

from app.core.config import Settings
from app.core.logging import clear_log_context, configure_logging
from app.core.middleware import (
    CORRELATION_ID_HEADER,
    REQUEST_ID_HEADER,
    RequestLoggingMiddleware,
)
from app.core.telemetry import HTTP_REQUESTS_TOTAL


async def _ok(request):
    return JSONResponse({"status": "ok"})


async def _boom(request):
    raise RuntimeError("route exploded")


class _FakeAuthMiddleware(BaseHTTPMiddleware):
    """Stands in for the real auth middleware (Module 24) which will set
    request.state.user_id before RequestLoggingMiddleware runs."""

    async def dispatch(self, request, call_next):
        request.state.user_id = "user-42"
        return await call_next(request)


def _build_app(*, with_fake_auth: bool = False) -> Starlette:
    app = Starlette(routes=[Route("/ok", _ok), Route("/boom", _boom)])
    # Starlette executes the LAST-added middleware OUTERMOST (first), so
    # RequestLoggingMiddleware must be added before the auth stand-in for
    # request.state.user_id to be visible when RequestLoggingMiddleware runs.
    app.add_middleware(RequestLoggingMiddleware)
    if with_fake_auth:
        app.add_middleware(_FakeAuthMiddleware)
    return app


@pytest.fixture(autouse=True)
def _clean():
    clear_log_context()
    yield
    clear_log_context()


def test_middleware_adds_request_and_correlation_id_headers() -> None:
    client = TestClient(_build_app(), raise_server_exceptions=False)

    response = client.get("/ok")

    assert response.status_code == 200
    assert REQUEST_ID_HEADER in response.headers
    assert CORRELATION_ID_HEADER in response.headers
    assert len(response.headers[REQUEST_ID_HEADER]) == 32


def test_middleware_reuses_incoming_request_id() -> None:
    client = TestClient(_build_app(), raise_server_exceptions=False)

    response = client.get("/ok", headers={REQUEST_ID_HEADER: "fixed-request-id"})

    assert response.headers[REQUEST_ID_HEADER] == "fixed-request-id"
    assert response.headers[CORRELATION_ID_HEADER] == "fixed-request-id"


def test_middleware_reuses_incoming_correlation_id_independent_of_request_id() -> None:
    client = TestClient(_build_app(), raise_server_exceptions=False)

    response = client.get(
        "/ok",
        headers={
            REQUEST_ID_HEADER: "req-1",
            CORRELATION_ID_HEADER: "corr-shared-across-services",
        },
    )

    assert response.headers[REQUEST_ID_HEADER] == "req-1"
    assert response.headers[CORRELATION_ID_HEADER] == "corr-shared-across-services"


def test_middleware_logs_request_started_and_completed(capsys) -> None:
    configure_logging(Settings(environment="prod"))
    client = TestClient(_build_app(), raise_server_exceptions=False)

    client.get("/ok")

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    events = {entry["event"] for entry in lines}

    assert "request_started" in events
    assert "request_completed" in events
    completed = next(e for e in lines if e["event"] == "request_completed")
    assert completed["status_code"] == 200
    assert "execution_time" in completed
    assert completed["request_id"] == lines[0]["request_id"]


def test_middleware_logs_request_failed_on_exception(capsys) -> None:
    configure_logging(Settings(environment="prod"))
    client = TestClient(_build_app(), raise_server_exceptions=False)

    response = client.get("/boom")

    assert response.status_code == 500
    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    events = {entry["event"] for entry in lines}
    assert "request_failed" in events
    failed = next(e for e in lines if e["event"] == "request_failed")
    assert "RuntimeError" in failed["exception"]


def test_middleware_records_prometheus_metrics() -> None:
    client = TestClient(_build_app(), raise_server_exceptions=False)

    before = HTTP_REQUESTS_TOTAL.labels(method="GET", path="/ok", status_code="200")._value.get()
    client.get("/ok")
    after = HTTP_REQUESTS_TOTAL.labels(method="GET", path="/ok", status_code="200")._value.get()

    assert after == before + 1


def test_middleware_binds_user_id_from_request_state(capsys) -> None:
    configure_logging(Settings(environment="prod"))
    client = TestClient(_build_app(with_fake_auth=True), raise_server_exceptions=False)

    client.get("/ok")

    lines = [json.loads(line) for line in capsys.readouterr().out.strip().splitlines()]
    completed = next(e for e in lines if e["event"] == "request_completed")
    assert completed["user_id"] == "user-42"
