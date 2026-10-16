"""Trusted local data-pack ingestion into a NEW isolated workspace, never a reset."""

import hashlib
import re
import uuid
from datetime import datetime

from .store import CompanyStore, SESSION_PREFIX
from ..store import LOCK


def import_workspace(data):
    nodes = data.get("nodes", [])
    edges = data.get("relationships", [])
    if not nodes or len(nodes) > 20000 or len(edges) > 50000:
        raise ValueError(
            "Data pack requires 1–20000 nodes and at most 50000 relationships"
        )
    nodes = [dict(n) for n in nodes]
    ids = [n.get("id") for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate node identifiers in data pack")
    for n in nodes:
        if n.get("kind") in {
            "Entity",
            "Metadata",
            "DemoSession",
            "Receipt",
            "Action",
            "Event",
        } or not re.fullmatch(r"[A-Z][A-Za-z0-9_]{0,47}", n.get("kind", "")):
            raise ValueError("Invalid or reserved entity label")
        if n["kind"] == "Source":
            if not isinstance(n.get("excerpt"), str) or not isinstance(
                n.get("enabled"), bool
            ):
                raise ValueError("Sources require excerpt and explicit enabled flag")
            stamp = datetime.fromisoformat(
                n.get("timestamp", "").replace("Z", "+00:00")
            )
            if not stamp.tzinfo:
                raise ValueError("Sources require timezone-aware recorded timestamp")
            n["content_hash"] = hashlib.sha256(n["excerpt"].encode()).hexdigest()
        if n["kind"] == "Rule" and not (n.get("subject_id") or n.get("client")):
            raise ValueError("Rules require an explicit subject_id or client scope")
    source_ids = {n["id"] for n in nodes if n["kind"] == "Source"}
    for e in edges:
        if (
            e.get("source") not in ids
            or e.get("target") not in ids
            or not re.fullmatch(r"[A-Z][A-Z0-9_]{0,47}", e.get("relation", ""))
        ):
            raise ValueError("Relationship endpoints or name are invalid")
        if any(s not in source_ids for s in e.get("source_ids", [])):
            raise ValueError(
                "Relationship evidence must refer to a Source in this pack"
            )
    for n in nodes:
        if (
            n["kind"] == "Rule"
            and n.get("status") == "accepted"
            and not any(
                e["source"] == n["id"]
                and e["relation"] == "SUPPORTED_BY"
                and e["target"] in source_ids
                for e in edges
            )
        ):
            raise ValueError("Accepted rules require a supporting Source relationship")
    with LOCK:
        id = uuid.uuid4().hex
        store = CompanyStore(SESSION_PREFIX + id)
        try:
            store.write(
                'CREATE (:Metadata {id:"dataset", revision:1, imported:true, dataset_description:$description})',
                dict(
                    description=str(
                        data.get(
                            "description",
                            "Imported company data pack; inspect source classifications",
                        )
                    )[:2000]
                ),
            )
            for n in nodes:
                store.upsert(n)
            for e in edges:
                store.link_evidence(
                    e["source"], e["relation"], e["target"], e.get("source_ids")
                )
            store.ensure_schema()
            return id
        except Exception:
            if store.name in store.db.list_graphs():
                store.graph.delete()  # Only this newly created, incomplete import.
            raise
