# ChronosGraph

**Company decision memory. Understand why a requirement exists, what still depends on it, and what must change before you can move on.**

Built for the Company Brain track of [WeMakeDevs x FalkorDB Graph Hacks](https://www.wemakedevs.org/hackathons/falkordb). Implementation started October 15, 2026. NovaPay and every included source are fictional.

## What works

- Real FalkorDB storage for company knowledge, relationships, accepted fact versions, source excerpts, receipts, and in-app actions. There is no in-memory graph substitute.
- An optional Gemini investigator selects read tools, inspects the graph, and returns an explanation. Deterministic constraint checks remain authoritative; the model cannot approve a conflicting change.
- Explicit partner scope and separate effective/knowledge timestamps, including late-arriving evidence.
- A clickable evidence graph and source inspector, history view, documentation conflicts, and persistent receipts.
- Sample event replay for an approved partner migration, an unapproved suggestion, and withdrawn evidence. Replay is idempotent and invalidates old receipts.
- FalkorDB graph-copy rehearsal that evaluates a partner-scoped alternative and removes the temporary scenario afterward.
- Repair drafts, downloadable Markdown, and idempotent in-app approval. No external messages, PRs, tickets, or production changes are published.

This first prototype checks **the payment worker's minimum retry delay**. Free text supplies investigation context; the explicit partner/delay/date controls define the assessed change. It does not parse arbitrary diffs, predict outages, or guarantee production safety. “No known conflict” means only that the proposed delay meets the supported, modeled requirement.

## Quick start

Requirements: Python 3.11+ (tested with 3.13), Node.js 20.19+, npm, and a running Docker engine. Ports: 6389 for FalkorDB, 8000 for the API, 5173 for the interface. All bind to loopback.

```sh
docker compose up -d
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
npm --prefix frontend ci
cp .env.example .env
chmod 600 .env
```

Edit `.env` locally and add `GEMINI_API_KEY`. The default model, `gemini-3.1-flash-lite`, was verified against the development key's available models and a real tool-loop invocation. Model access, quota, and availability depend on your account. You can change `GEMINI_MODEL`. Never commit the environment file or put an API key in browser code.

Start both development servers:

```sh
./scripts/dev.sh
```

Open [http://127.0.0.1:5173](http://127.0.0.1:5173). The company seed is loaded on first use. The checkbox **Investigate with Gemini** enables model calls; unchecked, the app honestly labels the result **Verified graph checks**. If Gemini fails, its error is surfaced and independently computed graph results remain available. Merely configuring a key does not trigger a generation request.

Manual startup in two terminals:

```sh
PYTHONPATH=backend .venv/bin/uvicorn chronos.app:app --host 127.0.0.1 --port 8000
```

```sh
npm --prefix frontend run dev
```

Stop dev servers with Ctrl+C. The database volume persists after container shutdown. Never run `docker compose down -v` unless you intend to delete local demo knowledge and receipts.

## Demo in three minutes

1. Start with both partners, 0 ms, effective/known October 15. Run the investigation: both modeled requirements are 250 ms.
2. Replay **Partner B migration**, then rerun. Partner A remains in conflict; Partner B's accepted minimum becomes 0 ms. The global runbook now conflicts with the Partner B decision.
3. Open **Time machine**. Choose October 11 as known then and investigate Partner B: 250 ms. Choose October 11 with hindsight: 0 ms. The migration applied October 10 but became known October 12.
4. Open **Rehearse change**, restore the current dates, and run rehearsal. It checks preserving Partner A's applicable minimum while applying the proposal to B, inside a copied graph. This is not a change to the accepted policy or base graph.
5. Prepare a repair plan, inspect sources, download it, and approve it in the workspace. Refresh and reopen a saved receipt to show persistence.
6. Optional challenge: replay the unapproved suggestion; it cannot replace policy. Withdraw incident evidence; Partner A becomes unassessable until authoritative evidence is restored.

Events are deliberately one-shot per fixture. For a completely clean recording, choose a fresh unused `FALKOR_GRAPH=chronos_demo_<name>` in `.env` and restart the API. This preserves previous graphs and receipts; it does not erase or reset another workspace. New fixture creation is limited to the server's configured `chronos_` namespace, not a user-supplied browser graph name.

## Architecture

```text
React / TypeScript / Vite interface
               |
          FastAPI API
          /         \
Verified checks    Gemini tool loop
          \         /
       Read-only Cypher tools
               |
          Real FalkorDB
company graph / temporal fact versions / source provenance
receipts / in-app actions / temporary scenario copies
```

The audited plan originally suggested Next.js. This implementation uses Vite because the application already has a dedicated FastAPI backend; an additional server-rendering layer would not improve this milestone. React Flow provides the inspectable graph. The PDF's multi-agent design and MCP packaging are intentionally deferred until the primary Company Brain workflow is reliable.

Source layout:

```text
backend/chronos/store.py    Parameterized graph queries, fixture replay, persistence
backend/chronos/engine.py   Scoped constraint checks and repair drafting
backend/chronos/agent.py    Bounded Gemini tool loop and citation validation
backend/chronos/app.py      Local HTTP API and action approval
backend/chronos/seed.py     Fictional company and late-arriving migration
backend/tests/             Real FalkorDB integration checks
frontend/src/              Responsive investigation workspace
docs/                      Product plan, competition fit, validation notes
```

Fact versions have half-open `valid_from`/`valid_to` and `recorded_from`/`recorded_to` intervals. Empty ends are open-ended. UTC timestamp strings use one normalized format so parameterized comparisons are consistent. Historical support currently covers retry constraint facts; ownership and topology are static fixture knowledge, not a fully temporal organization model.

The migration preserves the original “as known then” assertion and appends corrected historical/current versions. Receipts identify the application dataset revision and are conservatively marked stale after accepted fixture changes. This application revision is not FalkorDB's schema version.

Read tools use `GRAPH.RO_QUERY` with timeouts. Model calls receive typed tool results and synthetic source data, never database credentials. Graph writes happen only through server handlers. A process-local lock serializes fixture updates; the prototype is a single-process, trusted local application. Crash-atomic ingestion, authentication, source-level ACLs, multiple API workers, and untrusted multi-user hosting are not implemented.

## Verification

```sh
PYTHONPATH=backend .venv/bin/python -m pytest backend/tests -q
npm --prefix frontend run build
```

Tests require the real running FalkorDB. Each test uses a disposable uniquely named graph and deletes only that graph afterward. They cover original constraints, partner migration, both time axes, boundary dates, document contradictions, unapproved proposals, withdrawn evidence, idempotent replay, persistence, stale receipts, graph copying, missing links, input validation, and approval behavior.

See [validation notes](docs/VALIDATION.md) for what was actually run, and [competition fit](docs/COMPETITION_FIT.md) for rules and remaining submission work. No benchmark numbers or prize guarantees are claimed.

## Before submission

The core prototype runs locally. Still needed: a deployment decision, final polished demo recording, authenticated submission-panel requirements, broader ingestion, and further evaluation beyond the fictional fixture. The public event page prefers deployment; local-only entries need complete setup instructions and a working demo video. Check the organizer's authenticated panel for any additional requirements before submitting.
