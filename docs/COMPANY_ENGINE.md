# Company-wide investigation engine

The default `POST /api/company/ask` path uses [investigation.py](../backend/chronos/company/investigation.py). It does not choose a canned answer by Sunday-related keywords, assume Havells, evaluate every question as a warehouse closure, or substitute a known facility when the user asks about another company.

## Data versus implementation

Company names, policies, source text, effective/recorded intervals, entity identifiers, responsibility relationships and scalar business values belong in FalkorDB. [repository.py](../backend/chronos/company/repository.py) supplies bounded, parameterized read templates. Validation, query budgets, allowed operations and generic language handling remain implementation rules; removing these controls would not make the system more general.

The [logistics fixture](../backend/chronos/company/seed.py), its [guided-tour configuration](../backend/chronos/company/demo.py), and the scheduling simulator in [engine.py](../backend/chronos/company/engine.py) are explicitly sample-specific. The main interface hides the guided replay and rehearsal controls until **Guided walkthrough** is selected. General investigation remains the same while the guide is visible; the before/after simulation evaluates its explicitly limited scheduling model. The old scenario answer helper is retained for regression tests, not called by the general question endpoint.

## Retrieval and answers

1. Rank actual stored records using concrete query tokens, with selected-record context. Exclude internal capability registries and private runtime control records from AI discovery.
2. Traverse actual relationships and their evidence references; do not fabricate edges. Select applicable accepted rules using their subject scope, supporting sources and both time intervals.
3. Graph-retrieval mode returns stored facts, source excerpts, current ownership, or supported record counts. It explicitly avoids pretending these excerpts are a semantic answer or an approval.
4. With AI enabled, Groq, Gemini or OpenRouter can discover the actual schema, search records, inspect retrieved neighbors, read applicable rules, and calculate counts, sums, averages, minimums and maximums using observed scalar fields. Grouped results indicate truncation above 50 groups. Filters are equality filters; this is not arbitrary SQL/Cypher generation.
5. Validate cited source IDs and selected graph IDs against retrieved context. This prevents invented identifiers, **not unsupported semantic interpretations of valid sources**. Persist the actual provider, tool trace, evidence and context in a receipt.
6. Compare explicitly stored document `Claim` records against accepted rules for the same subject, field and dates. A mismatching document is flagged for review; it cannot override policy. No company-specific handbook comparison is required.
7. Report missing evidence or unavailable AI explicitly. Contradictory accepted rules retrieved for the same subject/field/date scope produce a review alert. General questions do not inherit sample closure-conflict badges.

Sources must be enabled and recorded by the cutoff. Rules must be accepted and active in both effective and recorded time. Changing a source or relationship changes the evidence returned. A proposal/chat cannot silently replace an accepted policy. Ownership/topology remain current relationships, not historical snapshots.

## Extensible data packs

A data pack contains `nodes` and `relationships` arrays. Nodes require `id`, `kind`, `title`; the trusted importer accepts validated label names and arbitrary additional record fields. Relationships require existing `source`/`target` identifiers, a validated relationship name, and optional `source_ids` referencing actual Source records. Additional entity types such as `Invoice` work without editing answer code.

`Source` records require an excerpt, explicit enabled state and timezone-aware recorded timestamp. The importer calculates content hashes. Accepted `Rule` records require a field, value, subject/client scope, effective and recorded intervals, and a supporting source edge. Imports are explicit local developer operations; an AI answer cannot write a new accepted rule.

Scalar fields with safe property names are mirrored natively for database inspection and generic aggregation. Nested values remain in the full JSON payload. Common identity and policy fields have indexes; database-enforced identity and mandatory-property constraints prevent duplicate/malformed identities. See [Database & schema](DATABASE.md) and the [inspection portal](INSPECTION.md).

## Evidence of generality and limits

The real-FalkorDB tests in [test_database_inspection.py](../backend/tests/test_database_inspection.py) import the unrelated [Atlas Studio fixture](../datasets/atlas-studio.json). They verify Marketing ownership, a Finance approval threshold, invoice counts and invoice arithmetic; change an owner and verify the answer changes; withdraw a source; and reject unsupported questions. These checks are deterministic and do not prove broad LLM semantic accuracy.

This is a stronger prototype, **not a production-ready enterprise deployment**. It still needs authenticated tenants/RBAC, source authorization, ingestion connectors, deployment hardening, tested backups/restores, concurrent-write coordination beyond a single process, load tests, and broader question-answer evaluations. Retrieval/tool budgets limit coverage. The system cannot answer every conceivable question or predict arbitrary business outcomes from absent data. Unknown questions should identify missing evidence, not receive a confident invented answer.

## Provider execution and answer validation

The configured chain is Groq → Gemini → OpenRouter's free router. OpenRouter is tried once more if its first attempt cannot produce a usable result. Paid OpenRouter model identifiers are rejected before a request. Availability, free-tier quotas and correct interpretation cannot be guaranteed.

Groq and OpenRouter select bounded read templates through structured JSON plans. Gemini uses native function calls. Both paths execute the same parameterized read-only FalkorDB templates, validate source and graph IDs, and reject numerical headlines that disagree with a requested server-calculated count/sum. This is not full semantic verification of generated prose. Explicit source membership does not prove entailment. The retrieved sources remain available for human review.

When AI is enabled and every attempt fails, the receipt says no AI answer was generated; it does not replace it with a canned answer. With AI explicitly disabled, graph-only retrieval remains available as a separate labeled mode. External inference does not hold the global database write lock. A revision change during investigation marks the resulting receipt stale; this is conservative invalidation, not a transactional historical snapshot.

Evidence graphs are scoped to selected answer records and cited sources. A sparse selection is never filled with the initial company overview. Calculation graphs use samples from the same filtered database query; unrelated one-off neighbors are omitted. Qualified count questions are sent to model-selected tools rather than labeled with an unfiltered total. The main page shows its evidence graph only after a question has been investigated.
