import json
import os
import re
import threading
from pathlib import Path

from dotenv import load_dotenv
from falkordb import FalkorDB

from .seed import fixture, migration_fixture

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
LOCK = threading.RLock()
KINDS = {
    "System",
    "File",
    "Person",
    "Team",
    "Project",
    "Decision",
    "Ticket",
    "Source",
    "Document",
    "Commitment",
    "FactVersion",
    "Receipt",
    "Action",
    "Event",
    "Change",
}


class Store:
    def __init__(self, graph_name=None):
        self.name = graph_name or os.getenv("FALKOR_GRAPH", "chronos_novapay")
        if not re.fullmatch(r"chronos_[a-zA-Z0-9_]+", self.name):
            raise ValueError("Graph names must use the chronos_ namespace")
        self.db = FalkorDB(
            host=os.getenv("FALKOR_HOST", "127.0.0.1"),
            port=int(os.getenv("FALKOR_PORT", "6389")),
            password=os.getenv("FALKOR_PASSWORD") or None,
            socket_timeout=5,
            socket_connect_timeout=3,
        )
        self.graph = self.db.select_graph(self.name)

    def read(self, query, params=None):
        return self.graph.ro_query(query, params or {}, timeout=2500).result_set

    def write(self, query, params=None):
        return self.graph.query(query, params or {}, timeout=5000).result_set

    def upsert(self, n):
        if n["kind"] not in KINDS:
            raise ValueError("Unknown node type")
        # Label is from the server-owned allowlist; all values are parameters.
        self.write(
            f"MERGE (n:Entity:{n['kind']} {{id:$id}}) SET n.payload=$payload, n.kind=$kind, n.title=$title",
            dict(id=n["id"], payload=json.dumps(n), kind=n["kind"], title=n["title"]),
        )
        if n["kind"] == "FactVersion":
            self.write(
                "MATCH (n:FactVersion {id:$id}) SET n.subject=$subject, n.field=$field, n.partner=$partner, n.status=$status, n.valid_from=$valid_from, n.valid_to=$valid_to, n.recorded_from=$recorded_from, n.recorded_to=$recorded_to",
                {
                    k: n[k]
                    for k in [
                        "id",
                        "subject",
                        "field",
                        "partner",
                        "status",
                        "valid_from",
                        "valid_to",
                        "recorded_from",
                        "recorded_to",
                    ]
                },
            )

    def link(self, a, relation, b):
        if not re.fullmatch("[A-Z_]+", relation):
            raise ValueError("Invalid relationship")
        self.write(
            f"MATCH (a:Entity {{id:$a}}), (b:Entity {{id:$b}}) MERGE (a)-[:{relation}]->(b)",
            dict(a=a, b=b),
        )

    def get(self, id):
        rows = self.read("MATCH (n:Entity {id:$id}) RETURN n.payload", {"id": id})
        return json.loads(rows[0][0]) if rows else None

    def seed(self):
        with LOCK:
            if self.name in self.db.list_graphs() and self.read(
                'MATCH (m:Metadata {id:"dataset"}) RETURN m.revision'
            ):
                return
            nodes, edges = fixture()
            for n in nodes:
                self.upsert(n)
            for e in edges:
                self.link(e["source"], e["relation"], e["target"])
            self.write('CREATE (:Metadata {id:"dataset", revision:1})')

    def revision(self):
        return int(
            self.read('MATCH (m:Metadata {id:"dataset"}) RETURN m.revision')[0][0]
        )

    def bump(self):
        self.write('MATCH (m:Metadata {id:"dataset"}) SET m.revision=m.revision+1')
        # Conservative invalidation: all receipts predate this company revision.
        self.write("MATCH (r:Receipt) SET r.stale=true")

    def snapshot(self):
        rows = self.read(
            'MATCH (n:Entity) WHERE NOT n.kind IN ["Receipt","Action"] RETURN n.payload LIMIT 300'
        )
        nodes = [json.loads(row[0]) for row in rows]
        edges = self.read(
            'MATCH (a:Entity)-[r]->(b:Entity) WHERE NOT a.kind IN ["Receipt","Action"] AND NOT b.kind IN ["Receipt","Action"] RETURN a.id, type(r), b.id LIMIT 600'
        )
        return dict(
            nodes=nodes,
            edges=[dict(source=a, relation=r, target=b) for a, r, b in edges],
            revision=self.revision(),
        )

    def facts(self, partner, effective_at, known_at, status="accepted"):
        rows = self.read(
            """MATCH (d:Decision)-[:APPLIES_TO]->(:System {id:"system-payments"})
            MATCH (d)-[:HAS_VERSION]->(f:FactVersion)-[:SUPPORTED_BY]->(s:Source)
            WHERE f.subject="system-payments" AND f.field="minimum_backoff_ms"
            AND f.partner=$partner AND f.status=$status
            AND f.valid_from <= $effective AND (f.valid_to="" OR $effective < f.valid_to)
            AND f.recorded_from <= $known AND (f.recorded_to="" OR $known < f.recorded_to)
            RETURN f.payload, s.payload, d.payload LIMIT 20""",
            dict(
                partner=partner, effective=effective_at, known=known_at, status=status
            ),
        )
        return [
            dict(fact=json.loads(f), source=json.loads(s), decision=json.loads(d))
            for f, s, d in rows
        ]

    def claims(self, partner, effective_at, known_at):
        rows = self.read(
            """MATCH (d:Document)-[:ASSERTS]->(f:FactVersion)-[:SUPPORTED_BY]->(s:Source)
            WHERE f.partner=$partner AND f.valid_from <= $effective
            AND (f.valid_to="" OR $effective < f.valid_to)
            AND f.recorded_from <= $known AND (f.recorded_to="" OR $known < f.recorded_to)
            RETURN f.payload, s.payload LIMIT 20""",
            dict(partner=partner, effective=effective_at, known=known_at),
        )
        return [dict(fact=json.loads(f), source=json.loads(s)) for f, s in rows]

    def owners(self):
        rows = self.read(
            'MATCH (p:Person)-[:OWNS]->(:System {id:"system-payments"}) RETURN p.payload'
        )
        return [json.loads(r[0]) for r in rows]

    def receipt(self, id):
        rows = self.read(
            "MATCH (r:Receipt {id:$id}) RETURN r.payload, coalesce(r.stale,false)",
            dict(id=id),
        )
        if not rows:
            return None
        data = json.loads(rows[0][0])
        data["stale"] = rows[0][1]
        return data

    def receipts(self):
        rows = self.read("MATCH (r:Receipt) RETURN r.id ORDER BY r.id DESC LIMIT 30")
        return [self.receipt(r[0]) for r in rows]

    def event(self, event):
        with LOCK:
            if self.get("event-" + event):
                return dict(
                    applied=False,
                    revision=self.revision(),
                    message="This sample event has already been applied.",
                )
            if event == "migration":
                source, corrected, current = migration_fixture()
                old = self.get("fact-b-original")
                old["recorded_to"] = "2026-10-12T09:00:00Z"
                self.upsert(old)
                for n in [source, corrected, current]:
                    self.upsert(n)
                for n in [corrected, current]:
                    self.link("decision-retry", "HAS_VERSION", n["id"])
                    self.link(n["id"], "GOVERNED_BY", "commitment-b")
                self.link(corrected["id"], "SUPPORTED_BY", "source-incident")
                self.link(current["id"], "SUPPORTED_BY", "source-migration")
                self.link(current["id"], "SUPERSEDES", "fact-b-original")
                self.link("project-migration", "DOCUMENTED_IN", "source-migration")
            elif event == "proposal":
                self.upsert(
                    dict(
                        id="source-proposal",
                        kind="Source",
                        title="Unapproved performance suggestion",
                        source_type="Chat export",
                        timestamp="2026-10-14T09:00:00Z",
                        excerpt="Suggestion only: could we remove the retry delay globally? No approval or partner confirmation has been recorded.",
                        enabled=True,
                        synthetic=True,
                    )
                )
                self.upsert(
                    dict(
                        id="proposal-retry",
                        kind="Decision",
                        title="Proposal: remove all retry delays",
                        approved=False,
                    )
                )
                self.link("proposal-retry", "SUPPORTED_BY", "source-proposal")
                self.link("proposal-retry", "APPLIES_TO", "system-payments")
            elif event == "withdraw-evidence":
                source = self.get("source-incident")
                source["enabled"] = False
                self.upsert(source)
            else:
                raise ValueError("Unsupported sample event")
            self.upsert(dict(id="event-" + event, kind="Event", title=event))
            self.bump()
            return dict(
                applied=True,
                revision=self.revision(),
                message="Sample event applied. Previous receipts are marked stale.",
            )

    def copy_scenario(self):
        import uuid

        name = "chronos_scenario_" + uuid.uuid4().hex
        self.graph.copy(name)
        return Store(name)
