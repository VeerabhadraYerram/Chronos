"""Regenerate the reference data dictionary offline; never export a visitor graph."""

import json
from collections import Counter, defaultdict
from pathlib import Path

from chronos.company.seed import fixture
from chronos.company.schema import properties, INDEXES


def main():
    nodes, edges = fixture()
    counts = Counter(n["kind"] for n in nodes)
    by_id = {n["id"]: n for n in nodes}
    labels = []
    for kind in sorted(counts):
        group = [n for n in nodes if n["kind"] == kind]
        fields = defaultdict(set)
        for node in group:
            for key, value in node.items():
                typ = (
                    "boolean"
                    if isinstance(value, bool)
                    else "integer"
                    if isinstance(value, int)
                    else "number"
                    if isinstance(value, float)
                    else "array"
                    if isinstance(value, list)
                    else "object"
                    if isinstance(value, dict)
                    else "null"
                    if value is None
                    else "string"
                )
                fields[key].add(typ)
        labels.append(
            dict(
                label=kind,
                initial_count=counts[kind],
                common_native_properties=dict(
                    id="string",
                    kind="string",
                    title="string",
                    payload="JSON-encoded string",
                    search_text="string",
                ),
                additional_native_properties=sorted(
                    {key for n in group for key in properties(n)}
                ),
                payload_field_types={k: sorted(v) for k, v in sorted(fields.items())},
                required_in_initial_fixture=sorted(
                    set.intersection(*(set(n) for n in group))
                ),
                representative_record=group[0],
            )
        )
    relations = defaultdict(list)
    for edge in edges:
        relations[edge["relation"]].append(edge)
    schema = dict(
        format="chronosgraph-reference-dictionary-v2",
        database="FalkorDB",
        disclosure="Independent Delhivery reference schema. Public names; synthetic private operations, agreements and roles. Not Delhivery internal data.",
        source="backend/chronos/company/seed.py",
        initial_business_entities=len(nodes),
        initial_relationships=len(edges),
        node_labels=labels,
        runtime_only_labels=dict(
            Receipt="Persisted investigation; native stale flag supplements payload",
            Action="Local review packet",
            Event="Replay idempotency marker",
            DemoSession="Creation registry; native created timestamp",
        ),
        metadata=dict(
            label="Metadata",
            properties=dict(
                id="dataset",
                revision="integer",
                schema_version=4,
                demo_config="JSON-encoded guided tour",
            ),
            carries_Entity_label=False,
        ),
        relationship_types=[
            dict(
                type=relation,
                initial_count=len(group),
                endpoint_label_pairs=sorted(
                    {
                        by_id[e["source"]]["kind"] + " -> " + by_id[e["target"]]["kind"]
                        for e in group
                    }
                ),
                properties=dict(
                    source_ids="array of Source IDs; empty for operational links without document provenance"
                ),
            )
            for relation, group in sorted(relations.items())
        ],
        database_enforced_unique_constraints=[dict(label="Entity", properties=["id"])],
        database_enforced_mandatory_constraints=[
            dict(label="Entity", properties=["id", "kind", "title", "payload"])
        ],
        explicit_indexes=[
            dict(label=label, properties=[field], type="RANGE")
            for label, fields in INDEXES.items()
            for field in fields
        ],
        amendment_relationship_types=["SUPERSEDES", "AMENDED_BY"],
        investigation_relationship_types=["USED", "PROPOSES"],
    )
    output = Path(__file__).resolve().parents[1] / "docs" / "database-schema.json"
    output.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n")
    print(
        f"Schema exported: {len(labels)} labels, {len(nodes):,} fixture entities, {len(edges):,} relationships."
    )


if __name__ == "__main__":
    main()
