# Queries behind the product

FalkorDB is the execution engine. These are the core parameterized patterns used by ChronosGraph, with their source implementations linked below. Agent tools execute bounded server-owned templates using `GRAPH.RO_QUERY`; a model cannot submit arbitrary Cypher or select a different visitor graph. Backend-controlled seeding, receipts, replays and graph-copy operations use write commands separately.

For tool discovery, [CompanyReader.tool_schema](../backend/chronos/company/repository.py) computes observed labels, counts and native property keys inside FalkorDB, without transferring every JSON payload. A second query returns observed relationship types and endpoint labels. This is a fresh database read, not a cached business answer:

```cypher
MATCH (n:Entity) WHERE NOT n.kind IN $private
RETURN n.kind, count(n), collect(DISTINCT keys(n)) ORDER BY n.kind
```

Private bookkeeping labels and internal payload/search properties are removed before the result is supplied to the model. The full reviewer catalog still inspects stored payload fields separately.

## Reviewer map

| User task | Graph operation | Implementation |
| --- | --- | --- |
| Find records for a question | Ranked lexical search over stored native fields | `CompanyReader.search` in [repository.py](../backend/chronos/company/repository.py) |
| Determine what currently applies | Accepted rules, enabled sources and two time intervals | `CompanyReader.rules` in [repository.py](../backend/chronos/company/repository.py) |
| Identify an outdated document statement | Policy → Claim → Source, compared with accepted rules | `CompanyReader.claims` in [repository.py](../backend/chronos/company/repository.py) |
| Count clients or calculate invoice amounts | Database aggregation, validated fields and parameterized filters | `CompanyReader.aggregate` in [repository.py](../backend/chronos/company/repository.py) |
| Find an owner and explore the proof | Bounded traversal plus real induced edges and provenance IDs | `CompanyStore.owners`, `neighborhood`, `subgraph` in [store.py](../backend/chronos/company/store.py) |
| Compare a proposed schedule | Actual `GRAPH.COPY`, scoped deterministic evaluation, cleanup | [engine.py](../backend/chronos/company/engine.py), `CompanyStore.copy_scenario` in [store.py](../backend/chronos/company/store.py) |
| Inspect data integrity | Cypher structural checks plus payload/hash validation | `CompanyReader.audit` in [repository.py](../backend/chronos/company/repository.py) |

These are implemented query patterns, not a claim to use PageRank, community detection or an unrestricted text-to-Cypher agent. Business traversal and rule selection happen in FalkorDB; answer synthesis and UI layout happen outside the database.

## Retrieve candidate records

The server derives at most 16 search terms from the question. `private` excludes investigation receipts, review actions and internal registry records so generated answers do not become company facts. The source cutoff is applied to Source records here; time applicability of commitments is handled by the rule query below.

```cypher
MATCH (n:Entity) WHERE NOT n.kind IN $private
AND (n.kind <> 'Source' OR (n.enabled=true AND toString(n.timestamp) <= $known))
WITH n, size([t IN $terms WHERE toLower(n.id) CONTAINS t OR toLower(n.title) CONTAINS t])*4 + size([t IN $terms WHERE n.search_text CONTAINS t]) AS score
WHERE score>0 OR size($terms)=0
RETURN n.payload ORDER BY score DESC,n.id LIMIT $limit
```

This is lexical retrieval, not semantic/vector search. The investigator can request further records and bounded connections using separate tools.

## Applicable accepted rules

From [CompanyReader.rules](../backend/chronos/company/repository.py), bounded to 100 rows. Both time values are canonical UTC strings fixed by the request context. `ids` contains only retrieved subjects or records; an empty list requests all applicable rules within the bounded result.

