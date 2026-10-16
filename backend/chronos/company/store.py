"""Real FalkorDB read templates and isolated visitor graphs for the reference demo."""

import json
import os
import re
import time
import uuid
from collections import defaultdict

from fastapi import HTTPException
from redis.exceptions import ResponseError

from ..store import Store, LOCK
from .seed import fixture, amendment
from .schema import persist, migrate
from .demo import CONFIG, upgrade_reference_records
from .timeutil import canonical

BASE_NAME = os.getenv("CHRONOS_COMPANY_GRAPH", "chronos_delhivery_reference_v1")
SESSION_PREFIX = "chronos_delhivery_demo_"
EXCLUDED = [
    "ScanEvent",
    "Shipment",
    "PickupRequest",
    "Manifest",
    "Receipt",
    "Action",
    "DemoSession",
]
KINDS = {
    "Record",
    "Company",
    "Client",
    "ClientWarehouse",
    "Facility",
    "Team",
    "Source",
    "Decision",
    "Policy",
    "Rule",
    "Campaign",
    "Route",
    "Manifest",
    "PickupRequest",
    "Shipment",
    "ScanEvent",
    "Receipt",
    "Action",
    "DemoSession",
    "Event",
}
RELATIONS = {
    "ASSERTS",
    "PART_OF",
    "OPERATED_BY",
    "PUBLIC_RELATIONSHIP",
    "BELONGS_TO",
    "EXPLAINED_BY",
    "OWNED_BY",
    "DOCUMENTED_IN",
    "APPLIES_AT",
    "SUPPORTED_BY",
    "HAS_COMMITMENT",
    "WHY",
    "ORIGIN",
    "DESTINATION",
    "USES_ROUTE",
    "FROM",
    "FOR_CLIENT",
    "AT",
    "COLLECTED_BY",
    "ON_MANIFEST",
    "HAS_SCAN",
    "SUPERSEDES",
    "AMENDED_BY",
    "USED",
    "PROPOSES",
}
RULE_FIELDS = [
    "client",
    "facility",
    "field",
    "status",
    "valid_from",
    "valid_to",
    "recorded_from",
    "recorded_to",
]


