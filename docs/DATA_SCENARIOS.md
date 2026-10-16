# Synthetic logistics depth

This is an independently designed Company Brain dataset, not a replica of Delhivery's private database. Public company names provide business context. Every private agreement, shipment, incident, amount, location identity and staff role is fictional. The data covers selected situations, not every logistics process.

## Public concepts informing the model

Delhivery's public help documents describe [delivery exceptions](https://help.delhivery.com/docs/exception-ndr), [return to origin](https://help.delhivery.com/docs/courier-returnrto), and [COD remittance](https://help.delhivery.com/docs/cod-remittance). These establish concepts only. Our amounts, controls, timings and incidents are synthetic assumptions; the public references do not validate them.

## Two distinct operational cohorts

- The original 1,200 Bengaluru shipments are the planned November Sunday-comparison cohort. Four scans each support that guided example.
- Another 210 October snapshot shipments cover seven other cities and seven statuses: delivered, in transit, out for delivery, failed delivery, return initiated, returned to origin, and on hold. These have three scans each, payment modes, declared/measured weights and service types. They do not change the Sunday rehearsal population.

The expanded initial seed contains **7,333 business records, 11,984 relationships and 24 labels**, plus separate dataset metadata. Replays and investigation history add further records. The inspector always reads actual current counts from FalkorDB.

## Connected investigation examples

| Situation | Evidence path | Example question |
| --- | --- | --- |
| COD mismatch | Decision → incident ticket → settlement → cash collection → shipment; Finance owns review | Why is the SUGAR COD mismatch being investigated? Does it prove cash loss? |
| Weight dispute | Decision → ticket → invoice → shipment with declared/measured weights; Finance and Operations have distinct roles | Who owns the Havells weight dispute, and what evidence is needed before a credit? |
| Failed delivery | Shipment → delivery exception → account team; reason and next action are explicit | What delivery exceptions are recorded, and who handles them? |
| Damaged return | Decision → ticket → return → shipment; Warehouse owns inspection | Why is the Chennai return awaiting inspection? |
| Capacity review | Decision → ticket → Mumbai facility → Operations | Is additional Mumbai staffing approved or still pending? |
| Scan ingestion gap | Decision → ticket → affected shipment; Technology owns investigation | Does a missing scan mean the parcel is lost? |
| Weather contingency | Proposed decision → ticket → route → facilities; Transport owns review | Is the Kolkata reroute approved? |
| Packaging hold | Decision → ticket → exception → shipment; Compliance owns review | Who reviews the HPCL packaging hold? |

There are 8 incident tickets, their 8 decision records, 16 ticket/chat sources plus 5 supporting procedure/directory sources, 24 fictional role identities, 21 vehicles, 36 invoices, 60 exceptions, 60 returns, 15 COD collections and 15 settlements. Four additional accepted review controls have source links and effective/recorded intervals. Current role membership and expertise are explicit graph relationships, not historical personnel records.

The examples are source material, not query/answer pairs. The general investigator cannot read guided-tour metadata or past receipts as company evidence. Saved receipts preserve what a prior run returned; they are not prewritten future responses. A field called `demo_config` contains optional tour questions and replay controls only.

## Validation and boundaries

Integration tests verify shipment relationships, source hashes, graph integrity, distinct statuses, incident-to-transaction paths and live count changes after adding records to an unrelated imported workspace. Existing workspaces receive an additive versioned extension; their history is retained and older receipts are marked stale. No demo graph is reset by tests.

Counts and sums are actual stored-data calculations. They are not live business metrics or historical snapshots of unversioned operational records. An unsuccessful attempt is not proof of loss; a proposed reroute is not approval; an invoice discrepancy is not authorization for a credit. The AI must distinguish these. Generated interpretation still needs review, and provider quotas or outages can prevent an answer.
