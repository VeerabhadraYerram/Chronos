"""Fixture-owned guided tour. This configuration is not company policy logic."""

CONFIG = dict(
    title="A quieter Sunday. An active promise.",
    description="Follow the synthetic Bengaluru scheduling example across departments.",
    question="Can we close the Bengaluru facility on Sundays?",
    effective_at="2026-11-08",
    known_at="2026-10-16",
    before_effective="2026-10-25",
    before_known="2026-10-14",
    examples=[
        dict(
            label="Explore the client promise",
            question="What does the Havells agreement require?",
        ),
        dict(
            label="Find the recorded reason",
            question="Why did we promise Sunday processing to Havells?",
        ),
        dict(label="Find the owner", question="Who owns the Bengaluru facility?"),
    ],
    events=[
        dict(
            id="amendment",
            label="Introduce approved amendment",
            description="Replay an approved synthetic Havells amendment, recorded 15 October and effective 1 November. This is a guided sample, not live ingestion.",
        ),
        dict(
            id="withdraw",
            label="Challenge original evidence",
            description="Withdraw the original synthetic agreement in this workspace.",
        ),
    ],
)

CLAIM = dict(
    id="claim-current-schedule",
    kind="Claim",
    title="Handbook statement: Sunday processing",
    subject_id="havells",
    client="havells",
    facility="facility-bengaluru",
    field="sunday_processing_required",
    value=True,
    status="documented",
    valid_from="2026-05-01T00:00:00Z",
    valid_to="",
    recorded_from="2026-05-01T09:00:00Z",
    recorded_to="",
    synthetic=True,
)
CLAIM_EDGES = [
    ("policy-schedule", "ASSERTS", "claim-current-schedule"),
    ("claim-current-schedule", "SUPPORTED_BY", "source-schedule"),
    ("claim-current-schedule", "APPLIES_AT", "facility-bengaluru"),
    ("claim-current-schedule", "FOR_CLIENT", "havells"),
]


def upgrade_reference_records(store):
    """Add a newly explicit demo assertion once; retain facts and invalidate receipts."""
    if store.demo_config() and not store.get(CLAIM["id"]):
        store.upsert(CLAIM)
        for a, relation, b in CLAIM_EDGES:
            store.link_evidence(a, relation, b, ["source-schedule"])
        store.bump()

    # Additive, versioned fixture expansion: never reset evidence, history or user edits.
    if store.demo_config():
        from .diversity import extension, VERSION
        from .schema import persist
        from collections import defaultdict

        marker = store.read(
            'MATCH (m:Metadata {id:"dataset"}) RETURN coalesce(m.depth_version,0)'
        )[0][0]
        if marker < VERSION:
            nodes, edges = extension()
            groups = defaultdict(list)
            for n in nodes:
                if not store.get(n["id"]):
                    groups[n["kind"]].append(n)
            if marker == 1:
                # Repair two template-linked transaction examples from extension v1.
                # Other records/history are retained; every older receipt is invalidated.
                for n in nodes:
                    if (
                        n["kind"] in {"Invoice", "Remittance"}
                        or n["id"] == "depth-source-returns"
                    ):
                        old = store.get(n["id"])
                        if (
                            old
                            and old.get("synthetic")
                            and old.get("title") == n["title"]
                        ):
                            old.update(
                                {
                                    k: n[k]
                                    for k in (
                                        ("excerpt", "content_hash")
                                        if n["kind"] == "Source"
                                        else ("status", "amount_inr")
                                    )
                                }
                            )
                            store.upsert(old)
                store.write(
                    "MATCH (:Ticket {id:'depth-ticket-cod'})-[r:AFFECTS]->(:Remittance {id:'depth-remittance-0021'}) DELETE r"
                )
                store.write(
                    "MATCH (:Ticket {id:'depth-ticket-weight'})-[r:AFFECTS]->(:Invoice {id:'depth-invoice-002'}) DELETE r"
                )
            for kind, group in groups.items():
                persist(store, group, kind)
            for e in edges:
                store.link_evidence(
                    e["source"], e["relation"], e["target"], e["source_ids"]
                )
            store.write(
                'MATCH (m:Metadata {id:"dataset"}) SET m.depth_version=$version',
                dict(version=VERSION),
            )
            if groups or marker == 1:
                store.bump()
