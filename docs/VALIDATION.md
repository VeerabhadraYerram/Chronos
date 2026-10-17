# Validation and audit evidence

## Company reference-workspace verification

The new real-FalkorDB suite covers the 1,200-consignment graph, active commitments, required relationships, effective/recorded boundaries, source withdrawal, isolated graph-copy previews, cost provenance, idempotent replay, stale review rejection, recorded reasons, unknown questions, parameterized input, read-only tools, contextual exploration, API validation and session isolation. See [test_company_reference.py](../backend/tests/test_company_reference.py).

The original 16 tests below are preserved. Together with 35 reference-workspace tests, 23 inspection/general-engine tests and seven public-deployment tests, the suite has **81 passing tests** at this implementation milestone. The frontend production build and two geometry tests also pass. Provider-fallback routing is tested with a controlled transport stub; live-provider status is recorded separately, not inferred from that stub. These checks do not prove model semantic correctness, real logistics outcomes, public deployment or exact replication of Delhivery's private systems.


[Run the evaluation](EVALUATION.md) · [CI workflow](../.github/workflows/ci.yml) · [Live GitHub runs](https://github.com/VeerabhadraYerram/Chronos/actions/workflows/ci.yml)

Local verification date: **October 17, 2026**. Environment: macOS ARM64, Python 3.13, Node.js 20.19.6, real FalkorDB v4.22.1. The image digest is pinned in Compose and CI. The live Actions run is the source for remote CI status; local results do not imply a remote run passed.

## Reproduce all checks

```sh
./scripts/check.sh
```

The script requires installed dependencies and a reachable real database. It uses disposable graphs, does not call Gemini, and does not reset the configured demo graph.

| Check | Command | Local result |
| --- | --- | --- |
| Integration suite | `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q` | 81 passed |
| Business scenario | `PYTHONPATH=backend .venv/bin/python scripts/evaluate.py` | 12 expected outcomes checked |
| Frontend | `npm --prefix frontend run build` | TypeScript check and production build passed |
| Documentation | `.venv/bin/python scripts/check_docs.py` | Local links, heading anchors, and image targets checked |

CI runs the same integration suite and business scenario against a real FalkorDB service, builds the client in a separate job, and checks documentation in a third job. Actions are pinned by commit SHA and the workflow has read-only repository permission. CI deliberately uses an empty Gemini key.

The inspection suite verifies enforced IDs, required native fields, complete pagination/export, hidden session registries, migration idempotency, structural fault detection, independent company data, changed-owner answers, generic arithmetic, withdrawn evidence, HTTP limits and cross-workspace boundaries. These checks use disposable real FalkorDB graphs.

A live Groq response on October 17 correctly reported 12 Client companies after the additive expansion. This verifies that run, not every possible future model response.

## Account expansion and graph layout checks

The account coverage extension verifies 12 clients, three distinct-city pickup warehouses per client, 36 assigned operational review items, 25 source-backed document statements, diverse accepted rule fields and additive migration with retained history. The scheduling simulation still uses exactly its original 1,200 consignments even though ordinary Bengaluru traffic is now present.

A regression crosses the database server's 10,000-row response cap with saved history and verifies complete catalog counts and full node/relationship exports. Internal catalog, migration and audit reads page in 1,000-record batches.

Two frontend geometry tests cover 100 coincident relationship labels, varied measured label heights, moving card obstacles and deterministic placement. Labels reserve padded rectangles against every card and previously placed label; when crowded, the search expands canvas space. Displaced labels retain dotted connectors. Browser checks on a real 11-record / 19-connection answer found zero label-to-label and label-to-card intersections before and after dragging and zooming. Fit View includes displaced labels. This prevents label occlusion; dense graphs still require pan/zoom for comfortable reading.

## Automated coverage

Source: [test_company_brain.py](../backend/tests/test_company_brain.py). Each test creates its own uniquely named graph.

| Test | Business invariant |
| --- | --- |
| `test_original_global_removal_conflicts` | 0 ms violates both original minima and has source-backed graph context. |
| `test_preserving_minimum_has_no_modeled_conflict` | Preserving 250 ms meets the modeled constraint. |
| `test_migration_only_changes_partner_b` | B's migration cannot erase A's requirement. |
| `test_effective_time_before_migration_keeps_original_requirement` | Earlier effective dates retain the old minimum. |
| `test_late_evidence_does_not_rewrite_what_was_known` | Historical belief differs from retrospective knowledge. |
| `test_half_open_valid_interval_boundary` | The new requirement applies at the exact effective boundary. |
| `test_document_conflict_is_scoped_to_migrated_partner` | Runbook disagreement is attributed to B. |
| `test_chat_proposal_cannot_override_accepted_policy` | A proposal cannot silently become policy. |
| `test_withdrawn_evidence_forces_abstention` | Unsupported original requirements do not produce confident assessments. |
| `test_event_replay_is_idempotent` | Duplicate migration does not increment revision again. |
| `test_receipt_survives_new_client_and_is_invalidated` | Saved context survives reconnection and becomes stale after change. |
| `test_graph_copy_is_independent` | Updating a copy does not change base graph behavior. |
| `test_unknown_time_and_missing_relationship_abstain` | Missing temporal/relationship evidence is surfaced. |
| `test_api_approval_idempotency_and_stale_block` | Duplicate approval reuses the action; changed evidence blocks it. |
| `test_api_rehearsal_preserves_base` | API rehearsal preserves the base revision and checks the scoped proposal. |
| `test_validation_rejects_invalid_scope_and_unzoned_date` | Unsupported partner scope, negative delay, and unzoned dates are rejected. |

The [business evaluator](../scripts/evaluate.py) independently walks the documented story, including clone isolation, scoped migration, both time axes, stale receipts, proposal handling, and source withdrawal. It prints pass/fail results from live queries; they are not canned application verdicts.

## Company workspace manual verification

- A real Groq run completed a model-selected graph read and returned an accepted investigation result. Gemini returned 503 during checks; fallback and graph-only states were explicitly labeled. Provider success is not an unrestricted quality benchmark, and API availability/quota can vary.
- Browser checks covered initial commitments, record inspection, graph-neighbor expansion, contextual follow-up, persisted history after reload, amendment replay, stale-receipt warnings, the changed answer and handbook-review flag, spatial/readable graph switching, graph-copy comparison, commitment-preserving alternative and a source-linked review packet.
- The 390 px mobile layout had a 390 px document width and readable controls in the inspected viewport. This is not a full accessibility audit.
- [Investigation capture](assets/company-investigation.jpg) and [comparison capture](assets/company-comparison.jpg) are native local screenshots, not design mockups.

## Preserved payments manual verification

- **Persistence:** compared graph content hashes and all 12 existing receipt IDs before and after a real database restart. Both matched. Append-only storage was enabled and the mount matched the official image's data directory. This is not a power-loss or disaster-recovery test.
- **Gemini:** performed a real model invocation that selected the constraint, owner, and conflict tools and returned accepted source IDs. The interface was also checked with a saved successful Gemini receipt. No automated adversarial or broad semantic-quality benchmark is claimed.
- **Interface:** inspected desktop and 390 px mobile layouts; checked source drawers, saved receipts, expanded graph, graph-scope switching, keyboard source activation, and Escape dismissal. No horizontal page overflow was observed at the tested mobile width. This is not a complete accessibility conformance audit.

The [workspace image](assets/workspace.png) is an actual captured UI state with fictional data. It shows B after migration. A screenshot alone is not evidence of backend correctness; use the executable checks above.

## Unverified or intentionally absent

Production deployment, general source ingestion, live connectors, expertise scoring, fully temporal ownership/topology/source access, external publishing, multi-user authorization, multi-worker operation, crash-atomic ingestion, and a fair retrieval-baseline benchmark remain outside current verification. Recorded timings are per-run observations, not performance guarantees.

## General-engine live provider check

On October 16, 2026 a real Groq invocation investigated the unrelated Atlas Studio fixture, selected `search_records` and `aggregate_records`, and returned INR 32,500 for the stored invoice sum. This was a manual live-provider check, separate from the deterministic 60-test suite. One earlier provider attempt failed and preserved the labeled graph-retrieval response; reliable broad semantic accuracy or model availability is not claimed. The extended fixture also tests generic document-assertion mismatches against accepted policy.

## Expanded workspace and provider checks (October 16)

The extended suite covers actual plural client counts that change with inserted data; typed JSON read plans executing real database arithmetic; rejection of a generated number that contradicts a database count; provider order and free-model restriction; and stale receipts when knowledge changes during inference. A controlled stub verifies routing and validation, not model semantics.

Live Groq generated the correct three-client count and the expanded fixture invoice sum of INR 153,450. A live OpenRouter free model generated the COD explanation, named Finance, and explicitly declined to infer cash loss, with source IDs from the retrieved graph. Some live attempts failed from rate limits, tool formatting or response validation; Gemini was also unavailable during some checks. These are examples, not an always-correct quality guarantee. The app retains an explicit unavailable state when every provider fails.

The separate database portal and main workspace are manually checked at desktop and mobile widths. Long IDs, structured values and document bodies are previewed in compact table rows; complete fields remain in the detail inspector/export. All operational data remains synthetic. See [Data scenarios](DATA_SCENARIOS.md).

## Free Render evaluation package

The existing 74-test milestone is supplemented by seven deployment-boundary tests: static frontend/inspection availability, excluded shared legacy APIs, origin/body/rate controls, a global AI admission budget, database/provider readiness, readiness independence from the workspace lock, and opt-in expiry limited to registered temporary visitor graphs. All seven pass against the finalized code; the existing tests passed in the full run. The two frontend layout tests and production build pass inside the Docker build.

A local ARM64 smoke test ran the submission container under a 512 MiB limit. It loaded the reference-only RDB, returned healthy readiness with 12 clients, passed the full structural audit, and produced a live Groq investigation. Direct Groq and OpenRouter checks also completed successfully. Temporary-workspace recovery was verified in the browser after replacing the disposable container. This is local container verification, not proof of Render deployment, AMD64 resource behavior or provider availability at judging time.

The free Render Blueprint provisions one web service, with the frontend, API and loopback-only actual FalkorDB. No paid disk or database is declared. Cold starts, ephemeral storage, one-hour inactive-workspace expiry and public capacity limits are documented in [deployment instructions](DEPLOYMENT.md). The live Render URL is recorded below; the final demo video remains a separate release check.

## Live Render verification — October 17, 2026

The public [app](https://chronosgraph.onrender.com) and [inspection portal](https://chronosgraph.onrender.com/database) returned HTTPS 200; `/readyz` confirmed real FalkorDB readiness. Groq answered the external-client count with 12. A separate SUGAR cash-reconciliation investigation completed through the free OpenRouter fallback, identified Finance ownership and distinguished an unmatched settlement from evidence of loss. The latter took about 105 seconds across provider attempts; free-provider answers are not consistently fast or always available.

The live evidence map contained eight relationship labels with zero measured label/label or label/card intersections. Clicking a relationship opened its actual supporting records. The inspection portal initially encountered database errors, then recovered on retry; catalog loading took about 9.5 seconds on the deployed free instance. A follow-up patch reduces catalog transfer to payloads and native key names in 250-record pages, retains complete schema discovery, raises bounded hosted database timeouts, and fixes a half-connected portal state after an initial error. The patch was deployed as `872f57f`; its live catalog displayed all 9,992 records, 12 clients and 36 warehouses. A subsequent full inspection exposed a separate health-probe problem: Render recorded a five-second health timeout and restarted the instance while the global workspace lock was held. Readiness now reads only reference metadata without that lock or any seed/migration writes. A regression test holds the workspace lock while requiring readiness to complete independently. Final live verification of this correction is recorded after deployment. A 512 MiB container restricted to 0.1 CPU completed repeated catalog reads with 9,992 records and 36 work items, and passed the structural audit. Full scans remained slow (about 21–32 seconds in that constrained local test); no faster hosted latency is claimed.

The final demo video and authenticated organizer submission remain outstanding.
