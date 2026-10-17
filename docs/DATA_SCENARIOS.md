# Synthetic logistics depth

This is an independently designed Company Brain dataset, not a replica of Delhivery's private database. Public company names provide business context. Every private agreement, shipment, incident, amount, location identity and staff role is fictional. The data covers selected situations, not every logistics process.

## Public concepts informing the model

Delhivery's public help documents describe [delivery exceptions](https://help.delhivery.com/docs/exception-ndr), [return to origin](https://help.delhivery.com/docs/courier-returnrto), and [COD remittance](https://help.delhivery.com/docs/cod-remittance). These establish concepts only. Our amounts, controls, timings and incidents are synthetic assumptions; the public references do not validate them.

## Three distinct operational cohorts

- The original 1,200 Bengaluru shipments are the planned November Sunday-comparison cohort. Four scans each support that guided example.
- Another 210 October snapshot shipments cover seven other cities and seven statuses: delivered, in transit, out for delivery, failed delivery, return initiated, returned to origin, and on hold. These have three scans each, payment modes, declared/measured weights and service types. They do not change the Sunday rehearsal population.

- A further 480 October shipments connect all 12 accounts to 36 pickup warehouses across multiple cities, with handling holds, rescheduling, damage review, billing and settlements. Their origin facility is distinct from live parcel position.

The Sunday comparison explicitly selects its 1,200-record cohort; ordinary Bengaluru traffic cannot change that population.

The expanded initial seed contains **9,991 business records, 17,207 relationships and 25 labels**, plus separate dataset metadata. Replays and investigation history add further records. The inspector always reads actual current counts from FalkorDB.

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

The complete fixture has 20 review tickets, 22 decisions, 24 role identities, 21 vehicles, 72 invoices, 252 exceptions, 156 returns, 39 COD collections and 39 settlements. Its 43 accepted rules span 12 handling controls plus billing, escalation and scheduling. Claims preserve 25 document statements, including four handling guides that disagree with current accepted terms. Current role membership and expertise are graph relationships, not historical personnel records.

The 13 Campaign records describe client programmes (festive replenishment, regional rollout, returns improvement and inventory rebalance). They provide planning rationale, never policy authority. The 36 WorkItems represent assigned pending review work across Operations, Account Management and Finance. Action rows remain actual user-created local review packets; no completed user activity is seeded to inflate that table.

Public account context comes from Delhivery's [Q1 FY24 release](https://www.delhivery.com/uploads/2023/08/PressRelease.pdf), [FY24 annual report](https://www.delhivery.com/uploads/2024/08/Annual_Report_FY24.pdf) and [press archive](https://www.delhivery.com/company/press-release). Those establish historical business context only. The 36 warehouse locations and private terms are modeled, not verified real account infrastructure.

The examples are source material, not query/answer pairs. The general investigator cannot read guided-tour metadata or past receipts as company evidence. Saved receipts preserve what a prior run returned; they are not prewritten future responses. A field called `demo_config` contains optional tour questions and replay controls only.

## Validation and boundaries

Integration tests verify shipment relationships, source hashes, graph integrity, distinct statuses, incident-to-transaction paths and live count changes after adding records to an unrelated imported workspace. Existing workspaces receive an additive versioned extension; their history is retained and older receipts are marked stale. No demo graph is reset by tests.

Counts and sums are actual stored-data calculations. They are not live business metrics or historical snapshots of unversioned operational records. An unsuccessful attempt is not proof of loss; a proposed reroute is not approval; an invoice discrepancy is not authorization for a credit. The AI must distinguish these. Generated interpretation still needs review, and provider quotas or outages can prevent an answer.
