# Contract / SOW template — open-salesforce

> Reverse-topo node 03 / 13. Back-solves 02 (onboarding). Every clause here exists to make the weekend migration, reconciliation sign-off, data-residency attestation, and 30-day hyper-care *legally executable*. Customer counsel should be able to redline this in ≤2 rounds.

Template is splittable into three instruments so procurement / legal can route in parallel: (A) **MSA**, (B) **Order Form**, (C) **SOW-Migration**. Node 08 (pricing) fills the $ cells.

---

## A. Master Services Agreement (MSA) — open-salesforce

**Parties.** etzhayyim Co., Jp. ("Provider") and `<Customer legal name>` ("Customer").

**1. Definitions**
- **Tenant DID**: the `did:web:<slug>.opensaas.etzhayyim.com` identifier provisioned for Customer. Controls all Customer data written to `com.etzhayyim.apps.opensaas.salesforce.*` collections.
- **Seat DID**: a path-based DID `did:web:<slug>.opensaas.etzhayyim.com:seat:<role>-<nn>`. One per named human user.
- **Tier-1 Data**: records under `com.etzhayyim.apps.opensaas.salesforce.{account,contact,lead,opportunity,case,activity}`. Public within the tenant, federation-ready.
- **Tier-3 Data**: raw PII + exact financials stored in per-tenant Preferences vault (AES-KW + device-key-unwrapped). Never present in Tier-1 AT records.
- **Content-addressed activity**: `activity` records emitted by the PDS commit pipeline `derive` rule. Each row is cryptographically tied to the `opportunity` / `case` / `lead` commit that caused it.

**2. Grant.** Provider grants Customer a non-exclusive, non-transferable right to access `https://salesforce.opensaas.etzhayyim.com/` and the underlying XRPC methods (`createLead`, `convertLead`, `listPipeline`, all `com.atproto.repo.*` scoped to the Tenant DID) for Customer's internal business use.

**3. Data ownership.** Customer owns all content written under the Tenant DID. Provider owns the open-salesforce software, lexicons, and derive-rule engine. Export obligation: on termination, Provider delivers, within 30 days, a repo-archive dump of every record under the Tenant DID in AT Protocol JSON + Iceberg Parquet. No egress fee.

**4. Data residency.** Provider runs the Tenant DID's Worker and RisingWave shard in the region named in the applicable Order Form (JPN or EUR). Changing region requires a written amendment and a re-migration.

**5. PII / APPI / GDPR.** (a) Tier-3 vault lives in Customer's region. (b) Provider is a Processor; Customer is Controller. (c) Art-17 / APPI §30 deletion: Customer calls `POST /api/vault/purge` with a subject identifier → cascade purge across Tier-3 vault + Tier-1 hashed indices reset within 72h, attestation emitted as an `activity(kind=note, source=manual-ui)` signed by the executing seat DID.

**6. Security.**
- Seat authentication: WebAuthn passkey only. No password fallback.
- Secrets (Salesforce import credentials, SAP webhook tokens, Murakumo API keys): `etzhayyim vault` zero-knowledge store, never in env vars.
- Audit log: every XRPC call hits the append-only `com.etzhayyim.audit.*` stream, retention 7y, exportable as OCEL 2.0.

**7. Uptime.** 99.5% monthly for `https://salesforce.opensaas.etzhayyim.com/`. Service credit: 5% of monthly fee per 1% miss, capped at 50%. Scheduled maintenance windows (Sun 02:00–04:00 local) excluded.

**8. LLM use.** If Customer enables per-seat LLM, invocation targets the Murakumo fleet DID configured in the Order Form. Provider does not retain Customer prompt content. Customer may substitute its own LLM endpoint via `kotodama.Invoke` at any time.

**9. Limitation of liability.** Capped at 12 months of Platform Fee (not one-time services).

**10. Term & termination.** Initial term 36 months (matches pricing node 08). Either party may terminate for material breach with 30-day cure. On termination, §3 export obligation applies.

**11. Governing law.** Tokyo District Court, or for EU customers, Amsterdam under Dutch law.

---

## B. Order Form

