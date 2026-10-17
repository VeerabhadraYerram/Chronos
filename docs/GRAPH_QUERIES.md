# Queries behind the product

FalkorDB is the execution engine. These are the core parameterized patterns used by ChronosGraph, with their source implementations linked below. Agent tools execute bounded server-owned templates using `GRAPH.RO_QUERY`; a model cannot submit arbitrary Cypher or select a different visitor graph. Backend-controlled seeding, receipts, replays and graph-copy operations use write commands separately.

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

A chat proposal or a handbook assertion cannot turn into an accepted rule through retrieval.

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

[CompanyStore.record_graph, neighborhood and owners](../backend/chronos/company/store.py) retrieve real relationships, supporting Source IDs and current ownership. The displayed evidence map contains the records selected for the actual question. Visual layout does not invent business edges. Ownership/topology are current-state relationships, not historical reconstructions.

## Change comparison

The guided comparison uses `GRAPH.COPY` on a uniquely named server-controlled graph, evaluates the proposed schedule against the copied graph, verifies the original revision is unchanged, then removes the disposable copy. It is not an in-memory simulation of relationships. [Implementation](../backend/chronos/company/engine.py).

Its population query explicitly separates the planned comparison cohort from ordinary Bengaluru traffic:

```cypher
MATCH (s:Shipment)-[:AT]->(:Facility {id:"facility-bengaluru"})
MATCH (s)-[:FOR_CLIENT]->(c:Client)
WHERE s.scenario_cohort=$cohort AND ($client="all" OR c.id=$client)
RETURN c.id,c.title,count(s) ORDER BY c.title
```

The baseline scenario passes `cohort="bengaluru-scheduling"`. It does not claim to predict actual carrier outcomes or apply changes to a real company.

## Reproduce

Run `./scripts/check.sh` against local FalkorDB. The integration suite checks that removing a real required relationship changes the answer, time boundaries are preserved, source withdrawal forces uncertainty, a changed record updates calculations, and graph-copy comparisons leave the original workspace intact. Test graphs are disposable; the user's reference workspace is not reset.
