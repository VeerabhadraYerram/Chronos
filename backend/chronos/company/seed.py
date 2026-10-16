"""A documented logistics reference model, never Delhivery's private schema/data."""

import hashlib
from datetime import datetime, timedelta, timezone

PUBLIC_SOURCES = [
    (
        "public-services",
        "Delhivery · published services",
        "https://www.delhivery.com/services/express-parcel",
        "Public reference",
        "Delhivery publishes express parcel delivery services. This establishes the business context, not the demo's private operating rules.",
    ),
    (
        "public-lifecycle",
        "Delhivery One · order lifecycle",
        "https://help.delhivery.com/docs/update-forward-order",
        "Public reference",
        "Public help documents distinguish Pending, Ready to Ship, Ready for Pickup, In Transit and Out for Delivery stages, with different editable attributes.",
    ),
    (
        "public-pickups",
        "Delhivery · developer FAQ",
        "https://one.delhivery.com/developer-portal/document/b2c/detail/faq",
        "Public reference",
        "The public developer FAQ describes client warehouses, pickup requests, waybills and tracking events. These concepts inform this independently designed schema.",
    ),
    (
        "public-clients",
        "Delhivery · partnership announcements",
        "https://www.delhivery.com/company/press-release",
        "Public reference",
        "Delhivery's press archive lists relationships with Havells India, HPCL and SUGAR Cosmetics. Their inclusion does not establish any demo agreement, location, service level or Sunday arrangement.",
    ),
]
CLIENTS = [
    ("havells", "Havells India", "Electrical goods"),
    ("sugar", "SUGAR Cosmetics", "Cosmetics"),
    ("hpcl", "HPCL", "Lubricants"),
]
TEAMS = [
    ("operations", "Operations", "Facility scheduling and processing"),
    ("sales", "Sales", "Commercial commitments"),
    ("accounts", "Account Management", "Client amendments and communication"),
    ("finance", "Finance", "Documented staffing costs"),
    ("transport", "Transport", "Linehaul manifests and dispatch"),
    ("warehouse", "Warehouse", "Inbound scans and sorting"),
    ("compliance", "Compliance", "Agreement review"),
    ("technology", "Technology", "Operational systems"),
]
CITIES = [
    "Bengaluru",
    "Mumbai",
    "Delhi",
    "Chennai",
    "Hyderabad",
    "Pune",
    "Kolkata",
    "Ahmedabad",
]


