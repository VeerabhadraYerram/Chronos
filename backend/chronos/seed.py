"""Entirely fictional, deliberately small company fixture; no external integrations."""

import hashlib


def fixture():
    nodes, edges = [], []

    def node(id, kind, title, **props):
        nodes.append(dict(id=id, kind=kind, title=title, **props))

    def edge(a, relation, b):
        edges.append(dict(source=a, target=b, relation=relation))

    node(
        "system-payments",
        "System",
        "Payment worker",
        description="Partner-specific outbound payment retries",
    )
    node(
        "system-checkout",
        "System",
        "Checkout API",
        description="Calls the payment worker; impact is a dependency, not a failure prediction",
    )
    node(
        "file-worker",
        "File",
        "payment_worker.py",
        path="services/payments/payment_worker.py",
    )
    node("person-maya", "Person", "Maya Chen", role="Payments owner")
    node("person-leo", "Person", "Leo Martin", role="Partner engineering")
    node("team-platform", "Team", "Payments platform")
    node("project-migration", "Project", "Partner B migration")
    edge("system-checkout", "DEPENDS_ON", "system-payments")
    edge("file-worker", "PART_OF", "system-payments")
    edge("person-maya", "OWNS", "system-payments")
    edge("person-maya", "MEMBER_OF", "team-platform")
    edge("person-leo", "LEADS", "project-migration")
    edge("project-migration", "CHANGES", "system-payments")
    node("decision-retry", "Decision", "Keep a partner retry buffer", approved=True)
    node("ticket-88", "Ticket", "PAY-88 · Burst retry incident", status="resolved")
    node(
        "source-incident",
        "Source",
        "Incident review · PAY-88",
        source_type="Ticket",
        timestamp="2026-04-03T10:00:00Z",
        excerpt="Partner A and Partner B reject burst retries. The payments team approved a minimum 250 ms delay between retry attempts. Applies to outbound payments only.",
        enabled=True,
    )
    node(
        "source-chat",
        "Source",
        "Payments decision thread",
        source_type="Chat export",
        timestamp="2026-04-04T10:00:00Z",
        excerpt="Maya: Approved. Keep the 250 ms minimum for both partners until a partner-specific migration is accepted. A performance refactor alone does not remove the requirement.",
        enabled=True,
    )
    node("doc-retry", "Document", "Payment retry runbook", revision="1")
    node(
        "source-runbook",
        "Source",
        "Runbook · revision 1",
        source_type="Markdown",
        timestamp="2026-04-05T10:00:00Z",
        excerpt="Outbound retries require a minimum 250 ms delay for Partner A and Partner B. Owner: Maya Chen.",
        enabled=True,
    )
    edge("ticket-88", "RESULTED_IN", "decision-retry")
    edge("decision-retry", "SUPPORTED_BY", "source-chat")
    edge("decision-retry", "APPLIES_TO", "system-payments")
    for partner in ["a", "b"]:
        upper = partner.upper()
        node(
            f"commitment-{partner}",
            "Commitment",
            f"Partner {upper} retry requirement",
            partner=partner,
        )
        node(
            f"fact-{partner}-original",
            "FactVersion",
            f"Partner {upper} · minimum 250 ms",
            subject="system-payments",
            field="minimum_backoff_ms",
            value=250,
            partner=partner,
            status="accepted",
            valid_from="2026-04-04T00:00:00Z",
            valid_to="",
            recorded_from="2026-04-04T10:00:00Z",
            recorded_to="",
        )
        edge("decision-retry", "HAS_VERSION", f"fact-{partner}-original")
        edge(f"fact-{partner}-original", "SUPPORTED_BY", "source-incident")
        edge(f"fact-{partner}-original", "GOVERNED_BY", f"commitment-{partner}")
        node(
            f"doc-claim-{partner}",
            "FactVersion",
            f"Runbook says Partner {upper}: 250 ms",
            subject="system-payments",
            field="minimum_backoff_ms",
            value=250,
            partner=partner,
            status="documentation",
            valid_from="2026-04-05T00:00:00Z",
            valid_to="",
            recorded_from="2026-04-05T10:00:00Z",
            recorded_to="",
        )
        edge("doc-retry", "ASSERTS", f"doc-claim-{partner}")
        edge(f"doc-claim-{partner}", "SUPPORTED_BY", "source-runbook")
    for n in nodes:
        if n["kind"] == "Source":
            n["content_hash"] = hashlib.sha256(n["excerpt"].encode()).hexdigest()
            n["synthetic"] = True
    return nodes, edges


def migration_fixture():
    source = dict(
        id="source-migration",
        kind="Source",
        title="Accepted Partner B migration",
        source_type="Decision record",
        timestamp="2026-10-12T09:00:00Z",
        excerpt="Approved by Maya Chen: Partner B moved to the new retry protocol effective October 10. Its minimum delay is now 0 ms. Partner A remains at 250 ms. Recorded in company knowledge on October 12.",
        enabled=True,
        synthetic=True,
    )
    source["content_hash"] = hashlib.sha256(source["excerpt"].encode()).hexdigest()
    corrected = dict(
        id="fact-b-historical",
        kind="FactVersion",
        title="Partner B · historical 250 ms",
        subject="system-payments",
        field="minimum_backoff_ms",
        value=250,
        partner="b",
        status="accepted",
        valid_from="2026-04-04T00:00:00Z",
        valid_to="2026-10-10T00:00:00Z",
        recorded_from="2026-10-12T09:00:00Z",
        recorded_to="",
    )
    current = dict(
        id="fact-b-migrated",
        kind="FactVersion",
        title="Partner B · minimum 0 ms",
        subject="system-payments",
        field="minimum_backoff_ms",
        value=0,
        partner="b",
        status="accepted",
        valid_from="2026-10-10T00:00:00Z",
        valid_to="",
        recorded_from="2026-10-12T09:00:00Z",
        recorded_to="",
    )
    return source, corrected, current
