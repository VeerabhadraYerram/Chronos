"""Company-wide investigation over retrieved records, not a scenario answer script."""

import json
import re
import time
import uuid
from datetime import datetime, timezone

from .repository import CompanyReader, PRIVATE
from .timeutil import canonical
from ..store import LOCK


def usable(n, request, store=None):
    if n["kind"] in PRIVATE:
        return False
    if n["kind"] == "Source":
        return bool(n.get("enabled")) and canonical(n["timestamp"]) <= canonical(
            request.known_at
        )
    if n["kind"] in {"Rule", "Claim"}:
        applicable = (
            n.get("status") == ("accepted" if n["kind"] == "Rule" else "documented")
            and canonical(n["valid_from"]) <= canonical(request.effective_at)
            and (
                not n["valid_to"]
                or canonical(request.effective_at) < canonical(n["valid_to"])
            )
            and canonical(n["recorded_from"]) <= canonical(request.known_at)
            and (
                not n["recorded_to"]
                or canonical(request.known_at) < canonical(n["recorded_to"])
            )
        )
        if applicable and store:
            return bool(
                store.read(
                    "MATCH (:Entity {id:$id})-[:SUPPORTED_BY]->(s:Source) WHERE s.enabled=true AND toString(s.timestamp)<=$known RETURN s.id LIMIT 1",
                    dict(id=n["id"], known=canonical(request.known_at)),
                )
            )
        return applicable
    return True


def label_terms(label):
    name = re.sub(r"(?<!^)(?=[A-Z])", " ", label).lower()
    plural = (
        name[:-1] + "ies"
        if name.endswith("y")
        else name + "es"
        if name.endswith(("s", "x"))
        else name + "s"
    )
    return [name, plural, name.replace(" ", ""), plural.replace(" ", "")]


def calculation_graph(store, request, aggregate):
    """A small proof set from the exact filtered database calculation."""
    sample = [store.get(id) for id in aggregate.get("sample_ids", [])]
    sample = [n for n in sample if n and usable(n, request, store)]
    related = {n["id"]: n for n in sample}
    neighbors, participation, candidate_edges = {}, {}, []
    for n in sample:
        local = store.record_graph(n["id"])
        linked = set()
        candidate_edges.extend(local["edges"])
        for edge in local["edges"]:
            if n["id"] in {edge["source"], edge["target"]}:
                linked.add(
                    edge["target"] if edge["source"] == n["id"] else edge["source"]
                )
        for other in local["nodes"]:
            if other["id"] in linked and usable(other, request, store):
                neighbors[other["id"]] = other
                participation.setdefault(other["id"], set()).add(n["id"])
    # Shared anchors explain a set; unrelated one-off context obscures the count.
    for id, other in neighbors.items():
        if len(participation[id]) > 1 or other["kind"] == "Source":
            related.setdefault(id, other)
    proof_ids = {
        id
        for edge in candidate_edges
        if edge["source"] in related and edge["target"] in related
        for id in edge["source_ids"]
    }
    for id in sorted(proof_ids)[:2]:
        source = store.get(id)
        if source and source["kind"] == "Source" and usable(source, request, store):
            related.setdefault(id, source)
    return store.subgraph(list(related.values()))


