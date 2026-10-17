"""Nationwide reference accounts and cross-department knowledge, versioned separately."""

import hashlib
import json
import re
from collections import defaultdict

VERSION = 1
PRESENTATION_VERSION = 1
DISCLOSURE = "Independent reference workspace: real organisation names, with synthetic private accounts, terms, locations and operations. This is not Delhivery's internal database."

# Public publications establish business context, never these private account terms.
ACCOUNTS = [
    (
        "havells",
        "Havells India",
        "Electrical goods",
        ["Bengaluru", "Delhi", "Kolkata"],
        "pickup_cutoff_hour_local",
        18,
        17,
        "Pickup bookings after the cutoff move to the next working pickup run.",
    ),
    (
        "sugar",
        "SUGAR Cosmetics",
        "Cosmetics",
        ["Bengaluru", "Mumbai", "Hyderabad"],
        "cod_reconciliation_review_days",
        2,
        3,
        "Unmatched cash collections require reconciliation before any loss is asserted.",
    ),
    (
        "hpcl",
        "HPCL",
        "Lubricants",
        ["Bengaluru", "Ahmedabad", "Chennai"],
        "packaging_review_required",
        True,
        False,
        "Packaging acceptance requires Compliance review; this does not authorize hazardous-goods carriage.",
    ),
    (
        "tata-motors",
        "Tata Motors",
        "Automotive",
        ["Pune", "Mumbai", "Delhi"],
        "spare_part_serial_check_required",
        True,
        False,
        "Spare-part serial references must be checked at receiving.",
    ),
    (
        "mamaearth",
        "Mamaearth",
        "Personal care",
        ["Delhi", "Mumbai", "Hyderabad"],
        "return_inspection_window_hours",
        24,
        48,
        "Returned products need inspection before a disposition decision.",
    ),
    (
        "mars-petcare",
        "Mars Petcare",
        "Pet care",
        ["Hyderabad", "Delhi", "Mumbai"],
        "storage_condition_review_required",
        True,
        False,
        "Storage suitability needs a recorded product-handling review, not an inferred temperature specification.",
    ),
    (
        "wakefit",
        "Wakefit",
        "Furniture",
        ["Bengaluru", "Hyderabad", "Pune"],
        "two_person_handling_required",
        True,
        False,
        "Bulky consignments require a two-person handling plan.",
    ),
    (
        "fabindia",
        "Fabindia",
        "Apparel and home",
        ["Delhi", "Jaipur", "Mumbai"],
        "festive_dispatch_cutoff_hour_local",
        17,
        16,
        "The dispatch cutoff governs handover, not a guaranteed final delivery time.",
    ),
    (
        "lenskart",
        "Lenskart",
        "Eyewear",
        ["Delhi", "Kolkata", "Hyderabad"],
        "proof_of_delivery_required",
        True,
        False,
        "A recorded proof of delivery is required to close the delivery task.",
    ),
    (
        "decathlon",
        "Decathlon",
        "Sporting goods",
        ["Bengaluru", "Pune", "Kochi"],
        "volumetric_weight_divisor",
        5000,
        6000,
        "Weight disputes must retain package measurements and the accepted divisor.",
    ),
    (
        "libas",
        "Libas",
        "Apparel",
        ["Delhi", "Jaipur", "Kolkata"],
        "reverse_pickup_window_hours",
        48,
        72,
        "The reverse-pickup review window does not itself approve a refund.",
    ),
    (
        "mokobara",
        "Mokobara",
        "Travel goods",
        ["Bengaluru", "Mumbai", "Hyderabad"],
        "high_value_signature_required",
        True,
        False,
        "High-value handovers need a recipient signature before closure.",
    ),
]
CITIES = {
    "Bengaluru": "Karnataka",
    "Mumbai": "Maharashtra",
    "Delhi": "Delhi",
    "Chennai": "Tamil Nadu",
    "Hyderabad": "Telangana",
    "Pune": "Maharashtra",
    "Kolkata": "West Bengal",
    "Ahmedabad": "Gujarat",
    "Jaipur": "Rajasthan",
    "Kochi": "Kerala",
    "Lucknow": "Uttar Pradesh",
    "Indore": "Madhya Pradesh",
    "Nagpur": "Maharashtra",
    "Gurugram": "Haryana",
}
OLD_CITIES = {
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Kolkata",
    "Ahmedabad",
}
PUBLIC = [
    (
        "account-context-q1",
        "Client context · published mandates",
        "https://www.delhivery.com/uploads/2023/08/PressRelease.pdf",
        "The Q1 FY24 release names Tata Motors and Mamaearth among contracts won. This is historical public business context; private locations and terms are separately modeled.",
    ),
    (
        "account-context-fy24",
        "Client context · annual report",
        "https://www.delhivery.com/uploads/2024/08/Annual_Report_FY24.pdf",
        "The FY24 annual report includes Wakefit, Fabindia, Lenskart, Decathlon, Libas and Mokobara in its client context. The publication does not establish this workspace's warehouse network or contract terms.",
    ),
    (
        "account-context-mars",
        "Client context · Mars Petcare announcement",
        "https://www.delhivery.com/company/press-release",
        "The press archive lists the April 2025 Mars Petcare supply-chain partnership announcement. Operational details in this workspace are independent assumptions.",
    ),
]