```cypher
MATCH (r:Rule)-[:SUPPORTED_BY]->(s:Source)
WHERE r.status='accepted' AND s.enabled=true AND toString(s.timestamp) <= $known
AND toString(r.valid_from) <= $effective AND (r.valid_to='' OR $effective < toString(r.valid_to))
AND toString(r.recorded_from) <= $known AND (r.recorded_to='' OR $known < toString(r.recorded_to))
AND (size($ids)=0 OR r.id IN $ids OR r.subject_id IN $ids OR r.client IN $ids OR r.facility IN $ids)
RETURN r.payload,s.payload ORDER BY r.id LIMIT 100
```

A chat proposal or a handbook assertion cannot turn into an accepted rule through retrieval. When the initial evidence includes policy records, the server also runs this template before model planning. The AI receives the actual applicable rule values and time bounds, with their supporting sources prioritized over older excerpts. The automatic read is marked `server_policy_check` in the trace; it is not attributed to model tool selection. This context is bounded to 12 rule/source pairs and explicitly marks truncation.

## What an operating document says

From [CompanyReader.claims](../backend/chronos/company/repository.py). The server compares each retrieved assertion's subject, facility, field and value with applicable accepted rules. Disagreements generate a relevant document-review alert. A Claim alone is not policy authority.

```cypher
MATCH (p:Policy)-[:ASSERTS]->(c:Claim)-[:SUPPORTED_BY]->(s:Source)
WHERE s.enabled=true AND toString(s.timestamp)<=$known
AND toString(c.valid_from)<=$effective AND (c.valid_to='' OR $effective<toString(c.valid_to))
AND toString(c.recorded_from)<=$known AND (c.recorded_to='' OR $known<toString(c.recorded_to))
RETURN p.payload,c.payload,s.payload LIMIT 100
```

## Live arithmetic and evidence paths

[CompanyReader.aggregate](../backend/chronos/company/repository.py) validates labels, numeric/group fields and equality filters against the observed schema. It counts or sums actual nodes, returns a bounded record sample and reports truncation. The investigator must not present an unfiltered total as the answer to a filtered question.

For **“How many external client companies are recorded?”**, the actual aggregate template resolves to the following query when `label="Client"`, `metric="count"`, with no filters or grouping:

```cypher
MATCH (n:Entity) WHERE n.kind=$label AND true
WITH DISTINCT n
RETURN n.kind,count(n) ORDER BY count(n) DESC LIMIT 51
```

The initial fixture returns `Client, 12`; **12 is computed by FalkorDB**, not a frontend constant. An accompanying query returns at most five sample IDs for inspection; those five samples are not the population counted. Grouped results expose at most 50 groups and signal truncation if a 51st exists. Numeric fields and grouping/filter field names are server-validated before template construction; filter values remain parameters.

Current ownership uses:

```cypher
MATCH (:Entity {id:$id})-[r:OWNED_BY|OPERATED_BY]->(t:Team)
RETURN t.payload,coalesce(r.source_ids,[])
```

For example, `id="facility-bengaluru"` resolves its recorded team. This does not reconstruct historical ownership.

[CompanyStore.record_graph, neighborhood and owners](../backend/chronos/company/store.py) retrieve real relationships, supporting Source IDs and current ownership. The displayed evidence map contains the records selected for the actual question. Visual layout does not invent business edges. Ownership/topology are current-state relationships, not historical reconstructions.

The one-hop neighborhood template is:

```cypher
MATCH (root:Entity {id:$id})-[*0..1]-(n:Entity)
WHERE NOT n.kind IN $excluded
RETURN DISTINCT n.payload LIMIT 32
```

The server may select a maximum depth of two using its own fixed template. For operational records, `record_graph` instead retrieves up to 16 direct neighbors. Once records are selected, the actual connections among their IDs are fetched with:

```cypher
MATCH (a:Entity)-[r]->(b:Entity)
WHERE a.id IN $ids AND b.id IN $ids
RETURN a.id,type(r),b.id,coalesce(r.source_ids,[]) LIMIT 150
```

This is why a graph item can be expanded and inspected: its edges come from stored relationships, including their source IDs. A missing edge is not filled in by the LLM or a layout algorithm. FalkorDB's knowledge graph is the underlying stored data; the UI's **Map** and **Readable trail** are two renderings of a retrieved subgraph. They are not a visualization of the LLM's private reasoning, nor proof that every generated sentence is correct.

