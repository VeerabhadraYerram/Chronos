# Submission release checklist

ChronosGraph targets the Company Brain track. The [official brief](https://www.wemakedevs.org/hackathons/falkordb) was checked October 17, 2026. Deadline: October 18, 2026, 11:59 PM IST. Live hosting is preferred; projects without deployment need complete setup instructions and a working demo video. Confirm additional submission fields inside the authenticated organizer panel.

## Before submitting

- Verify the live service are healthy and run the [deployment evaluation](DEPLOYMENT.md#dashboard-steps) in a fresh browser.
- Supply the public app URL and the separate `/database` inspection link.
- Check that the public [repository](https://github.com/VeerabhadraYerram/Chronos) is accessible without an account and that CI passes on the submitted commit.
- Record and watch the final demo video. Show a real question, source inspection, graph follow-up, and one change that alters the applicable answer. Avoid edits that conceal provider failures or imply unfinished integrations are live.
- Explain the user: an operations or account manager checking what was decided, why, who owns it and whether it still applies. Clarify that company names are public but private operating records are modeled.
- Complete registration, team details and the submission form in the organizer panel; these cannot be inferred from repository readiness.

The authenticated submission checklist supplied on October 17 additionally requires a public source repository, README setup and graph data model, the Cypher queries or graph algorithms the product depends on, a demo video, live deployment or complete local instructions, and the selected track. The source-backed read templates are in [company/store.py](../backend/chronos/company/store.py) and [company/repository.py](../backend/chronos/company/repository.py); the [database guide](DATABASE.md) describes the graph model and [core query guide](GRAPH_QUERIES.md) collects the actual Cypher patterns.

## Honest scope

FalkorDB is central to retrieval, ownership connections, accepted rules, source provenance, saved investigations and isolated comparisons. The agent uses bounded read tools and provider fallbacks. Evidence graphs are question-specific.

This prototype has no live company ingestion, enterprise permissions, universal semantic correctness guarantee or external operational execution. Changes in the guided walkthrough are labeled replays. Ownership/topology are current-state relationships. The review packet prepares human work; it does not book capacity, change a real contract or send messages.

A code/test milestone alone is not a completed submission. Hosting, disclosure of free-hosting memory resets, a verified video, reviewer access and the actual organizer submission remain release steps.
