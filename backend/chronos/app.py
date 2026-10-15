import json
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from redis.exceptions import RedisError

from .agent import run_agent
from .engine import investigate, repair_plan
from .models import Investigation, Replay
from .store import LOCK, Store

logger = logging.getLogger("chronos")


def database():
    try:
        store = Store()
        store.seed()
        return store
    except (RedisError, OSError):
        raise HTTPException(
            503,
            "FalkorDB is unavailable. Start the project database with docker compose up -d.",
        )


app = FastAPI(title="ChronosGraph", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/api/health")
def health():
    try:
        store = database()
        revision = store.revision()
        connected = True
    except HTTPException:
        revision = None
        connected = False
    return dict(
        database="FalkorDB",
        connected=connected,
        revision=revision,
        gemini_configured=bool(os.getenv("GEMINI_API_KEY")),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
        dataset="NovaPay · synthetic company",
        supported_scope="Payment worker minimum_backoff_ms",
    )


@app.get("/api/graph")
def graph():
    with LOCK:
        return database().snapshot()


@app.post("/api/investigate")
def run(request: Investigation):
    start = time.perf_counter()
    with LOCK:
        store = database()
        receipt = investigate(store, request)
    if request.use_gemini:
        try:
            with LOCK:
                if store.revision() != receipt["revision"]:
                    raise ValueError(
                        "Company knowledge changed. Rerun the investigation."
                    )
                summary, trace, elapsed = run_agent(store, request, receipt)
                receipt.update(
                    agent_summary=summary,
                    trace=receipt["trace"] + trace,
                    model_ms=elapsed,
                    mode="gemini_agent",
                )
        except Exception:
            # Provider errors may contain request details; do not log or return raw errors.
            receipt["agent_error"] = (
                "Gemini could not complete the investigation. Check the configured key, model access, and quota. The verified graph checks below are still available."
            )
    receipt["total_ms"] = round((time.perf_counter() - start) * 1000, 2)
    with LOCK:
        receipt["stale"] = store.revision() != receipt["revision"]
        store.upsert(receipt)
        store.write(
            "MATCH (r:Receipt {id:$id}) SET r.stale=$stale",
            dict(id=receipt["id"], stale=receipt["stale"]),
        )
    return receipt


@app.post("/api/events/replay")
def replay(request: Replay):
    return database().event(request.event)


@app.get("/api/receipts")
def receipts():
    with LOCK:
        return database().receipts()


@app.post("/api/receipts/{id}/repair")
def repair(id: str):
    with LOCK:
        store = database()
        receipt = store.receipt(id)
        if not receipt:
            raise HTTPException(404, "Investigation not found")
        if receipt["stale"]:
            raise HTTPException(
                409,
                "This receipt is stale. Rerun the investigation before preparing work.",
            )
        action = store.get("action-" + id)
        if action:
            return action
        action = repair_plan(store, receipt)
        store.upsert(action)
        store.link(id, "PROPOSES", action["id"])
        return action


@app.post("/api/actions/{id}/approve")
def approve(id: str):
    with LOCK:
        store = database()
        action = store.get(id)
        if not action or action["kind"] != "Action":
            raise HTTPException(404, "Draft not found")
        receipt = store.receipt(action["receipt_id"])
        if not receipt or receipt["stale"]:
            raise HTTPException(
                409, "Evidence has changed; investigate again before approval."
            )
        action["status"] = "approved_in_app"
        store.upsert(action)
        return action


@app.post("/api/rehearse")
def rehearse(request: Investigation):
    with LOCK:
        store = database()
        base_revision = store.revision()
        baseline = request.model_copy(update={"partner": "all"})
        before = investigate(store, baseline, persist=False)
        scenario = store.copy_scenario()
        try:
            # Model the narrower proposal: preserve Partner A's verified minimum,
            # and evaluate the requested delay for Partner B. No policy is changed.
            alternatives = []
            for partner in ["a", "b"]:
                minimum = next(
                    (
                        c["minimum_ms"]
                        for c in before["checks"]
                        if c["partner"] == partner
                    ),
                    None,
                )
                chosen = (
                    minimum
                    if partner == "a" and minimum is not None
                    else request.proposed_ms
                )
                change_id = "scenario-change-" + partner
                scenario.upsert(
                    dict(
                        id=change_id,
                        kind="Change",
                        title="Rehearsed Partner " + partner.upper() + " retry delay",
                        partner=partner,
                        proposed_ms=chosen,
                    )
                )
                scenario.link(change_id, "MODIFIES", "file-worker")
                proposed = scenario.get(change_id)
                sub = request.model_copy(
                    update={
                        "partner": partner,
                        "proposed_ms": proposed["proposed_ms"],
                        "use_gemini": False,
                    }
                )
                alternatives.extend(investigate(scenario, sub, persist=False)["checks"])
            revision_unchanged = store.revision() == base_revision
            return dict(
                before=before["checks"],
                alternative=alternatives,
                base_unchanged=revision_unchanged,
                revision=base_revision,
                method="FalkorDB graph copy; partner-scoped proposal",
                assumptions=[
                    "Preserve the verified Partner A minimum; apply the proposed delay to Partner B.",
                    "Only modeled retry constraints are checked. Dependencies do not predict outages.",
                ],
            )
        finally:
            scenario.graph.delete()
