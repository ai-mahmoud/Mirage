"""Request-ID correlation.

A per-request id is generated (or taken from an incoming X-Request-ID
header, so a caller that already has one — e.g. a load balancer, or
ai/'s own middleware replying to a request backend/ initiated — keeps
it) at the edge, stored in a ContextVar so any code running within that
request can read it without threading it through every function
signature, and attached to every log record via RequestIdLogFilter
(logging_config.py). ai_client.py forwards it on every outgoing call to
ai/, so one request's logs can be grepped across both services' streams.

RequestIdMiddleware is plain ASGI, not Starlette's BaseHTTPMiddleware —
BaseHTTPMiddleware runs the downstream app in a separate task and is
documented to interact badly with app-level exception handlers (a
generic `@app.exception_handler(Exception)` handler's response can get
lost and the original exception re-raised instead). Plain ASGI
middleware doesn't have that failure mode.
"""

from __future__ import annotations

import logging
import uuid
from contextvars import ContextVar

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

_request_id: ContextVar[str] = ContextVar("request_id", default="-")

REQUEST_ID_HEADER = "X-Request-ID"


def get_request_id() -> str:
    """get_request_id: -> String
    Purpose: the current request's correlation id, or "-" outside any
    request (e.g. at import time, in a script).
    """
    return _request_id.get()


class RequestIdMiddleware:
    """Assigns/propagates a request id for the duration of one request,
    and echoes it back as a response header so a client (or a test) can
    correlate its own logs against the server's."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = headers.get(REQUEST_ID_HEADER.lower()) or uuid.uuid4().hex
        # Also stashed on scope["state"] (-> Request.state) so an
        # exception-handler registered for the bare `Exception` type can
        # read it directly — FastAPI routes that handler through
        # Starlette's ServerErrorMiddleware, which sits OUTSIDE every
        # add_middleware()-added middleware including this one, so by the
        # time it runs, this middleware's own frame (and thus a `finally`
        # reset of the ContextVar) has already unwound.
        scope.setdefault("state", {})["request_id"] = request_id
        _request_id.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        # Deliberately no ContextVar.reset() here: each request is handled
        # in its own asyncio Task, which gets an isolated copy of the
        # current Context, so this set() never leaks into sibling
        # requests — and NOT resetting is what keeps get_request_id()
        # correct for code that runs during exception unwinding (e.g. the
        # generic exception handler's own logging) rather than clearing
        # it out from under that code.
        await self.app(scope, receive, send_with_request_id)


class RequestIdLogFilter(logging.Filter):
    """Stamps every log record with the current request id, so a JSON log
    line is greppable by request even when it's logged deep inside
    session_service.py or auth.py, far from the route handler."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
