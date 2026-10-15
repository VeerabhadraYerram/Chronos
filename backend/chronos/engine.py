"""Deterministic evidence checks. Gemini may investigate, but cannot override them."""

import time
import uuid
from datetime import datetime, timezone

from .models import Investigation


def investigate(store, request: Investigation, persist=True):
    started = time.perf_counter()
    trace = []
    sources = {}
    checks = []
    conflicts = []
    fact_ids = []
    path_nodes = {"file-worker", "system-payments", "decision-retry"}
    for partner in ["a", "b"] if request.partner == "all" else [request.partner]:
        t = time.perf_counter()
        rows = store.facts(partner, request.effective_at, request.known_at)
        trace.append(
            dict(
                tool="find_applicable_constraints",
                scope=partner,
                ms=round((time.perf_counter() - t) * 1000, 2),
                rows=len(rows),
            )
        )
        supported = [r for r in rows if r["source"].get("enabled")]
        for row in supported:
            sources[row["source"]["id"]] = row["source"]
            fact_ids.append(row["fact"]["id"])
            path_nodes.update(
                [row["fact"]["id"], row["source"]["id"], "commitment-" + partner]
            )
        values = {r["fact"]["value"] for r in supported}
        if len(values) != 1:
            checks.append(
                dict(
                    partner=partner,
                    status="insufficient_evidence",
                    minimum_ms=None,
                    proposed_ms=request.proposed_ms,
                    reason="No single supported, accepted constraint applies to this partner and time.",
                )
            )
        else:
            minimum = next(iter(values))
            checks.append(
                dict(
                    partner=partner,
                    status="conflict"
                    if request.proposed_ms < minimum
                    else "no_known_conflict",
                    minimum_ms=minimum,
                    proposed_ms=request.proposed_ms,
                    reason=f"Proposed {request.proposed_ms} ms; accepted minimum {minimum} ms.",
                )
            )
            for claim in store.claims(partner, request.effective_at, request.known_at):
                if claim["source"].get("enabled") and claim["fact"]["value"] != minimum:
                    sources[claim["source"]["id"]] = claim["source"]
                    conflicts.append(
                        dict(
                            partner=partner,
                            document=claim["source"]["title"],
                            claim_ms=claim["fact"]["value"],
                            accepted_ms=minimum,
                            source_id=claim["source"]["id"],
                            message=f"Runbook says {claim['fact']['value']} ms; accepted Partner {partner.upper()} constraint is {minimum} ms.",
                        )
                    )
                    path_nodes.update(
                        ["doc-retry", claim["fact"]["id"], claim["source"]["id"]]
                    )
    owners = store.owners()
    path_nodes.update(o["id"] for o in owners)
    assessment = (
        "conflict"
        if any(c["status"] == "conflict" for c in checks)
        else (
            "insufficient_evidence"
            if any(c["status"] == "insufficient_evidence" for c in checks)
            else "no_known_conflict"
        )
    )
    gaps = []
    if any(c["status"] == "insufficient_evidence" for c in checks):
        gaps.append(
            "At least one partner lacks a single current, supported accepted requirement. Obtain authoritative evidence before deciding."
        )
    gaps.append(
        "This assessment checks the modeled minimum retry delay only. It does not prove production safety or inspect arbitrary code."
    )
    snapshot = store.snapshot()
    graph_nodes = [n for n in snapshot["nodes"] if n["id"] in path_nodes]
    graph_edges = [
        e
        for e in snapshot["edges"]
        if e["source"] in path_nodes and e["target"] in path_nodes
    ]
    receipt = dict(
        id="receipt-"
        + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        + "-"
        + uuid.uuid4().hex[:8],
        kind="Receipt",
        title=request.question,
        created_at=datetime.now(timezone.utc).isoformat(),
        request=request.model_dump(),
        assessment=assessment,
        checks=checks,
        conflicts=conflicts,
        sources=list(sources.values()),
        owners=owners,
        gaps=gaps,
        trace=trace,
        revision=store.revision(),
        stale=False,
        graph=dict(nodes=graph_nodes, edges=graph_edges),
        fact_ids=fact_ids,
        graph_ms=round((time.perf_counter() - started) * 1000, 2),
        model_ms=0,
        mode="graph_checks",
        agent_summary=None,
    )
    receipt["total_ms"] = round((time.perf_counter() - started) * 1000, 2)
    if persist:
        store.upsert(receipt)
        for id in fact_ids:
            store.link(receipt["id"], "USED", id)
    return receipt


def repair_plan(store, receipt):
    request = receipt["request"]
    lines = [
        "# Proposed payment retry update",
        "",
        f"Investigation: {receipt['id']}",
        f"Company revision: {receipt['revision']}",
        "",
        f"Checked effective time: {request['effective_at']}",
        f"Knowledge cutoff: {request['known_at']}",
        "",
        "## Accepted partner requirements",
    ]
    for c in receipt["checks"]:
        lines.append(
            f"- Partner {c['partner'].upper()}: "
            + (
                f"minimum {c['minimum_ms']} ms."
                if c["minimum_ms"] is not None
                else "evidence incomplete; do not change yet."
            )
        )
    lines += [
        "",
        "## Required work",
        "- Keep partner-specific retry settings; preserve every still-applicable minimum.",
        "- Update the runbook to distinguish partner scopes and effective dates.",
        "- Verify retry behavior against partner-specific tests before deployment.",
        "- Ask the system owner to review evidence gaps and the proposed change.",
        "",
        "## Supporting sources",
    ]
    lines += [f"- {s['id']}: {s['title']}" for s in receipt["sources"]]
    lines += [
        "",
        "Prepared as an in-app draft. No external ticket, PR, or production change has been created.",
    ]
    return dict(
        id="action-" + receipt["id"],
        kind="Action",
        title="Partner-scoped retry repair",
        status="draft",
        receipt_id=receipt["id"],
        reviewer=receipt["owners"][0]["title"] if receipt["owners"] else "Unassigned",
        markdown="\n".join(lines),
    )