| Field | Value |
|---|---|
| Customer legal name | `<to fill>` |
| Tenant DID | `did:web:<slug>.opensaas.etzhayyim.com` |
| Region | `JPN` \| `EUR` |
| Seats included | `unlimited` (flat plan) |
| Murakumo LLM fleet | `did:web:murakumo.etzhayyim.com:fleet:<tier>` |
| Platform Fee (annual, 3 yr) | ¥`<pricing node 08>` |
| Start date | `<YYYY-MM-DD>` |
| Co-marketing logo rights | ☐ opt-in (discount applies only if checked) |

---

## C. SOW — Migration (Salesforce Sales Cloud → open-salesforce)

**C.1 Scope.** One-time migration of Accounts, Contacts, Leads, Opportunities, Cases, Tasks/Events/EmailMessages, Users from Customer's Salesforce org into the Tenant DID, per the onboarding playbook (node 02).

**C.2 Window.** Single named weekend: **Fri 18:00 local → Mon 09:00 local**. Customer provides `sfdc_export.zip` by Thu 18:00 local (T-24h).

**C.3 Field map.** The map table in node 02 (Salesforce → W Protocol lexicon) is incorporated by reference as Schedule C-1. Any field outside the map is dropped; Customer reviews the drop list by Sat 12:00 and signs off before ingest proceeds.

**C.4 Reconciliation gate.** Integration wiring (SAP, HubSpot, BI subscriber) **does not begin** until Customer signs off the reconciliation report on Sun 18:00. Gate tolerances:
- Account / Contact / Lead / Case count: ±0.
- Opportunity pipeline JPY sum: ±¥10,000.
- Activity count: ±1% (derived vs. imported ambiguity acknowledged).

**C.5 Resumability.** All ingest batches are content-addressed (`sha256(batch.jsonl)` → B2). Provider may re-run any batch without duplication. Weekend power loss is not a breach.

**C.6 Exclusions (hard).** Custom Apex, Visualforce, Sales Cloud Flows, Salesforce-native reports, Einstein forecasts. Customer must port or drop before migration weekend.

**C.7 Personnel.** Provider: 1 named on-call engineer across the window. Customer: 1 named DRI reachable within 15 min. Escalation path per Schedule C-2.

**C.8 Acceptance.** Monday 09:00 smoke test: VP Sales (or delegated AE) runs `listPipeline` + re-stages 5 opportunities + confirms derived `activity(kind=stage-change)` rows. Acceptance email triggers the Platform Fee invoice start date.

**C.9 Rollback.** If reconciliation gate fails beyond tolerance and Customer calls rollback by Sun 12:00, Provider executes `migrate --rollback` (deletes all records with `created_at >= migration-start-iso` from the Tenant DID), waives the migration fee, and refunds any Platform Fee paid. Zero cross-tenant impact (tenant = DID).

**C.10 Hyper-care (30 days post-acceptance).** Separate retainer line item. Includes: 1-biz-hour response on P1 within JPN/EUR business hours, weekly pipeline reconciliation vs. exported BI, free seat-DID re-issuance for up to 10% of seats (lost device, etc.). Feeds pricing node 08.

**C.11 Fees.**
| Item | Amount | Timing |
|---|---|---|
| Migration services | ¥`<node 08>` | 50% on SOW execution, 50% on acceptance |
| SAP + HubSpot integration | ¥`<node 08>` | On integration acceptance |
| Hyper-care retainer (30 d) | ¥`<node 08>` | Monthly, on acceptance date |
| Reference-customer discount | −¥`<node 08>` | Net against year-1 invoice if Order Form §logo opted-in |

---

## What this SOW forces the POC (04) to prove
- APPI + GDPR posture **in writing** in ≤ 21 days — so Customer counsel has this MSA executable before the migration weekend is scheduled.
- A reconciliation report format that matches §C.4 tolerances — so the gate is mechanical, not judgmental.
- A credible data-residency attestation mechanism — so §4 isn't a promise, it's an audit artifact.
- A rollback rehearsal — so §C.9 isn't theoretical.
- A named engineer + named DRI process — so §C.7 is staffable, not a bottleneck.
