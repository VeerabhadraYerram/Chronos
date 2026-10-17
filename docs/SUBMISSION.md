# Submission requirements and reviewer guide

**Project:** ChronosGraph · **Track 03: Company Brain**

[Live application](https://chronosgraph.onrender.com) · [Separate database inspection](https://chronosgraph.onrender.com/database) · [Public repository](https://github.com/VeerabhadraYerram/Chronos)

This checklist maps each requirement in the organizer's submission panel, supplied on October 17, 2026, to a concrete artifact. The [official event page](https://www.wemakedevs.org/hackathons/falkordb) was rechecked the same day. Deadline: **October 18, 2026, 11:59 PM IST**. Panel-only fields and successful submission must be checked in the signed-in organizer account.

## Required artifacts

| Organizer requirement | Status | Evidence for reviewers |
| --- | --- | --- |
| Public source-code repository | Present | [VeerabhadraYerram/Chronos](https://github.com/VeerabhadraYerram/Chronos); source, MIT license, tests and CI workflow are included. |
| README with setup instructions and graph data model | Present | [README setup](../README.md#run-locally), [core model diagram](../README.md#how-falkordb-shapes-the-answer), [complete database guide](DATABASE.md), [machine-readable schema](database-schema.json). |
| Cypher queries or graph algorithms the product depends on | Present | [Dedicated Cypher guide](GRAPH_QUERIES.md): actual templates for retrieval, rules, claims, counts, ownership, evidence paths, integrity checks and graph-copy comparison, with implementation links. |
| Demo video showing the working project | **Missing — required before submission** | No final video URL is available yet. Do not mark this complete until the recorded video is uploaded and its playback/access checked. |
| Live deployment, or complete local setup if deployment is unavailable | Present | [Live app](https://chronosgraph.onrender.com), [database portal](https://chronosgraph.onrender.com/database), [local setup](../README.md#run-locally), [hosting boundaries](DEPLOYMENT.md), [dated live verification](VALIDATION.md#live-render-verification--october-17-2026). |
| Track being entered | Declared in repository | **Track 03: Company Brain**, also stated in the README. Select the same track in the actual submission form. |

## Where to begin the technical review

1. Open the live app and ask a company question. The receipt identifies the provider that actually completed the investigation.
2. Click an evidence record or connection, inspect the original excerpt, then ask a contextual follow-up. The map shows retrieved records for that question, not the entire company graph.
3. Use the guided walkthrough to replay an approved amendment, compare effective and known dates, and inspect the changed applicable answer. Replayed events are labeled.
4. Open the separate database portal and choose **Create workspace**. Browse records, complete fields, actual relationships, schema/indexes and structural integrity checks. To inspect an app investigation itself, use that app workspace's ID; a new portal workspace has independent history.
5. Read [GRAPH_QUERIES.md](GRAPH_QUERIES.md) alongside the linked source. Run `./scripts/check.sh` for the real FalkorDB integration suite, business-scenario evaluation, frontend build and documentation checks. Tests use disposable graphs and preserve the user's demo graph.

The intended user is an operations or account manager checking what was decided, why, who owns it and whether it still applies. The [competition-fit map](COMPETITION_FIT.md) connects the five Company Brain focus points to the implementation.

## Remaining release actions

- Record and watch the final demo video. Show a real question, source inspection, graph follow-up and one change that alters the applicable answer. Avoid edits that conceal failures or imply unfinished integrations are live.
- Add the uploaded video link to this file, the README and the organizer form. Verify it without the owner's signed-in session.
- Verify the live app and public repository shortly before submitting; confirm CI on the submitted code commit. Free hosting may take about a minute to wake, and provider quotas can interrupt AI answers.
- Complete registration, team details, track selection and the organizer's submission form. **A repository checklist does not prove the form was submitted.**

## Honest scope

FalkorDB is central to retrieval, ownership connections, accepted rules, source provenance, saved investigations and isolated comparisons. The agent uses bounded read tools and provider fallbacks. Evidence graphs are question-specific.

Private operating records are modeled; the project is not Delhivery's actual database or an affiliated product. There is no live company ingestion, enterprise permission system, universal semantic correctness guarantee or external operational execution. Ownership/topology are current-state relationships. Review packets prepare human work; they do not change a real contract or send messages.

The free deployment resets hosted visitor investigations on server restart and expires inactive workspaces after one hour. Local Docker storage is persistent. These limitations are disclosed rather than presented as production durability.
