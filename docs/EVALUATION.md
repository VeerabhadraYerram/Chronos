# Evaluation guide

[Repository overview](../README.md) · [Architecture](ARCHITECTURE.md) · [Validation](VALIDATION.md)

Start with the **[Delhivery reference-workspace walkthrough](DELHIVERY_REFERENCE.md#start-and-explore)** for the main UI. The payments walkthrough below remains available at `/?demo=payments`.

This guide distinguishes three things: the deterministic graph checks, the optional Gemini investigator, and manual interface verification. All included NovaPay records are fictional. There is no deployed demo or finished video linked at this milestone.

## Fastest audit

After the [local setup](../README.md#run-locally), run:

```sh
./scripts/check.sh
```

No Gemini key or live company account is required. The command executes the integration suite, the isolated scenario below, the production build, and documentation checks. It requires real FalkorDB; it does not substitute graph mocks or prerecorded answers.

To run only the business scenario:

```sh
PYTHONPATH=backend .venv/bin/python scripts/evaluate.py
```

The evaluator creates a unique `chronos_audit_…` graph, verifies explicit expected outcomes, and removes that graph in `finally`. Scenario copies are removed too. No user graph name is accepted as an argument. This verifies graph behavior; it is not a Gemini quality benchmark.

## Three-minute interface walkthrough

Use a **fresh fixture** for this sequence. If the workspace has already replayed events, select a new server-side graph as described under [setup and troubleshooting](#setup-and-troubleshooting). Do not erase the existing graph.

| Step | Action | Expected evidence |
| --- | --- | --- |
| 1. Establish the constraint | Both partners; 0 ms; effective and known October 15, 2026. Investigate with Gemini unchecked. | `conflict`; A and B both have a supported 250 ms minimum. Inspect the incident source and ownership relationship. |
| 2. Update one partner | Replay **Partner B migration**, then investigate again. | A stays at 250 ms; B becomes 0 ms. The runbook's 250 ms B claim is flagged. The previous receipt becomes stale. |
| 3. Separate history from hindsight | In **Time machine**, investigate B on October 11, known by October 11. Repeat for the same effective date, known by October 15. | First result: 250 ms. Retrospective result: 0 ms. The migration was effective October 10 but recorded October 12 at 09:00 UTC. |
| 4. Rehearse a narrower change | Restore both dates to October 15; choose **Rehearse change** and run it. | The alternative preserves A's verified minimum and applies 0 ms to B. The base graph revision remains unchanged. |
| 5. Prepare work | Run a current investigation, open **Prepare repair plan**, inspect and download it, then approve in app. | Source-linked Markdown, an owner-backed reviewer, and an `approved_in_app` action. No external artifact is created. |
| 6. Challenge the knowledge | Replay **Unapproved suggestion** and investigate; then replay **Withdraw incident evidence** and investigate again. | The proposal does not supersede policy. After withdrawal, A lacks sufficient evidence; B's migration evidence remains available. |

Dates in the UI are evaluated at **12:00 UTC**. The API accepts timezone-qualified timestamps and normalizes them to UTC. Withdrawn source availability is a present-state flag, not a historical permission timeline.

## Evaluate the Gemini agent separately

1. Add your own `GEMINI_API_KEY` to an ignored root `.env`, preserving any existing file. Restart the API.
2. Enable **Investigate with Gemini**, keep a supported partner/delay/date scope, and investigate.
3. Look for **Gemini + verified graph checks**, an AI explanation, and the selected tools in the trace. A configured key alone is not evidence of a successful model run.
4. Open each supporting source. Confirm the explanation respects the scope and does not imply complete code review or production safety.

The server checks the response shape and source IDs. It does not prove that every generated sentence is semantically entailed. A rejected model response or provider failure leaves the independently computed graph result visible, with a sanitized agent error. Graph-only output must not be presented as a successful agent investigation.

## Expected outcomes

The automated evaluator follows this story with isolated graphs:

| Check | Expected result |
| --- | --- |
| Initial global removal | `conflict` |
| Preserved original minimum | `no_known_conflict` in the modeled scope |
| Migration in a copied graph | B meets 0 ms; base still requires 250 ms |
| Scoped migration in the audit graph | A: 250 ms; B: 0 ms |
| Old runbook | One conflict for B |
| Late evidence | October 11 then: 250 ms; hindsight: 0 ms |
| Duplicate migration replay | No second revision increment |
| Previous receipt | Stale after the knowledge update |
| Unapproved chat suggestion | A's accepted minimum stays 250 ms |
| Withdrawn incident source | A: `insufficient_evidence` |

The integration suite also checks time boundaries, missing relationships, receipt reloading, approval idempotency, and stale-action rejection. See [test-to-behavior mapping](VALIDATION.md#automated-coverage).

## Setup and troubleshooting

### A fresh demo without losing previous work

Stop the API, choose a new unused graph in the server environment, and restart:

```sh
FALKOR_GRAPH=chronos_review_01 ./scripts/dev.sh
```

Use a different suffix for another fresh run. An existing environment variable takes precedence over `.env`. Graph names must start with `chronos_` and contain letters, digits, or underscores. The browser cannot select arbitrary graph names. This is configuration separation, not an enterprise tenant-access system.

### Database unavailable

Run `docker compose up -d --wait`. Verify the engine is running and port 6389 is free. The official container entrypoint uses `REDIS_ARGS`; Compose mounts its actual data directory, `/var/lib/falkordb/data`. No cloud account is needed.

### Port already in use

Stop the previous project dev command before starting another. The interface expects API port 8000 and its Vite proxy is configured in [vite.config.ts](../frontend/vite.config.ts). Default service ports are listed in the README.

### Events are disabled

Sample events are intentionally one-shot within a fixture. Use a fresh graph name to reproduce the sequence. Resetting or deleting a user's graph is not part of the test workflow.

### Gemini is unavailable

The key is optional for the graph audit. For agent evaluation, check your account's model access and quota, and set `GEMINI_MODEL` if needed. Do not publish a key or raw provider error in an issue.

### Stale receipt or repair rejection

Knowledge changed after that investigation. Run it again before preparing or approving work. Stale-action rejection is expected behavior.
