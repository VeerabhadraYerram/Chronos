"""Real FalkorDB integration tests for the independently modeled logistics demo."""

import uuid
import pytest
from fastapi.testclient import TestClient
from chronos.app import app
from chronos.company.store import CompanyStore
from chronos.company.api import Query
from chronos.company.engine import (
    scenario_answer as answer,
    evaluate,
    simulate,
    prepare,
)


@pytest.fixture(scope="module")
def base():
    store = CompanyStore("chronos_reference_test_base_" + uuid.uuid4().hex)
    store.seed()
    yield store
    store.graph.delete()


@pytest.fixture
def store(base):
    name = "chronos_reference_test_" + uuid.uuid4().hex
    base.copy_to(name)
    store = CompanyStore(name)
    yield store
    store.graph.delete()


def query(**changes):
    defaults = dict(
        question="Can we close the Bengaluru facility on Sundays?",
        effective_at="2026-11-08T12:00:00Z",
        known_at="2026-10-16T12:00:00Z",
    )
    defaults.update(changes)
    return Query(session_id="a" * 32, **defaults)


def test_operational_dataset_is_real_connected_graph(store):
    stats = store.stats()
    assert stats["labels"]["Shipment"] == 1410
    assert stats["labels"]["ScanEvent"] == 5430
    assert stats["labels"]["Client"] == 3
    assert stats["labels"]["Facility"] == 8
    assert stats["connections"] > 9000
    assert sum(n["count"] for n in store.operational_sample()) == 1200
    rows = store.read(
        "MATCH (s:Shipment)-[:ON_MANIFEST]->(:Manifest)-[:USES_ROUTE]->(:Route)-[:ORIGIN]->(f:Facility) MATCH (s)-[:AT]->(same:Facility) WHERE f.id<>same.id RETURN count(s)"
    )
    assert rows[0][0] == 0


def test_closure_conflict_is_scoped_to_havells(store):
    r = answer(store, query())
    assert r["assessment"] == "conflict"
    assert [(c["client"], c["sunday_required"]) for c in r["checks"]] == [
        ("havells", True),
        ("sugar", False),
        ("hpcl", False),
    ]
    assert len(r["graph"]["nodes"]) <= 7
    assert "source-havells-agreement" in {s["id"] for s in r["sources"]}


def test_real_relationship_required_not_payload_only(store):
    store.write('MATCH (:Client {id:"havells"})-[r:HAS_COMMITMENT]->(:Rule) DELETE r')
    result = evaluate(store, query().effective_at, query().known_at)
    assert result["checks"][0]["status"] == "insufficient_evidence"


def test_suggestion_does_not_override_accepted_agreement(store):
    proposal = store.get("decision-proposal")
    assert proposal["approved"] is False
    assert answer(store, query())["assessment"] == "conflict"


def test_amendment_changes_only_havells_after_effective_boundary(store):
    store.replay("amendment")
    before = answer(store, query(effective_at="2026-10-31T23:59:59Z"))
    after = answer(store, query(effective_at="2026-11-01T00:00:00Z"))
    assert before["assessment"] == "conflict"
    assert after["assessment"] == "no_known_conflict"
    assert before["checks"][1:] == after["checks"][1:]


def test_recorded_time_preserves_original_belief(store):
    store.replay("amendment")
    then = answer(store, query(known_at="2026-10-14T12:00:00Z"))
    now = answer(store, query(known_at="2026-10-16T12:00:00Z"))
    assert then["checks"][0]["sunday_required"] is True
    assert now["checks"][0]["sunday_required"] is False
    assert "source-amendment" not in {s["id"] for s in then["sources"]}


def test_withdrawn_evidence_yields_unknown_not_permission(store):
    store.replay("withdraw")
    r = answer(store, query())
    assert r["assessment"] == "insufficient_evidence"
    assert r["checks"][0]["sunday_required"] is None
    assert "source-havells-agreement" not in {s["id"] for s in r["sources"]}


def test_scoped_graph_copy_comparison_cleans_up_and_preserves_base(store):
    graphs = set(store.db.list_graphs())
    revision = store.revision()
    result = simulate(store, query())
    assert result["base_unchanged"]
    assert result["rows"][0]["before"] == "Sunday processing"
    assert result["rows"][0]["after"] == "Monday queue"
    assert result["rows"][0]["alternative"] == "Sunday processing"
    assert sum(r["queued_after"] for r in result["rows"]) == 1200
    assert sum(r["queued_alternative"] for r in result["rows"]) == 800
    assert store.revision() == revision
    assert set(store.db.list_graphs()) == graphs


