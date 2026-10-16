"""Versioned synthetic business depth; public concepts, never private company facts."""

import hashlib

VERSION = 2
RELATIONS = {
    "HAS_EXCEPTION",
    "RETURN_OF",
    "RECONCILES",
    "BILLED_TO",
    "COVERS",
    "ASSIGNED_TO",
    "MEMBER_OF",
    "DISCUSSES",
    "RESOLVES",
    "AFFECTS",
    "USES_VEHICLE",
    "KNOWS_ABOUT",
}


def extension():
    nodes, edges = [], []

    def node(id, kind, title, **data):
        nodes.append(dict(id=id, kind=kind, title=title, synthetic=True, **data))

    def edge(a, rel, b, proof="depth-source-operations"):
        edges.append(dict(source=a, relation=rel, target=b, source_ids=[proof]))

    def source(id, title, text, department, typ="Synthetic document"):
        excerpt = "SYNTHETIC EXAMPLE. " + text
        node(
            id,
            "Source",
            title,
            excerpt=excerpt,
            department=department,
            source_type=typ,
            enabled=True,
            timestamp="2026-10-12T09:00:00Z",
            content_hash=hashlib.sha256(excerpt.encode()).hexdigest(),
        )

    source(
        "depth-source-operations",
        "October operations snapshot",
        "October sample shipments span delivery, transit, failed attempts, returns and holds across seven facilities. Snapshot at 12 October; future November scenario shipments are a separate planned demo cohort. IDs, events, routes and customer outcomes are fictional.",
        "Operations",
        "Synthetic event ledger",
    )
    source(
        "depth-source-cod",
        "COD reconciliation procedure",
        "Finance reconciles collected cash against settlement batches. A pending settlement is not proof of cash loss. Disputed entries require shipment-level reconciliation and a finance reviewer before adjustment. This fixture specifies no real Delhivery settlement SLA.",
        "Finance",
    )
    source(
        "depth-source-returns",
        "Returns and failed-attempt procedure",
        "An unsuccessful delivery records a reason and a next action: retry, request address correction, or return for client review. Damaged returns need inspection. Address corrections require client confirmation before a retry. A failed attempt alone does not authorize disposal or compensation.",
        "Operations",
    )
    source(
        "depth-source-billing",
        "Weight dispute and invoice review",
        "Billing disputes must retain measured and declared weights, invoice line evidence and client correspondence. Finance owns billing adjustments; Operations owns reweigh evidence. Do not infer a charge from parcel weight without an accepted rate card.",
        "Finance",
    )
    source(
        "depth-source-people",
        "Synthetic role and expertise directory",
        "Role identities are fictional placeholders, not Delhivery employees. Membership and expertise describe the current fixture only. Operations handles capacity, Finance handles reconciliation, Compliance reviews claims, Technology handles scan ingestion incidents.",
        "People",
    )
    stories = [
        (
            "capacity",
            "Mumbai peak capacity",
            "operations",
            "A temporary sorting backlog needs a staffing review",
            "planned",
            "No outage or future delay has been predicted. Staffing approval is pending.",
        ),
        (
            "scan",
            "Hyderabad missing scan events",
            "technology",
            "A delayed scan feed made tracking incomplete",
            "investigating",
            "A tracking gap is not evidence that a parcel is lost. Reconcile the manifest with physical scans.",
        ),
        (
            "weight",
            "Havells invoice weight dispute",
            "finance",
            "Declared and measured weights differ on a billed consignment",
            "review_required",
            "The proposed credit is not approved. Operations must supply reweigh evidence.",
        ),
        (
            "cod",
            "SUGAR COD settlement mismatch",
            "finance",
            "A collection is not matched to its settlement batch",
            "reconciling",
            "Investigate the batch reference before asserting a financial loss.",
        ),
        (
            "return",
            "Chennai return quality check",
            "warehouse",
            "A returned parcel needs a damage inspection",
            "inspection_pending",
            "No client refund or compensation is approved by this record.",
        ),
        (
            "address",
            "Pune incomplete address",
            "accounts",
            "A delivery retry needs a corrected address",
            "awaiting_client",
            "Do not expose personal addresses in this demo; only city and synthetic postal zones are stored.",
        ),
        (
            "weather",
            "Kolkata weather contingency",
            "transport",
            "A route contingency was proposed after a weather advisory",
            "proposed",
            "The chat is a proposal, not an approved reroute or a confirmed delivery prediction.",
        ),
        (
            "safety",
            "HPCL packaging review",
            "compliance",
            "A packaging exception needs a compliance review",
            "on_hold",
            "This does not model or approve hazardous-goods carriage. No real product handling classification is asserted.",
        ),
    ]
    for i, (key, title, team, problem, status, limit) in enumerate(stories):
        proof = "depth-source-incident-" + key
        source(
            proof,
            title + " · incident ticket",
            problem + ". " + limit,
            team.title(),
            "Synthetic ticket",
        )
        node(
            "depth-ticket-" + key,
            "Ticket",
            title,
            status=status,
            priority=["high", "medium", "low"][i % 3],
            department=team.title(),
            description=problem + ". " + limit,
            opened_at="2026-10-12T08:00:00Z",
        )
        node(
            "depth-decision-" + key,
            "Decision",
            title + " · review decision",
            status="proposed" if status == "proposed" else "recorded",
            description=limit,
        )
        edge("depth-ticket-" + key, "SUPPORTED_BY", proof, proof)
        edge("depth-ticket-" + key, "OWNED_BY", "team-" + team, proof)
        edge("depth-decision-" + key, "WHY", "depth-ticket-" + key, proof)
        edge("depth-decision-" + key, "DOCUMENTED_IN", proof, proof)
        edge("depth-decision-" + key, "OWNED_BY", "team-" + team, proof)
        node(
            "depth-chat-" + key,
            "Source",
            title + " · team discussion",
            excerpt="SYNTHETIC CHAT PROPOSAL. Please review: " + limit,
            department=team.title(),
            source_type="Synthetic chat",
            enabled=True,
            timestamp="2026-10-12T10:00:00Z",
            content_hash=hashlib.sha256(
                ("SYNTHETIC CHAT PROPOSAL. Please review: " + limit).encode()
            ).hexdigest(),
        )
        edge(
            "depth-chat-" + key, "DISCUSSES", "depth-ticket-" + key, "depth-chat-" + key
        )
    clients = ["havells", "sugar", "hpcl"]
    cities = ["mumbai", "delhi", "chennai", "hyderabad", "pune", "kolkata", "ahmedabad"]
    for i, team in enumerate(
        [
            "operations",
            "sales",
            "accounts",
            "finance",
            "transport",
            "warehouse",
            "compliance",
            "technology",
        ]
    ):
        for j in range(3):
            id = f"depth-person-{i}-{j}"
            node(
                id,
                "Person",
                f"DEMO {team.title()} role {j + 1}",
                role=["Lead", "Analyst", "Reviewer"][j],
                department=team.title(),
                identity_type="fictional_role",
                description="Synthetic role identity, not a real employee.",
            )
            edge(id, "MEMBER_OF", "team-" + team, "depth-source-people")
            edge(
                id,
                "KNOWS_ABOUT",
                ["depth-ticket-capacity", "depth-ticket-cod", "depth-ticket-scan"][j],
                "depth-source-people",
            )
    for i in range(21):
        city = cities[i % 7]
        node(
            f"depth-vehicle-{i:02}",
            "Vehicle",
            f"DEMO fleet unit {i:02}",
            vehicle_type=["van", "rigid_truck", "linehaul_truck"][i % 3],
            capacity_kg=[1000, 7000, 16000][i % 3],
            status=["available", "assigned", "maintenance"][i % 3],
            facility="facility-" + city,
        )
        edge(f"depth-vehicle-{i:02}", "AT", "facility-" + city)
        node(
            f"depth-route-{i:02}",
            "Route",
            city.title() + " → " + cities[(i + 1) % 7].title(),
            mode="Road",
            status="planned",
        )
        edge(f"depth-route-{i:02}", "ORIGIN", "facility-" + city)
        edge(f"depth-route-{i:02}", "DESTINATION", "facility-" + cities[(i + 1) % 7])
        node(
            f"depth-manifest-{i:02}",
            "Manifest",
            f"DEMO-OCT-MANIFEST-{i:02}",
            status=["closed", "dispatched", "reconciled"][i % 3],
        )
        edge(f"depth-manifest-{i:02}", "USES_ROUTE", f"depth-route-{i:02}")
        edge(f"depth-manifest-{i:02}", "USES_VEHICLE", f"depth-vehicle-{i:02}")
        node(
            f"depth-pickup-{i:02}",
            "PickupRequest",
            f"DEMO-OCT-PICKUP-{i:02}",
            status="collected",
            pickup_date="2026-10-10",
            client=clients[i % 3],
        )
        edge(f"depth-pickup-{i:02}", "FROM", "warehouse-" + clients[i % 3])
    statuses = [
        "delivered",
        "in_transit",
        "out_for_delivery",
        "delivery_failed",
        "return_initiated",
        "returned_to_origin",
        "on_hold",
    ]
    for i in range(210):
        client = clients[i % 3]
        city = cities[i % 7]
        status = statuses[i % 7]
        sid = f"depth-shipment-{i:04}"
        node(
            sid,
            "Shipment",
            f"DEMO-OCT-AWB-{i:06}",
            client=client,
            facility="facility-" + city,
            status=status,
            arrival_at="2026-10-11T08:00:00Z",
            snapshot_at="2026-10-12T12:00:00Z",
            payment_mode="COD" if i % 2 else "Prepaid",
            declared_weight_kg=round(0.5 + (i % 25) * 0.2, 2),
            measured_weight_kg=round(
                0.5 + (i % 25) * 0.2 + (0.4 if i % 11 == 0 else 0), 2
            ),
            service_type=["express_parcel", "surface_parcel", "reverse_pickup"][i % 3],
            description="Synthetic October operational snapshot, separate from the November scheduling cohort.",
        )
        for rel, target in [
            ("FOR_CLIENT", client),
            ("AT", "facility-" + city),
            ("COLLECTED_BY", f"depth-pickup-{i % 21:02}"),
            ("ON_MANIFEST", f"depth-manifest-{i % 21:02}"),
        ]:
            edge(sid, rel, target)
        for j, stage in enumerate(["manifested", "collected", status]):
            scan = f"depth-scan-{i:04}-{j}"
            node(
                scan,
                "ScanEvent",
                stage,
                event_at=f"2026-10-{10 + j:02}T08:00:00Z",
                sequence=j,
                facility="facility-" + city,
            )
            edge(sid, "HAS_SCAN", scan)
        if status in {"delivery_failed", "on_hold"}:
            eid = f"depth-exception-{i:04}"
            node(
                eid,
                "DeliveryException",
                f"{city.title()} · {status}",
                reason="incomplete_address"
                if status == "delivery_failed"
                else "packaging_review",
                status="open",
                next_action="client_review",
                client=client,
            )
            edge(sid, "HAS_EXCEPTION", eid, "depth-source-returns")
            edge(eid, "OWNED_BY", "team-accounts", "depth-source-returns")
            edge(eid, "SUPPORTED_BY", "depth-source-returns", "depth-source-returns")
        if status in {"return_initiated", "returned_to_origin"}:
            rid = f"depth-return-{i:04}"
            node(
                rid,
                "Return",
                f"Return {i:04}",
                status=status,
                reason="consignee_refused" if i % 2 else "unsuccessful_delivery",
                quality_check="pending"
                if status == "return_initiated"
                else "inspected",
                client=client,
            )
            edge(rid, "RETURN_OF", sid, "depth-source-returns")
            edge(rid, "OWNED_BY", "team-warehouse", "depth-source-returns")
        if i % 2 and status == "delivered":
            cid = f"depth-cod-{i:04}"
            rid = f"depth-remittance-{i:04}"
            amount = 750 + (i % 20) * 125
            node(
                cid,
                "CODCollection",
                f"COD collection {i:04}",
                client=client,
                amount_inr=amount,
                status="collected",
                collected_at="2026-10-12T08:00:00Z",
            )
            node(
                rid,
                "Remittance",
                f"Settlement {i:04}",
                client=client,
                amount_inr=0 if i % 5 == 2 else amount,
                status="reconciling" if i % 5 == 2 else "settled",
                batch_reference=f"DEMO-BATCH-{i:04}",
            )
            edge(cid, "COVERS", sid, "depth-source-cod")
            edge(rid, "RECONCILES", cid, "depth-source-cod")
            edge(rid, "OWNED_BY", "team-finance", "depth-source-cod")
    for i in range(36):
        client = clients[i % 3]
        id = f"depth-invoice-{i:03}"
        node(
            id,
            "Invoice",
            f"DEMO invoice {i:03}",
            client=client,
            amount_inr=1200 + i * 175,
            tax_inr=round((1200 + i * 175) * 0.18, 2),
            currency="INR",
            status=["paid", "open", "disputed"][(i // 3) % 3],
            department="Finance",
            issue_date="2026-10-12",
            due_date="2026-10-26",
            description="Synthetic shipping invoice. No real tariff is represented.",
        )
        edge(id, "BILLED_TO", client, "depth-source-billing")
        edge(id, "OWNED_BY", "team-finance", "depth-source-billing")
        edge(id, "SUPPORTED_BY", "depth-source-billing", "depth-source-billing")
        edge(id, "COVERS", f"depth-shipment-{i:04}", "depth-source-billing")
    policies = [
        (
            "cod-review",
            "COD discrepancy review",
            "finance",
            "depth-source-cod",
            "finance_review_required",
            True,
        ),
        (
            "return-inspection",
            "Damaged return inspection",
            "warehouse",
            "depth-source-returns",
            "inspection_required_before_disposal",
            True,
        ),
        (
            "billing-review",
            "Weight dispute evidence",
            "finance",
            "depth-source-billing",
            "reweigh_evidence_required",
            True,
        ),
        (
            "address-review",
            "Address correction approval",
            "accounts",
            "depth-source-returns",
            "client_confirmation_required",
            True,
        ),
    ]
    for key, title, team, proof, field, value in policies:
        pid = "depth-policy-" + key
        rid = "depth-rule-" + key
        node(
            pid,
            "Policy",
            title,
            description="Accepted synthetic review control; not a real Delhivery policy.",
            department=team.title(),
        )
        node(
            rid,
            "Rule",
            title + " · accepted control",
            subject_id=pid,
            field=field,
            value=value,
            status="accepted",
            valid_from="2026-10-12T00:00:00Z",
            valid_to="",
            recorded_from="2026-10-12T09:00:00Z",
            recorded_to="",
        )
        edge(pid, "HAS_COMMITMENT", rid, proof)
        edge(rid, "SUPPORTED_BY", proof, proof)
        edge(pid, "OWNED_BY", "team-" + team, proof)
        edge(pid, "DOCUMENTED_IN", proof, proof)
    # Cross-department incident paths link decisions to concrete operational evidence.
    for key, target in [
        ("cod", "depth-remittance-0007"),
        ("weight", "depth-invoice-006"),
        ("return", "depth-return-0004"),
        ("address", "depth-exception-0003"),
        ("scan", "depth-shipment-0010"),
        ("capacity", "facility-mumbai"),
        ("weather", "depth-route-05"),
        ("safety", "depth-exception-0006"),
    ]:
        edge("depth-ticket-" + key, "AFFECTS", target, "depth-source-incident-" + key)
    return nodes, edges
