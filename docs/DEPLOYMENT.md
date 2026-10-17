# Free Render deployment

The [Render Blueprint](../render.yaml) creates **one Free web service** containing the built React frontend, Python API and real FalkorDB. No Vercel deployment, paid database or disk is required. The database listens only on `127.0.0.1` inside the container. This is an evaluation deployment, not durable production hosting.

The live app is [chronosgraph.onrender.com](https://chronosgraph.onrender.com); the separate portal is [database inspection](https://chronosgraph.onrender.com/database). They were checked on October 17, 2026; see [validation](VALIDATION.md) for scope. The public repository is [VeerabhadraYerram/Chronos](https://github.com/VeerabhadraYerram/Chronos).

## Free-hosting trade-offs

[Render Free services](https://render.com/docs/free) sleep after 15 idle minutes, take about a minute to restart and lose filesystem changes on sleep/restart/redeploy. Reference company records reload from the seed. Visitor investigations, replays and review packets are temporary and are lost on server restart. Isolated workspaces also expire after one hour of inactivity, allowing a small free instance to reclaim capacity. The interface discloses this. A stale browser workspace is replaced with an explicit notice; explicit expired share links show an error and allow a new workspace.

This still runs actual FalkorDB queries and graph copies. Nothing is replaced with a frontend answer cache or a relationship simulation. It cannot demonstrate restart-durable memory on the free host. The local Docker volume continues to support persistent local storage.

Use a free workspace and **Free** compute. Do not add a paid disk, private service or paid workspace upgrade. Review Render's bandwidth/build allowances and spend settings: free compute alone does not guarantee zero overage charges if a payment method is attached. No paid resource is authorized for this project.

## Dashboard steps

1. Sign in to [Render](https://dashboard.render.com/). Choose **New → Blueprint**, connect **VeerabhadraYerram/Chronos**, branch `main`, and `render.yaml`.
2. Confirm it proposes exactly **one web service**, named `chronosgraph`, on the **Free** plan. Stop if any paid resources appear.
3. Enter provider keys only in Render's secret environment fields: `GROQ_API_KEY`, `GEMINI_API_KEY`, `OPENROUTER_API_KEY`. At least one working provider is required for readiness. Groq is first, Gemini second, OpenRouter free models last. Unconfigured fallbacks may be left empty where allowed; otherwise add them later in the service's Environment settings. Never paste keys into issues or commit them. Rotate keys previously shared in chat before public hosting. Use provider free quotas and account spend controls.
4. Choose **Deploy Blueprint**. Wait for a successful build and healthy service. The Render-provided HTTPS URL is the product link. The image contains a reference-only FalkorDB snapshot generated from the source fixture during the build. Startup loads that real graph without rebuilding every record; readiness verifies it. The database is internal; no Redis/FalkorDB port or credentials need to be shared.
5. Open the public URL in a fresh browser. Ask a company-count question, a source-backed account question, and a follow-up from a clicked graph item. Check the actual live provider badge and cited text. Test before/after separately in the guided walkthrough.
6. Submit `/database` on the same origin as the separate inspection link. Reviewers can choose **Create workspace**. A copied workspace-specific inspection link is temporary and can expire after sleep/restart; do not present it as permanent. Capability links grant access to modeled records and investigation history, not enterprise authentication.

Automatic deploys are off so a push cannot silently replace the judged version. Manually deploy a tested commit from Render when needed.

## Runtime boundaries

The [public entrypoint](../backend/chronos/public.py) serves the frontend and company/inspection APIs on one origin. It excludes the old global NovaPay API and API documentation. The local development entrypoint remains unchanged. The public build also hides the original payments prototype navigation.

One process/replica coordinates graph changes. API admission limits: 90 requests/minute/client, 12 workspace requests/minute/client, 8 AI calls/minute/client, 120 AI calls/hour globally, 64 KiB request bodies and two simultaneous AI investigations. Counters are process-local and reset on restart; they are not a billing guarantee or distributed anti-abuse service. Render must be the only public ingress because forwarded client addresses are trusted from its proxy. Configure provider spend/quota controls separately.

The free Blueprint allows six active isolated workspaces. Reference data is unchanged when a visitor workspace expires. Expiry is opt-in via `CHRONOS_EPHEMERAL=1`; it is disabled for the user's persistent local workspace. Restarting free hosting removes all container data, and the clean reference is loaded again. Catalog discovery reads payloads and native key names in 250-record pages, preserving complete field coverage while avoiding duplicate native values. Hosted database reads/writes are bounded to 10 seconds and socket waits to 30 seconds; local defaults remain 2.5/5/5 seconds. These are not inference timeouts. The service cannot guarantee availability, provider quota, source truth or semantic correctness.

`/healthz` is process liveness. `/readyz` checks reachable seeded FalkorDB and at least one configured provider key. It does not invoke a model or prove current quota. A successful live investigation is a separate release check.

## Local container verification

```sh
docker build -t chronosgraph-evaluation:local .
```

The Docker build context allowlist excludes `.env`, Git metadata and runtime data. Keys are injected at runtime. Python and FalkorDB run as a non-root user. The image build generates a reference-only RDB using the pinned database and source fixture, without provider keys, receipts or visitor capabilities. Each free container start loads a fresh runtime copy of that reference. A supervisor starts both, stops both on termination, and exits if either crashes. FalkorDB is bound to loopback and has no public listener. The Redis graph module is copied from the same pinned official FalkorDB image used by local development.
