# Company Brain fit

The [official Graph Hacks brief](https://www.wemakedevs.org/hackathons/falkordb#tracks) was rechecked **October 17, 2026**. ChronosGraph enters **Track 03: Company Brain**: connected company records, decisions, sources and ownership across departments.

The general investigator covers the recorded company knowledge; the guided Sunday-processing comparison demonstrates one scoped change workflow. The [reference-workspace guide](DELHIVERY_REFERENCE.md) explains the walkthrough and [data scenarios](DATA_SCENARIOS.md) describe broader finance, returns, compliance and operational examples. Private records and the schema are independently modeled, not Delhivery's actual internal data.

## Organizer focus mapped to the current product

| Organizer focus | Current implementation | Evidence | Boundary |
| --- | --- | --- | --- |
| Knowledge from docs, tickets and chats in one graph | Source excerpts connect with policies, claims, incidents, decisions and operational records. | [Database model](DATABASE.md), [retrieval and provenance queries](GRAPH_QUERIES.md), live record/source inspector. | Included records and replayed updates; no live ingestion connectors. |
| Who owns what, and who knows what | Recorded ownership/operating-team edges, department and person records; contextual graph exploration. | `CompanyStore.owners` in [store.py](../backend/chronos/company/store.py), [ownership query](GRAPH_QUERIES.md#live-arithmetic-and-evidence-paths). | Ownership is implemented; expertise ranking and historical ownership are not. |
| Tracing decisions back to their source | Question-specific evidence maps, source IDs, original excerpts, relationship inspection and saved investigation receipts. | [Evidence queries](GRAPH_QUERIES.md#live-arithmetic-and-evidence-paths), [general engine](COMPANY_ENGINE.md). | Valid source IDs do not prove that every generated sentence is correct or that a document is authentic. |
| Keeping knowledge current as things change | Effective/recorded rule intervals, approved amendment replay, outdated-document alerts and stale receipts. | [Accepted-rule and claim queries](GRAPH_QUERIES.md#applicable-accepted-rules), [temporal tests](../backend/tests/test_company_reference.py). | Replays are labeled; continuous synchronization and temporal topology are not implemented. |
| Answers with clear sources | Bounded graph retrieval, source inspection and a provider-labeled explanation; explicit unavailability if all providers fail. | [Cypher guide](GRAPH_QUERIES.md), [live verification](VALIDATION.md#live-render-verification--october-17-2026). | Source coverage and model semantics still require review; no always-correct claim. |

## Mandatory technology and agent behavior

FalkorDB is the primary database for company knowledge, relationships, temporal rules, investigation receipts and review packets. The agent selects bounded server-owned read tools using `GRAPH.RO_QUERY`; it cannot execute arbitrary Cypher or access database credentials. Groq is preferred, Gemini is the next provider and OpenRouter free models are the final fallback. The receipt identifies the provider that completed the run. Graph-only retrieval is labeled separately.

The scheduling comparison uses a real `GRAPH.COPY`, scoped checks and disposable-copy cleanup. The [query guide](GRAPH_QUERIES.md) links this to the implementation. It is a modeled comparison, not a real operating action or general outage predictor. The older NovaPay example is preserved for local exploration; it is not the primary submitted workflow. Secondary-track qualification and multi-agent capabilities are not claimed.

## Public rules and submission boundary

The public page requires central FalkorDB use and new submission/main implementation work during the event; general libraries and infrastructure may be reused. It permits coding assistants with builder responsibility. The event runs October 15–18, 2026; submissions close October 18 at 11:59 PM IST. Deployment is preferred; local projects need complete setup instructions and a working demo video. Teams may have up to four members.

Implementation began October 15, 2026. The repository supplies setup and evaluation instructions. The [live app](https://chronosgraph.onrender.com) and [inspection portal](https://chronosgraph.onrender.com/database) are available. A final video and authenticated submission remain separate work. The public text inspected exposes no numerical judging rubric; none is invented here. Confirm any panel-only requirements and registration before submitting.
