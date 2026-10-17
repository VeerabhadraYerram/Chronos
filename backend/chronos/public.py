"""Bounded public evaluation entrypoint; local-only legacy routes are excluded."""

import json
import os
import time
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from redis.exceptions import RedisError
from starlette.concurrency import run_in_threadpool

from .company.api import router as company_router
from .company.inspection_api import router as inspection_router
from .company.store import CompanyStore, BASE_NAME
from .store import LOCK


class EvaluationLimits:
    """Single-process admission limits, not enterprise identity or DDoS protection."""

    def __init__(self, app, api_per_minute=90, ai_per_hour=120, max_body=65536):
        self.app = app
        self.api_per_minute = api_per_minute
        self.ai_per_hour = ai_per_hour
        self.max_body = max_body
        self.windows = defaultdict(deque)
        self.active_ai = 0

    def allow(self, key, limit, seconds):
        now = time.monotonic()
        if len(self.windows) > 4096:
            for old in list(self.windows):
                if not self.windows[old] or self.windows[old][-1] < now - 3600:
                    del self.windows[old]
            if key not in self.windows and len(self.windows) > 4096:
                return False
        hits = self.windows[key]
        while hits and hits[0] <= now - seconds:
            hits.popleft()
        if len(hits) >= limit:
            return False
        hits.append(now)
        return True

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        headers = dict(scope["headers"])
        path = scope["path"]

        async def reject(status, message, retry=None):
            response = JSONResponse(
                {"detail": message},
                status_code=status,
                headers={
                    "Cache-Control": "no-store",
                    **({"Retry-After": str(retry)} if retry else {}),
                },
            )
            await response(scope, receive, send)

        async def protected_send(message):
            if message["type"] == "http.response.start":
                message["headers"] = list(message.get("headers", [])) + [
                    (b"x-content-type-options", b"nosniff"),
                    (b"referrer-policy", b"no-referrer"),
                    (b"x-frame-options", b"DENY"),
                    (
                        b"permissions-policy",
                        b"camera=(), microphone=(), geolocation=()",
                    ),
                ]
                if not path.startswith("/database"):
                    message["headers"].append(
                        (
                            b"content-security-policy",
                            b"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
                        )
                    )
                if path.startswith("/api/"):
                    message["headers"].append((b"cache-control", b"no-store"))
            await send(message)

        if not path.startswith("/api/") or scope["method"] != "POST":
            return await self.app(scope, receive, protected_send)
        origin = headers.get(b"origin")
        if origin:
            parsed = urlsplit(origin.decode(errors="replace"))
            if parsed.scheme not in {
                "https",
                "http",
            } or parsed.netloc.encode() != headers.get(b"host"):
                return await reject(
                    403, "Use this website to access its evaluation API."
                )
        client = (scope.get("client") or ("unknown", 0))[0]
        if not self.allow(("api", client), self.api_per_minute, 60):
            return await reject(429, "Too many requests. Please try again shortly.", 60)
        if path == "/api/company/session" and not self.allow(
            ("sessions", client), 12, 60
        ):
            return await reject(
                429, "Please reuse your workspace or try again in a minute.", 60
            )
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body.extend(message.get("body", b""))
            if len(body) > self.max_body:
                return await reject(
                    413, "Request is too large for this evaluation service."
                )
            if not message.get("more_body"):
                break
        ai = False
        if path == "/api/company/ask":
            try:
                payload = json.loads(body)
                # Validation accepts truthy boolean input; budget it conservatively.
                ai = isinstance(payload, dict) and bool(payload.get("use_gemini"))
            except (ValueError, UnicodeDecodeError):
                pass
        if ai:
            if self.active_ai >= 2:
                return await reject(
                    429, "Two investigations are running. Please try again shortly.", 15
                )
            if not self.allow(("ai-client", client), 8, 60):
                return await reject(
                    429, "AI request limit reached. Please try again in a minute.", 60
                )
            if not self.allow(("ai-global",), self.ai_per_hour, 3600):
                return await reject(
                    429,
                    "The hourly AI evaluation budget is exhausted. Please try later.",
                    3600,
                )
            self.active_ai += 1
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        try:
            await self.app(scope, replay, protected_send)
        finally:
            if ai:
                self.active_ai -= 1


def create_app(static_dir=None, **limits):
    app = FastAPI(
        title="ChronosGraph evaluation", docs_url=None, redoc_url=None, openapi_url=None
    )
    app.add_middleware(EvaluationLimits, **limits)
    app.include_router(company_router)
    app.include_router(inspection_router)

    @app.get("/healthz")
    def live():
        return {"status": "running"}

    @app.get("/readyz")
    async def ready():
        def check():
            with LOCK:
                store = CompanyStore(BASE_NAME)
                store.seed()
                return store.revision()

        try:
            revision = await run_in_threadpool(check)
        except (RedisError, OSError):
            raise HTTPException(503, "FalkorDB is not ready.")
        if not any(
            os.getenv(k)
            for k in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY")
        ):
            raise HTTPException(
                503, "Configure an AI provider before opening evaluation."
            )
        return {"status": "ready", "database": "FalkorDB", "revision": revision}

    directory = Path(static_dir or os.getenv("CHRONOS_STATIC_DIR", "frontend/dist"))
    if not (directory / "index.html").is_file():
        raise RuntimeError("Build the frontend before starting the evaluation server.")
    app.mount("/", StaticFiles(directory=directory, html=True), name="frontend")
    return app