def test_amended_comparison_and_cost_are_from_graph(store):
    store.replay("amendment")
    cost = store.get("source-finance")
    cost["full_shift_inr"] = 21000
    store.upsert(cost)
    result = simulate(store, query())
    assert result["assessment"] == "no_known_conflict"
    assert result["cost"]["before_inr"] == 21000
    assert result["cost"]["alternative_inr"] == 0
    assert all(r["alternative"] == "Monday queue" for r in result["rows"])


def test_before_and_after_do_not_invent_missing_requirements(store):
    store.replay("withdraw")
    result = simulate(store, query())
    assert result["rows"][0]["alternative"] == "Review evidence first"
    assert result["cost"]["alternative_inr"] is None


def test_replay_is_idempotent_and_invalidates_receipts(store):
    r = answer(store, query())
    first = store.replay("amendment")
    second = store.replay("amendment")
    assert first["applied"] and not second["applied"]
    assert first["revision"] == second["revision"]
    assert store.receipt(r["id"])["stale"]
    with pytest.raises(RuntimeError):
        prepare(store, r["id"])


def test_why_requires_recorded_reason_relationship(store):
    q = query(
        question="Why did we promise Sunday processing to Havells?",
        focus_id="rule-havells-original",
    )
    first = answer(store, q)
    assert "source-campaign" in {n["id"] for n in first["graph"]["nodes"]}
    assert "campaign" in first["summary"].lower()
    store.write(
        'MATCH (:Decision)-[r:EXPLAINED_BY]->(:Source {id:"source-campaign"}) DELETE r'
    )
    assert "do not establish" in answer(store, q)["summary"]


def test_unknown_question_and_search_injection_do_not_change_graph(store):
    revision = store.revision()
    r = answer(store, query(question="zzqxx nonexistent confidential"))
    assert "could not find evidence" in r["summary"]
    store.search("'; MATCH (n) DETACH DELETE n //")
    assert store.revision() == revision
    assert store.stats()["labels"]["Shipment"] == 1410


def test_read_tools_cannot_write(store):
    with pytest.raises(Exception):
        store.read('CREATE (:Forbidden {id:"write-test"})')
    assert not store.read("MATCH (n:Forbidden) RETURN n")


def test_contextual_exploration_and_packet(store):
    graph = store.neighborhood("rule-havells-original")
    assert {"havells", "source-havells-agreement", "team-accounts"}.issubset(
        {n["id"] for n in graph["nodes"]}
    )
    assert any(e["source_ids"] for e in graph["edges"])
    r = answer(store, query(focus_id="rule-havells-original"))
    packet = prepare(store, r["id"])
    assert "synthetic" in packet["markdown"].lower()
    assert "Account Management" in packet["markdown"]


def test_api_uses_real_session_store_and_validates_scope(store, monkeypatch):
    import chronos.company.api as module

    monkeypatch.setattr(module, "safe_store", lambda id: store)
    client = TestClient(app)
    response = client.post(
        "/api/company/ask",
        json={"session_id": "a" * 32, "question": "Can we close Sundays?"},
    )
    assert response.status_code == 200
    assert response.json()["assessment"] == "not_assessed"
    assert response.json()["intent"] == "company_investigation"
    assert response.json()["sources"]
    assert client.post("/api/company/simulate", json={"session_id": "a" * 32}).json()[
        "base_unchanged"
    ]
    assert (
        client.post(
            "/api/company/events",
            json={"session_id": "a" * 32, "event": "arbitrary-write"},
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/company/ask", json={"session_id": "a" * 32, "known_at": "2026-10-16"}
        ).status_code
        == 422
    )


def test_session_changes_are_isolated(base, store):
    other_name = "chronos_reference_test_" + uuid.uuid4().hex
    base.copy_to(other_name)
    other = CompanyStore(other_name)
    try:
        store.replay("amendment")
        assert answer(store, query())["assessment"] == "no_known_conflict"
        assert answer(other, query())["assessment"] == "conflict"
        assert other.revision() == 1
    finally:
        other.graph.delete()


def test_exact_shipment_search_and_scan_exploration(store):
    records = store.search("DEMO-AWB-000001")
    assert records[0]["id"] == "shipment-0001"
    graph = store.record_graph("shipment-0001")
    assert sum(n["kind"] == "ScanEvent" for n in graph["nodes"]) == 4
    assert any(n["id"] == "sugar" for n in graph["nodes"])


def test_other_facility_policy_is_not_invented(store):
    r = answer(store, query(question="Can we close the Mumbai facility on Sundays?"))
    assert r["assessment"] == "not_assessed"
    assert "only for Bengaluru" in r["summary"]