class CompanyStore(Store):
    def upsert(self, n):
        if not re.fullmatch(r"[A-Z][A-Za-z0-9_]{0,47}", n["kind"]) or n["kind"] in {
            "Entity",
            "Metadata",
        }:
            raise ValueError("Unsupported entity label")
        existing = self.get(n["id"])
        if existing and existing["kind"] != n["kind"]:
            raise ValueError("Record kind cannot change for an existing identifier")
        persist(self, [n], n["kind"])

    def ensure_schema(self):
        with LOCK:
            migrate(self)

    def link_evidence(self, a, relation, b, source_ids=None):
        if not re.fullmatch(r"[A-Z][A-Z0-9_]{0,47}", relation):
            raise ValueError("Unsupported relationship name")
        rows = self.write(
            f"MATCH (a:Entity {{id:$a}}),(b:Entity {{id:$b}}) MERGE (a)-[r:{relation}]->(b) SET r.source_ids=$sources RETURN count(r)",
            dict(a=a, b=b, sources=source_ids or []),
        )
        if not rows or rows[0][0] != 1:
            raise ValueError("Both relationship endpoints must exist")

    def demo_config(self):
        rows = self.read('MATCH (m:Metadata {id:"dataset"}) RETURN m.demo_config')
        return json.loads(rows[0][0]) if rows and rows[0][0] else None

    def seed(self):
        with LOCK:
            if self.name in self.db.list_graphs() and self.read(
                'MATCH (m:Metadata {id:"dataset"}) RETURN m.revision'
            ):
                self.ensure_schema()
                if self.get("facility-bengaluru") and not self.demo_config():
                    self.write(
                        'MATCH (m:Metadata {id:"dataset"}) SET m.demo_config=$demo',
                        dict(demo=json.dumps(CONFIG)),
                    )
                upgrade_reference_records(self)
                return
            nodes, edges = fixture()
            grouped = defaultdict(list)
            for n in nodes:
                grouped[n["kind"]].append(
                    dict(
                        id=n["id"],
                        payload=json.dumps(n),
                        kind=n["kind"],
                        title=n["title"],
                    )
                )
            for kind, records in grouped.items():
                for start in range(0, len(records), 250):
                    self.write(
                        f"UNWIND $rows AS x MERGE (n:Entity:{kind} {{id:x.id}}) SET n.payload=x.payload,n.kind=x.kind,n.title=x.title",
                        dict(rows=records[start : start + 250]),
                    )
            for n in nodes:
                if n["kind"] == "Rule":
                    self.upsert(n)
            relationships = defaultdict(list)
            for e in edges:
                relationships[e["relation"]].append(e)
            for rel, records in relationships.items():
                assert rel in RELATIONS
                for start in range(0, len(records), 250):
                    self.write(
                        f"UNWIND $rows AS x MATCH (a:Entity {{id:x.source}}),(b:Entity {{id:x.target}}) MERGE (a)-[r:{rel}]->(b) SET r.source_ids=x.source_ids",
                        dict(rows=records[start : start + 250]),
                    )
            self.write('CREATE (:Metadata {id:"dataset", revision:1})')
            self.ensure_schema()
            self.write(
                'MATCH (m:Metadata {id:"dataset"}) SET m.demo_config=$demo',
                dict(demo=json.dumps(CONFIG)),
            )

    def stats(self):
        kinds = self.read(
            'MATCH (n:Entity) WHERE NOT n.kind IN ["Receipt","Action","DemoSession"] RETURN n.kind,count(n) ORDER BY n.kind'
        )
        edges = self.read("MATCH (:Entity)-[r]->(:Entity) RETURN count(r)")[0][0]
        return dict(
            entities=sum(count for _, count in kinds),
            connections=edges,
            labels=dict(kinds),
            revision=self.revision(),
        )

    def neighborhood(self, id, depth=1):
        # Depth is server-clamped, never interpolated from a model-supplied query.
        depth = 2 if depth == 2 else 1
        rows = self.read(
            f"MATCH (root:Entity {{id:$id}})-[*0..{depth}]-(n:Entity) WHERE NOT n.kind IN $excluded RETURN DISTINCT n.payload LIMIT 32",
            dict(id=id, excluded=EXCLUDED),
        )
        nodes = [json.loads(r[0]) for r in rows]
        return self.subgraph(nodes)

    def record_graph(self, id):
        root = self.get(id)
        if not root:
            return dict(nodes=[], edges=[])
        if root["kind"] in {
            "Shipment",
            "Manifest",
            "PickupRequest",
            "ScanEvent",
            "Route",
        }:
            rows = self.read(
                "MATCH (a:Entity {id:$id})-[r]-(b:Entity) RETURN DISTINCT b.payload,b.id ORDER BY b.id LIMIT 16",
                dict(id=id),
            )
            return self.subgraph([root] + [json.loads(row[0]) for row in rows])
        return self.neighborhood(id)

    def subgraph(self, nodes):
        ids = [n["id"] for n in nodes]
        rows = self.read(
            "MATCH (a:Entity)-[r]->(b:Entity) WHERE a.id IN $ids AND b.id IN $ids RETURN a.id,type(r),b.id,coalesce(r.source_ids,[]) LIMIT 150",
            dict(ids=ids),
        )
        return dict(
            nodes=nodes,
            edges=[
                dict(source=a, relation=r, target=b, source_ids=s)
                for a, r, b, s in rows
            ],
        )

    def search(self, query, kind=None):
        terms = [
            t.lower()
            for t in re.findall(r"[a-zA-Z0-9]+", query)
            if len(t) > 2
            and t.lower()
            not in {
                "what",
                "which",
                "this",
                "that",
                "does",
                "from",
                "have",
                "with",
                "show",
                "tell",
                "about",
                "could",
                "would",
                "should",
                "give",
                "their",
                "there",
                "where",
                "when",
                "they",
                "them",
                "why",
                "how",
                "can",
            }
        ][:10]
        if not terms:
            return []
        rows = self.read(
            "MATCH (n:Entity) WHERE NOT n.kind IN $excluded AND ($kind='' OR n.kind=$kind) AND any(term IN $terms WHERE toLower(n.title) CONTAINS term OR toLower(n.payload) CONTAINS term) RETURN n.payload ORDER BY CASE WHEN toLower(n.id)=$exact OR toLower(n.title)=$exact THEN 0 WHEN n.kind='Source' THEN 1 ELSE 2 END,n.title LIMIT 18",
            dict(
                exact=query.lower().strip(),
                excluded=["ScanEvent", "DemoSession", "Receipt", "Action"],
                kind=kind or "",
                terms=terms,
            ),
        )
        return [json.loads(r[0]) for r in rows]

    def commitments(self, effective, known, client="all"):
        rows = self.read(
            """MATCH (c:Client)-[:HAS_COMMITMENT]->(r:Rule)-[:APPLIES_AT]->(f:Facility {id:"facility-bengaluru"})
            MATCH (r)-[:SUPPORTED_BY]->(s:Source)
            WHERE r.field="sunday_processing_required" AND r.status="accepted" AND ($client="all" OR c.id=$client)
            AND toString(r.valid_from) <= $effective AND (r.valid_to="" OR $effective < toString(r.valid_to))
            AND toString(r.recorded_from) <= $known AND (r.recorded_to="" OR $known < toString(r.recorded_to))
            RETURN c.payload,r.payload,s.payload LIMIT 30""",
            dict(client=client, effective=canonical(effective), known=canonical(known)),
        )
        return [
            dict(client=json.loads(c), rule=json.loads(r), source=json.loads(s))
            for c, r, s in rows
        ]

    def operating_policy(self):
        rows = self.read(
            'MATCH (p:Policy)-[:APPLIES_AT]->(:Facility {id:"facility-bengaluru"}) RETURN p.payload LIMIT 1'
        )
        policy = json.loads(rows[0][0]) if rows else None
        if not policy or "sunday_clients" not in policy:
            raise ValueError("Demo operating configuration is unavailable")
        return policy

    def documents(self):
        rows = self.read(
            'MATCH (p:Policy)-[:APPLIES_AT]->(:Facility {id:"facility-bengaluru"}) MATCH (p)-[:DOCUMENTED_IN]->(s:Source) RETURN p.payload,s.payload'
        )
        return [dict(policy=json.loads(p), source=json.loads(s)) for p, s in rows]

    def operational_sample(self, client="all"):
        rows = self.read(
            """MATCH (s:Shipment)-[:AT]->(:Facility {id:"facility-bengaluru"})
            MATCH (s)-[:FOR_CLIENT]->(c:Client)
            WHERE $client="all" OR c.id=$client RETURN c.id,c.title,count(s) ORDER BY c.title""",
            dict(client=client),
        )
        return [dict(client=id, title=title, count=count) for id, title, count in rows]

    def owners(self, id="facility-bengaluru"):
        rows = self.read(
            "MATCH (:Entity {id:$id})-[r:OWNED_BY|OPERATED_BY]->(t:Team) RETURN t.payload,coalesce(r.source_ids,[])",
            dict(id=id),
        )
        return [dict(team=json.loads(t), source_ids=s) for t, s in rows]

    def replay(self, event):
        with LOCK:
            if self.get("event-" + event):
                return dict(
                    applied=False,
                    message="This sample event is already present.",
                    revision=self.revision(),
                )
            if event == "amendment":
                source = amendment()
                self.upsert(source)
                old = self.get("rule-havells-original")
                old["recorded_to"] = "2026-10-15T09:00:00Z"
                self.upsert(old)
                corrected = {
                    **old,
                    "id": "rule-havells-history",
                    "title": "Havells · Sunday commitment before 1 Nov",
                    "recorded_from": "2026-10-15T09:00:00Z",
                    "recorded_to": "",
                    "valid_to": "2026-11-01T00:00:00Z",
                }
                current = {
                    **old,
                    "id": "rule-havells-amended",
                    "title": "Havells · six-day processing from 1 Nov",
                    "value": False,
                    "recorded_from": "2026-10-15T09:00:00Z",
                    "recorded_to": "",
                    "valid_from": "2026-11-01T00:00:00Z",
                    "valid_to": "",
                }
                for rule, sid in [
                    (corrected, "source-havells-agreement"),
                    (current, "source-amendment"),
                ]:
                    self.upsert(rule)
                    self.link_evidence("havells", "HAS_COMMITMENT", rule["id"], [sid])
                    self.link_evidence(
                        rule["id"], "APPLIES_AT", "facility-bengaluru", [sid]
                    )
                    self.link_evidence(rule["id"], "SUPPORTED_BY", sid, [sid])
                    self.link_evidence(
                        rule["id"], "OWNED_BY", "team-accounts", ["source-owners"]
                    )
                self.link_evidence(
                    "source-havells-agreement",
                    "AMENDED_BY",
                    source["id"],
                    [source["id"]],
                )
                self.link_evidence(
                    current["id"], "SUPERSEDES", old["id"], [source["id"]]
                )
            elif event == "withdraw":
                source = self.get("source-havells-agreement")
                source["enabled"] = False
                self.upsert(source)
            else:
                raise ValueError("Unknown sample event")
            self.upsert(
                dict(id="event-" + event, kind="Event", title=event, synthetic=True)
            )
            self.bump()
            return dict(
                applied=True,
                message="Synthetic event replayed in your workspace. Earlier investigations are stale.",
                revision=self.revision(),
            )

    def copy_to(self, name):
        # GRAPH.COPY can briefly fail to fork while background persistence is busy.
        # Retry only that failure, never substitute an in-memory clone or delete a graph.
        for attempt in range(3):
            try:
                self.graph.copy(name)
                return
            except ResponseError as error:
                if "could not fork" not in str(error) or attempt == 2:
                    raise
                time.sleep(0.15 * (attempt + 1))

    def copy_scenario(self):
        name = "chronos_company_trial_" + uuid.uuid4().hex
        self.copy_to(name)
        return CompanyStore(name)


