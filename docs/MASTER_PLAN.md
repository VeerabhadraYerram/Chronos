# ChronosGraph: Final Product Master Plan

Prepared October 15, 2026. Planning assumption: one builder, approximately 36 focused build hours before October 18, 11:59 PM IST. Adjust scope downward if fewer hours are available. This is a product recommendation, not a prediction of judging results.

## 1. The product decision

**ChronosGraph is a company decision memory that investigates proposed changes, shows the evidence behind its assessment, and prepares the work needed to make the change safely.**

Pitch: “Your company remembers what it built. ChronosGraph remembers why, what still depends on it, and what must change before you can move on.”

Primary user: the engineering lead at a small software company approving a consequential change. Primary task: understand whether a proposed change conflicts with a still-active company decision or commitment, then coordinate a resolution.

Target Company Brain first. Code is the trigger; company knowledge is the product. Every demonstration must connect a change to people, decisions, documents, and a business commitment. An isolated AI code reviewer would weaken this positioning.

The single demo story: fictional company NovaPay wants to remove a 250 ms retry delay from its payment worker. A previous incident led to a partner-specific constraint. A later partner migration changes the constraint for one partner, but not another. ChronosGraph must distinguish who is affected, which evidence is current, what remains unknown, and what work would permit a narrower change.

## 2. Audit of the supplied blueprint

Reviewed all ten pages of the supplied ChronosGraph blueprint. Keep the decision-lineage thesis, connected company knowledge, traceable results, event replay interface, and seeded fictional company. Revise the following before implementation.

| Blueprint claim or design | Audit finding | Final decision |
|---|---|---|
| “90%” of submissions fail; judges see hundreds of identical projects | No supporting evidence is provided. This is persuasive language, not research or a judging rubric. | Remove these claims. Differentiate through demonstrated behavior. |
| Four unique use cases | Section 2 develops only Use Case A; other concepts appear later in the demo. | Use one cohesive workflow with successive capabilities. |
| Four-hop/five-hop lineage | The shown query has six relationship segments: MODIFIES, INCLUDES, RESOLVES, DISCUSSED_IN, RESULTED_IN, GOVERNED_BY. | Derive hop count from the actual returned path. |
| Query supported by the schema | File, Commit, and Contract labels used in the example are absent from the schema table. Many query relationships are also absent; MODIFIES targets System in the table but File in the query. | Define and test one canonical schema. Remove Commit from the minimum version. |
| Decision tracing proves a code constraint | A path indicates a relationship, but cannot alone establish that a particular diff violates a constraint. A document may also be obsolete or apply to another partner. | Represent explicit scoped constraints; distinguish evidence, inference, and verdict. |
| Bi-temporal graph | valid_from/valid_until capture only when a fact applies; they do not record when the system learned or corrected it. | Implement both valid time and recorded time at the application layer. Do not claim a native temporal database feature. |
| A new chat message automatically invalidates a decision | A suggestion may not be an authorized decision. Newer does not necessarily mean authoritative. | Extract a candidate, compare scope and authority, and require explicit acceptance for policy updates. |
| Native centrality MCP tool | Graph algorithms exist, but the PDF does not establish an available MCP tool with that name or interface. | Use the database client and typed application tools. MCP is optional packaging. |
| Centrality identifies the true expert or bus factor | Centrality describes structural importance. It does not establish competence, availability, or knowledge redundancy. | Rank reviewers using ownership and recent relevant evidence; show the contributing evidence. Defer bus-factor claims. |
| Agent blocks a risky PR | Posting a comment does not prevent merging. Enforcement requires an appropriate check and repository rules. | Minimum: assessment and action proposal in the app. Optional: real check on a configured demo repository; verify enforcement before saying “blocked.” |
| Private chat evidence posted to GitHub | Could reveal evidence outside its original audience. | Demo with intentionally public fictional data. Any future connector must enforce source permissions before retrieval and publication. |
| Strict isolation shown by switching graphs | A company graph and its agent-memory graph are not two separate tenants. A UI toggle does not prove access control. | Keep memory with its company for the minimum version. A real isolation demo needs two tenants and server-side negative tests. |
| Three agents imply Track 2 qualification | Three boxes in a diagram do not demonstrate durable memory or handoff correctness. | Start with one tool-using investigator. Add a second agent only after the primary workflow is complete. |
| Under-3 ms traversal and 2.4 ms display | These are unmeasured example numbers; even fast graph queries do not establish end-to-end agent latency. | Display measured graph, model, and total timings separately. |
| Vector RAG confidently approves the bad change | The shown comparison predetermines the baseline answer. Other retrieval approaches may find the evidence. | Drop the comparison from the main demo. If evaluated, use an actual baseline, equal inputs, and publish results including losses. |
| Automatic documentation repair | A policy may intentionally differ by version, partner, or date. Not every difference is staleness. | Detect scoped conflicts and draft a patch with evidence; require approval before publishing. |
| Four external tool ecosystems and full continuous ingestion | Connector setup, permissions, event ordering, and entity resolution consume the short build window. | One actual repository input if feasible; Markdown/JSON source uploads and clearly labeled event replay for everything else. |