Selecting **Ask about this** passes that record ID, the parent receipt and the selected dates into a new investigation. It runs fresh graph reads and creates a new evidence snapshot; it does not simply reuse the preceding answer. Explicit neighbor expansion can include historical records, whose dates remain inspectable.

**Inspect retrieval trace** exposes executed read tools, row counts and elapsed tool durations. `server_policy_check` identifies the automatic policy refresh separately from model-selected reads. The approximately 7 ms policy read shown in the recording is one measured tool execution, including backend handling and database access; it is not an isolated FalkorDB benchmark or an end-to-end response-time promise. Provider synthesis contributes separately to the total investigation duration.

## Change comparison

The guided comparison uses `GRAPH.COPY` on a uniquely named server-controlled graph, evaluates the proposed schedule against the copied graph, verifies the original revision is unchanged, then removes the disposable copy. It is not an in-memory simulation of relationships. [Implementation](../backend/chronos/company/engine.py).

Its population query explicitly separates the planned comparison cohort from ordinary Bengaluru traffic:

```cypher
MATCH (s:Shipment)-[:AT]->(:Facility {id:"facility-bengaluru"})
MATCH (s)-[:FOR_CLIENT]->(c:Client)
WHERE s.scenario_cohort=$cohort AND ($client="all" OR c.id=$client)
RETURN c.id,c.title,count(s) ORDER BY c.title
```

The baseline scenario passes `cohort="bengaluru-scheduling"`, selecting 1,200 consignments across Havells, SUGAR and HPCL. For October 25, full Sunday closure conflicts with Havells' applicable rule; **Preserve commitments** keeps Havells processing and queues the other two clients for Monday. For November 8 after the approved amendment is recorded and effective, full closure has no modeled commitment conflict. The same copied-graph workflow reads each date's actual applicable rule versions; the frontend does not select a canned verdict. This does not claim to predict delivery outcomes, cover every client or apply changes to a real company. Preparing a human-review packet is a separate explicit operation.

## Structural verification

Two actual checks from the separate portal's `CompanyReader.audit` are:

```cypher
MATCH (n:Rule)
WHERE NOT (n)-[:SUPPORTED_BY]->(:Source)
RETURN count(n)
```

```cypher
MATCH (n:Rule)
WHERE (n.valid_to<>'' AND n.valid_to<=n.valid_from)
   OR (n.recorded_to<>'' AND n.recorded_to<=n.recorded_from)
RETURN count(n)
```

A zero count means no violation of that specific check. It does not prove document authenticity, policy completeness or semantic correctness of an AI answer. The portal also checks identifiers, required properties, shipment/scan relationships, source excerpt hashes and parity between native fields and serialized records.

## Reproduce

Run `./scripts/check.sh` against local FalkorDB. The integration suite checks that removing a real required relationship changes the answer, time boundaries are preserved, source withdrawal forces uncertainty, a changed record updates calculations, and graph-copy comparisons leave the original workspace intact. Test graphs are disposable; the user's reference workspace is not reset.

For a direct read-only count after starting the app once to initialize its reference graph, run this from the repository root:

```sh
PYTHONPATH=backend .venv/bin/python - <<'PY'
from chronos.company.store import CompanyStore, BASE_NAME
store = CompanyStore(BASE_NAME)
rows = store.read(
    'MATCH (n:Entity) WHERE n.kind=$label AND true '
    'WITH DISTINCT n RETURN n.kind,count(n) ORDER BY count(n) DESC LIMIT 51',
    {'label': 'Client'},
)
print(rows)
PY
```

This executes `GRAPH.RO_QUERY` against your local reference graph without seeding, resetting or writing to it. Actual counts depend on the stored graph revision. The public inspection portal deliberately does not expose arbitrary Cypher execution or database credentials.