def test_answer_graph_respects_knowledge_cutoff(store):
    store.replay("amendment")
    r = answer(store, query(known_at="2026-10-14T12:00:00Z", focus_id="havells"))
    assert "source-amendment" not in {n["id"] for n in r["graph"]["nodes"]}
    assert "recorded October 15" not in r["summary"]


def test_provider_fallback_uses_same_verified_context(store, monkeypatch):
    from chronos.company import agent
    from chronos.company.providers import ProviderUnavailable

    calls = []
    monkeypatch.setenv("GEMINI_API_KEY", "test-placeholder-not-a-real-key")
    monkeypatch.setenv("GROQ_API_KEY", "test-placeholder-not-a-real-key")

    def provider(store, request, receipt, provider):
        calls.append(provider)
        if provider == "groq":
            raise ProviderUnavailable("groq", 503)
        assert receipt["assessment"] == "conflict"
        return dict(summary=receipt["summary"], mode="gemini_agent", provider="gemini")

    monkeypatch.setattr(agent, "investigate", provider)
    r = answer(store, query(use_gemini=True))
    assert r["mode"] == "gemini_agent"
    assert r["assessment"] == "conflict"
    assert calls == ["groq", "gemini"]
    answer(store, query(use_gemini=True))
    assert calls == ["groq", "gemini", "groq", "gemini"]


def test_simulation_reads_operating_configuration_from_graph(store):
    policy = store.operating_policy()
    policy["sunday_clients"] = []
    store.upsert(policy)
    result = simulate(store, query())
    assert all(row["before"] == "Monday queue" for row in result["rows"])
    assert result["assessment"] == "conflict"


def test_amended_commitment_flags_graph_connected_handbook(store):
    store.replay("amendment")
    r = answer(store, query())
    assert r["documents_to_review"][0]["id"] == "policy-schedule"
    store.write("MATCH (:Policy)-[r:APPLIES_AT]->(:Facility) DELETE r")
    assert answer(store, query())["documents_to_review"] == []


@pytest.mark.parametrize(
    "question",
    [
        "Who owns the Bengaluru facility?",
        "What are the Sunday staffing costs?",
        "How many Sunday consignments are recorded?",
        "Why did we promise Sunday processing to Havells?",
    ],
)
def test_information_queries_do_not_inherit_closure_warning(store, question):
    r = answer(store, query(question=question))
    assert r["assessment"] == "conflict"  # Audit check is retained, not a UI verdict.
    assert "commitment_conflict" not in {a["category"] for a in r["alerts"]}
    if not r["commitment_context"]:
        assert r["documents_to_review"] == []


def test_alerts_follow_actual_commitments_and_document_relationships(store):
    original = answer(store, query())
    alert = next(
        a for a in original["alerts"] if a["category"] == "commitment_conflict"
    )
    assert alert["source_ids"] == ["source-havells-agreement"]
    store.replay("amendment")
    amended = answer(store, query())
    assert {a["category"] for a in amended["alerts"]} == {
        "no_modeled_conflict",
        "document_outdated",
    }
    owner = answer(store, query(question="Who owns the Bengaluru facility?"))
    assert owner["alerts"] == []
    assert owner["documents_to_review"] == []


def test_scope_and_withdrawal_alerts_do_not_report_false_permission(store):
    outside = answer(store, query(question="Can we close Mumbai on Sundays?"))
    assert [a["category"] for a in outside["alerts"]] == ["outside_scope"]
    assert not outside["commitment_context"]
    store.replay("withdraw")
    missing = answer(store, query())
    assert [a["category"] for a in missing["alerts"]] == ["evidence_incomplete"]


def test_ai_failure_is_separate_from_company_policy_alerts(store, monkeypatch):
    from chronos.company import agent

    def unavailable(*args):
        raise RuntimeError("private upstream detail must never appear")

    monkeypatch.setattr(agent, "run_investigator", unavailable)
    r = answer(
        store, query(question="Who owns the Bengaluru facility?", use_gemini=True)
    )
    assert [a["category"] for a in r["alerts"]] == ["investigator_unavailable"]
    assert "private upstream detail" not in str(r["alerts"])


def test_focused_applicability_followup_keeps_document_alert_relevant(store):
    store.replay("amendment")
    rule = answer(store, query())["checks"][0]["rule_ids"][0]
    r = answer(store, query(question="Does this still apply?", focus_id=rule))
    assert r["commitment_context"]
    assert [a["category"] for a in r["alerts"]] == ["document_outdated"]
