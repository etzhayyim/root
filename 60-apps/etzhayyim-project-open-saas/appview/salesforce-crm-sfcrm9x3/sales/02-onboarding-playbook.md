# Onboarding playbook — Salesforce → open-salesforce weekend migration

> Reverse-topo node 02 / 13. Back-solves the 01 case-study claim: *"148k contacts, 6.2k opportunities, 23k cases over one weekend, resumable."* If this playbook does not hold, the case study is a lie. Every step below is an actual command or XRPC call; no prose-only steps.

## Entry criteria (Friday 18:00 local)
- Customer signed SOW (node 03).
- Tenant DID provisioned: `did:web:<slug>.opensaas.etzhayyim.com` (created by `etzhayyim deploy` on the tenant's CF account).
- `sfdc_export.zip` from Salesforce Data Loader in hand (Accounts, Contacts, Leads, Opportunities, Cases, Activities, Users).
- Customer's identity team has chosen the seat DID naming rule (recommended: `did:web:<slug>.opensaas.etzhayyim.com:seat:<role>-<nn>`).

## Exit criteria (Monday 09:00 local)
- `listPipeline({tenantDid})` returns the same stage rollup totals as the customer's last Salesforce pipeline report, ±0.5%.
- All 22 seats (or N) can log in at `https://salesforce.opensaas.etzhayyim.com/` with their WebAuthn passkey.
- 5 VP-owned opportunities re-stage successfully → `activity(kind=stage-change)` auto-derived rows present.
- Customer's EU sub's separate tenant (`did:web:acme-eu.opensaas.etzhayyim.com`) is also up with zero-byte data (to prove the multi-tenant split before real EU data lands).

## Timeline

### Friday 18:00–20:00 — provisioning
1. `etzhayyim deploy --project open-saas --appview salesforce-crm-sfcrm9x3 --tenant-did did:web:acme.opensaas.etzhayyim.com`
2. DNS: CNAME `acme.opensaas.etzhayyim.com` → CF route; `_atproto` TXT auto-provisioned by `etzhayyim dns-sync`.
3. Seed plan: `POST /api/open-saas/tenants` on open-saas-console with `{ name: "Acme Robotics K.K.", planId: "enterprise-flat" }`.
4. `etzhayyim vault create --tenant acme --policy appi-gdpr` for Tier-3 Preferences vault.

### Friday 20:00–23:00 — schema map
Apply the canonical Salesforce → W Protocol mapping (deliver as `migration/map.jsonl`):

| Salesforce object / field | W Protocol lexicon / field | Tier |
|---|---|---|
| Account.Name | `com.etzhayyim.apps.opensaas.salesforce.account.name` | 1 |
| Account.Industry → ISIC rev4 lookup | `.industry` | 1 |
| Account.AnnualRevenue → band | `.annualRevenueJpyBand` | 1 (exact → Tier 3) |
| Contact.Email → `sha256(lower)` | `.emailHash` + raw to Tier 3 | 1/3 |
| Contact.Phone → `sha256(E.164)` | `.phoneHash` + raw to Tier 3 | 1/3 |
| Lead.Status (Open/Working/…) | `.status` (new/contacted/qualifying/…) | 1 |
| Opportunity.StageName | `.stage` | 1 |
| Opportunity.Amount (JPY) | `.amountJpy` + `.amountBand` | 1 |
| Opportunity.CloseDate | `.closeDate` | 1 |
| Case.Status / Priority / Origin | `.status` / `.priority` / `.origin` | 1 |
| Task/Event/EmailMessage | `com.etzhayyim.apps.opensaas.salesforce.activity` with `source=import` | 1 |
| User (22 seats) | seat DID + WebAuthn passkey | identity |

Rule: any field not in the map table is dropped, not guessed. Customer reviews the dropped-field list before proceeding (target: ≤ 3% drop).

### Saturday 00:00–12:00 — ingest
- Run `etzhayyim opensaas migrate sfdc --in sfdc_export.zip --map migration/map.jsonl --tenant did:web:acme.opensaas.etzhayyim.com --parallel 8`.
- Ingest order (matters — foreign keys resolve in-order):
  1. Users → seat DIDs (WebAuthn enrollment email queued, passkeys set Monday).
  2. Accounts (`createRecord` → `com.etzhayyim.apps.opensaas.salesforce.account`).
  3. Contacts (hashed + Tier-3 stash in one vault write per contact).
  4. Leads.
  5. Opportunities (skip activities; they derive from later stage-change events).
  6. Cases.
  7. Historical Activities → `activity` records with `source=import` (not derived).
- **Resumability**: each batch writes a content-addressed manifest (`sha256(batch.jsonl)` → B2). Re-running with the same manifest key is a no-op. Weekend power loss → `migrate --resume` picks up.

### Saturday 12:00–18:00 — derivation warm-up
- Replay the last 6 months of Salesforce stage transitions → triggers the `derive` rule in `kotodama.jsonld` (opportunity stage-change → activity). This seeds `activity` rows so Monday morning's pipeline review sees history.
- Start RisingWave MV `mv_opensaas_salesforce_pipeline_by_stage` and wait for steady-state (<100ms freshness, usually <5min).

### Saturday 18:00–Sunday 12:00 — reconciliation
- `etzhayyim opensaas reconcile --against sfdc_export.zip`:
  - Account count match: ±0 (hard fail if mismatch).
  - Contact count match: ±0.
  - Opportunity pipeline JPY sum: ±¥10,000 (rounding in band conversion).
  - Case open count: ±0.
  - Activity count: tolerance ±1% (derived vs. imported ambiguity is expected).
- Diff report goes to customer; they sign off in writing before Sunday 18:00.

### Sunday 18:00–Monday 08:00 — integration wiring
- SAP S/4 → open-salesforce: inbound webhook → `createRecord(com.etzhayyim.apps.opensaas.salesforce.opportunity)` on win, updates `account.type` to `customer-direct`.
- HubSpot Marketing → `createLead` XRPC with `source=web-form` and pre-hashed email.
- Outbound: subscribe a BI Worker to `com.etzhayyim.apps.opensaas.salesforce.*` commit stream → customer's BigQuery (they keep their existing dashboards).

### Monday 08:00–09:00 — seat activation
- Bulk-mail 22 enrollment links (from Tier-3 vault — *not* from the AT record). Each seat completes WebAuthn registration → passkey stored in their device Keychain / authenticator. Seat DID activates on first passkey auth.
- VP Sales runs the smoke script: `listPipeline`, open top 5 opportunities, change stage on one deal → sees `activity(kind=stage-change)` appear in under 200ms.

## Failure modes we've pre-documented
- **Email not uniquely hashable** (duplicates, role mailboxes): dedupe on `sha256(lower(email)) + sha256(accountName)`; manual review queue capped at 2% of contacts (~3k for Acme).
- **Stage name customisation**: if the customer has >7 custom stages, we add a `stageAlias` field to their tenant's `opportunity` extension record; derive rule sees both.
- **Activity spam from import**: if historical Activities > 500k, we write them to Iceberg cold tier directly (not RisingWave hot MV). UI shows them via `at://` deep-link on demand.
- **Weekend abort**: `migrate --rollback` deletes all records with `created_at >= <migration-start-iso>` from the tenant DID. Zero cross-tenant impact because tenant = DID.

## What this forces the SOW (03) to contain
- Named weekend window (Fri 18:00 local → Mon 09:00 local) with a single on-call engineer from us + named customer DRI.
- Reconciliation sign-off clause before integration wiring begins (i.e., we don't wire SAP until the pipeline totals match).
- 30-day post-migration hyper-care retainer (separate line item — feeds pricing node 08).
- Explicit *exclusion*: custom Apex code, custom Visualforce pages, Sales Cloud Flows → out of scope; customer must port or drop before migration weekend.
- Data-residency attestation: every record written to the tenant DID's CF account / RisingWave region matches the SOW's declared region (JPN or EUR).
