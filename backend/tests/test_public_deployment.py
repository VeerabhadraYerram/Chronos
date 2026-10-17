"""Public entrypoint controls: no external inference or user graph mutation."""

import importlib
from fastapi.testclient import TestClient


def public(tmp_path, **limits):
    from chronos.public import create_app

    (tmp_path / "index.html").write_text("<h1>ChronosGraph</h1>")
    return TestClient(create_app(tmp_path, **limits))


def test_public_entrypoint_excludes_legacy_mutations_and_docs(tmp_path):
    client = public(tmp_path)
    for path in [
        "/api/events/replay",
        "/api/actions/anything/approve",
        "/api/investigate",
    ]:
        assert client.post(path, json={}).status_code in {404, 405}
    assert client.get("/docs").status_code == 404
    root = client.get("/")
    assert root.status_code == 200 and "ChronosGraph" in root.text
    assert "frame-ancestors 'none'" in root.headers["content-security-policy"]
    assert client.get("/healthz").json() == {"status": "running"}
    assert client.get("/database").status_code == 200
    assert (
        client.post("/api/company/session", json={"session_id": "bad"}).status_code
        == 400
    )


def test_public_origin_body_size_and_request_limits(tmp_path):
    client = public(tmp_path, api_per_minute=2, max_body=64)
    assert (
        client.post(
            "/api/company/ask", json={}, headers={"Origin": "https://other.example"}
        ).status_code
        == 403
    )
    assert client.post("/api/company/ask", content="x" * 65).status_code == 413
    assert client.post("/api/company/ask", json={}).status_code == 422
    assert client.post("/api/company/ask", json={}).status_code == 429


def test_ai_hourly_budget_is_global_and_graph_reads_remain_available(tmp_path):
    client = public(tmp_path, ai_per_hour=1)
    # Invalid schema never calls providers, but consumes the conservative admission budget.
    assert client.post("/api/company/ask", json={"use_gemini": True}).status_code == 422
    denied = client.post("/api/company/ask", json={"use_gemini": True})
    assert denied.status_code == 429 and denied.headers["retry-after"] == "3600"
    assert client.post("/api/company/search", json={}).status_code == 422


def test_readiness_requires_database_and_provider(tmp_path, monkeypatch):
    module = importlib.import_module("chronos.public")

    class DB:
        def __init__(self, name):
            pass

        def seed(self):
            raise AssertionError("Readiness must not seed or migrate data")

        def read(self, query):
            return [[4, 4]]

    monkeypatch.setattr(module, "CompanyStore", DB)
    for key in ("GROQ_API_KEY", "GEMINI_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(key, raising=False)
    client = public(tmp_path)
    assert client.get("/readyz").status_code == 503
    monkeypatch.setenv("GROQ_API_KEY", "configured-test-value")
    assert client.get("/readyz").json()["database"] == "FalkorDB"


def test_readiness_does_not_wait_for_workspace_inspection(tmp_path, monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from chronos.store import LOCK

    module = importlib.import_module("chronos.public")

    class DB:
        def __init__(self, name):
            pass

        def read(self, query):
            return [[1, 4]]

    monkeypatch.setattr(module, "CompanyStore", DB)
    monkeypatch.setenv("GROQ_API_KEY", "configured-test-value")
    client = public(tmp_path)
    with ThreadPoolExecutor(max_workers=1) as executor:
        LOCK.acquire()
        try:
            response = executor.submit(client.get, "/readyz").result(timeout=2)
            assert response.status_code == 200
        finally:
            LOCK.release()


def test_session_expiry_is_explicitly_opt_in(tmp_path, monkeypatch):
    from chronos.company.store import expire_evaluation_sessions

    class NoReads:
        def read(self, *args):
            raise AssertionError(
                "Persistent local sessions must not be scanned or removed"
            )

    monkeypatch.delenv("CHRONOS_EPHEMERAL", raising=False)
    expire_evaluation_sessions(NoReads())


def test_expiry_only_removes_registered_temporary_session_graphs(monkeypatch):
    import time
    import uuid
    from chronos.company.store import (
        CompanyStore,
        expire_evaluation_sessions,
        SESSION_PREFIX,
    )

    base = CompanyStore("chronos_expiry_test_" + uuid.uuid4().hex)
    visitor = CompanyStore(SESSION_PREFIX + uuid.uuid4().hex)
    id = visitor.name.removeprefix(SESSION_PREFIX)
    try:
        base.write("CREATE (:Metadata {id:'dataset',revision:1})")
        visitor.write("CREATE (:Metadata {id:'dataset',revision:1})")
        base.upsert(dict(id="company", kind="Company", title="Disposable expiry test"))
        base.upsert(
            dict(id="session-" + id, kind="DemoSession", title="Temporary visitor")
        )
        base.write(
            "MATCH (s:DemoSession) SET s.created=$old", dict(old=time.time() - 7200)
        )
        visitor.upsert(
            dict(id="receipt", kind="Receipt", title="Temporary investigation")
        )
        monkeypatch.delenv("CHRONOS_EPHEMERAL", raising=False)
        expire_evaluation_sessions(base)
        assert visitor.name in base.db.list_graphs()
        monkeypatch.setenv("CHRONOS_EPHEMERAL", "1")
        expire_evaluation_sessions(base)
        assert visitor.name not in base.db.list_graphs()
        assert base.name in base.db.list_graphs()
        assert base.read("MATCH (s:DemoSession) RETURN count(s)")[0][0] == 0
    finally:
        if visitor.name in base.db.list_graphs():
            visitor.graph.delete()
        if base.name in base.db.list_graphs():
            base.graph.delete()
