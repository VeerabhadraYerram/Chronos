"""Separate read-only reviewer portal. No database credentials or arbitrary Cypher."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import Field
from redis.exceptions import RedisError

from .api import Session, safe_store
from .repository import CompanyReader
from ..store import LOCK

router = APIRouter()
ROOT = Path(__file__).parent / "inspector"
HEADERS = {
    "Cache-Control": "no-store",
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
}


class Inspection(Session):
    session_id: str = Field(min_length=32, max_length=32, pattern="^[a-f0-9]+$")
    label: str = Field(default="", max_length=80)
    query: str = Field(default="", max_length=240)
    relation: str = Field(default="", max_length=80)
    record_id: str = Field(default="", max_length=200)
    offset: int = Field(default=0, ge=0, le=1000000)
    limit: int = Field(default=50, ge=1, le=100)


@router.get("/database")
def portal():
    return FileResponse(
        ROOT / "index.html",
        headers={
            **HEADERS,
            "Content-Security-Policy": "default-src 'none'; script-src 'self'; style-src 'self'; connect-src 'self'; img-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'",
        },
    )


@router.get("/database/assets/{name}")
def asset(name: str):
    if name not in {"inspector.js", "inspector.css"}:
        raise HTTPException(404, "Asset not found")
    return FileResponse(ROOT / name, headers=HEADERS)


@router.post("/api/database/{operation}")
def inspect(operation: str, request: Inspection):
    with LOCK:
        try:
            reader = CompanyReader(safe_store(request.session_id))
            if operation == "catalog":
                result = reader.catalog()
            elif operation == "rows":
                result = reader.rows(
                    request.label, request.query, request.offset, request.limit
                )
            elif operation == "relationships":
                result = reader.edges(
                    request.relation, request.record_id, request.offset, request.limit
                )
            elif operation == "record":
                result = reader.record(request.record_id)
            elif operation == "audit":
                result = reader.audit()
            elif operation == "export":
                result = reader.export()
            else:
                raise HTTPException(404, "Read operation not found")
            return JSONResponse(result, headers=HEADERS)
        except (RedisError, OSError):
            raise HTTPException(503, "Database inspection is temporarily unavailable")
