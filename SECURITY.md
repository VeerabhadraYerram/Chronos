# Security and trust boundaries

ChronosGraph is a **trusted local prototype**. The default UI, API, and database ports bind to loopback. It currently has no authentication, source-level authorization, rate limiting, or production deployment configuration. Do not expose the default services directly as a public company knowledge system.

## Implemented controls

- Model tools execute server-owned, parameterized read templates through `GRAPH.RO_QUERY`, with query timeouts.
- Graph names come from server configuration; the browser cannot submit an arbitrary graph key.
- The Gemini key stays in the ignored server-side `.env`. Health responses disclose only a configuration flag.
- Raw provider exceptions are not returned or logged by the investigation handler.
- Generated response shape and cited source IDs are checked before accepting the model explanation.
- Stale receipts cannot prepare or approve actions; approval records are local and idempotent.
- Sample updates and synthetic sources are labeled. No external publishing tool is exposed to the model.

## Limits

An approved source ID does not prove semantic correctness. Prompt instructions reduce instruction-following risk from source text but are not a complete prompt-injection defense. Withdrawn source availability, ownership, and topology are not fully temporal.

Graph separation is not a permission system. The process-local lock is not distributed coordination, and multi-query ingestion is not crash-atomic. In-app approval is an audit state, not an authorization boundary for external systems. Durable local receipts are not signed or tamper-evident.

Add authentication, source permissions, approved write policies, stronger operational controls, and security evaluation before ingesting confidential company data or opening access to untrusted users.

## Reporting

Do not include credentials, private company records, or raw provider requests in public issues. Contact the repository owner through an established private channel before sharing sensitive details. If GitHub private vulnerability reporting is enabled for the repository, its Security tab may be used. No response-time commitment or managed security service is implied.

## Company reference workspace

The main workspace stores only synthetic demo operations and separately marked public references. Visitor graph copies use random capability IDs, not authenticated user accounts. Their isolation does not provide enterprise identity, permissions or source-level access control. The instance caps reference-session creation at 40 and persists graphs without automatic expiry. Run the service locally until hosting-level spend controls, rate limits and session lifecycle management are configured. The preserved NovaPay mutation endpoints remain local prototype APIs.

The selected Gemini or Groq provider receives synthetic excerpts, the user question, dates and scoped tool outputs. Do not enter private company records into this demo without a separate data-handling review. Read tools use parameterized `GRAPH.RO_QUERY`; the model cannot submit arbitrary Cypher or choose another session graph.
