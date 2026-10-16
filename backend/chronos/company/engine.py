"""Graph-derived commitments and scheduling previews. No frontend verdicts."""

import json
import time
import uuid
from datetime import datetime, timedelta, timezone

from .seed import CLIENTS
from .alerts import commitment_context, investigation_alerts


def evaluate(store, effective, known, client="all", close=True):
    started = time.perf_counter()
    rows = store.commitments(effective, known, client)
    checks = []
    for id, title, _ in CLIENTS:
        if client not in ("all", id):
            continue
        selected = [
            r for r in rows if r["client"]["id"] == id and r["source"].get("enabled")
        ]
        values = {r["rule"]["value"] for r in selected}
        requirement = next(iter(values)) if len(values) == 1 else None
        status = (
            "insufficient_evidence"
            if requirement is None
            else "conflict"
            if close and requirement
            else "no_known_conflict"
        )
        checks.append(
            dict(
                client=id,
                title=title,
                sunday_required=requirement,
                status=status,
                rule_ids=[r["rule"]["id"] for r in selected],
                source_ids=[r["source"]["id"] for r in selected],
            )
        )
    assessment = (
        "conflict"
        if any(c["status"] == "conflict" for c in checks)
        else "insufficient_evidence"
        if any(c["status"] == "insufficient_evidence" for c in checks)
        else "no_known_conflict"
    )
    return dict(
        checks=checks,
        assessment=assessment,
        rows=rows,
        ms=round((time.perf_counter() - started) * 1000, 2),
    )


def useful_graph(
    store,
    checks,
    focus=None,
    mode="answer",
    search_nodes=None,
    known="2026-10-16T12:00:00Z",
):
    def visible(n):
        return n["kind"] != "Source" or (
            n.get("enabled") and n.get("timestamp", "") <= known
        )

    proof_nodes = {}
    if mode == "why":
        rule_ids = [id for c in checks for id in c["rule_ids"]]
        proof = store.read(
            "MATCH (r:Rule)-[:WHY]->(d:Decision)-[:EXPLAINED_BY]->(s:Source) WHERE r.id IN $ids RETURN d.payload,s.payload LIMIT 8",
            dict(ids=rule_ids),
        )
        for decision, source in proof:
            for raw in [decision, source]:
                node = json.loads(raw)
                if visible(node):
                    proof_nodes[node["id"]] = node
    if focus:
        graph = store.record_graph(focus)
        # Historical/future commitments remain discoverable in explicit exploration,
        # but an answer graph only displays the rules used for this assessment.
        active = {id for c in checks for id in c["rule_ids"]}
        nodes = [
            n
            for n in graph["nodes"]
            if visible(n) and (n["kind"] != "Rule" or n["id"] in active)
        ]
        if nodes:
            combined = {n["id"]: n for n in nodes}
            combined.update(proof_nodes)
            return store.subgraph(list(combined.values()))
    chosen = next(
        (c for c in checks if c["status"] == "conflict"), checks[0] if checks else None
    )
    ids = {"facility-bengaluru"}
    if chosen:
        ids.add(chosen["client"])
        ids.update(chosen["rule_ids"])
        ids.update(chosen["source_ids"])
        ids.add("team-accounts")
    ids.update(proof_nodes)
    if search_nodes and mode == "search":
        ids.update(n["id"] for n in search_nodes[:6])
    nodes = [n for id in ids if (n := store.get(id)) and visible(n)]
    return store.subgraph(nodes)


def infer_intent(question):
    q = question.lower()
    if any(w in q for w in ["why", "reason", "campaign"]):
        return "why"
    if any(w in q for w in ["who", "owner", "department", "responsib", "review"]):
        return "owners"
    if any(w in q for w in ["cost", "saving", "finance", "expens"]):
        return "cost"
    if any(
        w in q
        for w in [
            "shipment",
            "parcel",
            "consignment",
            "how many",
            "pickup",
            "manifest",
            "scan",
        ]
    ):
        return "operations"
    if any(
        w in q
        for w in [
            "when",
            "still",
            "amend",
            "current",
            "old",
            "changed",
            "agreement",
            "applicab",
        ]
    ):
        return "history"
    if any(w in q for w in ["sunday", "close", "closure", "stop", "weekend", "open"]):
        return "closure"
    return "search"


