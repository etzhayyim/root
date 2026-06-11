# Case study — Acme Robotics K.K. replaces Salesforce Sales Cloud with open-salesforce (imagined closed-won)

> Reverse-topo node 01 / 13. This is the *end state* — nothing in the sales funnel depends on it existing; every earlier artifact must eventually produce this. It is written first so every subsequent piece (onboarding, SOW, POC, demo, pricing, landing) can be back-solved to deliver exactly this outcome.

## Customer
- **Acme Robotics K.K.** — industrial robotics OEM, 480 employees, Nagoya HQ, FY26 revenue ¥8.2B.
- CTO-sponsored, VP Sales as economic buyer, 22 seats on Salesforce Sales Cloud Enterprise.
- Pre-existing spend: **¥14.8M / year** (license only; implementation partner retainer separate).

## Trigger
- Salesforce contract auto-renewal quote arrived +18% YoY.
- Procurement asked CTO to evaluate OSS / self-hosted alternatives that satisfy `個人情報保護法 (APPI)` + EU GDPR for their EU subsidiary.
- VP Sales had a parallel complaint: AI features locked behind Einstein GPT add-on, couldn't expose their own LLM fleet (Murakumo) inside the CRM.

## Why open-salesforce won
1. **PII topology matched APPI/GDPR out of the box.** Tier-1 AT records carry `emailHash` / `phoneHash` only; raw PII lives in per-tenant Tier-3 Preferences with `com.etzhayyim.consent.*` + Art-17 cascade purge. Legal signed off in 3 weeks (vs. 9-month Sales Cloud residency review).
2. **Own LLM at the seat level.** Each seat DID (`did:web:acme.opensaas.etzhayyim.com:seat:ae-03`) invokes Murakumo directly via Agent-to-Agent (`kotodama.Invoke`). No Einstein add-on line item.
3. **Activity log is federation-grade, not screenshot-grade.** `com.etzhayyim.apps.opensaas.salesforce.activity` is derived from opportunity.stage / case.status / conversion commits; every activity row is cryptographically tied to the commit that caused it, so audit trail is content-addressed, not "trust the CRM".
4. **Price.** ¥3.6M / year flat for unlimited seats on the tenant's own Worker + RisingWave.

## Deal shape
| Line item | Value |
|---|---|
| Platform fee (open-salesforce, 3 yr) | ¥10.8M |
| Migration services (Sales Cloud export → W Protocol records) | ¥6.2M one-time |
| Integration (SAP S/4 + HubSpot Marketing) | ¥3.4M one-time |
| Reference-customer discount (logo rights + 2 case-study references per year) | −¥1.8M |
| **Total year-1 ACV** | **¥18.6M** |
| **Net vs. Salesforce renewal** | **−¥14.6M over 3 yr** |

## Proof points the customer cited publicly
- "We moved 148k contacts, 6.2k opportunities, 23k cases across one weekend. Content-addressed blob store meant migration was resumable."
- "The CRM is a tenant DID, not a hostname. When our EU sub spun up, it was a 4-line `etzhayyim deploy`, not a new org negotiation."
- "Einstein replacement cost ¥0 — our own Murakumo fleet already had capacity."

## What this case study forces earlier artifacts to do
- **Onboarding (02)** must be weekend-migratable for 100k+ contacts + 5k+ opportunities.
- **SOW (03)** must separate platform / migration / integration cleanly.
- **POC (04)** must prove APPI + GDPR posture in under 21 days.
- **Discovery (05)** must qualify on: (a) Salesforce renewal quote trigger, (b) LLM-in-CRM appetite, (c) data residency obligation.
- **Content (06)** must have a deep-dive on "content-addressed activity log" and "per-seat LLM".
- **Outbound (07)** must hook on Salesforce renewal invoice timing (T-90 to T-60 days).
- **Pricing (08)** must land under ¥4M for a mid-market (~500-seat-equivalent) tenant flat.
- **Demo (09)** must show lead→convert→stage-change→derived-activity in one flow, live.
- **Landing (10)** must open with migration-off-Salesforce, not "we built a CRM".
- **Messaging (11)** must anchor on: PII topology / own-LLM / federation-grade audit / flat price.
- **Positioning (12)** = the category ("sovereign CRM") before the product.
- **ICP (13)** = Japan / EU mid-market with a Salesforce renewal in the next 6 months AND a material own-LLM plan.

## Decision
- Next tick (T+10m) produces the onboarding playbook that *delivers* the migration claim above.
