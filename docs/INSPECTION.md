# Separate database inspection portal

Open the **[live database portal](https://chronosgraph.onrender.com/database)**, or **[http://127.0.0.1:8000/database](http://127.0.0.1:8000/database)** after starting the local backend. This is a separate page served by FastAPI; it is not a tab in the main investigation interface and does not require the Vite frontend to run.

Enter the workspace ID shown in the prototype's **About this workspace** dialog. Alternatively, create a fresh reference demo copy. **Copy inspection link** produces a URL whose fragment identifies this workspace. Reviewers opening that link see the same stored records and saved investigations, rather than an exported sample or screenshots. A local URL works only on the machine running the server; use the live Render URL for public review. Hosted workspace links are temporary and can expire on restart or after an hour of inactivity. Use the permanent `/database` root link in submissions; reviewers can create a fresh workspace there.

## What reviewers can inspect

- Every business node label as a paginated table, including the 6,870 scans and 1,890 shipments in the logistics fixture. Runtime receipts, local review drafts, replay markers and dataset metadata are included when present.
- Search across the selected label's complete serialized records, with stable ID ordering and exact filtered counts. Pages contain up to 100 records; the interface uses 50.
- All decoded fields and native database properties, including the original serialized payload, via the record inspector.
- Every directed business relationship, with its endpoints, endpoint labels, actual relationship properties and source references. Direct connections have their own pagination; there is no graph-neighborhood sampling in the database table view.
- Observed field types, actual index status, actual database constraint status and relationship endpoint types. Observed fields describe data; they are not all mandatory constraints.
- Structural integrity results calculated from real graph reads. These detect implemented classes of broken structure, not factual authenticity or every possible business inconsistency.
- A complete JSON snapshot of the visible workspace nodes and relationships, with metadata and a reproducible content hash. Export runs under the application's process lock. Exports above 25,000 nodes or 50,000 relationships are refused explicitly; pagination remains available. Writes outside this process are not covered by that lock.

The private `DemoSession` creation registry is excluded because it can contain other workspace capability identifiers. Database credentials, environment variables, other graph names and other visitors' graphs are never exposed. This is full inspection of the selected business workspace, not server administration.

## Read-only boundary

The portal offers fixed read operations through `POST /api/database/{operation}`: `catalog`, `rows`, `relationships`, `record`, `audit`, and `export`. Request bodies contain the workspace ID and bounded paging/filter values. There is no arbitrary Cypher, delete, edit, database connection string, or provider key field. All data reads use `GRAPH.RO_QUERY`. Creating a demo workspace provisions a separate copy using the existing session endpoint; opening an older workspace may trigger its non-destructive schema migration.

The application uses an opaque workspace ID as a demo capability, **not production authentication**. Treat a copied link as read access to that synthetic workspace. The fragment avoids placing the ID in the initial page request; API requests still carry it in the body. The portal sets no-store caching, a self-only content security policy, and no-referrer headers, and renders records as text rather than HTML.

## Import another company

The core engine is described in [Company-wide investigation](COMPANY_ENGINE.md). Import a trusted local JSON data pack into a **new** graph:

```sh
PYTHONPATH=backend .venv/bin/python scripts/import_company.py datasets/atlas-studio.json
```

The command prints separate prototype and inspection URLs. It never clears an existing graph. The supplied Atlas Studio fixture is fictional and tests Finance, Marketing, invoice totals and ownership without logistics assumptions. Public ingestion and uploads are intentionally absent from the read-only reviewer portal.

The portal starts with an evaluator overview. Grouped navigation separates company knowledge, operations/finance and investigation history/setup. Tables show compact two-line previews; selecting a record opens all fields, structured values and paginated connections. Full document text and internal IDs do not expand rows. Metadata is explicitly identified as configuration, not generated business answers.

Catalog, audit and export reads use batches below the database server response cap. Full export assembles every page, including graphs with more than 10,000 relationships; its existing 25,000-record / 50,000-relationship limit still applies.