def scenario_answer(store, request):
    start = time.perf_counter()
    client = request.client
    focus = store.get(request.focus_id) if request.focus_id else None
    if focus and focus.get("client") in {"havells", "sugar", "hpcl"}:
        client = focus["client"]
    if focus and focus["kind"] == "Client":
        client = focus["id"]
    q = request.question.lower()
    named = [id for id, title, _ in CLIENTS if id in q or title.lower() in q]
    if len(named) == 1:
        client = named[0]
    request = request.model_copy(update={"client": client})
    result = evaluate(store, request.effective_at, request.known_at, client)
    intent = infer_intent(q)
    relevant_commitments = commitment_context(q, intent, focus)
    evidence_gap = False
    sources = {r["source"]["id"]: r["source"] for r in result["rows"]}
    search = store.search(request.question)
    for n in search:
        if n["kind"] == "Source":
            sources[n["id"]] = n
    for id in ["source-owners", "source-schedule", "source-dispatch"]:
        sources[id] = store.get(id)
    if intent == "why":
        sources["source-campaign"] = store.get("source-campaign")
    if intent == "cost":
        sources["source-finance"] = store.get("source-finance")
    graph = useful_graph(
        store, result["checks"], request.focus_id, intent, search, request.known_at
    )
    available = [
        s
        for s in sources.values()
        if s and s.get("enabled") and s.get("timestamp", "") <= request.known_at
    ]
    source_ids = {s["id"] for s in available}
    required = [c["title"] for c in result["checks"] if c["sunday_required"] is True]
    missing = [c["title"] for c in result["checks"] if c["sunday_required"] is None]
    if intent == "why":
        # A motive is evidence only if the graph still links the decision to it.
        reason = store.read(
            'MATCH (r:Rule)-[:WHY]->(:Decision)-[:EXPLAINED_BY]->(s:Source {id:"source-campaign"}) WHERE r.id IN $ids RETURN s.payload LIMIT 1',
            dict(ids=[id for c in result["checks"] for id in c["rule_ids"]]),
        )
        if (
            client in ("all", "havells")
            and reason
            and "source-campaign" in source_ids
            and (
                not focus
                or focus["kind"]
                in {"Rule", "Client", "Facility", "Decision", "Campaign"}
                or focus["id"] == "source-campaign"
            )
        ):
            summary = (
                "The recorded reason comes from the synthetic Sales handover: "
                + json.loads(reason[0][0])["excerpt"]
            )
        else:
            evidence_gap = True
            summary = "The retrieved records do not establish a recorded reason for this selection. A processing schedule alone does not explain why it was agreed."
    elif intent == "owners":
        owners = store.owners(request.focus_id or "facility-bengaluru")
        if owners:
            summary = (
                "Recorded owner: "
                + ", ".join(o["team"]["title"] for o in owners)
                + ". The responsibility matrix assigns client amendments to Account Management, staffing assumptions to Finance, and dispatch updates to Transport. These are demo roles, not named real employees."
            )
        else:
            evidence_gap = True
            summary = "No direct owner relationship was retrieved for the selected item. The demo responsibility matrix identifies Operations for facility hours and Account Management for client amendments; this does not prove ownership of every record."
    elif intent == "cost":
        cost = store.get("source-finance")
        summary = f"The synthetic Finance sheet assumes INR {cost['full_shift_inr']:,} for a full Sunday shift and INR {cost['restricted_shift_inr']:,} for a Havells-only shift. Full closure removes that modeled shift cost; a retained exception does not. These are scenario assumptions, not measured savings or a full financial forecast."
    elif intent == "operations":
        counts = store.operational_sample(client)
        summary = (
            "The Sunday fixture contains "
            + ", ".join(f"{r['count']:,} {r['title']} consignments" for r in counts)
            + " at Bengaluru. Their pickup requests, manifests, lanes and scan records are stored in FalkorDB. Closure queues them for Monday processing; it does not establish a delivery date."
        )
    elif intent == "search":
        relevant = [
            n for n in search if n["kind"] not in {"Facility", "Team", "Company"}
        ]
        evidence_gap = not relevant
        summary = (
            (
                "I found related records: "
                + "; ".join(n["title"] for n in relevant[:4])
                + ". Select a record to inspect its evidence, or ask about its commitment, owner, dates or processing impact."
            )
            if relevant
            else "I could not find evidence for that question in this demo workspace. It models Bengaluru Sunday processing, client commitments, departments and sample consignments. Please clarify the client or record; I will not invent a company fact."
        )
    else:
        if missing:
            summary = (
                "Evidence is incomplete for "
                + ", ".join(missing)
                + ". Do not treat a missing requirement as permission to close."
            )
        elif required:
            summary = (
                "Closing Bengaluru for every selected client conflicts with the active Sunday-processing commitment for "
                + ", ".join(required)
                + ". A campaign ending or a chat suggestion does not remove an accepted commitment."
            )
        else:
            summary = "No Sunday-processing conflict was found in the selected clients' supported demo agreements for these dates. Closure would queue Sunday consignments for Monday. Other operating requirements still need review."
        if (amended := store.get("source-amendment")) and amended[
            "timestamp"
        ] <= request.known_at:
            summary += " The approved demo amendment has separate effective and recorded dates; both control whether it applies."
    if request.focus_id:
        focus = store.get(request.focus_id)
        if (
            focus
            and focus["kind"] == "Source"
            and focus.get("enabled")
            and focus.get("timestamp", "") <= request.known_at
        ):
            summary = "Selected source: " + focus["title"] + ". " + summary
            if focus["id"] not in source_ids:
                available.append(focus)
    unsupported_cities = [
        city
        for city in [
            "Mumbai",
            "Delhi",
            "Chennai",
            "Hyderabad",
            "Pune",
            "Kolkata",
            "Ahmedabad",
        ]
        if city.lower() in q
    ]
    supported_scope = not unsupported_cities
    if not supported_scope:
        summary = (
            "The workspace includes demo facility records for "
            + ", ".join(unsupported_cities)
            + ", but accepted Sunday commitments and scheduling previews are implemented only for Bengaluru. I cannot determine another facility's closure policy from Bengaluru evidence."
        )
    documents = []
    havells = next((c for c in result["checks"] if c["client"] == "havells"), None)
    for doc in store.documents():
        if (
            supported_scope
            and relevant_commitments
            and havells
            and havells["sunday_required"] is False
            and "havells" in doc["policy"].get("sunday_clients", [])
        ):
            documents.append(
                dict(
                    id=doc["policy"]["id"],
                    title=doc["policy"]["title"],
                    source_id=doc["source"]["id"],
                    reason="The current handbook still schedules Havells on Sundays; the applicable amended commitment no longer requires it.",
                )
            )
    receipt = dict(
        id="company-receipt-" + uuid.uuid4().hex,
        kind="Receipt",
        title=request.question,
        domain="company",
        created_at=datetime.now(timezone.utc).isoformat(),
        request=request.model_dump(),
        assessment=result["assessment"] if supported_scope else "not_assessed",
        checks=result["checks"],
        summary=summary,
        sources=available,
        graph=graph,
        revision=store.revision(),
        stale=False,
        mode="graph_search",
        intent=intent,
        commitment_context=relevant_commitments and supported_scope,
        documents_to_review=documents,
        trace=[
            dict(
                tool="read_applicable_commitments",
                rows=len(result["rows"]),
                ms=result["ms"],
            ),
            dict(tool="search_company_records", rows=len(search)),
        ],
        followups=[
            "Why did we promise Sunday processing to Havells?",
            "Who must review a Sunday closure?",
            "What happens to the Sunday consignments?",
        ],
        limits=[
            "Synthetic operational records and agreements; not Delhivery's private system.",
            "Only accepted, supported commitments determine the scheduling check. Ownership and topology are current demo relationships.",
        ],
    )
    if request.use_gemini:
        try:
            from .agent import run_investigator

            addition = run_investigator(store, request, receipt)
            receipt.update(addition)
        except Exception as error:
            receipt["agent_error"] = (
                "The AI investigator is temporarily unavailable (503). Verified graph checks are retained."
                if getattr(error, "code", None) == 503
                else "The AI investigator did not complete this run. Verified graph checks are retained. Check configured provider access and quota locally."
            )
    # Model prose cannot create, remove, or select the deterministic alert categories.
    receipt["alerts"] = investigation_alerts(
        receipt,
        relevant_commitments,
        evidence_gap and supported_scope and receipt["mode"] == "graph_search",
    )
    receipt["total_ms"] = round((time.perf_counter() - start) * 1000, 2)
    store.upsert(receipt)
    store.write("MATCH (r:Receipt {id:$id}) SET r.stale=false", dict(id=receipt["id"]))
    for s in receipt["sources"]:
        store.link_evidence(receipt["id"], "USED", s["id"], [s["id"]])
    return receipt


