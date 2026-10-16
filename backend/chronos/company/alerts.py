"""Display alerts from verified results, scoped to the current investigation.

These rules do not decide policy; FalkorDB commitment checks do. Unknown language
does not imply that a proposed action was checked or approved.
"""

import re


def commitment_context(question, intent, focus=None):
    q = question.lower()
    sunday = bool(re.search(r"\b(sundays?|weekends?)\b", q))
    closure = bool(re.search(r"\b(close|closing|closure|closed|shut|stop)\b", q))
    if intent in {"owners", "cost"}:
        return False
    if (
        focus
        and focus.get("kind") in {"Rule", "Policy"}
        and intent in {"history", "why", "closure"}
    ):
        return True
    return (sunday and intent in {"closure", "history", "why"}) or (
        closure and intent != "search"
    )


def investigation_alerts(receipt, relevant, evidence_gap=False):
    alerts = []

    def add(category, severity, title, message, source_ids=None):
        alerts.append(
            dict(
                category=category,
                severity=severity,
                title=title,
                message=message,
                source_ids=source_ids or [],
            )
        )

    if receipt["assessment"] == "not_assessed":
        add(
            "outside_scope",
            "info",
            "Outside modeled scope",
            "Accepted Sunday commitments are modeled only for Bengaluru. This question has no supported closure verdict.",
        )
    else:
        if relevant:
            closure_question = bool(
                re.search(
                    r"\b(close|closing|closure|closed|shut|stop)\b",
                    receipt["title"],
                    re.I,
                )
            )
            checks = receipt["checks"]
            conflicts = [c for c in checks if c["status"] == "conflict"]
            missing = [c for c in checks if c["sunday_required"] is None]
            # A known conflict and a separate evidence gap may both matter.
            if conflicts and closure_question:
                add(
                    "commitment_conflict",
                    "warning",
                    "Commitment conflict",
                    "Full Sunday closure conflicts with the applicable commitment for "
                    + ", ".join(c["title"] for c in conflicts)
                    + ".",
                    sorted({s for c in conflicts for s in c["source_ids"]}),
                )
            if missing:
                add(
                    "evidence_incomplete",
                    "warning",
                    "Evidence incomplete",
                    "A supported commitment is missing or ambiguous for "
                    + ", ".join(c["title"] for c in missing)
                    + ". Missing evidence is not permission to close.",
                )
            # Do not label an ordinary history/why question as an approved proposal.
            if not conflicts and not missing and closure_question:
                add(
                    "no_modeled_conflict",
                    "success",
                    "No modeled conflict",
                    "No Sunday commitment conflict was found for the selected clients and dates. Other operating requirements still need review.",
                )
            if receipt["documents_to_review"]:
                add(
                    "document_outdated",
                    "warning",
                    "Operating document needs review",
                    "The handbook still schedules Sunday processing that the applicable Havells amendment no longer requires.",
                    [d["source_id"] for d in receipt["documents_to_review"]],
                )
        if evidence_gap:
            add(
                "answer_evidence_gap",
                "info",
                "Answer evidence missing",
                "The retrieved records do not establish the requested fact. Inspect a source or clarify the question.",
            )
    if receipt.get("provider_note"):
        add(
            "provider_fallback",
            "info",
            "Backup AI provider used",
            receipt["provider_note"],
        )
    if receipt.get("agent_error"):
        add(
            "investigator_unavailable",
            "warning",
            "AI investigator unavailable",
            receipt["agent_error"],
        )
    return alerts
