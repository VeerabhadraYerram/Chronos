# Delhivery reference workspace

ChronosGraph investigates **why an operating decision exists, whether its commitment still applies, and what a proposed change would do**. The primary example is Sunday processing at a Bengaluru facility.

## Public facts versus synthetic records

Delhivery is a real logistics business. Its public [service description](https://www.delhivery.com/services/express-parcel), [order lifecycle](https://help.delhivery.com/docs/update-forward-order), and [developer FAQ](https://one.delhivery.com/developer-portal/document/b2c/detail/faq) inform the entity types and workflow. Its [press archive](https://www.delhivery.com/company/press-release) lists business relationships with Havells India, HPCL and SUGAR Cosmetics.

**This is an independent reference implementation, not Delhivery's internal system or exact private schema.** Public relationships do not establish the demo's agreements. Every facility record, consignment, scan, department responsibility, conversation, cost and operating commitment is synthetic. No actual customer incident, agreement, employee identity or live logistics integration is represented.

## The operating story

Operations wants to close Bengaluru on Sundays. A synthetic Havells service agreement requires Sunday processing; SUGAR and HPCL have six-day processing. A Sales handover records a weekend campaign as the reason. Ending the campaign does not amend the agreement. An Operations chat is a proposal, not an approval.

A separately replayed approved **demo amendment** changes Havells to six-day processing effective **November 1, 2026**, recorded **October 15, 2026 at 09:00 UTC**. Both clocks matter. The existing handbook remains a separate record for human review.

## Start and explore

Open the [live app](https://chronosgraph.onrender.com), or follow the [local setup](../README.md#run-locally) and open `http://127.0.0.1:5173/`. Local services can be stopped without affecting Render: the deployed frontend, API and FalkorDB run independently.

1. Select **Guided walkthrough**. Ask **Can we close the Bengaluru facility on Sundays?** The investigator retrieves the original agreement. The separate guided rehearsal produces the deterministic Havells conflict.
2. Read the small evidence trail. Each row is a real relationship; click a record or connection to inspect it. Switch to **Map** for a spatial view.
3. Select a commitment and ask **Why does this exist?**, **Does this still apply?**, or a custom follow-up. **Explore connections** performs another bounded graph read. Exploration can show historical records; inspect their intervals.
4. Replay **Introduce approved amendment**. Existing receipts become stale. Rerun for November 8, known by October 16: the investigator retrieves the amended agreement; the guided rehearsal confirms no modeled Sunday commitment conflict.
5. Change the effective date to October 25: Havells still requires Sunday processing. Change the knowledge cutoff to October 14: the original belief remains available even for a November effective date.
6. Open **Before & after**, run comparison, and toggle **Full proposal / Preserve commitments**. The real graph copy is discarded after the calculation; base knowledge stays unchanged.
7. Prepare and download a source-linked review packet from a current investigation. No external ticket or operating change is made.
8. Search **Company records** for `DEMO-AWB-000001`, a source title or a department. Operational records have bounded graph inspection too.

The AI investigator is enabled by default for new browser sessions when a server key is configured. The provider order is Groq → Gemini → OpenRouter free models. The successful provider, mode and tool trace are displayed. Graph-only retrieval is an explicitly selected separate mode. If every configured provider fails, the investigation states that no AI answer was generated; it does not substitute a canned explanation. The guided scheduling checks remain a separate deterministic operation. Natural language does not grant arbitrary database access or write authority.

For the full field dictionary, physical storage layout, relational equivalents, lifecycle rules and Cypher examples, see [Database & schema](DATABASE.md).

## General engine and guided boundaries

The default investigator uses the [company-wide engine](COMPANY_ENGINE.md), rather than routing all questions through this example. Alerts describe missing evidence, conflicting retrieved accepted rules, unavailable selected evidence, actual provider fallback, or stale context. The guided rehearsal alone produces its explicit Sunday closure verdict. Historical receipts retain the context and alerts recorded when created.

Select **Guided walkthrough** to expose the sample replay and rehearsal controls. Their text comes from the dataset's tour configuration. Normal investigation does not show a Havells amendment card by default. The complete database is available through a [separate inspection link](INSPECTION.md).

## Dataset and schema

The initial seed has **9,991 business entities and 17,207 relationships**, including:

| Graph label | Count | Meaning |
| --- | ---: | --- |
| Company | 1 | Public business identity |
| Client | 12 | Real organization names; synthetic operating commitments |
| Facility | 14 | Synthetic processing-centre records |
| ClientWarehouse | 36 | Synthetic registered pickup locations |
| Team | 8 | Department responsibilities, not real employee identities |
| Route | 81 | 24 Bengaluru lanes plus 57 October lanes |
| Manifest | 81 | Planned lane-linked manifests |
| PickupRequest | 117 | Synthetic collected pickup requests |
| Shipment | 1,890 | 1,200 November scenario consignments plus 690 October operational consignments |
| ScanEvent | 6,870 | Four per November consignment; three per October consignment |
| Rule | 43 | Accepted, temporally scoped handling, billing and scheduling controls |
| Source | 102 | Seven public context references plus 95 modeled records |
| Decision | 22 | Accepted decision and unapproved proposal |
| Policy | 17 | Operating handbooks and account guides |
| Campaign | 13 | Client promotions, rollouts and capacity programmes |

The replay adds source and rule versions. Counts come from FalkorDB, not frontend constants. Receipts and review packets are additional persisted entities. Waybills are local fixture identifiers, not live tracking IDs.

```mermaid
flowchart LR
    Client -->|HAS_COMMITMENT| Rule
    Rule -->|APPLIES_AT| Facility
    Rule -->|SUPPORTED_BY| Source
    Rule -->|OWNED_BY| Team
    Rule -->|WHY| Decision
    Decision -->|EXPLAINED_BY| Handover[Source: Sales handover]
    Shipment -->|FOR_CLIENT| Client
    Shipment -->|AT| Facility
    Shipment -->|COLLECTED_BY| PickupRequest
    PickupRequest -->|FROM| ClientWarehouse
    Shipment -->|ON_MANIFEST| Manifest
    Manifest -->|USES_ROUTE| Route
    Shipment -->|HAS_SCAN| ScanEvent
```

## Temporal semantics

Rules use half-open valid and recorded intervals. Original belief remains queryable before the amendment was recorded. The corrected historical version ends November 1; the amended version starts then. An enabled supporting source and the graph relationships are required for a supported result. Missing, withdrawn or contradictory evidence yields insufficient evidence, rather than permission to close.

Source availability is a current flag. Ownership and network topology are current synthetic relationships, not historical versions. “Before” in the comparison means current demo configuration, not a reconstruction of the historical operating system.

## Simulation boundaries

The 1,200 Sunday fixture arrivals are replayed on the first Sunday on or after the selected effective date. Commitments are checked for that scenario date. The current handbook processes Havells on Sunday and queues the other clients. Full closure queues all selected fixture arrivals for Monday. The scoped alternative preserves supported Sunday exceptions and refuses to infer missing requirements.

The Finance source supplies shift-cost assumptions. Figures are not measured Delhivery costs, guaranteed savings or full staffing/transport forecasts. Processing is not delivery: the comparison does not predict customer experience, actual vehicle capacity, delivery dates or outages.

## Architecture and API

[Company store](../backend/chronos/company/store.py), [engine](../backend/chronos/company/engine.py), [Investigator tools](../backend/chronos/company/agent.py), [API](../backend/chronos/company/api.py), and [fixture](../backend/chronos/company/seed.py) are separate from the preserved NovaPay implementation.

The immutable reference graph is `chronos_delhivery_reference_v1` by default. Each visitor receives an opaque random ID and a real graph copy named `chronos_delhivery_demo_…`. Local storage retains only that demo session ID. Session mutations never target the original payments graph. Scenario copies use `chronos_company_trial_…` and are deleted in `finally`.

| POST route | Purpose |
| --- | --- |
| `/api/company/session` | Create or reopen a session; return stats, initial graph, sources and receipts |
| `/api/company/ask` | Investigate a question with optional focus, client and two dates |
| `/api/company/explore` | Inspect a record and bounded neighbors |
| `/api/company/search` | Search records through a parameterized template |
| `/api/company/simulate` | Compare rules in a disposable graph copy |
| `/api/company/events` | Replay the allowlisted synthetic amendment or source withdrawal |
| `/api/company/packet` | Prepare a review draft from a current receipt |

Read tools call `GRAPH.RO_QUERY`; the model receives neither credentials nor arbitrary Cypher execution. Tool, argument, record-ID and citation bounds are enforced. Citation membership is not semantic proof. The model may still require human review.

## Hosting boundary

The [live Render app](https://chronosgraph.onrender.com) serves the built frontend, API and loopback-only FalkorDB from one Free service. Local Docker is independent of that deployment. Local workspaces use persistent Docker storage and default to a 40-session cap; hosted workspaces are capped at six, expire after one hour of inactivity and reset on server restart. Cold starts and full database scans can be slow. See [deployment details](DEPLOYMENT.md) and [dated verification](VALIDATION.md#live-render-verification--october-17-2026).

Session IDs are capabilities, not production authentication. The public entrypoint excludes the preserved payments API and OpenAPI docs. A single-process lock coordinates graph operations, but external inference does not hold it; revision changes can mark a resulting receipt stale. Readiness reads reference metadata without taking the workspace lock. Admission limits do not guarantee availability, provider quota or production security.

The original payments workflow remains locally at `/?demo=payments`; it is excluded from the public evaluation entrypoint. Its model and API documentation are marked as legacy scope.

See [Synthetic logistics depth](DATA_SCENARIOS.md) for the additional operational, finance, incident and people records, example investigations and limitations.
