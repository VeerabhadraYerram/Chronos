"""Real-DB transparency, constraints, and cross-domain investigation checks."""

import json
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ResponseError

from chronos.app import app
from chronos.company.api import Query
from chronos.company.importer import import_workspace
from chronos.company.investigation import answer
from chronos.company.repository import CompanyReader
from chronos.company.store import CompanyStore, SESSION_PREFIX

PACK = Path(__file__).resolve().parents[2] / "datasets/atlas-studio.json"


@pytest.fixture(scope="module")
def reference():
    s = CompanyStore("chronos_inspection_test_" + uuid.uuid4().hex)
    s.seed()
    yield s
    s.graph.delete()


@pytest.fixture
def atlas():
    id = import_workspace(json.loads(PACK.read_text()))
    s = CompanyStore(SESSION_PREFIX + id)
    yield s, id
    s.graph.delete()


def q(id, question, **extra):
    return Query(session_id=id, question=question, use_gemini=False, **extra)


def test_enforced_ids_and_mandatory_fields(reference):
    constraints = reference.graph.list_constraints()
    assert {c["type"] for c in constraints} == {"UNIQUE", "MANDATORY"}
    assert all(c["status"] == "OPERATIONAL" for c in constraints)
    with pytest.raises(ResponseError):
        reference.write(
            'CREATE (:Entity {id:"havells",kind:"Client",title:"Duplicate",payload:"{}"})'
        )
    with pytest.raises(ResponseError):
        reference.write(
            'CREATE (:Entity {id:"bad-required",title:"Missing kind",payload:"{}"})'
        )
    assert reference.get("havells")["title"] == "Havells India"


def test_catalog_pagination_and_complete_native_record(reference):
    r = CompanyReader(reference)
    c = r.catalog()
    assert c["records"] == 6155  # Includes Metadata; excludes private registry.
    assert (
        next(item for item in c["labels"] if item["label"] == "ScanEvent")["count"]
        == 4800
    )
    assert c["indexes"] and c["metadata"]["schema_version"] == 4
    assert not any(
        field in {"valid_from", "recorded_from", "arrival_at", "event_at", "timestamp"}
        for index in c["indexes"]
        for field in index["properties"]
    )
    first = r.rows("ScanEvent", limit=100)
    last = r.rows("ScanEvent", offset=4700, limit=100)
    assert first["total"] == last["total"] == 4800
    assert len(first["rows"]) == len(last["rows"]) == 100
    assert not {n["id"] for n in first["rows"]} & {n["id"] for n in last["rows"]}
    native = r.record("shipment-0000")["properties"]
    assert native["client"] == "havells" and native["status"] == "received_at_facility"
    assert r.rows("Shipment", query="' OR 1=1 DELETE n")["total"] == 0


def test_registry_cannot_reveal_other_workspace_capabilities(reference):
    reference.upsert(
        dict(id="session-private-test", kind="DemoSession", title="Registry entry")
    )
    reader = CompanyReader(reference)
    try:
        assert reader.rows("DemoSession")["total"] == 0
        assert not any(
            item["label"] == "DemoSession" for item in reader.catalog()["labels"]
        )
        with pytest.raises(Exception) as error:
            reader.record("session-private-test")
        assert error.value.status_code == 404
    finally:
        reference.write('MATCH (n:DemoSession {id:"session-private-test"}) DELETE n')


def test_snapshot_export_is_complete_and_read_only(atlas):
    s, id = atlas
    reader = CompanyReader(s)
    before = s.stats()
    export = reader.export()
    assert len(export["nodes"]) == len(json.loads(PACK.read_text())["nodes"]) + 1
    assert len(export["relationships"]) == len(
        json.loads(PACK.read_text())["relationships"]
    )
    assert len(export["content_sha256"]) == 64
    assert s.stats() == before
    edges = reader.edges(record_id="campaign-spring", limit=1)
    assert edges["total"] == 2 and len(edges["rows"]) == 1


def test_audit_detects_real_missing_relationship(atlas):
    s, id = atlas
    r = CompanyReader(s)
    assert r.audit()["passed"]
    s.write("MATCH (:Rule)-[r:SUPPORTED_BY]->(:Source) DELETE r")
    check = next(
        c for c in r.audit()["checks"] if c["name"] == "Rules have source relationships"
    )
    assert check["violations"] == 1 and not check["passed"]


def test_migration_preserves_facts_and_is_idempotent(atlas):
    s, id = atlas
    before = s.get("rule-expense-limit")
    revision = s.revision()
    s.write("MATCH (m:Metadata) SET m.schema_version=0")
    s.ensure_schema()
    s.ensure_schema()
    assert s.get("rule-expense-limit") == before
    assert s.revision() == revision
    assert all(c["status"] == "OPERATIONAL" for c in s.graph.list_constraints())