def fixture():
    nodes, edges = [], []

    def node(id, kind, title, **p):
        n = dict(id=id, kind=kind, title=title, synthetic=True, **p)
        nodes.append(n)
        return n

    def edge(a, rel, b, evidence=None):
        edges.append(dict(source=a, relation=rel, target=b, source_ids=evidence or []))

    def source(id, title, excerpt, department, date="2026-05-01", **p):
        return node(
            id,
            "Source",
            title,
            excerpt=excerpt,
            department=department,
            source_type=p.pop("source_type", "Demo document"),
            enabled=True,
            timestamp=date + "T09:00:00Z",
            content_hash=hashlib.sha256(excerpt.encode()).hexdigest(),
            **p,
        )

    node(
        "delhivery",
        "Company",
        "Delhivery",
        description="Independent reference demo using public business concepts. Not an internal system or affiliated product.",
    )
    for id, title, url, typ, excerpt in PUBLIC_SOURCES:
        source(
            id,
            title,
            excerpt,
            "Public",
            source_type=typ,
            url=url,
            classification="public_reference",
        )
    for id, title, role in TEAMS:
        node("team-" + id, "Team", title, description=role)
        edge("team-" + id, "PART_OF", "delhivery")
    for i, city in enumerate(CITIES):
        node(
            "facility-" + city.lower(),
            "Facility",
            city + " facility",
            city=city,
            facility_type="Demo processing centre",
            current_sunday_open=(i == 0),
            description="Synthetic facility; no actual Delhivery warehouse identity or operating schedule is represented.",
        )
        edge(
            "facility-" + city.lower(),
            "OPERATED_BY",
            "team-operations",
            ["source-schedule"],
        )
    for id, title, sector in CLIENTS:
        node(
            id,
            "Client",
            title,
            sector=sector,
            description="Real company name; agreements and activity in this workspace are synthetic.",
        )
        edge(id, "PUBLIC_RELATIONSHIP", "delhivery", ["public-clients"])
        node(
            "warehouse-" + id,
            "ClientWarehouse",
            title + " pickup location",
            city="Bengaluru",
            description="Synthetic registered pickup location",
        )
        edge("warehouse-" + id, "BELONGS_TO", id, ["source-schedule"])
    source(
        "source-havells-agreement",
        "Havells · demo service agreement",
        "SYNTHETIC AGREEMENT. Bengaluru must process Havells consignments on Sundays as well as Monday–Saturday. This is an ongoing commitment; a campaign ending does not end the obligation. Account Management owns amendments.",
        "Sales",
    )
    source(
        "source-sugar-agreement",
        "SUGAR · demo service agreement",
        "SYNTHETIC AGREEMENT. Bengaluru processes SUGAR consignments Monday–Saturday. Sunday arrivals can wait until Monday. No Sunday-processing commitment is recorded.",
        "Sales",
    )
    source(
        "source-hpcl-agreement",
        "HPCL · demo service agreement",
        "SYNTHETIC AGREEMENT. Bengaluru processes HPCL consignments Monday–Saturday. Sunday processing is not required. This demo models scheduling only, not hazardous-goods handling.",
        "Sales",
    )
    source(
        "source-campaign",
        "Havells · demo campaign handover",
        "SYNTHETIC SALES NOTE. Sunday processing was requested for the Havells weekend campaign. The campaign ended September 30, 2026. The signed service commitment continues unless an approved amendment changes it.",
        "Sales",
        source_type="Demo handover",
        date="2026-09-30",
    )
    source(
        "source-schedule",
        "Bengaluru · current demo schedule",
        "SYNTHETIC OPERATING POLICY. Bengaluru is open for Havells processing on Sundays. SUGAR and HPCL follow six-day processing. Operations owns the facility schedule; Transport owns dispatch. Processing is not proof of final delivery.",
        "Operations",
        source_type="Demo handbook",
    )
    source(
        "source-finance",
        "Bengaluru · demo Sunday staffing estimate",
        "SYNTHETIC FINANCE SHEET. A full Sunday shift costs INR 18,000 in this fixture. A retained Havells-only shift costs INR 7,000. These are supplied scenario assumptions, not measured Delhivery costs, guaranteed savings or a complete cost model.",
        "Finance",
        source_type="Demo cost sheet",
        full_shift_inr=18000,
        restricted_shift_inr=7000,
    )
    source(
        "source-proposal",
        "Operations · Sunday closure proposal",
        "SYNTHETIC CHAT. Proposal: close Bengaluru on Sundays because volumes are lower. Account Management: discussion is not client approval; confirm Havells' active agreement and amendment effective date first. No policy was approved in this thread.",
        "Operations",
        date="2026-10-14",
        source_type="Demo chat export",
        approval_status="proposal",
    )
    source(
        "source-ticket",
        "Warehouse · demo Sunday processing ticket",
        "SYNTHETIC TICKET OPS-214. Havells consignments were held pending a Sunday staffing decision. The resolution referred staff to the accepted agreement, not the closure suggestion. No real customer incident is described.",
        "Warehouse",
        date="2026-10-12",
        source_type="Demo ticket",
    )
    source(
        "source-dispatch",
        "Transport · demo processing handover",
        "SYNTHETIC ROUTING RULE. Consignments at the Bengaluru facility on a closed Sunday are scheduled for Monday processing. Keeping a client exception permits Sunday processing for that client. Neither rule determines delivery time or actual vehicle capacity.",
        "Transport",
    )
    source(
        "source-owners",
        "Department review responsibilities",
        "SYNTHETIC RESPONSIBILITY MATRIX. Operations owns facility hours; Sales owns original commitments; Account Management owns client amendments; Finance reviews staffing assumptions; Transport updates dispatch; Warehouse updates handling instructions.",
        "Operations",
    )
    source(
        "source-technology",
        "Technology · demo change checklist",
        "SYNTHETIC CHECKLIST. Update the approved processing calendar, route scheduler configuration and warehouse handbook together. Do not disable tracking or pickup request validation. No real system is connected.",
        "Technology",
    )
    node(
        "decision-sunday",
        "Decision",
        "Keep Sunday processing for Havells",
        description="The recorded client promise outlives the launch campaign.",
        approved=True,
    )
    node(
        "campaign",
        "Campaign",
        "Havells weekend campaign",
        ended_at="2026-09-30",
        description="Synthetic campaign; its end does not amend an agreement.",
    )
    edge("decision-sunday", "EXPLAINED_BY", "source-campaign", ["source-campaign"])
    edge("decision-sunday", "OWNED_BY", "team-sales", ["source-owners"])
    edge("campaign", "DOCUMENTED_IN", "source-campaign", ["source-campaign"])
    node(
        "policy-schedule",
        "Policy",
        "Bengaluru processing handbook",
        sunday_required=True,
        sunday_clients=["havells"],
        description="Current demo handbook still tells staff to keep Havells Sunday processing.",
    )
    edge("policy-schedule", "DOCUMENTED_IN", "source-schedule", ["source-schedule"])
    edge("policy-schedule", "APPLIES_AT", "facility-bengaluru", ["source-schedule"])
    edge("policy-schedule", "OWNED_BY", "team-warehouse", ["source-owners"])
    node("decision-proposal", "Decision", "Proposal: close Sundays", approved=False)
    edge("decision-proposal", "SUPPORTED_BY", "source-proposal", ["source-proposal"])
    edge("decision-proposal", "APPLIES_AT", "facility-bengaluru", ["source-proposal"])
    for id, title, _ in CLIENTS:
        rule_id = "rule-" + id + "-original"
        node(
            rule_id,
            "Rule",
            title
            + " · "
            + (
                "Sunday processing required"
                if id == "havells"
                else "Monday–Saturday processing"
            ),
            client=id,
            facility="facility-bengaluru",
            field="sunday_processing_required",
            value=id == "havells",
            status="accepted",
            valid_from="2026-05-01T00:00:00Z",
            valid_to="",
            recorded_from="2026-05-02T09:00:00Z",
            recorded_to="",
            description="Accepted synthetic service commitment",
        )
        edge(id, "HAS_COMMITMENT", rule_id, ["source-" + id + "-agreement"])
        edge(
            rule_id, "APPLIES_AT", "facility-bengaluru", ["source-" + id + "-agreement"]
        )
        edge(
            rule_id,
            "SUPPORTED_BY",
            "source-" + id + "-agreement",
            ["source-" + id + "-agreement"],
        )
        edge(rule_id, "OWNED_BY", "team-accounts", ["source-owners"])
        if id == "havells":
            edge(rule_id, "WHY", "decision-sunday", ["source-campaign"])
    # Relational logistics concepts are represented as graph labels/relationships.
    # IDs are unmistakably synthetic, not live waybills or customer identifiers.
    for i in range(24):
        city = "Bengaluru"
        dest = CITIES[1 + (i % 7)]
        node(
            f"lane-{i:02}",
            "Route",
            f"{city} → {dest}",
            mode="Road",
            schedule="Synthetic lane",
        )
        edge(f"lane-{i:02}", "ORIGIN", "facility-" + city.lower())
        edge(f"lane-{i:02}", "DESTINATION", "facility-" + dest.lower())
        node(f"manifest-{i:02}", "Manifest", f"DEMO-MANIFEST-{i:03}", status="planned")
        edge(f"manifest-{i:02}", "USES_ROUTE", f"lane-{i:02}")
    for i in range(60):
        client = CLIENTS[i % 3][0]
        node(
            f"pickup-{i:03}",
            "PickupRequest",
            f"DEMO-PICKUP-{i:03}",
            status="collected",
            pickup_date="2026-11-07",
        )
        edge(f"pickup-{i:03}", "FROM", "warehouse-" + client)
    start = datetime(2026, 11, 8, 8, tzinfo=timezone.utc)
    for i in range(1200):
        client = CLIENTS[i % 3][0]
        shipment = f"shipment-{i:04}"
        arrival = start + timedelta(minutes=(i // 3) % 180)
        node(
            shipment,
            "Shipment",
            f"DEMO-AWB-{i:06}",
            client=client,
            facility="facility-bengaluru",
            arrival_at=arrival.isoformat().replace("+00:00", "Z"),
            status="received_at_facility",
            description="Synthetic Sunday scenario consignment; not a live parcel.",
        )
        edge(shipment, "FOR_CLIENT", client)
        edge(shipment, "AT", "facility-bengaluru")
        edge(shipment, "COLLECTED_BY", f"pickup-{i % 60:03}")
        edge(shipment, "ON_MANIFEST", f"manifest-{i % 24:02}")
        for j, status in enumerate(
            ["Manifested", "Pickup scheduled", "Collected", "Received at facility"]
        ):
            scan = f"scan-{i:04}-{j}"
            node(
                scan,
                "ScanEvent",
                status,
                event_at=(arrival - timedelta(hours=12 - j * 4))
                .isoformat()
                .replace("+00:00", "Z"),
                sequence=j,
                description="Synthetic operational event",
            )
            edge(shipment, "HAS_SCAN", scan)
    return nodes, edges


def amendment():
    text = "SYNTHETIC APPROVED AMENDMENT. Recorded October 15, 2026. Effective November 1, 2026, Havells accepts Monday–Saturday processing at Bengaluru. Sunday consignments may be queued for Monday. Until November 1 the original Sunday commitment remains applicable. Sales and Account Management approved this demo record."
    source = dict(
        id="source-amendment",
        kind="Source",
        title="Havells · approved demo amendment",
        synthetic=True,
        enabled=True,
        source_type="Demo amendment",
        department="Account Management",
        timestamp="2026-10-15T09:00:00Z",
        excerpt=text,
        content_hash=hashlib.sha256(text.encode()).hexdigest(),
    )
    return source
