"""Session-scoped reference demo API. No arbitrary Cypher or live-system writes."""

import os
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator
from redis.exceptions import RedisError

from ..store import LOCK
from .store import new_session, session_store
from .engine import simulate, prepare
from .investigation import answer
from .coverage import workspace_disclosure

router = APIRouter(prefix="/api/company")


class Session(BaseModel):
    session_id: str | None = Field(default=None, max_length=32)


class Query(BaseModel):
    session_id: str = Field(min_length=32, max_length=32)
    question: str = Field(
        default="What evidence is available in this company workspace?",
        min_length=3,
        max_length=1500,
    )
    focus_id: str | None = Field(default=None, max_length=100)
    parent_receipt_id: str | None = Field(default=None, max_length=100)
    client: str = Field(default="all", min_length=1, max_length=200)
    effective_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT12:00:00Z"
        )
    )
    known_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT12:00:00Z"
        )
    )
    use_gemini: bool = False
    close_sunday: bool = True

    @field_validator("effective_at", "known_at")
    @classmethod
    def timestamps(cls, value):
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            raise ValueError("Timezone is required")
        return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
        raise HTTPException(
            503,
            "The database could not complete this workspace request. Please retry shortly.",
        )


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
            roots = [
                store.get(r[0])
                for r in store.read(
                    "MATCH (n:Entity) WHERE n.kind IN ['Company','Team','Client','Decision'] RETURN n.id ORDER BY CASE WHEN n.kind='Company' THEN 0 ELSE 1 END,n.title LIMIT 10"
                )
            ]
            graph = store.subgraph(roots)
            return dict(
                session_id=id,
                company=next(
                    (
                        store.get(r[0])
                        for r in store.read(
                            "MATCH (n:Company) RETURN n.id ORDER BY n.id LIMIT 1"
                        )
                    ),
                    None,
                ),
                clients=[
                    store.get(r[0])
                    for r in store.read("MATCH (n:Client) RETURN n.id ORDER BY n.title")
                ],
                demo=store.demo_config(),
                stats=store.stats(),
                sources=[store.get(s) for s in sources],
                graph=graph,
                gemini_configured=bool(os.getenv("GEMINI_API_KEY")),
                investigator_configured=bool(
                    os.getenv("GEMINI_API_KEY")
                    or os.getenv("GROQ_API_KEY")
                    or os.getenv("OPENROUTER_API_KEY")
                ),
                amendment_loaded=bool(store.get("source-amendment")),
                receipts=[r for r in store.receipts() if r.get("domain") == "company"],
                disclosure=(
                    workspace_disclosure()
                    if store.demo_config()
                    else store.read(
                        'MATCH (m:Metadata {id:"dataset"}) RETURN coalesce(m.dataset_description,"Company evidence workspace; inspect source classifications")'
                    )[0][0]
                ),
            )
    except (RedisError, OSError):
        raise HTTPException(
            503,
            "The database could not complete this workspace request. Please retry shortly.",
        )


@router.post("/ask")
def ask(request: Query):
    with LOCK:
        store = safe_store(request.session_id)
        if request.focus_id and not store.get(request.focus_id):
            raise HTTPException(404, "Selected record not found.")
    # Never hold the global write lock while waiting for external inference.
    return answer(store, request)


@router.post("/explore")
def explore(request: Explore):
    with LOCK:
        store = safe_store(request.session_id)
        node = store.get(request.id)
        if not node or node["kind"] in {"Receipt", "Action", "DemoSession"}:
            raise HTTPException(404, "Record not found.")
        graph = store.record_graph(request.id)
        if request.depth == 2 and node["kind"] not in {
            "Shipment",
            "ScanEvent",
            "Manifest",
            "PickupRequest",
            "Route",
        }:
            graph = store.neighborhood(request.id, request.depth)
        return dict(entity=node, graph=graph, owners=store.owners(request.id))


@router.post("/simulate")
def simulation(request: Query):
    with LOCK:
        store = safe_store(request.session_id)
        if not store.demo_config():
            raise HTTPException(422, "This workspace has no registered demo simulation")
        return simulate(store, request)


@router.post("/events")
def events(request: Event):
    with LOCK:
        store = safe_store(request.session_id)
        if not store.demo_config():
            raise HTTPException(422, "This workspace has no registered demo replay")
        return store.replay(request.event)


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
