"""Versioned, non-destructive physical schema for company graphs."""

import json
import re
import time
from datetime import datetime, timezone

VERSION = 4
NATIVE_FIELDS = (
    "client",
    "facility",
    "field",
    "status",
    "valid_from",
    "valid_to",
    "recorded_from",
    "recorded_to",
    "value",
    "city",
    "arrival_at",
    "event_at",
    "sequence",
    "enabled",
    "classification",
    "source_type",
    "department",
    "timestamp",
    "content_hash",
    "synthetic",
    "subject_id",
    "record_type",
)
INDEXES = {
    "Entity": ("id", "kind", "title"),
    "Rule": ("field", "client", "subject_id"),
    "Shipment": ("client", "status"),
    "Source": ("enabled",),
}
# Regression-tested temporal predicates use explicit string comparisons. Do not
# route interval checks through range indexes in the pinned database configuration.
TEMPORAL_INDEXES = {
    "Rule": ("valid_from", "recorded_from"),
    "Shipment": ("arrival_at",),
    "ScanEvent": ("event_at",),
    "Source": ("timestamp",),
}


def properties(n):
    for key in ("id", "kind", "title"):
        if not isinstance(n.get(key), str) or not n[key].strip():
            raise ValueError("Records require nonempty id, kind and title")
    if len(n["id"]) > 200:
        raise ValueError("Record id is too long")
    if n["kind"] == "Rule":
        for key in (
            "field",
            "value",
            "status",
            "valid_from",
            "valid_to",
            "recorded_from",
            "recorded_to",
        ):
            if key not in n:
                raise ValueError("Rule is missing temporal or policy fields")
        for start, end in (
            ("valid_from", "valid_to"),
            ("recorded_from", "recorded_to"),
        ):
            a = datetime.fromisoformat(n[start].replace("Z", "+00:00"))
            b = (
                datetime.fromisoformat(n[end].replace("Z", "+00:00"))
                if n[end]
                else None
            )
            if not a.tzinfo or (b and (not b.tzinfo or b <= a)):
                raise ValueError(
                    "Rule intervals require timezone-aware, increasing boundaries"
                )
    return {
        k: v
        for k, v in n.items()
        if re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", k)
        and k not in SYSTEM_FIELDS
        and isinstance(v, (str, int, float, bool))
    }


SYSTEM_FIELDS = {"id", "kind", "title", "payload", "search_text", "stale", "created"}


def persist(store, records, kind):
    rows = []
    for original in records:
        n = dict(original)
        for field in (
            "valid_from",
            "valid_to",
            "recorded_from",
            "recorded_to",
            "timestamp",
            "arrival_at",
            "event_at",
        ):
            if n.get(field):
                stamp = datetime.fromisoformat(n[field].replace("Z", "+00:00"))
                if not stamp.tzinfo:
                    raise ValueError(
                        "Recorded and effective timestamps require a timezone"
                    )
                n[field] = (
                    stamp.astimezone(timezone.utc)
                    .isoformat(timespec="microseconds")
                    .replace("+00:00", "Z")
                )
        native = properties(n)
        rows.append(
            dict(
                id=n["id"],
                kind=n["kind"],
                title=n["title"],
                payload=json.dumps(n),
                search_text=" ".join(str(v) for v in n.values()).lower(),
                **native,
            )
        )
    existing_rows = store.read(
        "MATCH (n:Entity) WHERE n.id IN $ids RETURN n.id,keys(n)",
        dict(ids=[r["id"] for r in rows]),
    )
    existing = {r[0] for r in existing_rows}
    fields = set(NATIVE_FIELDS)
    fields.update(k for row in rows for k in row if k not in SYSTEM_FIELDS)
    fields.update(
        k
        for _, keys in existing_rows
        for k in keys
        if k not in SYSTEM_FIELDS and re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,63}", k)
    )
    for row in rows:
        for field in fields:
            row.setdefault(field, None)
    assignment = (
        "n.kind=x.kind,n.title=x.title,n.payload=x.payload,n.search_text=x.search_text,"
        + ",".join(f"n.{k}=x.{k}" for k in sorted(fields))
    )
    new = [r for r in rows if r["id"] not in existing]
    old = [r for r in rows if r["id"] in existing]
    # FalkorDB checks mandatory fields at CREATE, before a following SET.
    if new:
        store.write(
            f"UNWIND $rows AS x CREATE (n:Entity:{kind} {{id:x.id,kind:x.kind,title:x.title,payload:x.payload}}) SET "
            + assignment,
            dict(rows=new),
        )
    if old:
        store.write(
            "UNWIND $rows AS x MATCH (n:Entity {id:x.id}) SET " + assignment,
            dict(rows=old),
        )


def migrate(store):
    """Preserve facts, revisions and history. Never reset a graph to upgrade it."""
    version = store.read(
        'MATCH (m:Metadata {id:"dataset"}) RETURN coalesce(m.schema_version,0)'
    )
    if version and version[0][0] >= VERSION:
        return
    rows = store.read("MATCH (n:Entity) RETURN n.payload ORDER BY n.id")
    groups = {}
    for row in rows:
        n = json.loads(row[0])
        groups.setdefault(n["kind"], []).append(n)
    for kind, nodes in groups.items():
        for offset in range(0, len(nodes), 250):
            persist(store, nodes[offset : offset + 250], kind)
    existing_indexes = store.read(
        "CALL db.indexes() YIELD label,properties,types RETURN label,properties,types"
    )
    indexed = {
        (label, field)
        for label, fields, types in existing_indexes
        if "RANGE" in str(types)
        for field in fields
    }
    for label, fields in TEMPORAL_INDEXES.items():
        for field in fields:
            if (label, field) in indexed:
                store.graph.drop_node_range_index(label, field)
    # Resume partial migrations without recreating an existing index.
    for label, fields in INDEXES.items():
        for field in fields:
            if (label, field) not in indexed:
                store.graph.create_node_range_index(label, field)
    constraints = store.graph.list_constraints()
    for typ, fields in (
        ("UNIQUE", ["id"]),
        ("MANDATORY", ["id", "kind", "title", "payload"]),
    ):
        if not any(
            c["label"] == "Entity"
            and c["type"] == typ
            and sorted(c["properties"]) == sorted(fields)
            for c in constraints
        ):
            if typ == "UNIQUE":
                store.graph.create_node_unique_constraint("Entity", *fields)
            else:
                store.graph.create_node_mandatory_constraint("Entity", *fields)
    for _ in range(100):
        statuses = store.graph.list_constraints()
        if any(c["status"] == "FAILED" for c in statuses):
            raise RuntimeError(
                "Schema constraint validation failed; existing data retained"
            )
        if statuses and all(c["status"] == "OPERATIONAL" for c in statuses):
            break
        time.sleep(0.05)
    else:
        raise RuntimeError("Schema constraints are not yet operational")
    store.write(
        'MATCH (m:Metadata {id:"dataset"}) SET m.schema_version=$version',
        dict(version=VERSION),
    )