## 3. The feature set, in build order

### P0: Decision receipts

Input: a proposed change, target system, partner scope, and optional diff. The investigator chooses typed tools to find relevant constraints, fetch decision history, inspect dependencies, and retrieve evidence. The result contains:

- Assessment: conflict found, no known conflict in checked scope, or insufficient evidence.
- Proposed change and exact scope checked.
- Applicable decision and constraint versions.
- Clickable evidence excerpts with source IDs and timestamps.
- The actual relationship path used, with directions and labels.
- Known gaps, disputed assertions, and suggested next action.
- Run ID, tool trace, dataset revision, and measured timings.

Do not equate “no known conflict” with “safe.” Avoid fake numerical confidence. Show evidence coverage and missing links instead. The agent selects tools and synthesizes explanations; deterministic application logic validates source IDs and explicit constraint checks.

Done when changing or deleting an essential supporting fact changes the assessment appropriately. A screenshot of a prewritten answer does not qualify.

### P0: Time Machine

Ask two distinct questions: “What applied on this date?” and “What did we know as of this date?” Provide date presets before implementing a slider.

Example: a partner migration takes effect October 10 but is only uploaded October 12. An October 11 assessment using knowledge available October 11 must differ from a retrospective October 11 assessment using today's knowledge.

Display valid time and recorded time side by side. History is append-only; corrections add versions rather than erasing the record. This is the most distinctive temporal feature and must be correct before visual embellishment.

### P0: Contradiction Inbox

Import a document saying the backoff is mandatory globally and a newer accepted decision narrowing it to Partner A. Compare assertions with the same subject, field, scope, and overlapping valid interval. Flag a contradiction, or a possible scope mismatch, with both excerpts.

An unapproved chat message becomes a proposal. It cannot silently supersede an approved requirement. A reviewer can accept, reject, or request clarification; the choice and rationale persist across sessions.

Minimum supported facts: required backoff in milliseconds, governing partner, decision approval, document claim, and owner. Do not promise general contradiction detection across arbitrary prose.

### P1: Rehearsal Mode

“What changes if we remove this constraint?” Copy the small company graph into a server-owned scenario graph, apply the proposed change, and rerun the same checks. Show a before/after list of affected services, company commitments, owners, and documents.

This is dependency impact analysis under explicit assumptions. It does not prove that an outage will occur or forecast financial loss. Model conditional dependencies explicitly; an ordinary DEPENDS_ON edge does not imply failure propagation.

Make the feature tangible: baseline says two partner flows remain in conflict; scoped alternative changes one flow and preserves the other's constraint. Use deterministic rules over the fictional fixture, not a model-generated “risk percentage.”

FalkorDB documents GRAPH.COPY. Verify it against the pinned deployment early. Fallback: reconstruct a scenario graph from the same versioned seed plus event log. Scenario changes must never write to the base graph.

### P1: Repair Plan

Turn a receipt into a concrete work package: proposed narrower change, documentation patch, required verification steps, reviewer recommendation with reasons, and remaining questions. Each proposed action references its supporting receipt.

