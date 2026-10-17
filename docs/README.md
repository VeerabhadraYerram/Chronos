# ChronosGraph documentation

ChronosGraph enters **Track 03: Company Brain**. Start with the [live application](https://chronosgraph.onrender.com) or the [separate database portal](https://chronosgraph.onrender.com/database). Private operating records are modeled; this is not Delhivery's actual internal system or an affiliated product.

## For evaluators

| Question | Start here |
| --- | --- |
| Where is each required submission artifact? | [Submission requirements and reviewer guide](SUBMISSION.md) — the final video and organizer form remain outstanding |
| What does the product do, and how can I try it? | [Repository README](../README.md), [main evaluation steps](EVALUATION.md#main-company-brain-review) |
| Where are the actual Cypher queries? | [Query guide](GRAPH_QUERIES.md) — source-linked retrieval, temporal rules, aggregation, ownership and evidence traversal |
| What is in FalkorDB? | [Database and schema](DATABASE.md), [machine-readable schema](database-schema.json), [inspection portal guide](INSPECTION.md) |
| Is the product broader than the Sunday example? | [Company-wide engine](COMPANY_ENGINE.md), [data scenarios](DATA_SCENARIOS.md) |
| How does the company example work? | [Reference-workspace walkthrough](DELHIVERY_REFERENCE.md) |
| How does it meet the chosen track? | [Competition-fit map](COMPETITION_FIT.md) |
| What was actually tested? | [Dated validation evidence](VALIDATION.md), [CI workflow](../.github/workflows/ci.yml) |
| Where does it run, and what are the limits? | [Free Render deployment](DEPLOYMENT.md), [security boundaries](../SECURITY.md) |

## For developers

[Current architecture](ARCHITECTURE.md#current-company-workspace) · [Current API](API.md#current-company-and-public-apis) · [Contribution guide](../CONTRIBUTING.md) · [Roadmap](ROADMAP.md)

The main investigation uses real FalkorDB records and bounded read tools. Provider order is Groq → Gemini → OpenRouter free models. Citation and numeric checks are limited validations, not a guarantee of correct answers. Unknown evidence and unavailable providers are explicit states.

The local Docker volume persists records. The Free Render instance hosts its own frontend, API and FalkorDB; local services can be stopped independently. Hosted visitor workspaces reset on server restart and expire after one hour of inactivity. Readiness does not establish live provider quota or production readiness.

## Preserved material

The payments-specific portions of [architecture](ARCHITECTURE.md#preserved-payments-architecture), [API](API.md#preserved-local-payments-api), [graph model](DATA_MODEL.md) and [evaluation](EVALUATION.md#three-minute-interface-walkthrough) document the earlier local NovaPay workflow. It is excluded from the public evaluation entrypoint.

The [original master plan](planning/MASTER_PLAN.md) is design history. It contains proposals, not a current capability checklist. Use the current engine, roadmap and dated validation for implemented scope.
