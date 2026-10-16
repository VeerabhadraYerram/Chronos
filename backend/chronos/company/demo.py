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
