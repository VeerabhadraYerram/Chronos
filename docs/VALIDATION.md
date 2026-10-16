# Validation and audit evidence

## Company reference-workspace verification

The new real-FalkorDB suite covers the 1,200-consignment graph, active commitments, required relationships, effective/recorded boundaries, source withdrawal, isolated graph-copy previews, cost provenance, idempotent replay, stale review rejection, recorded reasons, unknown questions, parameterized input, read-only tools, contextual exploration, API validation and session isolation. See [test_company_reference.py](../backend/tests/test_company_reference.py).

The original 16 tests below are preserved. Together with the new 31 integration tests, the suite has **47 passing tests** at this implementation milestone. The frontend production build also passes. Provider-fallback routing is tested with a controlled transport stub; live-provider status is recorded separately, not inferred from that stub. These checks do not prove model semantic correctness, real logistics outcomes, public deployment or exact replication of Delhivery's private systems.


[Run the evaluation](EVALUATION.md) · [CI workflow](../.github/workflows/ci.yml) · [Live GitHub runs](https://github.com/VeerabhadraYerram/Chronos/actions/workflows/ci.yml)

Local verification date: **October 16, 2026**. Environment: macOS ARM64, Python 3.13, Node.js 20.19.6, real FalkorDB v4.22.1. The image digest is pinned in Compose and CI. The live Actions run is the source for remote CI status; local results do not imply a remote run passed.

## Reproduce all checks

```sh
./scripts/check.sh
```

The script requires installed dependencies and a reachable real database. It uses disposable graphs, does not call Gemini, and does not reset the configured demo graph.

| Check | Command | Local result |
| --- | --- | --- |
| Integration suite | `PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q` | 47 passed |
| Business scenario | `PYTHONPATH=backend .venv/bin/python scripts/evaluate.py` | 12 expected outcomes checked |
| Frontend | `npm --prefix frontend run build` | TypeScript check and production build passed |
| Documentation | `.venv/bin/python scripts/check_docs.py` | Local links, heading anchors, and image targets checked |

CI runs the same integration suite and business scenario against a real FalkorDB service, builds the client in a separate job, and checks documentation in a third job. Actions are pinned by commit SHA and the workflow has read-only repository permission. CI deliberately uses an empty Gemini key.

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
