"""Reusable request-logging middleware for FastAPI (Module 2).

Generates/propagates request_id and correlation_id (via headers, so a
caller can supply their own to correlate across services), binds them —
plus user_id if request.state.user_id was already set upstream (e.g. by
an auth dependency in a later module) — to the structlog context for the
duration of the request, logs request_started / request_completed /
request_failed with execution_time, and records Prometheus HTTP metrics.

Starlette's BaseHTTPMiddleware is used rather than a raw ASGI middleware
because FastAPI apps are Starlette apps — this is directly
`app.add_middleware(RequestLoggingMiddleware)`-able.
"""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger, log_context, new_request_id
from app.core.telemetry import HTTP_REQUEST_SECONDS, HTTP_REQUESTS_TOTAL

REQUEST_ID_HEADER = "X-Request-ID"
CORRELATION_ID_HEADER = "X-Correlation-ID"

logger = get_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or new_request_id()
        correlation_id = request.headers.get(CORRELATION_ID_HEADER) or request_id
        user_id = getattr(request.state, "user_id", None)
        method = request.method
        path = request.url.path

        start = time.perf_counter()

        with log_context(
            request_id=request_id, correlation_id=correlation_id, user_id=user_id
        ):
            logger.info("request_started", method=method, path=path)
            try:
                response = await call_next(request)
            except Exception:
                execution_time = time.perf_counter() - start
                HTTP_REQUESTS_TOTAL.labels(
                    method=method, path=path, status_code="500"
                ).inc()
                HTTP_REQUEST_SECONDS.labels(method=method, path=path).observe(
                    execution_time
                )
                logger.exception(
                    "request_failed",
                    method=method,
                    path=path,
                    execution_time=execution_time,
                )
                raise

            execution_time = time.perf_counter() - start
            HTTP_REQUESTS_TOTAL.labels(
                method=method, path=path, status_code=str(response.status_code)
            ).inc()
            HTTP_REQUEST_SECONDS.labels(method=method, path=path).observe(execution_time)
            logger.info(
                "request_completed",
                method=method,
                path=path,
                status_code=response.status_code,
                execution_time=execution_time,
            )

            response.headers[REQUEST_ID_HEADER] = request_id
            response.headers[CORRELATION_ID_HEADER] = correlation_id
            return response