def simulate(store, request):
    """Read a real graph copy; remove only this disposable scenario in finally."""
    base_revision = store.revision()
    trial = store.copy_scenario()
    try:
        dt = datetime.fromisoformat(request.effective_at.replace("Z", "+00:00"))
        sunday = dt + timedelta(days=(6 - dt.weekday()) % 7)
        effective = sunday.strftime("%Y-%m-%dT12:00:00Z")
        check = evaluate(
            trial, effective, request.known_at, "all", request.close_sunday
        )
        trial.upsert(
            dict(
                id="trial-calendar",
                kind="Policy",
                title="Proposed Sunday calendar",
                sunday_open=not request.close_sunday,
                synthetic=True,
            )
        )
        trial.link_evidence(
            "trial-calendar", "APPLIES_AT", "facility-bengaluru", ["source-dispatch"]
        )
        policy = trial.get("trial-calendar")
        counts = trial.operational_sample()
        rows = []
        operating = trial.operating_policy()
        for c in check["checks"]:
            count = next((n["count"] for n in counts if n["client"] == c["client"]), 0)
            current_open = (
                c["client"] in operating["sunday_clients"]
            )  # Current configuration, not historical replay.
            proposed_open = policy["sunday_open"]
            scoped_open = (
                None
                if c["sunday_required"] is None
                else proposed_open or c["sunday_required"]
            )
            rows.append(
                dict(
                    **c,
                    consignments=count,
                    before="Sunday processing" if current_open else "Monday queue",
                    after="Sunday processing" if proposed_open else "Monday queue",
                    alternative="Review evidence first"
                    if scoped_open is None
                    else "Sunday processing"
                    if scoped_open
                    else "Monday queue",
                    queued_before=0 if current_open else count,
                    queued_after=0 if proposed_open else count,
                    queued_alternative=None
                    if scoped_open is None
                    else 0
                    if scoped_open
                    else count,
                )
            )
        cost = trial.get("source-finance")
        return dict(
            assessment=check["assessment"],
            rows=rows,
            scenario_sunday=effective[:10],
            known_at=request.known_at,
            revision=base_revision,
            base_unchanged=store.revision() == base_revision,
            method="Real FalkorDB graph copy; explicit processing-calendar rules",
            cost=dict(
                before_inr=cost["full_shift_inr"],
                proposed_inr=0 if request.close_sunday else cost["full_shift_inr"],
                alternative_inr=None
                if any(c["sunday_required"] is None for c in check["checks"])
                else cost["restricted_shift_inr"]
                if request.close_sunday
                and any(c["sunday_required"] for c in check["checks"])
                else 0
                if request.close_sunday
                else cost["full_shift_inr"],
                source_id=cost["id"],
            ),
            documents_to_review=[d["policy"]["id"] for d in trial.documents()],
            assumptions=[
                "The 1,200 synthetic Sunday-arrival records are replayed on the scenario Sunday; they are not live forecasts.",
                "Before means the current demo handbook configuration, not a historically reconstructed schedule.",
                "Queuing for Monday processing does not predict final delivery, vehicle capacity or customer reaction.",
                "Costs are fixture assumptions only; no staffing, transport or financial systems are changed.",
            ],
        )
    finally:
        trial.graph.delete()


