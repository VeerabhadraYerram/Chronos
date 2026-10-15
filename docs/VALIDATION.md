# Validation record

Development validation on October 15, 2026, macOS ARM64, Python 3.13, Node 20.19.6.

- Real FalkorDB v4.22.1 container, image digest pinned in compose.yaml.
- Corrected persistence to use the image's supported REDIS_ARGS environment variable and /var/lib/falkordb/data mount. Compared graph content hashes and all 12 saved receipt IDs before/after a real database restart; all matched, with append-only storage enabled.
- Sixteen integration checks passed with independent disposable graphs. See backend/tests/test_company_brain.py.
- TypeScript check and Vite production build passed.
- Browser verified: a real graph investigation, partner migration result, documentation conflict, source-backed repair draft. Desktop and mobile layouts inspected during implementation.
- Gemini API authentication and account model listing succeeded. A real `gemini-3.1-flash-lite` investigation selected inspect_constraints, inspect_owners, and inspect_conflicts and returned a source ID validated against the graph. One observed run took approximately 16 seconds; this is a single observation, not a benchmark or latency promise.
- A model endpoint that timed out was replaced after checking account availability. Provider failures are shown without exposing raw provider errors or keys.

Remaining limitations: synthetic fixture only; no live ingestion connectors; no external action publishing; no production authentication or source ACLs; no deployment; no final submission video; no robust benchmark against alternative retrieval methods. Time-aware facts do not imply fully time-aware ownership or topology.

The API key is in an ignored local environment file and is never included in the repository. Rotate any key that was posted in chat.