Build an in-app review and approve flow first. A real GitHub draft PR containing the documentation patch is a stretch integration. If no external artifact exists, label the result “draft prepared,” never “PR created.”

### P2: Evidence Challenge

A judge removes a source or introduces a conflicting fact. The investigator reruns and explicitly changes its answer or abstains. This makes the app testable and shows that the graph influences its behavior. Track dependencies from receipts to facts so affected receipts are marked stale after an update.

### Deferred backlog

Organization-wide expert discovery, voice interface, Slack bot, four production connectors, autonomous merging, automatic production changes, general code vulnerability detection, quantified outage prediction, sophisticated graph algorithms without a user need, and a separate multi-agent memory platform. These can become later product work; they should not displace a working submission.

## 4. Interface and demonstration experience

Use a focused investigation workspace with three areas:

1. Left: proposed change, company scope, date presets, and replayable events.
2. Center: the evidence subgraph for this investigation, normally 8–15 nodes. A timeline below it shows accepted and superseded decisions.
3. Right: assessment, source excerpts, conflicts, missing evidence, and the repair proposal.

Tabs: Investigate, History, Rehearse. Show the fictional company and “Demo dataset” label consistently. Event replay buttons must say “Replay sample event,” not imply a live Slack connection.

Clicking a sentence highlights its source and path. Clicking a source opens its excerpt and provenance. Unsupported assertions get a visible warning. The graph must be useful to inspect, not a large decorative cloud.

Provide three presets: risky global removal, valid partner-scoped change, and incomplete evidence. Custom text input must invoke the same tools as presets.

## 5. Architecture and data contract

Recommended stack: Next.js + TypeScript + Tailwind + React Flow; FastAPI + Pydantic; official Python FalkorDB client; one available LLM with tool calling and structured output. Use server-sent events for the investigation trace if useful. Start with ordinary functions and a bounded agent loop; add LangGraph only if already familiar with it. Pin dependencies and a tested database image rather than relying on floating latest tags.

Flow: source upload or repository event -> normalization -> structured extraction -> entity and source validation -> accepted fact versions -> FalkorDB -> investigator tools -> deterministic verification -> receipt -> approved action.

Keep all core knowledge, accepted fact versions, decisions, receipts, and memory in FalkorDB. Raw files may be stored separately, referenced by immutable hash. Do not recreate the relationship engine in frontend JSON or hardcode fixture verdicts.

Canonical node labels:

| Label | Purpose |
|---|---|
| Person | Owner or reviewer, using a stable ID |
| System | Service or subsystem with stable identity |
| File | Repository and path; distinguish rename from new identity where supported |
| Change | Proposed diff/event and its explicit scope |
| Decision | Durable identity for a decision |
| FactVersion | Versioned assertion: subject_id, field, value, scope, valid_from, valid_to, recorded_from, recorded_to, status |
| Source | Source ID, source type, content hash, excerpt, URL if real, source timestamp, ingested timestamp |
| Document | Stable document identity and revision metadata |
| Commitment | Fictional partner requirement and governing scope |
| Receipt | Assessment, dataset revision, tool trace, evidence dependencies |
| Action | Proposal, approval state, idempotency key, optional verified external ID |

Core directions: Change MODIFIES File; File PART_OF System; Decision APPLIES_TO System; Decision HAS_VERSION FactVersion; FactVersion SUPPORTED_BY Source; FactVersion SUPERSEDES FactVersion; Decision GOVERNED_BY Commitment; Person OWNS System; Document ASSERTS FactVersion; System DEPENDS_ON System; Receipt USED FactVersion; Receipt PROPOSES Action. Add a Ticket node only if it earns its place in the demo.

Dependency and ownership changes also need versioning if they participate in historical answers. Represent these as versioned assertions rather than overwriting bare edges. Initially freeze those relationships in the fixture and explicitly limit historical claims to the supported versioned fields.

Temporal selection for a fact version uses half-open intervals:

`valid_from <= effective_at < valid_to` and `recorded_from <= known_at < recorded_to`, with null ends treated as open. Store comparable UTC timestamps consistently. A correction closes the previous recorded interval and appends the corrected version. A later business decision adds a new valid interval. Document examples and test both cases; a SUPERSEDES edge alone is insufficient.

Keep an ingestion ledger and a monotonically assigned application dataset revision for receipts. This revision is an application concept, not FalkorDB's query schema version parameter. Serialize accepted writes in the minimum version; a receipt must use one stable revision or detect a change and retry.

Typed investigator tools:

- resolve_entities(text, allowed_scope)
- find_applicable_constraints(system_id, partner_id, effective_at, known_at)
- trace_decision(decision_id, effective_at, known_at)
- get_evidence(source_ids)
- inspect_dependencies(system_id, bounded_depth)
- find_conflicts(subject_id, field, scope, interval)
- create_scenario(change_id)
- propose_actions(receipt_id)

Use parameterized templates, bounded paths, result limits, and query timeouts. Read tools execute via GRAPH.RO_QUERY; dedicated server-side handlers perform approved writes. The model does not receive arbitrary database credentials or permission to run unrestricted Cypher. Source text is data and cannot modify tool policies. An unavailable source is reported rather than invented.

For the hackathon, one company and no enterprise tenant claim is sufficient. If adding tenants, authenticate server-side and select graph names from trusted mappings. Graph separation alone does not implement user permissions. Never use a client-supplied graph name as authorization.

## 6. Dataset and proof

Start with 30–50 meaningful nodes and a small, documented set of relationships. Node count is not a success metric. Use one coherent timeline and stable IDs across repository, chat exports, and Markdown sources. Include distractors and similar names to exercise entity ambiguity.

Required cases:

1. Old incident, accepted backoff decision, supporting partner commitment, and current proposed global removal.
2. Later migration lifting the requirement for Partner B only.
3. Outdated documentation incorrectly stating the requirement remains global.
4. Unapproved chat suggestion to remove all delays.
5. Late-arriving record whose effective date precedes its ingestion date.
6. Missing or retracted evidence requiring abstention or reduced scope.
7. Duplicate event to prove ingestion idempotency.

Maintain at least 12 manually authored evaluation cases with expected constraint IDs, relevant sources, applicable time and partner scope, expected assessment, and forbidden unsupported assertions. At least four cases must require multiple source types, four exercise temporal/scope changes, and two require abstention; cases may overlap.

Necessary acceptance checks:

- Every displayed supporting source ID exists and belongs to the allowed dataset.
- Historical selection returns the expected fact versions for both time axes.
- A new proposal cannot supersede an approved constraint automatically.
- A scoped migration cannot erase another partner's requirement.
- Replay is idempotent and receipts persist after app restart.
- Rehearsal changes leave the base graph unchanged.
- Conflicting evidence produces a visible conflict, not silent preference for the latest text.
- Missing relationship evidence prevents a confident violation claim.
- Approving an action twice cannot publish it twice.
- A changed graph invalidates dependent receipts.

Collect measured graph query time, model time, total time, source validity, and scenario pass rate. Report observations with dataset size, environment, and run count. Do not turn one successful run into a performance claim.

Optional retrieval comparison: same model, source corpus, answer format, and comparable context budget for both systems. Run a real text/vector baseline and ChronosGraph on all evaluation cases; publish prompts, results, misses, and latency. No canned incorrect baseline responses. Cut this entire experiment if it threatens delivery.

## 7. Execution plan through the deadline

These are time budgets, not guarantees. Finish a basic deployed vertical slice before adding P1 features.

| Date / budget | Deliverable | Gate |
|---|---|---|
| Oct 15 / first 10 focused hours | Database smoke test; canonical seed; one tool-using investigation; evidence receipt; basic deployed or locally reproducible UI | A new proposed change causes real graph reads and a source-backed answer. |
| Oct 16 / next 10 hours | Valid/recorded time selection; contradiction workflow; persistent accepted/rejected decisions; evaluation fixtures | Late evidence and partner scope behave correctly. |
| Oct 17 / next 10 hours | Rehearsal Mode, repair drafts, interaction polish; one real repository input if time permits | Scenario isolation and before/after checks pass. |
| Oct 18 / remaining 6 hours | Run checks; improve errors; README, short video, sources and limitations; submission | A new user can reproduce the story. Reserve at least two hours before 11:59 PM IST for submission issues. |