def prepare(store, receipt_id):
    r = store.receipt(receipt_id)
    if not r or r.get("domain") != "company":
        raise ValueError("Investigation not found")
    if r["stale"] or r["revision"] != store.revision():
        raise RuntimeError(
            "Knowledge changed. Rerun the investigation before preparing work."
        )
    owners = store.read(
        "MATCH (n:Entity)-[:OWNED_BY|OPERATED_BY]->(t:Team) WHERE n.id IN $ids RETURN DISTINCT t.title ORDER BY t.title",
        dict(ids=[n["id"] for n in r["graph"]["nodes"]]),
    )
    reviewers = [row[0] for row in owners]
    lines = [
        "# Company evidence · review packet",
        "",
        "Draft based on the selected company evidence. Inspect source classifications and limitations before acting.",
        "",
        r["summary"],
        "",
        f"Effective: {r['request']['effective_at']}",
        f"Known by: {r['request']['known_at']}",
        f"Knowledge revision: {r['revision']}",
        "",
        "## Data classification",
        "Includes synthetic records."
        if any(n.get("synthetic") for n in r["sources"])
        else "Inspect each source classification.",
        "",
        "## Review scope",
        r["title"],
        "Confirm the evidence, applicability dates, recorded owners and any missing facts before authorizing a change.",
        "",
        "## Recorded owners in retrieved context",
        ", ".join(reviewers)
        if reviewers
        else "No owner relationship retrieved; assign a reviewer explicitly.",
        "Current relationships only; this is not a historical ownership reconstruction or authorization to act.",
        "",
        "## Evidence",
    ]
    lines.extend("- " + s["title"] + " (" + s["id"] + ")" for s in r["sources"])
    lines.extend(
        [
            "",
            "Draft for human review. No real company system, agreement, ticket or schedule has been changed.",
        ]
    )
    action = dict(
        id="company-action-" + receipt_id,
        kind="Action",
        title="Evidence review: " + r["title"],
        receipt_id=receipt_id,
        revision=r["revision"],
        status="draft",
        markdown="\n".join(lines),
        reviewer=", ".join(reviewers)
        if reviewers
        else "Human reviewer; ownership unconfirmed",
        synthetic=True,
    )
    store.upsert(action)
    store.link_evidence(receipt_id, "PROPOSES", action["id"])
    return action
