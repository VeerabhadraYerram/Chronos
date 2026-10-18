# Database, schema, and data dictionary

[Project overview](../README.md) · [Product walkthrough](../README.md#guided-change-walkthrough) · [Machine-readable schema](database-schema.json) · [Integration tests](../backend/tests/test_company_reference.py)

## 1. What database do we use?

**FalkorDB is the primary database.** It stores company context, operating records, commitments, source evidence, ownership, saved investigations, and review drafts. The backend reads relationships with parameterized Cypher through `GRAPH.RO_QUERY`; model-selected tools cannot run arbitrary Cypher or obtain credentials.

There is no SQL database behind the main workspace. When this document uses “table equivalent,” it means the familiar relational concept corresponding to a graph label. The implemented objects are **nodes, properties, and directed relationships**.

This document describes an independently designed Delhivery reference prototype. It is **not Delhivery's exact internal database or private schema**. Public business names and logistics concepts are distinguished from synthetic operating records. No private Delhivery agreements, employee records, shipment feeds, warehouse schedules, or client terms were obtained.

## 2. Database topology and persistence

| Graph or component | Purpose | Lifetime / boundary |
| --- | --- | --- |
| `chronos_delhivery_reference_v1` | Shared reference seed, plus a demo-session creation registry | Seeded once; operating knowledge is not changed by visitor replay |
| `chronos_delhivery_demo_<random ID>` | One visitor's company workspace | Isolated mutations and receipts; persistent locally, temporary on free Render; opaque capability ID kept in browser local storage |
| `chronos_company_trial_<random ID>` | Before/after rehearsal | Real `GRAPH.COPY`; removed in `finally` after comparison |
| `chronos_reference_test_<random ID>` | Integration-test fixture copies | Disposable; never the user's demo graph |
| `chronos_novapay` or configured legacy name | Preserved payments prototype | Separate from the main company workspace |
| Docker volume `chronosgraph-data` | FalkorDB persistent storage | Mounted at `/var/lib/falkordb/data`; append-only persistence configured in Compose |

`CHRONOS_COMPANY_GRAPH` can change the reference graph name. `FALKOR_GRAPH` controls the legacy payments graph; it does not redirect visitor sessions into that graph. Host, port, optional password and provider keys remain in the ignored root `.env`. No credential belongs in a database diagram or committed export.

Local session creation defaults to a cap of **40** per reference registry, with no automatic expiry. The free Render deployment explicitly sets a cap of **6** and expires registered visitor graphs after **one hour of inactivity**; server restarts also reset hosted visitor data. See [deployment boundaries](../README.md#deployment). No production identity system is implemented. The registry's `DemoSession` records can be inherited by later copies but are excluded from business-entity counts and model exploration. A new workspace preserves earlier active workspaces rather than resetting them.

## 3. Initial dataset size

The deterministic seed contains **9,991 business entities**, **17,207 directed relationships**, and a separate `Metadata` revision record. These are initial fixture counts, not a claim about Delhivery's real scale. Replays, receipts, review packets and session bookkeeping add records.

| Graph label | SQL-table equivalent | Initial rows/nodes | Example ID |
| --- | --- | ---: | --- |
| `Company` | companies | 1 | `delhivery` |
| `Client` | clients | 12 | `havells` |
| `ClientWarehouse` | client_warehouses | 36 | `warehouse-havells` |
| `Facility` | processing_facilities | 14 | `facility-bengaluru` |
| `Team` | departments | 8 | `team-operations` |
| `Route` | transport_lanes | 81 | `lane-00` |
| `Manifest` | manifests | 81 | `manifest-00` |
| `PickupRequest` | pickup_requests | 117 | `pickup-000` |
| `Shipment` | consignments | 1,890 | `shipment-0000` |
| `ScanEvent` | tracking_events | 6,870 | `scan-0000-0` |
| `Rule` | commitment_versions | 43 | `rule-havells-original` |
| `Source` | source_documents | 102 | `source-havells-agreement` |
| `Decision` | decisions | 22 | `decision-sunday` |
| `Policy` | operating_policies | 17 | `policy-schedule` |
| `Campaign` | campaign_context | 13 | `campaign` |
| `Claim` | document_assertions | 25 | `claim-current-schedule` |
| `Ticket` | incident_tickets | 20 | `depth-ticket-cod` |
| `Person` | fictional_role_directory | 24 | `depth-person-0-0` |
| `Vehicle` | fleet_units | 21 | `depth-vehicle-00` |
| `Invoice` | shipping_invoices | 72 | `depth-invoice-000` |
| `CODCollection` | cash_collections | 39 | `depth-cod-0007` |
| `Remittance` | settlement_entries | 39 | `depth-remittance-0007` |
| `Return` | return_requests | 156 | `depth-return-0004` |
| `DeliveryException` | failed_delivery_reviews | 252 | `depth-exception-0003` |
| `WorkItem` | operational_review_work | 36 | `work-havells-operations` |
| `Receipt` | investigation_receipts | 0 | Created by a question |
| `Action` | review_packets | 0 | Created from a current receipt |
| `Event` | applied_demo_events | 0 | Created by replay |
| `DemoSession` | session_registry | 0 | Created in the reference registry |
| `Metadata` | dataset_metadata | 1 | `dataset` |

`Metadata` does not carry `Entity`, so it is outside the 9,991 business-node total. Business statistics exclude `Receipt`, `Action`, and `DemoSession`. The relationship counter includes all `Entity` relationships present, including later receipt links; the initial count has no receipt links.

Seven sources provide curated public context; 95 contain modeled company records. Replaying the amendment adds one source and two rule versions while retaining the original belief.

## 4. Physical storage schema

### Common entity representation

Every business record has the shared label `Entity` and its domain label. A client is `(:Entity:Client)`; a shipment is `(:Entity:Shipment)`.

| Native property | Type | Purpose |
| --- | --- | --- |
| `id` | string | Stable application identifier and relationship lookup key |
| `kind` | string | Allowlisted domain label |
| `title` | string | Human-readable name and searchable summary |
| `payload` | JSON-encoded string | Complete domain record, including the common fields |

All scalar domain fields with safe property names are now mirrored as native FalkorDB properties, including rule values, source availability, shipment status/times, invoice amounts, and custom imported fields. The complete JSON `payload` preserves nested arrays/objects and the full record. `search_text` is a native discovery projection. Runtime `Receipt.stale` and registry creation times are native lifecycle fields; serialized receipts preserve their original context.

### Physical schema v4

- **UNIQUE** on `Entity.id`; **MANDATORY** on `Entity.id`, `kind`, `title`, and `payload`. Actual operational states are visible in the separate inspection portal.
- Range indexes for `Entity.id/kind/title`, `Rule.field/client/subject_id`, `Shipment.client/status`, and `Source.enabled`. Optional indexes may be present even when a custom workspace has no records of that label.
- Temporal predicates use explicit comparison of canonical UTC strings. Integration testing found unsuitable temporal string-index filtering in the pinned configuration; schema v4 removes those indexes and guards date predicates with `toString`. Correctness takes precedence over claiming faster date lookup.
- Versioned migrations add native projections/indexes/constraints without reseeding a workspace, changing its business revision, deleting facts, or clearing history. Failed constraint construction is surfaced rather than marked operational.
- New records include mandatory identity fields at creation. Application relationship writes require existing endpoints. The trusted importer validates source references and accepted-rule support. These are not database-enforced foreign-key or business-domain constraints.

The [separate inspection portal](#database-inspection) exposes complete business tables, relationships, observed fields, native properties, structural checks and JSON export. The [general investigator](../README.md#architecture-and-agent-behavior) discovers the actual workspace schema rather than assuming this reference dataset.

## 5. Domain data dictionary

The fields below appear in decoded records; scalar values are also mirrored natively. Optional fields depend on record type.

| Label | Important fields | Meaning |
| --- | --- | --- |
| `Company` | `description`, `synthetic` | Reference-workspace scope; real business name, independently modeled context |
| `Client` | `sector`, `description`, `synthetic` | Named business identity; private terms and operations remain invented |
| `ClientWarehouse` | `city`, `description` | Synthetic registered collection location, distinct from a processing facility |
| `Facility` | `city`, `facility_type`, `current_sunday_open`, `description` | Synthetic network location; scheduling comparison uses the linked operating policy |
| `Team` | `description` | Department responsibility; no real employee identity or inferred expertise |
| `Route` | `mode`, `schedule` | A synthetic road lane linked to origin and destination facilities |
| `Manifest` | `status` | Planned grouping of consignments associated with a route |
| `PickupRequest` | `status`, `pickup_date` | A collected synthetic pickup request linked to a client warehouse |
| `Shipment` | `client`, `facility`, `arrival_at`, `status`, `description` | November scenario or October snapshot consignment; traversals establish its client and location |
| `ScanEvent` | `event_at`, `sequence`, `description` | Ordered synthetic event in a consignment's history |
| `Rule` | `client`, `facility`, `field`, `value`, `status`, four interval bounds | Accepted temporal commitment; 19 modeled fields cover scheduling, pickup cutoffs, billing, COD, returns and handling/review controls; values are typed |
| `Source` | `excerpt`, `source_type`, `department`, `timestamp`, `enabled`, `content_hash`, optional `classification`, `url` | Inspectable source text, provenance category, current availability and content hash |
| `Decision` | `description`, `approved` | Accepted decision context or an explicitly unapproved proposal |
| `Policy` | `sunday_required`, `sunday_clients`, `description` | Current handbook configuration; `sunday_clients` drives the baseline Sunday-processing preview |
| `Campaign` | `ended_at`, `description` | Historical reason context; ending a campaign does not modify a commitment |
| `Receipt` | `request`, `summary`, `assessment`, `checks`, `sources`, `graph`, `revision`, `trace`, `mode`, optional provider metadata | Persisted investigation and evidence snapshot |
| `Action` | `receipt_id`, `revision`, `status`, `markdown`, `reviewer` | Source-linked local review draft; not an externally published ticket |
| `Event` | `synthetic` | One-shot replay marker, making the demo event idempotent |

The Finance source additionally stores `full_shift_inr` and `restricted_shift_inr`. These are explicit synthetic assumptions. They do not represent measured company costs or guaranteed savings.

## 6. Relationship schema

Each relationship is directed. The `source_ids` property is a list of supporting `Source.id` values. Empty lists identify synthetic operational links without attached document-level provenance. A hash or source ID is not an authenticity guarantee.

| From | Relationship | To | Meaning |
| --- | --- | --- | --- |
| Client | `PUBLIC_RELATIONSHIP` | Company | Publicly referenced business relationship, not evidence of demo terms |
| Client | `HAS_COMMITMENT` | Rule | Client's versioned processing commitment |
| Rule | `APPLIES_AT` | Facility | Facility scope of a commitment |
| Rule | `SUPPORTED_BY` | Source | Evidence for an accepted requirement |
| Rule | `OWNED_BY` | Team | Department responsible for that commitment |
| Rule | `WHY` | Decision | Recorded rationale context |
| Decision | `EXPLAINED_BY` | Source | Original explanation in a handover record |
| Decision | `SUPPORTED_BY` | Source | Supporting record, including a proposal explicitly marked unapproved |
| Decision | `APPLIES_AT` | Facility | Scope of the proposal |
| Decision | `OWNED_BY` | Team | Decision owner |
| Policy | `APPLIES_AT` | Facility | Scope of current operating instructions |
| Policy | `DOCUMENTED_IN` | Source | Handbook source |
| Policy | `OWNED_BY` | Team | Department maintaining the instructions |
| Facility | `OPERATED_BY` | Team | Current department responsibility |
| Team | `PART_OF` | Company | Organizational membership |
| ClientWarehouse | `BELONGS_TO` | Client | Ownership of the synthetic pickup location |
| PickupRequest | `FROM` | ClientWarehouse | Where the pickup occurred |
| Shipment | `COLLECTED_BY` | PickupRequest | Pickup request associated with the consignment |
| Shipment | `FOR_CLIENT` | Client | Shipment's client |
| Shipment | `AT` | Facility | Fixture's current processing location |
| Shipment | `ON_MANIFEST` | Manifest | Planned movement grouping |
| Manifest | `USES_ROUTE` | Route | Associated transport lane |
| Route | `ORIGIN` / `DESTINATION` | Facility | Lane endpoints |
| Shipment | `HAS_SCAN` | ScanEvent | Tracking history |
| Campaign | `DOCUMENTED_IN` | Source | Campaign handover |
| New Rule | `SUPERSEDES` | Original Rule | Visible replacement lineage introduced by amendment |
| Original Source | `AMENDED_BY` | New Source | Agreement amendment trail |
| Receipt | `USED` | Source | Source used in the company investigation |
| Receipt | `PROPOSES` | Action | Prepared human-review packet |

These are seed conventions, not database-enforced cardinalities. In this fixture each shipment has one client, one current facility, one pickup request and one manifest. The 1,200 scheduling-cohort shipments have four scans each; the other 690 have three each, totaling 6,870 scans. The model does not imply all real logistics systems use those cardinalities.

```mermaid
flowchart LR
    C[Client] -->|HAS_COMMITMENT| R[Rule version]
    R -->|APPLIES_AT| F[Facility]
    R -->|SUPPORTED_BY| S[Agreement source]
    R -->|OWNED_BY| T[Department]
    R -->|WHY| D[Decision]
    D -->|EXPLAINED_BY| H[Sales handover]
    SH[Shipment] -->|FOR_CLIENT| C
    SH -->|AT| F
    SH -->|COLLECTED_BY| P[Pickup request]
    P -->|FROM| W[Client warehouse]
    W -->|BELONGS_TO| C
    SH -->|ON_MANIFEST| M[Manifest]
    M -->|USES_ROUTE| L[Route]
    L -->|ORIGIN / DESTINATION| F
    SH -->|HAS_SCAN| E[Scan event]
```

## 7. Example records

These examples show decoded payloads. They are not live customer data.

```json
{
  "id": "shipment-0000",
  "kind": "Shipment",
  "title": "DEMO-AWB-000000",
  "synthetic": true,
  "client": "havells",
  "facility": "facility-bengaluru",
  "arrival_at": "2026-11-08T08:00:00Z",
  "status": "received_at_facility"
}
```

```json
{
  "id": "rule-havells-original",
  "kind": "Rule",
  "client": "havells",
  "facility": "facility-bengaluru",
  "field": "sunday_processing_required",
  "value": true,
  "status": "accepted",
  "valid_from": "2026-05-01T00:00:00Z",
  "valid_to": "",
  "recorded_from": "2026-05-02T09:00:00Z",
  "recorded_to": ""
}
```

The initial handbook has `sunday_clients: ["havells"]`. Its Sunday configuration is independent from the agreement versions: an amendment changes what is required, but does not silently rewrite operating instructions.

## 8. Two clocks and amendment history

A rule applies only when:

```text
valid_from <= effective_at < valid_to
recorded_from <= known_at < recorded_to
```

An empty end means no upper bound. The intervals are half-open. API timestamps require a timezone and normalize to UTC. Calendar inputs in the UI use 12:00 UTC.

After the synthetic amendment replay:

| Havells version | Sunday required | Effective interval | Recorded interval |
| --- | --- | --- | --- |
| Original belief | Yes | May 1 onward | May 2 at 09:00 → October 15 at 09:00 |
| Corrected historical commitment | Yes | May 1 → November 1 | October 15 at 09:00 onward |
| Amended commitment | No | November 1 onward | October 15 at 09:00 onward |

Therefore November 8 as known on October 14 still returns the original promise; November 8 as known on October 16 returns the amended requirement. October 25 still requires Sunday processing even after the amendment is recorded.

The query also requires client→rule→facility and rule→source relationships. The engine excludes disabled supporting sources. Missing support or multiple contradictory accepted values yields `insufficient_evidence`. A chat proposal never creates an accepted rule.

Ownership, topology and source availability are not fully versioned. Withdrawing a source affects later historical queries too. The two-clock implementation should not be described as complete historical reconstruction of the company.

## 9. Cypher implementation

The [dedicated query guide](GRAPH_QUERIES.md) collects the actual source-linked templates for search, temporal rules, claims, aggregation, ownership, evidence paths and structural checks. Queries are executed by FalkorDB, not by a frontend relationship engine.

## 10. Reads, writes, and invalidation

| Operation | Database behavior |
| --- | --- |
| New workspace | Seeds the reference if absent, copies the graph, records a session registry entry |
| Ask / follow-up | Reads question-specific context; refreshes applicable rules when policy records are retrieved; runs bounded provider-selected reads when AI is enabled; persists a receipt and `USED` links |
| Expand a node | Reads neighbors and the relationships between returned nodes |
| Approved amendment replay | Updates the original recorded interval, adds two rule versions and amendment evidence, links lineage, increments revision |
| Evidence withdrawal replay | Disables the original supporting source; increments revision |
| Revision change | Marks previous receipts stale conservatively across that workspace |
| Before/after preview | Copies the graph, adds a scenario policy in the copy, reads sample counts and accepted commitments, then deletes only the temporary copy |
| Prepare review packet | Requires a current receipt; writes an `Action` draft and a `PROPOSES` link |

The copy operation has a small bounded retry for a transient “could not fork” failure. It never substitutes a frontend or in-memory clone. Replay operations span multiple writes, coordinated by a process lock; they do not claim crash-atomic transactions or multi-worker coordination.

The model cannot accept policies, replay amendments, approve agreements, change a graph name or publish actions through its read tools. Those application operations remain separate from source text and model explanations.

**Ask about this** carries the selected record ID and parent investigation into the next question, alongside effective/recorded times. The receipt stores its retrieved evidence snapshot; breadcrumbs restore the actual parent chain. Prior generated summaries are not treated as company facts or reused as policy authority. A later revision marks earlier receipts stale; rerunning requires an explicit user action.

## 11. Source of truth and reproduction

- [Dataset generator](../backend/chronos/company/seed.py): initial records, sample events and public-reference boundaries.
- [Store](../backend/chronos/company/store.py): labels, native fields, relationships, read templates, graph copies and visitor sessions.
- [Engine](../backend/chronos/company/engine.py): evidence checks, reason paths, handbook review flags, simulation and review drafts.
- [API models](../backend/chronos/company/api.py): request schemas, timestamps and allowlisted events.
- [Investigator](../backend/chronos/company/agent.py): read tools, graph selection and citation bounds.
- [Integration tests](../backend/tests/test_company_reference.py): real-database checks with disposable graphs.

Run `./scripts/check.sh` after completing the [local setup](../README.md#run-locally). It runs the real FalkorDB suite, the preserved payments evaluator, frontend build, and documentation checks without external AI-provider calls. Never reset the user's demo graph to run tests.

The [machine-readable dictionary](database-schema.json) is generated from the initial fixture and includes field names/types, counts, representative records, and relationship endpoint types. It is a schema description, not a live runtime export or database-enforced migration.

Regenerate the dictionary directly from the fixture, without a database connection or provider call:

```sh
PYTHONPATH=backend .venv/bin/python scripts/export_schema.py
```

Generator: [export_schema.py](../scripts/export_schema.py).

The logistics fixture includes 25 explicit `Claim` records for handling and billing statements across 12 accounts, linked through `Policy → ASSERTS → Claim → SUPPORTED_BY → Source`. General investigation compares its subject/field/value with applicable accepted rules. Existing reference workspaces receive this fixture extension once and conservatively invalidate earlier receipts; this is separate from the physical schema migration.



## Operational situations

The dataset covers selected logistics cases, not every real process. The 1,200 planned November consignments support the Sunday comparison; another 210 October consignments cover seven other cities/statuses and another 480 connect all 12 accounts to their pickup warehouses. Ordinary traffic does not alter the explicitly selected comparison cohort.

| Situation | Evidence path | Example question |
| --- | --- | --- |
| COD mismatch | Decision → incident ticket → settlement → cash collection → shipment; Finance owns review | Why is the SUGAR COD mismatch being investigated? Does it prove cash loss? |
| Weight dispute | Decision → ticket → invoice → shipment with declared/measured weights; Finance and Operations have distinct roles | Who owns the Havells weight dispute, and what evidence is needed before a credit? |
| Failed delivery | Shipment → delivery exception → account team; reason and next action are explicit | What delivery exceptions are recorded, and who handles them? |
| Damaged return | Decision → ticket → return → shipment; Warehouse owns inspection | Why is the Chennai return awaiting inspection? |
| Capacity review | Decision → ticket → Mumbai facility → Operations | Is additional Mumbai staffing approved or still pending? |
| Scan ingestion gap | Decision → ticket → affected shipment; Technology owns investigation | Does a missing scan mean the parcel is lost? |
| Weather contingency | Proposed decision → ticket → route → facilities; Transport owns review | Is the Kolkata reroute approved? |
| Packaging hold | Decision → ticket → exception → shipment; Compliance owns review | Who reviews the HPCL packaging hold? |


Campaign records describe client programmes such as festive replenishment, regional rollout and returns improvement; they explain rationale but never override policy. WorkItems are assigned operational review work. Actions are only actual user-created review packets, so a fresh graph has none. Claims are document statements compared against accepted rules, not prewritten responses. Tour metadata and past receipts are excluded from company-fact discovery.

## Database inspection

Click **Explore database** in the main application's top bar to open the separate portal in a new tab for the **same workspace**. Its `#workspace=…` fragment preserves the investigation's graph selection. The ID is an access capability, not production authentication, and can expire. Use the permanent [live portal](https://chronosgraph.onrender.com/database) root URL for submission; it offers **Create workspace** for an independent copy. Locally the portal is at `http://127.0.0.1:8000/database`; an existing ID can also be entered manually.

Tables use compact previews; clicking a record exposes all decoded fields, native properties and paginated connections. The catalog groups company knowledge, operations/finance, and investigation/setup records. Search returns exact filtered counts. Pages use 50 records in the UI and accept at most 100. Schema/indexes and integrity views show actual database state; observed fields are not all mandatory constraints. All eight integrity checks are structural checks, not an endorsement of generated answers. The portal excludes the session registry, credentials and other visitors' graphs.

Fixed operations are `catalog`, `rows`, `relationships`, `record`, `audit` and `export`, through `POST /api/database/{operation}`. There is no arbitrary Cypher or edit/delete console. Reads use `GRAPH.RO_QUERY`; workspace creation uses the separate session API and reopening may apply non-destructive schema migration. JSON export assembles complete pages, including beyond the server's 10,000-row cap, and refuses more than 25,000 nodes or 50,000 relationships. The process lock covers this application's export, not writes from another process. Source hashes and structural checks do not prove factual truth.

## Import another company

The trusted local importer accepts JSON `nodes` and `relationships`, validates identities/endpoints/source references and accepted-rule support, calculates source hashes and creates a new graph without clearing existing data:

```sh
PYTHONPATH=backend .venv/bin/python scripts/import_company.py datasets/atlas-studio.json
```

The command prints app and inspection URLs. The unrelated fictional Atlas Studio fixture tests Finance approval, Marketing ownership and invoice arithmetic without logistics assumptions. Nodes require `id`, `kind` and `title`; safe scalar fields are mirrored natively for generic aggregation, while nested fields stay in the complete payload. Sources need an excerpt, enabled flag and timezone-aware timestamp. Accepted rules need subject/field/value, both time intervals and a supporting source edge. [Importer](../scripts/import_company.py) · [fixture](../datasets/atlas-studio.json) · [tests](../backend/tests/test_database_inspection.py).

This is a trusted developer operation, not a public document uploader, automatic extraction service or model-controlled policy write.

## Public references and boundaries

Delhivery's public [express-parcel service](https://www.delhivery.com/services/express-parcel), [order lifecycle](https://help.delhivery.com/docs/update-forward-order), [developer FAQ](https://one.delhivery.com/developer-portal/document/b2c/detail/faq), [delivery-exception guide](https://help.delhivery.com/docs/exception-ndr), [return-to-origin guide](https://help.delhivery.com/docs/courier-returnrto) and [COD guide](https://help.delhivery.com/docs/cod-remittance) inform entity types and terminology.

Historical account context comes from its [Q1 FY24 release](https://www.delhivery.com/uploads/2023/08/PressRelease.pdf), [FY24 annual report](https://www.delhivery.com/uploads/2024/08/Annual_Report_FY24.pdf) and [press archive](https://www.delhivery.com/company/press-release). Public business relationships do not establish our invented agreements, warehouse locations, staff responsibilities, incidents, amounts or policy terms. No private Delhivery schema, employee directory, shipment feed or client contract was obtained.

Operational snapshots and current relationships are not historical reconstructions. A missing scan is not proof of parcel loss, a settlement discrepancy is not proof of cash loss, and a proposal is not approval. The investigator must preserve these distinctions, but generated explanations still require review.
