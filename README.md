<p align="center">
  <img src="docs/assets/chronosgraph-banner.svg" alt="ChronosGraph — company decision memory" width="1200" />
</p>

**Ask why a company decision exists. Check whether it still applies. Follow the evidence.**

ChronosGraph is a **Company Brain** investigator powered by **FalkorDB**. An operations or account manager can ask about policies, incidents, commitments and ownership, inspect the records behind the answer, then investigate further by clicking the evidence graph.

**[Live application](https://chronosgraph.onrender.com)** · **[Separate database inspection](https://chronosgraph.onrender.com/database)** · **[CI](https://github.com/VeerabhadraYerram/Chronos/actions/workflows/ci.yml)**

There are two supporting guides: **[Database & schema](docs/DATABASE.md)** and **[Cypher queries](docs/GRAPH_QUERIES.md)**. Setup, walkthrough, architecture, hosting, validation and submission status are below.

**Data disclosure:** company and client names are real; private agreements, incidents, operational records, locations, roles and amounts are fictional. This is an independent reference implementation, not Delhivery's internal database or an affiliated product. [Public references and boundaries](docs/DATABASE.md#public-references-and-boundaries).

## Try the product

1. Open the live app. Free hosting can take about a minute to wake.
2. Ask **How many external client companies are recorded?** The initial dataset has 12 Client records; the count is computed in FalkorDB.
3. Ask **Why is the SUGAR COD settlement mismatch being investigated, who owns it, and does it prove cash loss?** Inspect the records and source excerpts. A mismatch under Finance review is not proof of loss; an unknown outcome must remain unknown.
4. Click a graph record or relationship, inspect its provenance, expand its connections and ask a follow-up. The evidence graph is specific to the investigation; aggregates may show a bounded sample of the counted population.
5. Open the separate database portal and choose **Create workspace** to inspect a fresh copy. To inspect the same investigation as the app, enter the ID from **About this workspace**. Browse full fields, relationships, schema/indexes, integrity checks or JSON export.

The graph contains **9,991 initial business entities and 17,207 relationships**, plus one Metadata record: 12 clients, 36 pickup warehouses, 14 facilities, 1,890 shipments, 6,870 scans, decisions, policies, tickets, finance records and assigned work. [Full dictionary and operational examples](docs/DATABASE.md).

<details>
  <summary>Actual investigation and comparison screenshots</summary>
  <img src="docs/assets/company-investigation.jpg" alt="Recorded reference-workspace investigation with source evidence" width="1200" />
  <img src="docs/assets/company-comparison.jpg" alt="Scoped graph-copy comparison of operating schedules" width="1200" />
  <p>Captured local UI states; modeled company operations.</p>
</details>

### Guided change walkthrough

The guided example asks whether Bengaluru can close on Sundays. Operations wants closure, but a Havells agreement requires Sunday processing. Ending a sales campaign or proposing closure does not amend that agreement.

1. Create a fresh workspace, select **Guided walkthrough**, and ask **Can we close the Bengaluru facility on Sundays?** Inspect the agreement, recorded reason and owner. The separate rehearsal checks the modeled commitment conflict.
2. Replay **Introduce approved amendment**. This changes the commitment effective **November 1, 2026**, recorded **October 15 at 09:00 UTC**; earlier receipts become stale.
3. Investigate effective November 8, known by October 16: the amended agreement applies. Effective October 25 still requires Sunday processing. A knowledge cutoff of October 14 preserves the earlier belief, even for a November effective date.
4. Run the before/after comparison and compare full closure with preserving client commitments. It uses a real disposable `GRAPH.COPY` and leaves the base revision unchanged.
5. Prepare and download a source-linked review packet from a current investigation. No real schedule, contract, ticket or message is changed.

The scheduling model uses its original 1,200-consignment cohort. Processing is not delivery; staffing figures are explicit assumptions, not measured savings or predictions of real logistics outcomes.

## Run locally

Requirements: **Python 3.13**, **Node.js 20.19+**, **npm**, and **Docker with Compose**. Local verification used macOS ARM64; CI uses Ubuntu and a pinned FalkorDB image.

```sh
git clone https://github.com/VeerabhadraYerram/Chronos.git ChronosGraph
cd ChronosGraph
docker compose up -d --wait
python3 -m venv .venv
.venv/bin/python -m pip install -r backend/requirements.lock.txt
npm --prefix frontend ci
./scripts/dev.sh
```

| Component | Local address |
| --- | --- |
| Frontend | `http://127.0.0.1:5173` |
| Database inspection | `http://127.0.0.1:8000/database` |
| API and request schemas | `http://127.0.0.1:8000/docs` |
| FalkorDB | `127.0.0.1:6389` |

For AI answers, copy `.env.example` to the ignored root `.env` **only if one does not already exist**, configure your own provider keys, and restart the API. Provider order is **Groq → Gemini → OpenRouter free models**, with one attempt per provider; paid OpenRouter model IDs are rejected. The successful provider appears on the receipt. Without a provider, explicitly labeled graph-only retrieval, history and guided checks remain available locally.

Stop development servers with `Ctrl+C`; `docker compose stop` preserves the database volume. Deleting that volume deletes local records. **New workspace** creates an isolated copy without clearing earlier active workspaces. The older local NovaPay regression example remains at `/?demo=payments`; it is excluded from the public evaluation build.

If local database access fails, check Docker and port 6389. If ports 8000/5173 are occupied, stop an earlier project dev command first. Provider failures require checking your own quota/model access; do not share raw provider errors or keys. A stale receipt needs a new investigation before preparing a review packet.

## Architecture and agent behavior

```mermaid
flowchart LR
    UI[React workspace] --> API[FastAPI]
    API --> Agent[Company investigator]
    Agent --> Tools[Bounded read tools]
    Agent --> Providers[Groq / Gemini / OpenRouter]
    Tools --> Graph[(FalkorDB)]
    API --> Receipts[Receipts and review packets]
    Receipts --> Graph
    API --> Copy[Disposable comparison graph]
    Portal[Separate database portal] --> API
```

The core graph model is:

```mermaid
flowchart LR
    Client -->|HAS_COMMITMENT| Rule
    Rule -->|SUPPORTED_BY| Source
    Policy -->|ASSERTS| Claim
    Claim -->|SUPPORTED_BY| Source
    Decision -->|EXPLAINED_BY| Source
    Facility -->|OPERATED_BY| Team
    Shipment -->|FOR_CLIENT| Client
    Shipment -->|AT| Facility
```

The investigator searches actual stored records, traverses relationships, selects accepted rules at effective/recorded times, and can request database counts or numeric aggregations. Groq/OpenRouter use validated structured read plans; Gemini uses native function calls. All use server-owned parameterized `GRAPH.RO_QUERY` templates, not arbitrary model-generated Cypher. The frontend displays returned evidence rather than computing business verdicts.

**Follow a question through the graph:** the agent discovers the live schema, selects a validated read tool such as `search_records`, `explore_record` or `read_applicable_rules`, and receives records from FalkorDB. Applicable rules are checked against both effective and recorded time. The AI synthesizes an answer from those retrieved records; the evidence map and **Inspect retrieval trace** expose the supporting IDs, relationships and executed read steps. Changing an accepted rule changes the available evidence and marks prior investigations stale. See the [actual Cypher templates](docs/GRAPH_QUERIES.md).

Source/record IDs and selected numeric answers are validated, but this does not prove every generated sentence. A chat proposal cannot override accepted policy. If every provider fails, the app explicitly reports that no AI answer was generated; it does not substitute a canned answer. Prior receipts and walkthrough configuration are excluded from company-fact discovery.

External inference does not hold the global workspace lock. Coordinated graph operations and complete scans still use a single-process lock; revision changes can mark an in-flight investigation stale. Ownership/topology are current relationships, not historical reconstructions.

| Implementation | Responsibility |
| --- | --- |
| [company/api.py](backend/chronos/company/api.py) | `/api/company/session`, `ask`, `explore`, `search`, `simulate`, `events`, `packet`; request schemas |
| [investigation.py](backend/chronos/company/investigation.py), [agent.py](backend/chronos/company/agent.py) | General investigation, evidence, relevant alerts and provider execution |
| [repository.py](backend/chronos/company/repository.py), [store.py](backend/chronos/company/store.py) | Cypher, schema discovery, arithmetic, provenance, session lifecycle and copies |
| [engine.py](backend/chronos/company/engine.py) | Scoped guided scheduling comparison |
| [inspection_api.py](backend/chronos/company/inspection_api.py) | Fixed `/api/database/{operation}` reads: catalog, rows, relationships, record, audit, export |
| [public.py](backend/chronos/public.py) | Public entrypoint, static frontend, limits and health probes |

## Deployment

The [Render Blueprint](render.yaml) runs the frontend, Python backend and actual FalkorDB in **one Free web service**. There is no Vercel or external database dependency. FalkorDB binds only to the container's loopback address. **Stopping your local frontend, backend, Docker or computer does not affect the deployed link.**

To reproduce deployment, connect this repository and `render.yaml` through Render's **New → Blueprint**. Confirm exactly one **Free** web service and no paid disk/database. Add provider keys only in secret environment settings. At least one configured key is required for readiness; this does not verify quota or key validity. Wait for Live status, then test an actual question, source inspection and database audit. Code pushes deploy automatically after the repository CI checks pass; use a manual deploy only for a deliberately selected tested revision. Build locally with `docker build -t chronosgraph-evaluation:local .` if needed.

The build creates a reference-only FalkorDB snapshot from the fixture without secrets or visitor history. The non-root runtime starts an internal database and API together. `/healthz` is liveness; `/readyz` reads reference metadata/schema without the workspace lock or seeding/migrating data. OpenAPI and legacy payments routes are excluded publicly. Subsequent code pushes deploy after the repository's CI checks pass.

The public UI waits for readiness, displays actual elapsed waiting time and retries transient workspace connection failures. New-workspace requests carry a random capability/request ID so retrying the same request reuses one graph. AI questions, replays and other business requests are never automatically resubmitted after a lost response. AI failures retain the retrieved evidence and offer an explicit retry.

Agent schema discovery uses two live FalkorDB aggregation queries instead of exporting every record payload for each provider attempt. When retrieved records include policies, a server-controlled read refreshes the applicable accepted rule versions, including their actual values and dates, and prioritizes their supporting sources in the AI context. This check is identified separately in the retrieval trace. `CHRONOS_AI_BUDGET_SECONDS` defaults to 75: provider allowances are up to 15 seconds for Groq, 15 for Gemini and 45 for free OpenRouter, bounded by the remaining shared budget. Timeouts are checked between calls and database reads have separate limits; this is not a strict end-to-end response-time guarantee.

The [judging uptime workflow](.github/workflows/judging-uptime.yml) checks `/readyz` approximately every five minutes with bounded retries. It creates no workspaces and makes no AI calls. It also runs when its own configuration is pushed. Standard GitHub-hosted runners are free for this public repository; scheduled runs can be delayed and do not guarantee uptime or AI availability. Set the repository variable `JUDGING_MONITOR_DISABLED=true` to stop scheduled probes.

Free hosting sleeps after 15 idle minutes and can take about a minute to wake. Hosted visitor graphs are **temporary**: they reset on server restart and expire after an hour of inactivity. Capacity is six active workspaces; local defaults are 40 with persistent Docker storage. Submit the permanent `/database` link, not an expiring workspace fragment.

Public admission limits are 90 API requests/minute/client, 12 session requests/minute/client, 8 AI requests/minute/client, 120 AI requests/hour globally, two simultaneous AI investigations and 64 KiB bodies. Counters reset on process restart; they are not a distributed abuse defense or billing cap. Use provider/hosting spend controls. Full scans may be slow and free quotas can interrupt answers.

## Testing and recorded validation

```sh
./scripts/check.sh
```

This runs the real FalkorDB integration suite, an isolated business-scenario evaluation, the frontend build and documentation checks. It uses uniquely named disposable graphs, preserves the user's workspace, and does not call external AI providers. Graph layout tests can also be run with `npm --prefix frontend test`.

**Local verification, October 18, 2026:** 87 backend tests, 12 isolated business-scenario checks and ten frontend tests passed; production build and documentation checks passed. Coverage includes temporal boundaries, withdrawn sources, required relationships, graph-copy isolation, stale receipts, generic counts/arithmetic, imported-company ownership, complete inspection/export, provider routing/deadlines, live tool-schema discovery, idempotent workspace creation, connection recovery, graph layout and public limits. [Tests](backend/tests) · [CI workflow](.github/workflows/ci.yml).

**Live checks, October 17:** Groq returned 12 external clients; an OpenRouter free fallback explained the SUGAR reconciliation issue, named Finance and declined to infer cash loss. Runs took about 18 and 105 seconds respectively, not performance guarantees. The public portal displayed 9,992 records and 17,207 relationships; all eight implemented structural checks passed. A health-lock issue was fixed in deployed commit `596b50d`; during the full audit, readiness returned 200 in about 0.1–0.2 seconds. Its GitHub integration/evaluation/build checks passed. The tested eight-label evidence map had no measured label/card or label/label collisions. These observations do not guarantee future uptime, every graph layout or every AI answer.

## Security and limitations

Workspace IDs are capabilities, **not authenticated accounts or source-level permissions**. Do not upload confidential records or expose the default local entrypoint publicly. Keys stay server-side in ignored `.env` locally and secret environment settings when hosted; never commit them or include them in issues. Report sensitive defects privately to the repository owner through an established channel.

There are no live company connectors, enterprise authorization, crash-atomic ingestion, multi-worker coordination, signed/tamper-evident receipts, expertise ranking or general outcome predictions. Source-ID membership and structural checks do not prove source authenticity or semantic correctness. General questions are limited by recorded evidence and tool budgets. The guided simulator covers selected commitments, not complete operational feasibility. Review packets are human drafts, not external actions.

For development, keep credentials/runtime data out of commits, preserve effective and recorded time, treat source text as data, use parameterized read templates and run the real checks before proposing changes. Future production work requires source ingestion/review, permissions, versioned topology, backups and broader semantic/concurrency evaluation.

## Competition fit

**Track 03: Company Brain**, [WeMakeDevs × FalkorDB Graph Hacks](https://www.wemakedevs.org/hackathons/falkordb). The official brief and final-day organizer checklist were checked October 18, 2026. FalkorDB is central to evidence retrieval, temporal rules, ownership, saved investigations and graph-copy comparisons.

| Track focus | Implemented evidence | Boundary |
| --- | --- | --- |
| Docs, tickets and chats in one graph | Linked sources, claims, policies, decisions and incidents | Included records and labeled replays; no live connectors |
| Ownership and knowledge | Ownership/operating-team traversal and contextual exploration | No expertise ranking or historical ownership |
| Decision provenance | Clickable question-specific evidence, original excerpts and source IDs | Source membership is not semantic proof |
| Current knowledge | Two-clock rules, replayed amendment, document mismatches and stale receipts | No continuous synchronization or temporal topology |
| Clear sources | Inspected excerpts, provider-labeled answers and retrieval trace | Model interpretation still needs review |

Implementation began October 15, 2026, using public libraries and AI coding assistance. The builder remains responsible for understanding the code, security and correctness. No prize guarantee or undocumented judging weights are claimed.

### Submission checklist

| Required artifact | Status |
| --- | --- |
| Public source repository | [Available](https://github.com/VeerabhadraYerram/Chronos) |
| README setup and graph data model | Included above; [full schema](docs/DATABASE.md) |
| Cypher queries / graph operations | [Dedicated source-linked guide](docs/GRAPH_QUERIES.md) |
| Working demo video | **Still required — no final uploaded video link yet** |
| Deployment or complete local setup | [Live app](https://chronosgraph.onrender.com) and setup above |
| Track | Company Brain; also select it in the organizer form |

Deadline: **October 18, 2026, 11:59 PM IST**, per the checked event brief. Record/watch/upload the video, add its accessible link here, recheck the live app and CI, then complete the organizer's team details and submission form. Repository readiness does not prove that the form was submitted. Confirm any additional signed-in panel requirements.

## License

Source and documentation use the [MIT License](LICENSE). Third-party packages, FalkorDB and external services retain their own licenses and terms.