def test_unrelated_finance_and_marketing_questions_use_actual_data(atlas):
    s, id = atlas
    owner = answer(
        s, q(id, "Who owns the Spring launch campaign?", focus_id="campaign-spring")
    )
    assert "Marketing" in owner["summary"]
    assert all(
        w not in owner["summary"]
        for w in ("Sunday", "Bengaluru", "Havells", "Delhivery")
    )
    policy = answer(s, q(id, "What is the Finance approval threshold?"))
    assert "10000" in policy["summary"]
    assert "source-expenses" in {n["id"] for n in policy["sources"]}
    assert policy["assessment"] == "not_assessed" and policy["checks"] == []
    assert any(a["category"] == "document_outdated" for a in policy["alerts"])
    claim = s.get("claim-old-threshold")
    claim["value"] = 10000
    s.upsert(claim)
    assert not any(
        a["category"] == "document_outdated"
        for a in answer(s, q(id, "What is the Finance approval threshold?"))["alerts"]
    )
    assert any(n["id"] == "rule-expense-limit" for n in policy["graph"]["nodes"])
    count = answer(s, q(id, "How many invoices are recorded?"))
    assert count["aggregates"][0]["groups"] == [dict(value="Invoice", count=2)]
    summed = answer(s, q(id, "What is the total invoice amount in INR?"))
    assert summed["aggregates"][0]["metric"] == "sum"
    assert "32,500" in summed["summary"]
    assert CompanyReader(s).aggregate("Invoice", metric="sum", field="amount_inr")[
        "groups"
    ] == [dict(value="Invoice", result=32500)]
    assert CompanyReader(s).aggregate("Invoice", "department")["groups"] == [
        dict(value="Marketing", count=2)
    ]


def test_imported_record_changes_answer_without_changing_engine(atlas):
    s, id = atlas
    s.upsert(dict(id="team-design", kind="Team", title="Design", synthetic=True))
    s.write('MATCH (:Campaign {id:"campaign-spring"})-[r:OWNED_BY]->(:Team) DELETE r')
    s.link_evidence("campaign-spring", "OWNED_BY", "team-design", ["source-brand"])
    result = answer(
        s, q(id, "Who owns the Spring launch campaign?", focus_id="campaign-spring")
    )
    assert "Design" in result["summary"] and "→ Marketing" not in result["summary"]


def test_absent_and_withdrawn_evidence_does_not_get_canned_answer(atlas):
    s, id = atlas
    missing = answer(s, q(id, "What is our quantum satellite timetable?"))
    assert any(a["category"] == "evidence_missing" for a in missing["alerts"])
    source = s.get("source-expenses")
    source["enabled"] = False
    s.upsert(source)
    result = answer(s, q(id, "What is the Finance approval threshold?"))
    assert "source-expenses" not in {n["id"] for n in result["sources"]}
    assert "rule-expense-limit" not in {n["id"] for n in result["graph"]["nodes"]}
    assert not CompanyReader(s).rules(
        q(id, "test").effective_at, q(id, "test").known_at
    )


def test_inspection_http_limits_isolation_and_assets(atlas):
    s, id = atlas
    client = TestClient(app)
    assert client.get("/database").status_code == 200
    assert (
        "default-src 'none'"
        in client.get("/database").headers["content-security-policy"]
    )
    assert client.get("/database/assets/unknown").status_code == 404
    data = client.post(
        "/api/database/rows", json=dict(session_id=id, label="Invoice", limit=1)
    ).json()
    assert data["total"] == 2 and len(data["rows"]) == 1
    assert (
        client.post(
            "/api/database/rows", json=dict(session_id=id, limit=101)
        ).status_code
        == 422
    )
    assert (
        client.post("/api/database/rows", json=dict(session_id="../other")).status_code
        == 422
    )
    assert (
        client.post("/api/database/write", json=dict(session_id=id)).status_code == 404
    )
    assert (
        client.post(
            "/api/database/record", json=dict(session_id=id, record_id="havells")
        ).status_code
        == 404
    )
    response = client.post("/api/company/session", json=dict(session_id=id)).json()
    assert response["company"]["title"] == "Atlas Studio" and response["demo"] is None
    assert (
        client.post("/api/company/simulate", json=dict(session_id=id)).status_code
        == 422
    )


def test_import_rejects_dangling_evidence_before_writing():
    data = json.loads(PACK.read_text())
    data["relationships"][0]["target"] = "missing"
    with pytest.raises(ValueError, match="endpoints"):
        import_workspace(data)


def test_reference_extension_preserves_history_and_invalidates_receipts(reference):
    from chronos.company.demo import upgrade_reference_records

    name = "chronos_extension_test_" + uuid.uuid4().hex
    reference.copy_to(name)
    store = CompanyStore(name)
    try:
        store.write('MATCH (n:Claim {id:"claim-current-schedule"}) DETACH DELETE n')
        receipt = answer(
            store,
            q(
                "a" * 32,
                "Who owns the Bengaluru facility?",
                focus_id="facility-bengaluru",
            ),
        )
        revision = store.revision()
        upgrade_reference_records(store)
        assert store.get(receipt["id"])["summary"] == receipt["summary"]
        assert store.receipt(receipt["id"])["stale"]
        assert store.revision() == revision + 1
        upgrade_reference_records(store)
        assert store.revision() == revision + 1
        assert store.get("claim-current-schedule")["value"] is True
    finally:
        store.graph.delete()


def test_fractional_recorded_boundary_is_preserved(atlas):
    s, id = atlas
    source = s.get("source-expenses")
    source["timestamp"] = "2026-01-01T09:00:00.500000Z"
    s.upsert(source)
    before = q(
        id,
        "What is the Finance approval threshold?",
        known_at="2026-01-01T09:00:00.499999Z",
    )
    after = q(
        id,
        "What is the Finance approval threshold?",
        known_at="2026-01-01T09:00:00.500000Z",
    )
    assert before.known_at.endswith(".499999Z")
    r = CompanyReader(s)
    assert not r.rules(before.effective_at, before.known_at)
    assert len(r.rules(after.effective_at, after.known_at)) == 1
    assert "source-expenses" not in {n["id"] for n in answer(s, before)["sources"]}
