# Local API reference

[Architecture](ARCHITECTURE.md) · [Request models](../backend/chronos/models.py) · [Route implementation](../backend/chronos/app.py)

Base URL: `http://127.0.0.1:8000`. With the API running, `/docs` serves interactive OpenAPI documentation and `/openapi.json` exposes its schema. The app is intended for a trusted local machine, not an unauthenticated public deployment.

## Routes

| Method | Path | Behavior |
| --- | --- | --- |
| `GET` | `/api/health` | Database connectivity, revision, Gemini configuration flag, and supported scope; never returns a key. |
| `GET` | `/api/graph` | Current company nodes/edges and revision; receipts and actions are omitted from this display snapshot. |
| `POST` | `/api/investigate` | Run graph checks, optionally invoke Gemini, and persist a receipt. |
| `GET` | `/api/receipts` | Up to 30 saved receipts with current staleness. |
| `POST` | `/api/events/replay` | Apply a predefined migration, proposal, or withdrawal once per fixture. |
| `POST` | `/api/rehearse` | Evaluate a partner-scoped alternative in a temporary real graph copy. |
| `POST` | `/api/receipts/{id}/repair` | Prepare or return an existing in-app draft for a current receipt. |
| `POST` | `/api/actions/{id}/approve` | Idempotently record in-app approval after checking receipt freshness. |

## Investigation request

```sh
curl --fail-with-body http://127.0.0.1:8000/api/investigate \
  -H 'Content-Type: application/json' \
  -d '{
    "question": "Can we remove the payment retry delay?",
    "partner": "all",
    "proposed_ms": 0,
    "effective_at": "2026-10-15T12:00:00Z",
    "known_at": "2026-10-15T12:00:00Z",
    "use_gemini": false
  }'
```

This writes a receipt into the configured demo graph. Use the [isolated evaluator](EVALUATION.md#fastest-audit) when you want an audit that leaves no records in your demo workspace.

| Field | Validation |
| --- | --- |
| `question` | 5–2,000 characters; supplies narrative context, not arbitrary target resolution. |
| `partner` | `all`, `a`, or `b`. |
| `proposed_ms` | Integer from 0 through 10,000. |
| `effective_at`, `known_at` | Timezone-qualified ISO timestamps, normalized to UTC. |
| `use_gemini` | Boolean; defaults to false. |

Assessment values: `conflict`, `insufficient_evidence`, and `no_known_conflict`. Other receipt fields include per-partner `checks`, documentary `conflicts`, source excerpts, owners, gaps, graph snapshot, dataset revision, tool trace, mode, and timings. Provider failure is surfaced as `agent_error` with graph checks retained; an HTTP 200 does not by itself prove an agent completed.

## Replay and rehearsal

Replay body: `{"event":"migration"}`, `{"event":"proposal"}`, or `{"event":"withdraw-evidence"}`. Already applied events return `applied: false` without another revision increment. These are synthetic predefined events, not live webhooks.

Rehearsal accepts the investigation fields. It checks both partners, returns `before` and `alternative` checks, reports the base revision comparison, includes assumptions, and removes its temporary copy. It does not update the base requirement or publish a change.

## Error semantics

| Status | Meaning |
| --- | --- |
| `404` | Receipt or action not found. |
| `409` | Stale evidence prevents preparing or approving work. |
| `422` | Request validation failed. |
| `503` | The database is unavailable through the application connection path. |

There is no authentication, pagination beyond the receipt limit, durable job queue, or general source-upload API. Configuration selects the graph server-side. See [security and trust boundaries](../SECURITY.md) before extending deployment.
