# Company Brain fit

The [official Graph Hacks brief](https://www.wemakedevs.org/hackathons/falkordb#tracks) was rechecked **October 16, 2026**. ChronosGraph targets Company Brain. The project connects company requirements, people, evidence, and follow-up work; the main trigger is a cross-department Sunday-processing decision in an independent Delhivery reference workspace. The original code-change demo is preserved separately.

The main implementation is described in the [reference-workspace guide](DELHIVERY_REFERENCE.md): source-backed commitments, department ownership, approved synthetic updates, two clocks, interactive evidence exploration and isolated scheduling comparisons. All private operational records are synthetic; the schema is independently designed.

## Preserved payments focus-to-evidence map

| Organizer focus | Current implementation | How to inspect it | Boundary |
| --- | --- | --- | --- |
| Docs, tickets, and chats connected | Fictional runbook, incident ticket, and chat excerpts share a graph with decisions and partner requirements. | [Seed](../backend/chronos/seed.py), all-company graph, source inspector. | Seed and predefined replay; no live ingestion. |
| Ownership and knowledge | `OWNS` traversal recommends the recorded system owner. | [Store.owners](../backend/chronos/store.py), repair reviewer. | Expertise discovery, contribution ranking, and availability are not implemented. |
| Decision provenance | Applicable facts link to original excerpts; receipts preserve the context used. | [Engine](../backend/chronos/engine.py), source buttons, evidence graph. | Source-ID checks are not semantic proof or document authenticity. |
| Knowledge stays current | Scoped migration changes the applicable minimum, flags the runbook, and invalidates old receipts. | [Evaluation steps 2–3](EVALUATION.md#three-minute-interface-walkthrough), temporal tests. | Replay is not continuous synchronization; only supported facts are temporal. |
| Clear sources | Receipt source list and optional Gemini citations are bounded to the investigation's evidence. | [Agent validation](../backend/chronos/agent.py), source inspector. | Model explanations require review. |

## Mandatory technology and agent behavior

FalkorDB is the primary store for knowledge, relationships, temporal assertions, receipts, and actions. Both the checks and Gemini read tools query it. Rehearsal uses a real graph copy. The [architecture](ARCHITECTURE.md) shows those responsibilities and the [tests](VALIDATION.md#automated-coverage) demonstrate behavior changes when facts or relationships change.

When enabled, Gemini selects read tools and produces an explanation. Graph-only mode is labeled separately. A configured key or a precomputed receipt is not presented as a fresh agent run. Secondary-track qualification and multi-agent capabilities are not claimed.

## Public rules and submission boundary

The public page requires central FalkorDB use and new submission/main implementation work during the event; general libraries and infrastructure may be reused. It permits coding assistants with builder responsibility. The event runs October 15–18, 2026; submissions close October 18 at 11:59 PM IST. Deployment is preferred; local projects need complete setup instructions and a working demo video. Teams may have up to four members.

Implementation began October 15, 2026. The repository supplies setup and evaluation instructions. A deployment, final video, and authenticated submission are still separate work. The public text inspected exposes no numerical judging rubric; none is invented here. Confirm any panel-only requirements and registration before submitting.
