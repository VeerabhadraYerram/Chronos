"""Domain-independent, bounded read templates for review and AI retrieval."""

import hashlib
import json
import re
from datetime import datetime, timezone

from fastapi import HTTPException

from .schema import NATIVE_FIELDS
from .timeutil import canonical
from .coverage import workspace_disclosure

VISIBLE = "(n:Entity OR n:Metadata) AND coalesce(n.kind,'Metadata') <> 'DemoSession'"
EDGE_VISIBLE = "a.kind <> 'DemoSession' AND b.kind <> 'DemoSession'"
PRIVATE = {"DemoSession", "Receipt", "Action", "Metadata"}


def unpack(props):
    record = dict(props)
    raw = record.get("payload")
    decoded = json.loads(raw) if raw else dict(record)
    return dict(
        id=record["id"],
        label=record.get("kind", "Metadata"),
        properties=record,
        record=decoded,
    )


class CompanyReader:
    def __init__(self, store):
        self.store = store

    def catalog(self):
        metadata = self.store.read(
            'MATCH (m:Metadata {id:"dataset"}) RETURN properties(m)'
        )[0][0]
        # Schema discovery needs payloads and native key names, not duplicate values
        # and search_text for every property of all 10,000 records.
        rows = self.store.read_all(
            f"MATCH (n) WHERE {VISIBLE} RETURN n.id,coalesce(n.kind,'Metadata'),n.payload,keys(n) ORDER BY n.id",
            page_size=250,
        )
        labels = {}
        for id, label, raw, native_keys in rows:
            record = json.loads(raw) if raw else metadata
            item = labels.setdefault(
                label,
                dict(label=label, count=0, fields={}, native_fields=set()),
            )
            item["count"] += 1
            item["native_fields"].update(native_keys)
            for field, value in record.items():
                typ = (
                    "null"
                    if value is None
                    else "boolean"
                    if isinstance(value, bool)
                    else "number"
                    if isinstance(value, (int, float))
                    else "array"
                    if isinstance(value, list)
                    else "object"
                    if isinstance(value, dict)
                    else "string"
                )
                item["fields"].setdefault(field, set()).add(typ)
        for item in labels.values():
            item["native_fields"] = sorted(item["native_fields"])
            item["fields"] = {k: sorted(v) for k, v in sorted(item["fields"].items())}
        relations = self.store.read(
            f"MATCH (a:Entity)-[r]->(b:Entity) WHERE {EDGE_VISIBLE} RETURN type(r),a.kind,b.kind,count(r) ORDER BY type(r),a.kind,b.kind"
        )
        constraints = self.store.read(
            "CALL db.constraints() YIELD type,label,properties,entitytype,status RETURN type,label,properties,entitytype,status"
        )
        indexes = self.store.read(
            "CALL db.indexes() YIELD label,properties,types,status RETURN label,properties,types,status"
        )
        return dict(
            labels=sorted(labels.values(), key=lambda x: x["label"]),
            relationships=[
                dict(type=t, source_label=a, target_label=b, count=c)
                for t, a, b, c in relations
            ],
            constraints=[
                dict(type=t, label=label, properties=p, entitytype=e, status=s)
                for t, label, p, e, s in constraints
            ],
            indexes=[
                dict(label=label, properties=p, types=t, status=s)
                for label, p, t, s in indexes
            ],
            company=next(
                (
                    json.loads(raw)
                    for id, label, raw, native_keys in rows
                    if label == "Company"
                ),
                None,
            ),
            metadata=metadata,
            records=len(rows),
            connections=sum(r[3] for r in relations),
            disclosure=workspace_disclosure(),
        )

    def rows(self, label, query="", offset=0, limit=50):
        # The label and text are parameters, never Cypher fragments.
        condition = (
            VISIBLE
            + " AND ($label='' OR coalesce(n.kind,'Metadata')=$label) AND ($q='' OR toLower(n.id) CONTAINS $q OR toLower(coalesce(n.payload,'')) CONTAINS $q)"
        )
        params = dict(label=label, q=query.lower()[:240], offset=offset, limit=limit)
        total = self.store.read(f"MATCH (n) WHERE {condition} RETURN count(n)", params)[
            0
        ][0]
        rows = self.store.read(
            f"MATCH (n) WHERE {condition} RETURN properties(n) ORDER BY n.id SKIP $offset LIMIT $limit",
            params,
        )
        return dict(
            rows=[unpack(r[0]) for r in rows],
            total=total,
            offset=offset,
            limit=limit,
            revision=self.store.revision(),
        )

    def edges(self, relation="", record_id="", offset=0, limit=50):
        condition = (
            EDGE_VISIBLE
            + " AND ($rel='' OR type(r)=$rel) AND ($id='' OR a.id=$id OR b.id=$id)"
        )
        params = dict(rel=relation, id=record_id, offset=offset, limit=limit)
        total = self.store.read(
            f"MATCH (a:Entity)-[r]->(b:Entity) WHERE {condition} RETURN count(r)",
            params,
        )[0][0]
        rows = self.store.read(
            f"MATCH (a:Entity)-[r]->(b:Entity) WHERE {condition} RETURN a.id,a.kind,a.title,type(r),b.id,b.kind,b.title,properties(r) ORDER BY a.id,type(r),b.id SKIP $offset LIMIT $limit",
            params,
        )
        return dict(
            rows=[
                dict(
                    source=a,
                    source_label=ak,
                    source_title=at,
                    relation=r,
                    target=b,
                    target_label=bk,
                    target_title=bt,
                    properties=p,
                )
                for a, ak, at, r, b, bk, bt, p in rows
            ],
            total=total,
            offset=offset,
            limit=limit,
            revision=self.store.revision(),
        )

    def record(self, id):
        rows = self.store.read(
            f"MATCH (n {{id:$id}}) WHERE {VISIBLE} RETURN properties(n)", dict(id=id)
        )
        if not rows:
            raise HTTPException(404, "Record not found in this workspace")
        return unpack(rows[0][0])

    def search(self, query, known, limit=12):
        import re

        stop = {
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
            "who",
            "the",
            "are",
            "was",
            "were",
            "company",
            "please",
            "our",
            "your",
            "for",
            "and",
            "all",
            "has",
            "its",
            "will",
            "than",
        }
        terms = [
            w.lower()
            for w in re.findall(r"[\w-]+", query)
            if len(w) > 2 and w.lower() not in stop
        ][:16]
        rows = self.store.read(
            """MATCH (n:Entity) WHERE NOT n.kind IN $private
            AND (n.kind <> 'Source' OR (n.enabled=true AND toString(n.timestamp) <= $known))
            WITH n, size([t IN $terms WHERE toLower(n.id) CONTAINS t OR toLower(n.title) CONTAINS t])*4 + size([t IN $terms WHERE n.search_text CONTAINS t]) AS score
            WHERE score>0 OR size($terms)=0
            RETURN n.payload ORDER BY score DESC,n.id LIMIT $limit""",
            dict(
                terms=terms,
                private=sorted(PRIVATE),
                known=canonical(known),
                limit=limit,
            ),
        )
        return [json.loads(r[0]) for r in rows]

    def rules(self, effective, known, ids=None):
        rows = self.store.read(
            """MATCH (r:Rule)-[:SUPPORTED_BY]->(s:Source)
            WHERE r.status='accepted' AND s.enabled=true AND toString(s.timestamp) <= $known
            AND toString(r.valid_from) <= $effective AND (r.valid_to='' OR $effective < toString(r.valid_to))
            AND toString(r.recorded_from) <= $known AND (r.recorded_to='' OR $known < toString(r.recorded_to))
            AND (size($ids)=0 OR r.id IN $ids OR r.subject_id IN $ids OR r.client IN $ids OR r.facility IN $ids)
            RETURN r.payload,s.payload ORDER BY r.id LIMIT 100""",
            dict(effective=canonical(effective), known=canonical(known), ids=ids or []),
        )
        return [dict(rule=json.loads(r), source=json.loads(s)) for r, s in rows]

    def claims(self, effective, known):
        rows = self.store.read(
            """MATCH (p:Policy)-[:ASSERTS]->(c:Claim)-[:SUPPORTED_BY]->(s:Source)
            WHERE s.enabled=true AND toString(s.timestamp)<=$known
            AND toString(c.valid_from)<=$effective AND (c.valid_to='' OR $effective<toString(c.valid_to))
            AND toString(c.recorded_from)<=$known AND (c.recorded_to='' OR $known<toString(c.recorded_to))
            RETURN p.payload,c.payload,s.payload LIMIT 100""",
            dict(effective=canonical(effective), known=canonical(known)),
        )
        return [
            dict(policy=json.loads(p), claim=json.loads(c), source=json.loads(s))
            for p, c, s in rows
        ]

    def aggregate(
        self,
        label,
        group_by="",
        filters=None,
        metric="count",
        field="",
        known=None,
        effective=None,
    ):
        if label in PRIVATE:
            raise ValueError("Internal records are not available to the investigator")
        observed = self.store.read(
            "MATCH (n:Entity) WHERE n.kind=$label UNWIND keys(n) AS field RETURN DISTINCT field",
            dict(label=label),
        )
        allowed = {
            r[0]
            for r in observed
            if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", r[0])
            and r[0] not in {"payload", "search_text", "stale", "created"}
        }
        filters = filters or {}
        if (
            metric not in {"count", "sum", "avg", "min", "max"}
            or (group_by and group_by not in allowed)
            or any(k not in allowed for k in filters)
            or (metric != "count" and field not in allowed)
        ):
            raise ValueError("Use an observed native field and supported aggregation")
        if metric != "count":
            types = self.store.read(
                f"MATCH (n:Entity) WHERE n.kind=$label AND n.{field} IS NOT NULL RETURN DISTINCT n.{field}",
                dict(label=label),
            )
            if not types or any(
                not isinstance(r[0], (int, float)) or isinstance(r[0], bool)
                for r in types
            ):
                raise ValueError("Arithmetic requires a numeric field")
        condition = " AND ".join(f"n.{k}=$filter_{k}" for k in filters) or "true"
        pattern = "MATCH (n:Entity)"
        time_params = {}
        if known and label == "Source":
            condition += " AND n.enabled=true AND toString(n.timestamp)<=$known"
            time_params["known"] = canonical(known)
        elif known and effective and label == "Rule":
            pattern = "MATCH (n:Entity)-[:SUPPORTED_BY]->(s:Source)"
            condition += " AND n.status='accepted' AND s.enabled=true AND toString(s.timestamp)<=$known AND toString(n.valid_from)<=$effective AND (n.valid_to='' OR $effective<toString(n.valid_to)) AND toString(n.recorded_from)<=$known AND (n.recorded_to='' OR $known<toString(n.recorded_to))"
            time_params.update(known=canonical(known), effective=canonical(effective))
        grouping = f"n.{group_by}" if group_by else "n.kind"
        expression = "count(n)" if metric == "count" else f"{metric}(n.{field})"
        rows = self.store.read(
            f"{pattern} WHERE n.kind=$label AND {condition} WITH DISTINCT n RETURN {grouping},{expression} ORDER BY {expression} DESC LIMIT 51",
            dict(
                label=label,
                **time_params,
                **{"filter_" + k: v for k, v in filters.items()},
            ),
        )
        samples = self.store.read(
            f"{pattern} WHERE n.kind=$label AND {condition} WITH DISTINCT n RETURN n.id ORDER BY n.id LIMIT 5",
            dict(
                label=label,
                **time_params,
                **{"filter_" + k: v for k, v in filters.items()},
            ),
        )
        return dict(
            label=label,
            sample_ids=[r[0] for r in samples],
            group_by=group_by or "kind",
            metric=metric,
            field=field,
            groups=[
                dict(value=v, **({"count": c} if metric == "count" else {"result": c}))
                for v, c in rows[:50]
            ],
            limit=50,
            groups_truncated=len(rows) > 50,
        )

    def audit(self):
        checks = []

        def check(name, query):
            count = self.store.read(query)[0][0]
            checks.append(dict(name=name, violations=count, passed=count == 0))

        check(
            "Unique entity identifiers",
            "MATCH (n:Entity) WITH n.id AS id,count(n) AS c WHERE c>1 RETURN count(id)",
        )
        check(
            "Required entity properties",
            "MATCH (n:Entity) WHERE n.id IS NULL OR n.kind IS NULL OR n.title IS NULL OR n.payload IS NULL RETURN count(n)",
        )
        check(
            "Rules have source relationships",
            "MATCH (n:Rule) WHERE NOT (n)-[:SUPPORTED_BY]->(:Source) RETURN count(n)",
        )
        check(
            "Shipments have client, facility, pickup and manifest",
            "MATCH (n:Shipment) WHERE NOT (n)-[:FOR_CLIENT]->(:Client) OR NOT (n)-[:AT]->(:Facility) OR NOT (n)-[:COLLECTED_BY]->(:PickupRequest) OR NOT (n)-[:ON_MANIFEST]->(:Manifest) RETURN count(n)",
        )
        check(
            "Scan events have a shipment",
            "MATCH (n:ScanEvent) WHERE NOT (:Shipment)-[:HAS_SCAN]->(n) RETURN count(n)",
        )
        check(
            "Temporal intervals are ordered",
            "MATCH (n:Rule) WHERE (n.valid_to<>'' AND n.valid_to<=n.valid_from) OR (n.recorded_to<>'' AND n.recorded_to<=n.recorded_from) RETURN count(n)",
        )
        hashes = self.store.read_all("MATCH (n:Source) RETURN n.payload ORDER BY n.id")
        bad = sum(
            hashlib.sha256(json.loads(r[0]).get("excerpt", "").encode()).hexdigest()
            != json.loads(r[0]).get("content_hash")
            for r in hashes
        )
        checks.append(
            dict(
                name="Source content hashes match stored excerpts",
                violations=bad,
                passed=bad == 0,
            )
        )
        rows = self.store.read_all(
            "MATCH (n:Entity) WHERE n.kind<>'DemoSession' RETURN properties(n) ORDER BY n.id",
            page_size=250,
        )
        mismatches = 0
        for (props,) in rows:
            n = json.loads(props["payload"])
            mismatches += any(
                props.get(k) != n.get(k)
                for k in NATIVE_FIELDS
                if isinstance(n.get(k), (str, int, float, bool))
            )
        checks.append(
            dict(
                name="Native fields match serialized records",
                violations=mismatches,
                passed=mismatches == 0,
            )
        )
        return dict(
            checks=checks,
            passed=all(c["passed"] for c in checks),
            revision=self.store.revision(),
            checked_at=datetime.now(timezone.utc).isoformat(),
            scope="Structural checks only; not a guarantee of source truth, policy completeness or production readiness.",
        )

    def export(self):
        catalog = self.catalog()
        if catalog["records"] > 25000 or catalog["connections"] > 50000:
            raise HTTPException(
                413, "Workspace exceeds single-export limit; use paginated inspection"
            )
        nodes, edges = [], []
        for offset in range(0, catalog["records"], 1000):
            nodes.extend(self.rows("", offset=offset, limit=1000)["rows"])
        for offset in range(0, catalog["connections"], 1000):
            edges.extend(self.edges(offset=offset, limit=1000)["rows"])
        contents = dict(nodes=nodes, relationships=edges)
        return dict(
            format="chronosgraph-workspace-v1",
            exported_at=datetime.now(timezone.utc).isoformat(),
            catalog=catalog,
            content_sha256=hashlib.sha256(
                json.dumps(contents, sort_keys=True).encode()
            ).hexdigest(),
            **contents,
        )