def fixture():
    nodes, edges = [], []

    def node(id, kind, title, **p):
        n = dict(id=id, kind=kind, title=title, synthetic=True, **p)
        nodes.append(n)
        return n

    def edge(a, rel, b, proof):
        edges.append(dict(source=a, relation=rel, target=b, source_ids=[proof]))

    def source(
        id,
        title,
        text,
        department="Operations",
        typ="Document",
        timestamp="2026-09-30T09:00:00Z",
        **p,
    ):
        return node(
            id,
            "Source",
            title,
            excerpt=text,
            department=department,
            source_type=typ,
            enabled=True,
            timestamp=timestamp,
            content_hash=hashlib.sha256(text.encode()).hexdigest(),
            **p,
        )

    for id, title, url, text in PUBLIC:
        source(
            id,
            title,
            text,
            "Public",
            "Published reference",
            classification="public_reference",
            url=url,
        )
    source(
        "network-register",
        "National warehouse and movement register",
        "Client pickup locations are distinct from carrier facilities. Each pickup originates at its linked client warehouse; manifests follow a route with the same origin as the shipment's facility. The shipment facility field identifies its processing origin, not its live physical position after delivery. October operational movements are separate from the November scheduling cohort.",
        typ="Operations ledger",
    )
    source(
        "account-finance-register",
        "Account billing and settlement register",
        "Invoices record stored shipping amounts before tax. Cash collections are matched to settlement references; an unmatched collection requires reconciliation and does not establish a cash loss or confirmed bank credit.",
        "Finance",
        "Finance ledger",
    )
    source(
        "account-exception-register",
        "Delivery exception and return register",
        "Delivery attempts can require address correction, appointment changes or handling inspection. Return records preserve their stated reason and quality-review state. A return does not itself approve a refund or compensation.",
        "Operations",
        "Exceptions ledger",
    )
    for city, state in CITIES.items():
        if city not in OLD_CITIES:
            node(
                "facility-" + city.lower(),
                "Facility",
                city + " facility",
                city=city,
                state=state,
                facility_type="Processing centre",
                current_sunday_open=False,
                description="Receiving, sorting and dispatch location.",
            )
            edge(
                "facility-" + city.lower(),
                "OPERATED_BY",
                "team-operations",
                "network-register",
            )
    warehouses = {}
    for i, (
        client,
        title,
        sector,
        cities,
        field,
        value,
        old_value,
        meaning,
    ) in enumerate(ACCOUNTS):
        proof = (
            "public-clients"
            if i < 3
            else "account-context-q1"
            if i < 5
            else "account-context-mars"
            if i == 5
            else "account-context-fy24"
        )
        if i >= 3:
            node(
                client,
                "Client",
                title,
                sector=sector,
                account_status="active",
                account_tier="enterprise" if i % 2 else "growth",
                service_mix=["Express parcel", "Part truckload", "Warehousing"][i % 3],
                description=sector + " account.",
            )
            edge(client, "PUBLIC_RELATIONSHIP", "delhivery", proof)
        edge(client, "OWNED_BY", "team-accounts", "network-register")
        warehouses[client] = []
        for j, city in enumerate(cities):
            wh = (
                "warehouse-" + client
                if i < 3 and j == 0
                else f"warehouse-{client}-{city.lower()}"
            )
            warehouses[client].append((wh, city))
            if not (i < 3 and j == 0):
                node(
                    wh,
                    "ClientWarehouse",
                    f"{title} · {city} {'returns centre' if j == 2 else 'dispatch warehouse'}",
                    client=client,
                    city=city,
                    state=CITIES[city],
                    warehouse_type=["Fulfilment", "Dispatch", "Returns"][j],
                    timezone="Asia/Kolkata",
                    status="active",
                    description="Client inventory, pickup and return handover location.",
                )
                edge(wh, "BELONGS_TO", client, "network-register")
            edge(wh, "AT", "facility-" + city.lower(), "network-register")
            pickup = f"network-pickup-{client}-{j}"
            route = f"network-route-{client}-{j}"
            manifest = f"network-manifest-{client}-{j}"
            destination = cities[(j + 1) % 3]
            node(
                pickup,
                "PickupRequest",
                f"{title} · {city} pickup",
                client=client,
                status="collected",
                pickup_date="2026-10-12",
                warehouse=wh,
                requested_pieces=20 + j * 5,
            )
            edge(pickup, "FROM", wh, "network-register")
            node(
                route,
                "Route",
                f"{city} → {destination} · {title}",
                mode="Road",
                service_type="Part truckload" if i % 3 == 0 else "Express parcel",
                status="active",
            )
            edge(route, "ORIGIN", "facility-" + city.lower(), "network-register")
            edge(
                route,
                "DESTINATION",
                "facility-" + destination.lower(),
                "network-register",
            )
            node(
                manifest,
                "Manifest",
                f"{title} · {city} outbound",
                status="reconciled",
                dispatch_date="2026-10-12",
                client=client,
            )
            edge(manifest, "USES_ROUTE", route, "network-register")
        facility = "facility-" + cities[0].lower()
        policy = f"account-guide-{client}"
        handbook = f"account-handbook-{client}"
        contract = f"account-contract-{client}"
        escalation = [4, 8, 12][i % 3]
        billing = [7, 10, 14][i % 3]
        clauses = [
            (field, value, meaning),
            (
                "service_review_escalation_hours",
                escalation,
                "Escalate unresolved operational reviews to Account Management.",
            ),
            (
                "billing_dispute_window_days",
                billing,
                "Billing disputes need invoice evidence and Finance review before an adjustment.",
            ),
        ]
        source(
            contract,
            title + " · service terms",
            f"Accepted terms effective 1 October 2026 at {cities[0]}: "
            + "; ".join(
                f"{key} = {json.dumps(v)}. {meaning}" for key, v, meaning in clauses
            ),
            "Account Management",
            "Service agreement",
        )
        asserted = old_value if i % 3 == 0 else value
        source(
            handbook,
            title + " · warehouse handling guide",
            f"The handling guide states {field} = {json.dumps(asserted)} and billing_dispute_window_days = {billing}. These are document statements; accepted service terms determine current obligations.",
            typ="Handbook",
            timestamp="2026-09-20T09:00:00Z",
        )
        node(
            policy,
            "Policy",
            title + " operating guide",
            client=client,
            facility=facility,
            status="published",
            department="Operations",
            description="Warehouse and account-handling instructions.",
        )
        edge(policy, "DOCUMENTED_IN", handbook, handbook)
        edge(policy, "OWNED_BY", "team-warehouse", handbook)
        edge(policy, "APPLIES_AT", facility, handbook)
        for key, v, meaning in clauses:
            rid = f"account-rule-{client}-{key}"
            node(
                rid,
                "Rule",
                title + " · " + key.replace("_", " "),
                subject_id=client,
                client=client,
                facility=facility,
                field=key,
                value=v,
                status="accepted",
                valid_from="2026-10-01T00:00:00Z",
                valid_to="",
                recorded_from="2026-09-30T09:00:00Z",
                recorded_to="",
                description=meaning,
            )
            edge(client, "HAS_COMMITMENT", rid, contract)
            edge(rid, "APPLIES_AT", facility, contract)
            edge(rid, "SUPPORTED_BY", contract, contract)
            edge(rid, "OWNED_BY", "team-accounts", contract)
        for key, v in [(field, asserted), ("billing_dispute_window_days", billing)]:
            cid = f"account-claim-{client}-{key}"
            node(
                cid,
                "Claim",
                title + " guide · " + key.replace("_", " "),
                subject_id=client,
                client=client,
                facility=facility,
                field=key,
                value=v,
                status="documented",
                valid_from="2026-09-20T00:00:00Z",
                valid_to="",
                recorded_from="2026-09-20T09:00:00Z",
                recorded_to="",
            )
            edge(policy, "ASSERTS", cid, handbook)
            edge(cid, "SUPPORTED_BY", handbook, handbook)
            edge(cid, "FOR_CLIENT", client, handbook)
            edge(cid, "APPLIES_AT", facility, handbook)
        programme = [
            "Festive replenishment",
            "Regional network rollout",
            "Returns improvement",
            "Inventory rebalance",
        ][i % 4]
        camp = f"programme-{client}"
        brief = f"programme-brief-{client}"
        status = ["active", "completed", "planned"][i % 3]
        source(
            brief,
            title + " · " + programme.lower() + " brief",
            f"{programme} covers {', '.join(cities)}. Programme status: {status}. A planning volume of {800 + i * 125} pieces informs capacity review, not a shipment forecast or a change to service terms. Finance approval is required before extra capacity is booked.",
            "Sales",
            "Programme brief",
        )
        node(
            camp,
            "Campaign",
            title + " · " + programme,
            client=client,
            programme_type=programme,
            status=status,
            start_date="2026-09-15"
            if status == "completed"
            else "2026-10-01"
            if status == "active"
            else "2026-10-20",
            end_date="2026-09-30" if status == "completed" else "2026-10-31",
            planned_pieces=800 + i * 125,
            description="A time-bounded client programme that creates a logistics planning requirement.",
        )
        edge(camp, "FOR_CLIENT", client, brief)
        edge(camp, "DOCUMENTED_IN", brief, brief)
        edge(camp, "OWNED_BY", "team-sales", brief)
        for city in cities:
            edge(camp, "APPLIES_AT", "facility-" + city.lower(), brief)
        ticket = f"account-review-{client}"
        incident = f"account-review-note-{client}"
        decision = f"account-decision-{client}"
        source(
            incident,
            title + " · cross-department review",
            f"Review the {field.replace('_', ' ')} control for {programme.lower()}. {meaning} Operations supplies handling evidence; Account Management verifies accepted terms; Finance reviews proposed costs. Additional capacity is awaiting approval.",
            "Account Management",
            "Review ticket",
        )
        node(
            ticket,
            "Ticket",
            title + " · " + field.replace("_", " ") + " review",
            client=client,
            status=["open", "investigating", "awaiting_client"][i % 3],
            priority="high" if i % 4 == 0 else "medium",
            department="Account Management",
            description=meaning,
        )
        edge(ticket, "SUPPORTED_BY", incident, incident)
        edge(ticket, "OWNED_BY", "team-accounts", incident)
        edge(ticket, "FOR_CLIENT", client, incident)
        edge(ticket, "AFFECTS", camp, incident)
        source(
            "account-chat-" + client,
            title + " · capacity discussion",
            "Proposal: book additional handling capacity after Finance review. No capacity purchase or service-term amendment has been approved by this discussion.",
            "Operations",
            "Chat proposal",
        )
        edge("account-chat-" + client, "DISCUSSES", ticket, "account-chat-" + client)
        node(
            decision,
            "Decision",
            title + " · retain accepted controls during programme review",
            client=client,
            status="recorded",
            approved=True,
            description="Continue accepted handling controls; extra capacity remains subject to approval.",
        )
        edge(decision, "WHY", ticket, incident)
        edge(decision, "EXPLAINED_BY", incident, incident)
        edge(decision, "OWNED_BY", "team-accounts", incident)
        for j, team in enumerate(["operations", "accounts", "finance"]):
            work = f"work-{client}-{team}"
            task = [
                "Collect handling evidence",
                "Review current service terms",
                "Review capacity budget",
            ][j]
            node(
                work,
                "WorkItem",
                title + " · " + task,
                client=client,
                status=["open", "in_progress", "awaiting_review"][(i + j) % 3],
                department={
                    "operations": "Operations",
                    "accounts": "Account Management",
                    "finance": "Finance",
                }[team],
                due_at=f"2026-10-{18 + (i % 5):02}T12:00:00Z",
                description="Pending internal review work; no external change has been executed.",
            )
            edge(work, "RESOLVES", ticket, incident)
            edge(work, "OWNED_BY", "team-" + team, incident)
            edge(work, "SUPPORTED_BY", incident, incident)
            person = f"depth-person-{ {'operations': 0, 'accounts': 2, 'finance': 3}[team] }-{i % 3}"
            edge(work, "ASSIGNED_TO", person, incident)
            edge(person, "KNOWS_ABOUT", policy, handbook)
        for k in range(40):
            j = k % 3
            wh, city = warehouses[client][j]
            sid = f"network-shipment-{client}-{k:03}"
            status = [
                "delivered",
                "in_transit",
                "out_for_delivery",
                "delivery_failed",
                "returned_to_origin",
                "return_initiated",
                "on_hold",
                "received_at_facility",
                "delivery_rescheduled",
                "damaged_at_facility",
            ][k % 10]
            node(
                sid,
                "Shipment",
                f"AWB-{i + 20:02}{k:06}",
                client=client,
                facility="facility-" + city.lower(),
                status=status,
                arrival_at="2026-10-12T08:00:00Z",
                snapshot_at="2026-10-15T12:00:00Z",
                payment_mode="COD" if (k // 10 + i) % 2 else "Prepaid",
                declared_weight_kg=round(0.5 + (k % 15) * 0.4, 2),
                measured_weight_kg=round(
                    0.5 + (k % 15) * 0.4 + (0.3 if k % 13 == 0 else 0), 2
                ),
                service_type="Part truckload"
                if sector in {"Furniture", "Automotive", "Lubricants"}
                else "Express parcel",
                warehouse=wh,
                description="October movement in the account's regional network.",
            )
            for rel, target in [
                ("FOR_CLIENT", client),
                ("AT", "facility-" + city.lower()),
                ("COLLECTED_BY", f"network-pickup-{client}-{j}"),
                ("ON_MANIFEST", f"network-manifest-{client}-{j}"),
            ]:
                edge(sid, rel, target, "network-register")
            for sequence, state in enumerate(["manifested", "collected", status]):
                scan = f"network-scan-{client}-{k:03}-{sequence}"
                node(
                    scan,
                    "ScanEvent",
                    state,
                    sequence=sequence,
                    event_at=f"2026-10-{10 + sequence:02}T08:00:00Z",
                    facility="facility-" + city.lower(),
                )
                edge(sid, "HAS_SCAN", scan, "network-register")
            if status in {
                "delivery_failed",
                "on_hold",
                "delivery_rescheduled",
                "damaged_at_facility",
            }:
                eid = f"network-exception-{client}-{k:03}"
                reason = {
                    "delivery_failed": "address_confirmation_needed",
                    "on_hold": "quality_review",
                    "delivery_rescheduled": "appointment_change",
                    "damaged_at_facility": "handling_inspection",
                }[status]
                owner = (
                    "team-accounts"
                    if status in {"delivery_failed", "delivery_rescheduled"}
                    else "team-warehouse"
                )
                node(
                    eid,
                    "DeliveryException",
                    title + " · " + reason.replace("_", " "),
                    client=client,
                    status="open",
                    reason=reason,
                    next_action="owner_review",
                    facility="facility-" + city.lower(),
                )
                edge(sid, "HAS_EXCEPTION", eid, "account-exception-register")
                edge(eid, "OWNED_BY", owner, "account-exception-register")
                edge(
                    eid,
                    "SUPPORTED_BY",
                    "account-exception-register",
                    "account-exception-register",
                )
            if status in {"returned_to_origin", "return_initiated"}:
                rid = f"network-return-{client}-{k:03}"
                node(
                    rid,
                    "Return",
                    title + " · return " + str(k),
                    client=client,
                    status=status,
                    reason="consignee_refused" if k % 2 else "unsuccessful_delivery",
                    quality_check="pending"
                    if status == "return_initiated"
                    else "inspected",
                )
                edge(rid, "RETURN_OF", sid, "account-exception-register")
                edge(rid, "OWNED_BY", "team-warehouse", "account-exception-register")
            if status == "delivered" and (k // 10 + i) % 2:
                cid = f"network-cod-{client}-{k:03}"
                rem = f"network-remittance-{client}-{k:03}"
                amount = 900 + i * 120 + k * 20
                settled = (k // 10 + i) % 3 != 0
                node(
                    cid,
                    "CODCollection",
                    title + " · cash collection " + str(k),
                    client=client,
                    amount_inr=amount,
                    status="collected",
                    collected_at="2026-10-12T08:00:00Z",
                )
                node(
                    rem,
                    "Remittance",
                    title + " · settlement " + str(k),
                    client=client,
                    amount_inr=amount if settled else 0,
                    status="settled" if settled else "reconciling",
                    batch_reference=f"SETTLEMENT-{client}-{k:03}",
                )
                edge(cid, "COVERS", sid, "account-finance-register")
                edge(rem, "RECONCILES", cid, "account-finance-register")
                edge(rem, "OWNED_BY", "team-finance", "account-finance-register")
            if k == 0:
                edge(ticket, "AFFECTS", sid, incident)
        for j in range(3):
            invoice = f"network-invoice-{client}-{j}"
            amount = 1800 + i * 250 + j * 900
            node(
                invoice,
                "Invoice",
                title + " · invoice " + str(j + 1),
                client=client,
                amount_inr=amount,
                tax_inr=round(amount * 0.18, 2),
                currency="INR",
                status=["paid", "open", "disputed"][(i + j) % 3],
                department="Finance",
                issue_date="2026-10-12",
                due_date="2026-10-26",
            )
            edge(invoice, "BILLED_TO", client, "account-finance-register")
            edge(invoice, "OWNED_BY", "team-finance", "account-finance-register")
            edge(
                invoice,
                "COVERS",
                f"network-shipment-{client}-{j:03}",
                "account-finance-register",
            )
            edge(
                invoice,
                "SUPPORTED_BY",
                "account-finance-register",
                "account-finance-register",
            )
    edge("campaign", "FOR_CLIENT", "havells", "source-campaign")
    edge("campaign", "OWNED_BY", "team-sales", "source-campaign")
    edge("decision-sunday", "WHY", "campaign", "source-campaign")
    return nodes, edges


def clean_record(record):
    """Remove repeated presentation disclaimers; retain flags and business meaning."""
    n = dict(record)
    for field in (
        "title",
        "description",
        "excerpt",
        "source_type",
        "facility_type",
        "schedule",
    ):
        text = n.get(field)
        if not isinstance(text, str):
            continue
        text = re.sub(r"^SYNTHETIC ([A-Z -]+)\.\s*", "", text)
        text = re.sub(r"\bsynthetic\s+", "", text, flags=re.I)
        text = (
            text.replace("This demo models", "This record covers")
            .replace("this demo", "this workspace")
            .replace("the demo's", "the workspace's")
        )
        text = re.sub(r"\bdemo\s+", "", text, flags=re.I)
        text = text.replace("DEMO-OCT-", "OCT-").replace("DEMO-", "")
        n[field] = text
    if n["kind"] == "Client" and n.get("description", "").startswith(
        "Real company name;"
    ):
        n["description"] = n.get("sector", "Client") + " account."
    if n["kind"] == "Company":
        n["description"] = (
            "Company context for connected logistics, account and department records."
        )
    if n["kind"] == "Facility":
        n["description"] = "Receiving, processing and dispatch location."
    if n["kind"] == "Shipment" and n["id"].startswith("shipment-"):
        n["description"] = "Planned consignment in the Bengaluru scheduling cohort."
        n["scenario_cohort"] = "bengaluru-scheduling"
    if n["kind"] == "Person":
        n["description"] = (
            "Current role, team membership and recorded subject expertise."
        )
    if n["kind"] == "Source":
        if n.get("classification") == "public_reference":
            n["synthetic"] = False
        n["content_hash"] = hashlib.sha256(n.get("excerpt", "").encode()).hexdigest()
    return n


def upgrade(store):
    """Add coverage once, then refresh business labels without rewriting history."""
    from .schema import persist

    marker = store.read(
        "MATCH (m:Metadata {id:'dataset'}) RETURN coalesce(m.coverage_version,0),coalesce(m.presentation_version,0)"
    )[0]
    changed = False
    if marker[0] < VERSION:
        nodes, edges = fixture()
        ids = {
            r[0]
            for r in store.read(
                "MATCH (n:Entity) WHERE n.id IN $ids RETURN n.id",
                dict(ids=[n["id"] for n in nodes]),
            )
        }
        groups = defaultdict(list)
        for n in nodes:
            if n["id"] not in ids:
                groups[n["kind"]].append(clean_record(n))
        for kind, group in groups.items():
            for start in range(0, len(group), 250):
                persist(store, group[start : start + 250], kind)
        by_relation = defaultdict(list)
        for e in edges:
            by_relation[e["relation"]].append(e)
        for rel, group in by_relation.items():
            assert re.fullmatch(r"[A-Z][A-Z0-9_]{0,47}", rel)
            for start in range(0, len(group), 250):
                store.write(
                    f"UNWIND $rows AS x MATCH (a:Entity {{id:x.source}}),(b:Entity {{id:x.target}}) MERGE (a)-[r:{rel}]->(b) SET r.source_ids=x.source_ids",
                    dict(rows=group[start : start + 250]),
                )
        changed = True
    if marker[1] < PRESENTATION_VERSION:
        groups = defaultdict(list)
        for (raw,) in store.read_all(
            "MATCH (n:Entity) WHERE NOT n.kind IN ['Receipt','Action','DemoSession'] RETURN n.payload ORDER BY n.id"
        ):
            before = json.loads(raw)
            after = clean_record(before)
            if after != before:
                groups[after["kind"]].append(after)
        for kind, group in groups.items():
            for start in range(0, len(group), 250):
                persist(store, group[start : start + 250], kind)
        changed = changed or bool(groups)
    if changed:
        config = store.demo_config()
        if config:
            from .demo import CONFIG

            store.write(
                "MATCH (m:Metadata {id:'dataset'}) SET m.demo_config=$config",
                dict(config=json.dumps(CONFIG)),
            )
        store.write(
            "MATCH (m:Metadata {id:'dataset'}) SET m.coverage_version=$coverage,m.presentation_version=$presentation",
            dict(coverage=VERSION, presentation=PRESENTATION_VERSION),
        )
        store.bump()
