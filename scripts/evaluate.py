"""Reproduce the fictional business scenario in disposable real FalkorDB graphs.

Run from the repository root with PYTHONPATH=backend. This does not call Gemini.
"""

import json
import sys
import uuid

from chronos.engine import investigate
from chronos.models import Investigation
from chronos.store import Store


def evaluate():
    results = []
    store = Store("chronos_audit_" + uuid.uuid4().hex)
    created = False

    def check(name, actual, expected):
        matched = actual == expected
        results.append({"check": name, "passed": matched})
        if not matched:
            raise AssertionError(f"Business scenario failed: {name}")

    def assess(target=store, **scope):
        return investigate(target, Investigation(use_gemini=False, **scope))

    try:
        # Mark creation before seeding so partial fixture creation can be cleaned up.
        created = True
        store.seed()
        original = assess()
        check("Initial global removal conflicts", original["assessment"], "conflict")
        check(
            "Preserving 250 ms meets the modeled minimum",
            assess(proposed_ms=250)["assessment"],
            "no_known_conflict",
        )

        scenario = store.copy_scenario()
        try:
            scenario.event("migration")
            check(
                "Copied graph applies B migration",
                assess(scenario, partner="b")["checks"][0]["minimum_ms"],
                0,
            )
            check(
                "Base graph remains at B 250 ms",
                assess(partner="b")["checks"][0]["minimum_ms"],
                250,
            )
        finally:
            scenario.graph.delete()

        store.event("migration")
        updated = assess()
        check(
            "Migration preserves partner scope",
            [c["minimum_ms"] for c in updated["checks"]],
            [250, 0],
        )
        check(
            "Runbook conflict is scoped to B",
            [c["partner"] for c in updated["conflicts"]],
            ["b"],
        )
        check(
            "Prior receipt becomes stale", store.receipt(original["id"])["stale"], True
        )
        check(
            "October 11 as known then",
            assess(
                partner="b",
                effective_at="2026-10-11T12:00:00Z",
                known_at="2026-10-11T12:00:00Z",
            )["checks"][0]["minimum_ms"],
            250,
        )
        check(
            "October 11 with later knowledge",
            assess(
                partner="b",
                effective_at="2026-10-11T12:00:00Z",
                known_at="2026-10-15T12:00:00Z",
            )["checks"][0]["minimum_ms"],
            0,
        )
        revision = store.revision()
        replay = store.event("migration")
        check(
            "Duplicate event does not change revision",
            (replay["applied"], store.revision()),
            (False, revision),
        )
        store.event("proposal")
        check(
            "Unapproved proposal does not replace A policy",
            assess(partner="a")["checks"][0]["minimum_ms"],
            250,
        )
        store.event("withdraw-evidence")
        check(
            "Withdrawn source requires abstention for A",
            assess(partner="a")["assessment"],
            "insufficient_evidence",
        )
    finally:
        if created and store.name in store.db.list_graphs():
            store.graph.delete()

    return {
        "database": "FalkorDB",
        "gemini_calls": 0,
        "checks": results,
        "passed": len(results),
        "temporary_graphs_cleaned_up": True,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(evaluate(), indent=2))
    except Exception as error:
        # Connection/provider exceptions can contain configuration details.
        print(
            json.dumps(
                {
                    "passed": False,
                    "error_type": type(error).__name__,
                    "help": "Start FalkorDB and install the pinned dependencies; see docs/EVALUATION.md.",
                }
            ),
            file=sys.stderr,
        )
        raise SystemExit(1)
