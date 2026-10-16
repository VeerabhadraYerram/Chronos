"""Session-scoped reference demo API. No arbitrary Cypher or live-system writes."""

import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from redis.exceptions import RedisError

from ..store import LOCK
from .store import new_session, session_store
from .engine import answer, evaluate, simulate, prepare, useful_graph

router = APIRouter(prefix="/api/company")


class Session(BaseModel):
    session_id: str | None = Field(default=None, max_length=32)


class Query(BaseModel):
    session_id: str = Field(min_length=32, max_length=32)
    question: str = Field(
        default="Can we close the Bengaluru facility on Sundays?",
        min_length=3,
        max_length=1500,
    )
    focus_id: str | None = Field(default=None, max_length=100)
    parent_receipt_id: str | None = Field(default=None, max_length=100)
    client: Literal["all", "havells", "sugar", "hpcl"] = "all"
    effective_at: str = "2026-11-08T12:00:00Z"
    known_at: str = "2026-10-16T12:00:00Z"
    use_gemini: bool = False
    close_sunday: bool = True

    @field_validator("effective_at", "known_at")
    @classmethod
    def timestamps(cls, value):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("Timezone is required")
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class Explore(BaseModel):
    session_id: str = Field(min_length=32, max_length=32)
    id: str = Field(min_length=1, max_length=100)
    depth: Literal[1, 2] = 1


class Event(BaseModel):
    session_id: str = Field(min_length=32, max_length=32)
    event: Literal["amendment", "withdraw"]


class Packet(BaseModel):
    session_id: str = Field(min_length=32, max_length=32)
    receipt_id: str = Field(min_length=1, max_length=100)


def safe_store(id):
    try:
        return session_store(id)
    except (RedisError, OSError):
        raise HTTPException(503, "FalkorDB is unavailable. Start the project database.")


@router.post("/session")
def session(request: Session):
    try:
        with LOCK:
            id = request.session_id or new_session()
            store = safe_store(id)
            sources = [
                r[0]
                for r in store.read("MATCH (s:Source) RETURN s.id ORDER BY s.title")
            ]
            checks = evaluate(store, "2026-11-08T12:00:00Z", "2026-10-16T12:00:00Z")[
                "checks"
            ]
            graph = useful_graph(store, checks)
            return dict(
                session_id=id,
                stats=store.stats(),
                sources=[store.get(s) for s in sources],
                graph=graph,
                gemini_configured=bool(os.getenv("GEMINI_API_KEY")),
                investigator_configured=bool(
                    os.getenv("GEMINI_API_KEY") or os.getenv("GROQ_API_KEY")
                ),
                amendment_loaded=bool(store.get("source-amendment")),
                receipts=[r for r in store.receipts() if r.get("domain") == "company"],
                disclosure="Independent Delhivery reference demo. Public company names; synthetic operational records, commitments, roles and policies. Not affiliated with Delhivery.",
            )
    except (RedisError, OSError):
        raise HTTPException(503, "FalkorDB is unavailable. Start the project database.")


@router.post("/ask")
def ask(request: Query):
    with LOCK:
        store = safe_store(request.session_id)
        if request.focus_id and not store.get(request.focus_id):
            raise HTTPException(404, "Selected record not found.")
        return answer(store, request)


@router.post("/explore")
def explore(request: Explore):
    with LOCK:
        store = safe_store(request.session_id)
        node = store.get(request.id)
        if not node or node["kind"] in {"Receipt", "Action", "DemoSession"}:
            raise HTTPException(404, "Record not found.")
        # For operational records, a read-only bounded traversal includes scan history.
        if node["kind"] in {"Shipment", "Manifest", "PickupRequest"}:
            rows = store.read(
                "MATCH (a:Entity {id:$id})-[r]-(b:Entity) RETURN DISTINCT b.payload LIMIT 16",
                dict(id=request.id),
            )
            import json

            graph = store.subgraph([node] + [json.loads(row[0]) for row in rows])
        else:
            graph = store.neighborhood(request.id, request.depth)
        return dict(entity=node, graph=graph, owners=store.owners(request.id))


@router.post("/simulate")
def simulation(request: Query):
    with LOCK:
        return simulate(safe_store(request.session_id), request)


@router.post("/events")
def events(request: Event):
    with LOCK:
        return safe_store(request.session_id).replay(request.event)


@router.post("/packet")
def packet(request: Packet):
    with LOCK:
        try:
            return prepare(safe_store(request.session_id), request.receipt_id)
        except RuntimeError as e:
            raise HTTPException(409, str(e))
        except ValueError:
            raise HTTPException(404, "Investigation not found.")


@router.post("/search")
def search(request: Query):
    with LOCK:
        return dict(records=safe_store(request.session_id).search(request.question))