def new_session():
    with LOCK:
        base = CompanyStore(BASE_NAME)
        base.seed()
        policy = base.get("policy-schedule")
        if "sunday_clients" not in policy:
            policy["sunday_clients"] = ["havells"]
            base.upsert(policy)
        sessions = base.read("MATCH (s:DemoSession) RETURN count(s)")[0][0]
        if sessions >= 40:
            raise HTTPException(
                429,
                "Demo capacity reached. Please reuse an existing workspace or try later.",
            )
        id = uuid.uuid4().hex
        base.copy_to(SESSION_PREFIX + id)
        base.upsert(
            dict(id="session-" + id, kind="DemoSession", title="Demo workspace")
        )
        base.write(
            "MATCH (s:DemoSession {id:$id}) SET s.created=$created",
            dict(id="session-" + id, created=time.time()),
        )
        return id


def session_store(id):
    if not re.fullmatch(r"[a-f0-9]{32}", id):
        raise HTTPException(400, "Invalid demo session.")
    store = CompanyStore(SESSION_PREFIX + id)
    if store.name not in store.db.list_graphs():
        raise HTTPException(404, "Workspace not found. Start a new demo workspace.")
    store.ensure_schema()
    if (
        store.get("facility-bengaluru")
        and not store.demo_config()
        and not store.read(
            'MATCH (m:Metadata {id:"dataset"}) RETURN coalesce(m.imported,false)'
        )[0][0]
    ):
        store.write(
            'MATCH (m:Metadata {id:"dataset"}) SET m.demo_config=$demo',
            dict(demo=json.dumps(CONFIG)),
        )
    upgrade_reference_records(store)
    policy = store.get("policy-schedule")
    if policy and "sunday_clients" not in policy:
        policy["sunday_clients"] = ["havells"]
        store.upsert(policy)
    return store
