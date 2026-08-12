"""Request-ID correlation. Mirrors backend/mirage_backend/request_context.py
exactly — see its docstring, including why RequestIdMiddleware is plain
ASGI rather than Starlette's BaseHTTPMiddleware (which is documented to
interact badly with app-level exception handlers).

ai/ mostly *receives* an X-Request-ID from backend/ (which originated it)
rather than generating its own — but generates one anyway when called
directly (e.g. local testing against ai/ without backend/ in front of
it), so a correlation id always exists to log against.
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
    return _request_id.get()


class RequestIdMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        request_id = headers.get(REQUEST_ID_HEADER.lower()) or uuid.uuid4().hex
        # Also stashed on scope["state"] (-> Request.state) so an
        # exception handler registered for the bare `Exception` type can
        # read it directly — see backend/mirage_backend/request_context.py's
        # docstring for why (FastAPI routes that handler outside every
        # add_middleware()-added middleware, including this one).
        scope.setdefault("state", {})["request_id"] = request_id
        _request_id.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                response_headers = MutableHeaders(scope=message)
                response_headers[REQUEST_ID_HEADER] = request_id
            await send(message)

        # Deliberately no ContextVar.reset(): each request runs in its own
        # asyncio Task with an isolated Context copy, so this never leaks
        # across requests, and not resetting keeps get_request_id()
        # correct for code running during exception unwinding.
        await self.app(scope, receive, send_with_request_id)


class RequestIdLogFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id()
        return True
