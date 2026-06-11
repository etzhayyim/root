# 30-Day Proof-of-Concept plan — open-salesforce

> Reverse-topo node 04 / 13. Back-solves 03 (SOW): this POC must produce, in ≤21 calendar days, the exact artifacts the MSA / SOW rely on — APPI+GDPR attestation, reconciliation-report format, data-residency audit, rollback rehearsal, named-DRI process. Day 22–30 is buffer. Nothing in this POC is a slide; every output is a file, a URL, or a signed commit.

## Entry (Day -3 to Day 0)
- Discovery call qualified (node 05) → customer has (a) a Salesforce renewal quote in the next 6 months, (b) a concrete own-LLM plan, (c) a data-residency obligation (APPI / GDPR / industry).
- POC Agreement (1-page, derived from MSA §§1–6 + §10) signed.
- Customer names: 1 Executive Sponsor (VP Sales or CTO), 1 DRI (RevOps / Salesforce admin), 1 Security reviewer.
- Provider names: 1 AE, 1 Solutions Engineer (on-call across Day 7 weekend if migration rehearsal included).

## Scope — 3 tracks, run in parallel

### Track 1 — Functional (own the happy path)
The customer must see their own business flow land on `https://salesforce.opensaas.etzhayyim.com/` with *their* data, not demo seeds.

- **Day 1–2**: provision sandbox Tenant DID `did:web:<slug>-poc.opensaas.etzhayyim.com` in customer's declared region. DNS + `_atproto` TXT auto via `etzhayyim dns-sync`.
- **Day 3**: customer exports a 10%-slice of Salesforce (1 business unit, ~3 months of records) → `sfdc_slice.zip`.
- **Day 4**: Provider runs `etzhayyim opensaas migrate sfdc --in sfdc_slice.zip --map poc/map.jsonl --tenant did:web:<slug>-poc.opensaas.etzhayyim.com --dry-run` → customer reviews drop list (target ≤3%).
- **Day 5**: real ingest (same command, no `--dry-run`). All records land under tenant DID as `com.etzhayyim.apps.opensaas.salesforce.{account,contact,lead,opportunity,case}`.
- **Day 6**: customer AEs log in (temporary passkey enrollment for 3 named seats), re-stage 3 opportunities → `activity(kind=stage-change)` rows derived within 200ms. Screenshot captured for the case study template.
- **Day 7**: customer calls `listPipeline({tenantDid})` and compares the stage rollup to their Salesforce pipeline report for the same slice. Delta target: ±0.5%.

### Track 2 — Compliance (own the legal path)
The customer's legal + security teams must be able to sign off the MSA without a bespoke residency review.

- **Day 1**: deliver the APPI / GDPR posture packet — Tier-1 vs Tier-3 PII topology, vault zero-knowledge invariant, Art-17 / APPI §30 cascade purge flow, content-addressed audit log.
- **Day 3**: security reviewer runs a live Art-17 rehearsal: pick one test contact → `POST /api/vault/purge` → verify within 72h the Tier-3 row is gone, the Tier-1 `contact.emailHash` is rotated to `sha256:deleted-<uuid>`, and an `activity(kind=note, source=manual-ui)` is written with the purge attestation signed by the executing seat DID.
- **Day 5**: data-residency attestation pull — `etzhayyim opensaas attest --tenant <did> --region <JPN|EUR>` produces a signed JSON of every CF colo ID + RisingWave replica region touched by the tenant in the last 7 days. Legal signs off attestation format.
- **Day 10**: counsel redlines MSA / SOW. Target: ≤ 2 redline rounds, all resolvable by AE + Provider counsel.

### Track 3 — Weekend rehearsal (own the migration)
De-risks SOW §C.4 (reconciliation gate) and §C.9 (rollback).

- **Day 12 (Fri) 18:00**: rehearsal of the full weekend playbook against the 10%-slice again, but this time running `migrate --rollback` on purpose at Sat 06:00 to time the rollback envelope (target: <15 min for 10%-slice; linear extrapolation for full migration goes into SOW).
- **Day 13 (Sat) 06:00–18:00**: redo the ingest, run `etzhayyim opensaas reconcile --against sfdc_slice.zip` → customer DRI signs off the reconciliation report format (this file becomes Schedule C-1b of the real SOW).
- **Day 14 (Sun) 10:00**: integration smoke — wire *one* SAP webhook into the sandbox tenant, trigger a fake won-opportunity → `createRecord(com.etzhayyim.apps.opensaas.salesforce.opportunity)` lands; `activity(kind=stage-change, source=derived-stage-change)` follows.

## Gate criteria (Day 21)

Exec-level review. Each gate is a file or a URL, not a claim.

| Gate | Artifact | Pass condition |
|---|---|---|
| Functional | `listPipeline` JSON for sandbox vs. Salesforce pipeline report | Stage-by-stage JPY delta ≤ ±0.5% |
| Functional | 3 re-staged opportunities with derived activities | Median stage-change → activity latency ≤ 200ms |
| Compliance | APPI / GDPR posture packet + Art-17 rehearsal log | Security sign-off email on file |
| Compliance | Data-residency attestation signed JSON | Every colo+region in attestation matches SOW-declared region |
| Migration | Reconciliation report format | DRI sign-off email + file committed as Schedule C-1b |
| Migration | Rollback envelope timing | <15 min for 10%-slice; linear projection acceptable for full |
| Integration | SAP webhook → opportunity → activity chain | One successful end-to-end in the sandbox |
| LLM | per-seat Murakumo invocation from within the CRM UI | one "summarise this opportunity" action run from `https://<slug>-poc.opensaas.etzhayyim.com/` with latency <3s |

## Disqualifying outcomes (honest kill criteria)

- Stage rollup delta >1.5% after three map-fix attempts → data model mismatch is deeper than migration can fix in one weekend → not an open-salesforce fit.
- Customer counsel cannot accept §5 (Processor/Controller) or §4 (residency clause) → sovereignty story fails → no deal.
- Rollback rehearsal leaves orphan records across tenants → product gap → Provider refunds POC fee and walks.

## POC commercials

- Flat POC fee: ¥`<pricing node 08>` (credited against year-1 Platform Fee if Customer signs by Day 45).
- Provider effort cap: 6 engineer-days (AE + SE combined). Overruns are Provider's risk.
- Sandbox tenant auto-deletes Day 30 unless rolled forward to production — `etzhayyim opensaas migrate --rollback --tenant <did>` runs on a schedule.

## What this POC plan forces the discovery script (05) to qualify

- The renewal date **must** be T-90 to T-180 from POC start — otherwise compliance-track legal review lands *after* the renewal, negating urgency.
- The named Security reviewer **must** exist on Day 1 — no POC without a counterparty for Track 2.
- The customer **must** be able to supply a 10%-slice export by Day 3 — if their Salesforce admin can't produce that, the full migration will also slip.
- The own-LLM plan **must** be real (named model / fleet / procurement track) — otherwise the per-seat Murakumo gate on Day 21 is performative.
- The data-residency obligation **must** be documented (APPI, GDPR, FSA, EBA, etc.) — the attestation artifact needs a named regulation to attest *against*.
