"""Integration checks require the real local FalkorDB container, never a graph mock."""

import uuid

import pytest
from fastapi.testclient import TestClient

from chronos.engine import investigate
from chronos.models import Investigation
from chronos.store import Store


@pytest.fixture
def store():
    s = Store("chronos_test_" + uuid.uuid4().hex)
    s.seed()
    yield s
    s.graph.delete()


def assess(store, **kwargs):
    return investigate(store, Investigation(**kwargs))


def test_original_global_removal_conflicts(store):
    r = assess(store)
    assert r["assessment"] == "conflict"
    assert [c["minimum_ms"] for c in r["checks"]] == [250, 250]
    assert {s["id"] for s in r["sources"]} == {"source-incident"}
    assert r["graph"]["edges"]


def test_preserving_minimum_has_no_modeled_conflict(store):
    assert assess(store, proposed_ms=250)["assessment"] == "no_known_conflict"


def test_migration_only_changes_partner_b(store):
    store.event("migration")
    r = assess(store)
    assert r["checks"][0]["status"] == "conflict"
    assert r["checks"][1]["status"] == "no_known_conflict"


def test_effective_time_before_migration_keeps_original_requirement(store):
    store.event("migration")
    assert (
        assess(store, partner="b", effective_at="2026-10-09T12:00:00Z")["checks"][0][
            "minimum_ms"
        ]
        == 250
    )


def test_late_evidence_does_not_rewrite_what_was_known(store):
    store.event("migration")
    then = assess(
        store,
        partner="b",
        effective_at="2026-10-11T12:00:00Z",
        known_at="2026-10-11T12:00:00Z",
    )
    retrospective = assess(
        store,
        partner="b",
        effective_at="2026-10-11T12:00:00Z",
        known_at="2026-10-15T12:00:00Z",
    )
    assert then["checks"][0]["minimum_ms"] == 250
    assert retrospective["checks"][0]["minimum_ms"] == 0


def test_half_open_valid_interval_boundary(store):
    store.event("migration")
    r = assess(store, partner="b", effective_at="2026-10-10T00:00:00Z")
    assert r["checks"][0]["minimum_ms"] == 0


def test_document_conflict_is_scoped_to_migrated_partner(store):
    store.event("migration")
    r = assess(store)
    assert len(r["conflicts"]) == 1
    assert r["conflicts"][0]["partner"] == "b"
    assert r["conflicts"][0]["source_id"] == "source-runbook"


def test_chat_proposal_cannot_override_accepted_policy(store):
    store.event("proposal")
    assert assess(store)["assessment"] == "conflict"
    assert store.get("proposal-retry")["approved"] is False


def test_withdrawn_evidence_forces_abstention(store):
    store.event("withdraw-evidence")
    r = assess(store)
    assert r["assessment"] == "insufficient_evidence"
    assert r["sources"] == []


def test_event_replay_is_idempotent(store):
    assert store.event("migration")["applied"] is True
    revision = store.revision()
    assert store.event("migration")["applied"] is False
    assert store.revision() == revision


def test_receipt_survives_new_client_and_is_invalidated(store):
    r = assess(store)
    assert Store(store.name).receipt(r["id"])["assessment"] == "conflict"
    store.event("migration")
    assert Store(store.name).receipt(r["id"])["stale"] is True


def test_graph_copy_is_independent(store):
    scenario = store.copy_scenario()
    try:
        scenario.event("migration")
        assert assess(scenario, partner="b")["assessment"] == "no_known_conflict"
        assert assess(store, partner="b")["assessment"] == "conflict"
        assert store.revision() == 1
    finally:
        scenario.graph.delete()


def test_unknown_time_and_missing_relationship_abstain(store):
    assert (
        assess(store, effective_at="2026-01-01T00:00:00Z")["assessment"]
        == "insufficient_evidence"
    )
    store.write(
        'MATCH (:Decision)-[r:HAS_VERSION]->(:FactVersion {id:"fact-a-original"}) DELETE r'
    )
    assert assess(store, partner="a")["assessment"] == "insufficient_evidence"


def test_api_approval_idempotency_and_stale_block(store, monkeypatch):
    from chronos import app

    monkeypatch.setattr(app, "database", lambda: store)
    client = TestClient(app.app)
    receipt = client.post("/api/investigate", json={"use_gemini": False}).json()
    action = client.post(f"/api/receipts/{receipt['id']}/repair", json={}).json()
    assert (
        client.post(f"/api/actions/{action['id']}/approve", json={}).json()["status"]
        == "approved_in_app"
    )
    assert (
        client.post(f"/api/actions/{action['id']}/approve", json={}).json()["id"]
        == action["id"]
    )
    store.event("migration")
    assert (
        client.post(f"/api/actions/{action['id']}/approve", json={}).status_code == 409
    )


def test_api_rehearsal_preserves_base(store, monkeypatch):
    from chronos import app

    monkeypatch.setattr(app, "database", lambda: store)
    client = TestClient(app.app)
    response = client.post("/api/rehearse", json={})
    assert response.status_code == 200
    data = response.json()
    assert data["base_unchanged"]
    assert data["alternative"][0]["proposed_ms"] == 250
    assert data["alternative"][1]["status"] == "conflict"
    assert store.revision() == 1


def test_validation_rejects_invalid_scope_and_unzoned_date(store):
    with pytest.raises(ValueError):
        Investigation(partner="other")
    with pytest.raises(ValueError):
        Investigation(known_at="2026-10-11")
    with pytest.raises(ValueError):
        Investigation(proposed_ms=-1)