If only 18 hours are available: build receipts, one valid-time history view with honest limitation, one conflict case, and draft actions. Drop recorded-time claims until implemented. If the agent loop is unreliable, constrain it to a small verified tool set and a maximum number of steps. If the graph UI takes more than two hours to stabilize, replace layout ambition with a readable path list.

Cut order: benchmark, second connector, second agent, external publishing, animated graph, general expert scoring. Protect provenance, temporal correctness, meaningful FalkorDB use, and a complete demo.

## 8. Three-minute demo

0:00–0:15: “Removing six lines of code looks easy. The hard part is remembering which company promise those lines protect.” Show the proposed global removal.

0:15–0:55: Run investigation live. Highlight code -> system -> accepted decision -> partner commitment, with original excerpts. Show conflict found and the specific scope. Acknowledge missing evidence if present.

0:55–1:25: Replay the migration record and show its effective and recorded dates. Compare the historical view with the current view. Partner B's requirement changes; Partner A's remains.

1:25–1:50: Reveal the outdated global documentation and an unapproved chat proposal. Show the conflict and why the proposal did not overwrite policy.

1:50–2:25: Rehearse the partner-scoped alternative. Compare affected commitments and documents. Show that the original graph is unchanged.

2:25–2:45: Prepare a documentation patch and reviewer task with evidence. Show an in-app approval and durable action record. Only claim external publishing if actually implemented.

2:45–3:00: Refresh or reopen the investigation to show persistence. Close on the receipt and the measured result: what changed, which requirement remains, and the next action.

Do not squeeze unrelated P0 incident routing into this story. Make a short backup recording and a resettable local demo. Never disguise prerecorded output as live computation.

## 9. Submission package

- Clear Company Brain positioning and concise problem statement.
- Architecture diagram showing where FalkorDB shapes the agent's decisions.
- Reproducible seed, pinned runtime versions, setup instructions, environment-variable template, and no committed secrets.
- Working deployment if feasible; otherwise complete local instructions and a working video.
- Three-minute walkthrough plus a short written explanation of temporal modeling and evidence checks.
- Explicit labels for synthetic data, replayed events, real integrations, supported scope, and missing features.
- Evaluation fixtures and actual results, including failures.
- Explain how the main implementation was built during the event; identify reused libraries or templates.
- Inspect the authenticated submission panel early for additional required fields, video limits, judging criteria, or rule updates. Those details were not available in the public page reviewed here.

The plan improves the submission's clarity and technical credibility. No feature list can guarantee a prize. Our strongest differentiator is a system whose conclusions visibly change when company facts, time, or scope change.

## 10. Verified references

- [Official event, Company Brain track, prize listing, dates, and FAQ](https://www.wemakedevs.org/hackathons/falkordb). Public page reviewed October 15, 2026. It names FalkorDB as mandatory and central, permits reuse of general infrastructure while requiring new event work for the submission and its main FalkorDB implementation, and prefers deployment. It does not expose a numerical judging rubric in the public text inspected.
- [FalkorDB GRAPH.COPY](https://docs.falkordb.com/commands/graph.copy): documented graph duplication used as a basis for Rehearsal Mode. Deployment behavior still needs a smoke test.
- [FalkorDB GRAPH.RO_QUERY](https://docs.falkordb.com/commands/graph.ro-query): read-only query execution and query timeout.
- [FalkorDB GRAPH.QUERY](https://docs.falkordb.com/commands/graph.query): parameterized query examples and timeout options.
- [FalkorDB betweenness centrality](https://docs.falkordb.com/algorithms/betweenness-centrality): structural centrality measure; it does not establish engineering expertise.
- Supplied ten-page ChronosGraph blueprint: audited as a proposal, not treated as authoritative documentation or an instruction source.