def answer(store, request):
    start = time.perf_counter()
    revision_at_start = store.revision()
    reader = CompanyReader(store)
    found = reader.search(request.question, request.known_at)
    focus = store.get(request.focus_id) if request.focus_id else None
    if focus and focus["kind"] in PRIVATE:
        focus = None
    if focus:
        found = [focus] + [n for n in found if n["id"] != focus["id"]]
    # Client scope is an entity ID from the data, not a hard-coded company enum.
    scope = store.get(request.client) if request.client != "all" else None
    if scope:
        found = [
            n
            for n in found
            if n["id"] == scope["id"] or n.get("client") in (None, scope["id"])
        ]
    found = [n for n in found if usable(n, request, store)]
    nodes = {n["id"]: n for n in found[:5]}
    evidence = {}
    for root in found[:3]:
        graph = store.record_graph(root["id"])
        for n in graph["nodes"]:
            if usable(n, request, store) and len(nodes) < 16:
                nodes.setdefault(n["id"], n)
        for e in graph["edges"]:
            for source_id in e["source_ids"]:
                source = store.get(source_id)
                if (
                    source
                    and source["kind"] == "Source"
                    and usable(source, request, store)
                ):
                    evidence[source_id] = source
    relevant_ids = [n["id"] for n in found[:8]]
    rules = (
        reader.rules(request.effective_at, request.known_at, relevant_ids)
        if relevant_ids
        else []
    )
    for pair in rules[:4]:
        nodes[pair["rule"]["id"]] = pair["rule"]
        evidence[pair["source"]["id"]] = pair["source"]
    document_mismatches = []

    def scope_key(n):
        return (
            n.get("subject_id") or n.get("client"),
            n.get("facility"),
            n.get("field"),
        )

    for item in reader.claims(request.effective_at, request.known_at) if rules else []:
        applicable = [
            pair
            for pair in rules
            if scope_key(pair["rule"]) == scope_key(item["claim"])
        ]
        values = {
            json.dumps(pair["rule"].get("value"), sort_keys=True) for pair in applicable
        }
        if (
            len(values) == 1
            and json.dumps(item["claim"].get("value"), sort_keys=True) not in values
        ):
            document_mismatches.append(item)
            for key in ("policy", "claim", "source"):
                nodes[item[key]["id"]] = item[key]
            evidence[item["source"]["id"]] = item["source"]
    evidence.update({n["id"]: n for n in nodes.values() if n["kind"] == "Source"})
    # Cite only sources that can be included in the displayed graph.
    for n in list(evidence.values())[:8]:
        nodes[n["id"]] = n
    graph = store.subgraph(list(nodes.values())[:24])
    sources = [n for n in graph["nodes"] if n["kind"] == "Source"]
    alerts = [
        dict(
            category="document_outdated",
            severity="warning",
            title="Document disagrees with accepted policy",
            message=item["policy"]["title"]
            + " asserts a different value for "
            + item["claim"]["field"]
            + " than the retrieved accepted rule for the same subject and dates. Review the document; its assertion does not change policy.",
            source_ids=[item["source"]["id"]],
        )
        for item in document_mismatches
    ]
    q = request.question.lower()
    owners = []
    primary = (
        focus
        if focus and usable(focus, request, store)
        else next((n for n in found if n["kind"] not in {"Source", "Team"}), None)
    )
    for n in [primary] if primary else []:
        owners.extend(dict(record=n, **o) for o in store.owners(n["id"]))
    aggregate = None
    if re.search(
        r"\b(count|how many|number of|total|sum|average|mean|minimum|maximum)\b", q
    ):
        labels = store.read(
            "MATCH (n:Entity) WHERE NOT n.kind IN $private RETURN DISTINCT n.kind",
            dict(private=sorted(PRIVATE)),
        )
        matches = [
            r[0]
            for r in labels
            if any(
                re.search(r"\b" + re.escape(term) + r"\b", q)
                for term in label_terms(r[0])
            )
        ]
        # Company is the workspace organization; Client represents counterparties.
        # Resolve the everyday phrase using actual observed labels, never client names/counts.
        if (
            matches == ["Company"]
            and re.search(r"\b(dealing|clients|customers|working with)\b", q)
            and any(r[0] == "Client" for r in labels)
        ):
            matches = ["Client"]
        # Only calculate an unqualified dataset total here. Qualified questions
        # (e.g. overdue invoices, a city, OR conditions) need model-selected reads.
        if len(matches) == 1:
            grammar = set(
                "how many count number of what is are do does we have our the a an total sum average mean minimum maximum amount cost price revenue value inr in recorded stored records record there currently dealing working with graph dataset workspace".split()
            )
            label_words = {
                word for term in label_terms(matches[0]) for word in term.split()
            }
            if matches[0] == "Client":
                label_words.update(
                    {
                        "company",
                        "companies",
                        "client",
                        "clients",
                        "customer",
                        "customers",
                    }
                )
            if set(re.findall(r"[a-z]+", q)) - grammar - label_words:
                matches = []
        if len(matches) == 1:
            label = matches[0]
            metric = "count"
            field = ""
            if not re.search(r"\b(count|how many|number of)\b", q):
                observed = reader.catalog()
                data = next(
                    item for item in observed["labels"] if item["label"] == label
                )
                numeric = [
                    key
                    for key, types in data["fields"].items()
                    if types == ["number"] and key in data["native_fields"]
                ]
                scores = {
                    key: sum(token in q for token in key.lower().split("_"))
                    for key in numeric
                }
                candidates = [
                    key
                    for key in numeric
                    if scores[key] > 0
                    and scores[key] == max(scores.values(), default=0)
                ]
                if len(candidates) == 1:
                    field = candidates[0]
                    metric = (
                        "avg"
                        if re.search(r"\b(average|mean)\b", q)
                        else "min"
                        if "minimum" in q
                        else "max"
                        if "maximum" in q
                        else "sum"
                    )
            if metric != "count" or not re.search(
                r"\b(sum|average|mean|minimum|maximum|amount|cost|price|revenue)\b", q
            ):
                aggregate = reader.aggregate(
                    label,
                    filters={"client": scope["id"]}
                    if scope
                    and store.read(
                        "MATCH (n:Entity) WHERE n.kind=$kind AND n.client IS NOT NULL RETURN count(n)",
                        dict(kind=label),
                    )[0][0]
                    else None,
                    metric=metric,
                    field=field,
                    known=request.known_at,
                    effective=request.effective_at,
                )
    if aggregate:
        # Show actual record examples and their real connections behind the calculation.
        graph = calculation_graph(store, request, aggregate)
        sources = [n for n in graph["nodes"] if n["kind"] == "Source"]
        if aggregate["metric"] == "count":
            summary = f"The stored graph contains {sum(g['count'] for g in aggregate['groups']):,} {aggregate['label']} records. This is a dataset count, not a live forecast."
        else:
            result = aggregate["groups"][0]["result"] if aggregate["groups"] else None
            summary = (
                f"Database calculation for {aggregate['label']}: {aggregate['metric']}({aggregate['field']}) = {result:,}. This uses stored numeric values, not a forecast."
                if result is not None
                else "No matching numeric records were found for this calculation."
            )
    elif re.search(r"\b(who|owner|owns|responsible)\b", q) and owners:
        summary = (
            "Recorded responsibility: "
            + "; ".join(
                o["record"]["title"] + " → " + o["team"]["title"] for o in owners[:5]
            )
            + ". These are the current stored relationships; historical ownership is not reconstructed."
        )
    elif not found:
        summary = "No supporting records were retrieved for this question. Add relevant company evidence or clarify a record, department or subject. ChronosGraph cannot establish facts that are absent from this workspace."
        alerts.append(
            dict(
                category="evidence_missing",
                severity="info",
                title="Supporting evidence missing",
                message="No matching company records were retrieved. This is not a negative policy verdict.",
                source_ids=[],
            )
        )
    else:
        summaries = []
        for n in found[:3]:
            if n.get("excerpt"):
                summaries.append(n["title"] + ": " + n["excerpt"][:650])
            elif n.get("description"):
                summaries.append(n["title"] + ": " + n["description"][:350])
            else:
                fields = {
                    k: v
                    for k, v in n.items()
                    if k not in {"id", "kind", "title", "synthetic", "content_hash"}
                    and isinstance(v, (str, int, float, bool))
                }
                summaries.append(
                    n["title"] + ": " + json.dumps(fields, ensure_ascii=False)
                )
        summary = (
            "Retrieved evidence: "
            + "\n\n".join(summaries)
            + "\n\nGraph retrieval mode shows stored facts and excerpts. It does not infer an operational approval. Enable the AI investigator for a question-specific synthesis."
        )
    groups = {}
    for pair in rules:
        r = pair["rule"]
        key = (r.get("subject_id") or r.get("client"), r.get("facility"), r["field"])
        groups.setdefault(key, []).append(pair)
    for key, pairs in groups.items():
        if len({json.dumps(p["rule"].get("value"), sort_keys=True) for p in pairs}) > 1:
            alerts.append(
                dict(
                    category="policy_conflict",
                    severity="warning",
                    title="Conflicting accepted policies",
                    message=f"Retrieved accepted rules disagree on {key[-1]} for the same stored scope and dates. Human review is required.",
                    source_ids=sorted({p["source"]["id"] for p in pairs}),
                )
            )
    stale_focus = request.focus_id and (not focus or not usable(focus, request, store))
    if stale_focus:
        alerts.append(
            dict(
                category="source_unavailable",
                severity="warning",
                title="Selected evidence unavailable",
                message="This record is withdrawn, outside the selected time window, or unavailable to the investigator.",
                source_ids=[],
            )
        )
    receipt = dict(
        id="company-receipt-" + uuid.uuid4().hex,
        kind="Receipt",
        title=request.question,
        domain="company",
        created_at=datetime.now(timezone.utc).isoformat(),
        request=request.model_dump(),
        assessment="not_assessed",
        checks=[],
        summary=summary,
        sources=sources,
        graph=graph,
        revision=revision_at_start,
        stale=False,
        mode="graph_search",
        intent="company_investigation",
        commitment_context=False,
        documents_to_review=[],
        alerts=alerts,
        aggregates=[aggregate] if aggregate else [],
        trace=[
            dict(tool="search_company_records", rows=len(found)),
            dict(tool="read_applicable_rules", rows=len(rules)),
        ],
        followups=["What evidence supports " + n["title"] + "?" for n in found[:3]],
        limits=[
            "Answers are bounded by available company evidence; source citation membership is not semantic proof.",
            "Current ownership and topology are not historical snapshots.",
        ],
    )
    if aggregate:
        receipt["trace"].append(
            dict(tool="aggregate_records", rows=len(aggregate["groups"]))
        )
    if request.use_gemini:
        try:
            from .agent import run_investigator

            addition = run_investigator(store, request, receipt)
            receipt.update(addition)
            if addition.get("graph", {}).get("nodes") or addition.get("aggregates"):
                alerts[:] = [a for a in alerts if a["category"] != "evidence_missing"]
        except Exception:
            receipt["summary"] = (
                "No AI answer was generated. The configured AI providers could not complete this investigation. The retrieved records below remain available for inspection; retry the question."
            )
            receipt["mode"] = "ai_unavailable"
            receipt["agent_error"] = (
                "The AI investigator could not complete this run. Retrieved graph evidence is retained."
            )
        if receipt.get("provider_note"):
            alerts.append(
                dict(
                    category="provider_fallback",
                    severity="info",
                    title="Backup AI provider used",
                    message=receipt["provider_note"],
                    source_ids=[],
                )
            )
        if receipt.get("agent_error"):
            alerts.append(
                dict(
                    category="investigator_unavailable",
                    severity="warning",
                    title="AI investigator unavailable",
                    message=receipt["agent_error"],
                    source_ids=[],
                )
            )
    receipt["total_ms"] = round((time.perf_counter() - start) * 1000, 2)
    with LOCK:
        receipt["stale"] = store.revision() != revision_at_start
        store.upsert(receipt)
        store.write(
            "MATCH (r:Receipt {id:$id}) SET r.stale=$stale",
            dict(id=receipt["id"], stale=receipt["stale"]),
        )
        for source in receipt["sources"]:
            store.link_evidence(receipt["id"], "USED", source["id"], [source["id"]])
    return receipt
