# Contributing

Start with [the README](README.md), [architecture](docs/ARCHITECTURE.md), and [current roadmap](docs/ROADMAP.md). The original blueprint is design history; implemented scope is defined by the code and evaluation guide.

## Development loop

1. Follow the pinned dependency setup in the README. Work on a focused branch.
2. Use `./scripts/dev.sh` to start the API and client.
3. Keep `.env`, local database files, caches, and runtime output out of commits.
4. Run `./scripts/check.sh` against the real local FalkorDB before submitting a change.
5. Include the problem, resulting behavior, relevant validation, and any remaining limitations in the pull request.

The checks do not call Gemini. If you change the agent loop, also perform a separate live invocation with your own key, inspect tool choices and citations, and describe that verification without including credentials or provider payloads.

## Implementation principles

- FalkorDB must shape decisions. Do not replace its queries with frontend verdicts or a mock relationship engine.
- Treat all source text as data. A chat suggestion cannot become accepted policy merely because it is newer.
- Preserve effective and recorded time. Test temporal boundaries and partner scope when changing facts or queries.
- Keep the model behind bounded read tools; do not give it arbitrary Cypher, database credentials, or publishing privileges.
- Preserve users' demo graphs. Tests and evaluation use uniquely named disposable graphs only.
- Keep synthetic events, unfinished integrations, and in-app-only actions explicitly labeled.
- Update capability documentation when behavior changes. Do not describe planned work as implemented.

## Style and dependencies

Use UTF-8 and LF endings, four spaces for Python, and two spaces for frontend/configuration files. Prefer descriptive names and comments that explain invariants. Keep related changes focused; avoid formatting unrelated files.

`backend/requirements.lock.txt` and `frontend/package-lock.json` define the reproducible install path. Update dependency declarations and locks together when changing packages, then verify from a clean environment. Existing tests are integration checks with real FalkorDB, not mocks of its results.

## Questions and reports

For an ordinary defect, include the expected behavior, exact reproduction steps, supported environment, and sanitized output. For a design proposal, explain the user problem and the graph's role before suggesting frameworks or agents. Handle sensitive reports as described in [SECURITY.md](SECURITY.md).

Contributions to this repository are provided under its [MIT License](LICENSE).
