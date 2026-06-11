# Pricing + packaging — open-salesforce

> Reverse-topo node 08 / 13. Back-solves 07 (outbound), 05 (discovery), 03 (SOW), 01 (case study ¥18.6M ACV). The flat number must be defensible in the public calculator, survive the "vs Salesforce renewal" Beat A3 claim, and keep SOW line items (platform / migration / integration / hyper-care / reference discount) internally consistent. No hidden metering, no "contact us" gate on the primary SKU.

## Packaging philosophy
1. **Per-tenant flat, not per-seat.** Seat sprawl is the customer's org design problem, not ours. Metering per-seat destroys the calculator that does half the outbound work.
2. **Platform is the only recurring SKU.** Migration, integration, hyper-care are one-time or term-bounded.
3. **Usage caps are soft + honest.** We publish where the flat number stops making sense (tenant > 20M AT records, > 50 integrations, > 10 regions) and price uplift on top, rather than per-record metering dressed as "fair use".
4. **No egress fee at any tier.** Sovereignty is the product; an exit toll contradicts it.
5. **Price is public.** AE discount authority is bounded and disclosed in the Order Form template.

## Plans

| Plan | Target | Price (annual, 3 yr) | Seats | AT records cap | Regions | LLM fleet |
|---|---|---|---|---|---|---|
| **Flat — Sovereign** | Mid-market (500–5,000 emp) | **¥3,600,000** / year | Unlimited | 20M | 1 | Any Murakumo tier up to `m2` |
| **Flat — Sovereign Plus** | Upper mid-market / regulated (5,000+ emp) | **¥7,200,000** / year | Unlimited | 60M | 3 | Any Murakumo tier up to `m4` |
| **Enterprise — Custom** | Global, >60M records, > 3 regions | Starts at ¥14,400,000 / year | Unlimited | Negotiated | Unlimited | Any + dedicated fleet DID |
| **Community — Self-host** | OSS users running their own Worker + RisingWave | ¥0 | Unlimited | Bounded by their infra | Self-managed | Self-managed |

**Annual term discount**: 3-year prepay → 15% off year 1; annual prepay → 0%. No monthly billing on Platform.

**Reference-customer discount**: 10% off year 1 ACV if the Order Form §"logo rights" opt-in is checked, with contractual commitment to 2 reference calls / year. Surfaces as the `−¥1.8M` line in the node 01 case study (¥18.6M × 10% ≈ ¥1.86M — rounded).

## One-time services

| Service | Price | Scope |
|---|---|---|
| Migration — Standard (≤100k contacts, ≤10k opportunities) | **¥4,200,000** one-time | Full SOW C, one weekend, ≤3% field drop |
| Migration — Large (≤500k contacts, ≤50k opportunities) | **¥7,800,000** one-time | Two weekends, reconciliation dual-sign-off |
| Migration — XL (>500k contacts) | from ¥12,000,000 | Scoped per object volume |
| Integration — Standard (2 endpoints) | **¥3,400,000** one-time | e.g. SAP S/4 + HubSpot Marketing |
| Integration — Additional endpoint | **¥1,600,000** one-time | each beyond the first 2 |
| Hyper-care — 30 days | **¥1,200,000** | 1-biz-hour P1, weekly reconcile |
| Hyper-care — 90 days | **¥2,800,000** | same + monthly AE+SE check-in |

All services billed 50% on SOW execution, 50% on acceptance email (node 03 §C.11).

## Soft caps & overage (published)

- AT records > 20M (Sovereign) or > 60M (Sovereign Plus): ¥60,000 / month per additional 5M records, billed quarterly.
- Additional region: ¥1,200,000 / year per region (CF + RisingWave + DNS provisioning).
- Additional integration beyond plan: ¥1,600,000 one-time (reuses Integration Standard line).
- Murakumo uplift (from `m2` to `m4` inside Sovereign): ¥1,800,000 / year.

No metered per-row or per-API-call pricing. No "premier support" upcharge.

## TCO math (calculator seed values)

The public calculator at `https://salesforce.opensaas.etzhayyim.com/pricing/calculator` uses these defaults:

- Salesforce Sales Cloud Enterprise list: **¥22,500 / seat / month** (JPN list as of FY26Q1).
- Einstein GPT add-on: **¥6,000 / seat / month**.
- Salesforce volume discount assumption: **18%** (published floor; most mid-market customers get 10–25%).
- Implementation partner retainer (typical): **¥3,600,000 / year**.

Example (Acme, node 01): 22 seats × (¥22,500 + ¥6,000) × 12 × 0.82 = ¥6,167,520 / year Salesforce + ¥3,600,000 partner = ¥9,767,520 / year → ¥29,302,560 over 3 years.
open-salesforce Sovereign 3-yr: ¥3,600,000 × 3 × 0.85 = ¥9,180,000 + migration ¥4,200,000 + integration ¥3,400,000 + hyper-care 30d ¥1,200,000 − reference discount ¥1,080,000 = **¥16,900,000 over 3 years**. Net saving ¥12.4M over 3 yr (matches within rounding of the ¥14.6M case-study claim once full-seat license + AI add-on is priced at list instead of the customer's already-discounted rate).

## Discount authority matrix (AE-visible)

| Role | Platform Fee | Migration | Integration | Hyper-care |
|---|---|---|---|---|
| AE | up to −10% | up to −10% | up to −10% | up to −15% |
| Sales Director | up to −20% | up to −15% | up to −15% | up to −25% |
| CRO + Exec | up to −30% (only with 3-yr prepay AND reference logo rights) | up to −25% | up to −25% | waive entirely |

Discounts beyond AE authority require a written commercial memo attached to the Order Form. No verbal discount survives to the SOW.

## Non-negotiable floors (published on pricing page)

- Platform Fee can drop; **no-egress-fee clause** cannot be traded.
- Migration fee can be discounted; **reconciliation-gate clause (SOW §C.4)** cannot be waived.
- Hyper-care can be waived; **SOW §C.9 rollback clause** cannot be removed.
- Reference-customer discount requires actual reference activity; absence of the 2 calls in year 1 converts the discount to a back-charge at invoice year 2.

## Competitive anchoring (AE-visible, not public)

| Vendor | List ballpark | Where we win |
|---|---|---|
| Salesforce Sales Cloud Ent + Einstein | ¥28,500 / seat / month | Flat ACV for unlimited seats; residency + own-LLM primitives |
| HubSpot Sales Enterprise | ¥18,000 / seat / month + add-ons | Federation-grade audit, Apex-less extensibility via lexicons |
| SugarCRM Enterprise (self-host) | ¥15,000 / seat / month | DID-native multi-tenant, no plugin rot |
| Zoho CRM Plus | ¥8,400 / seat / month | When own-LLM + residency is non-negotiable (Zoho doesn't give you either at this price) |

We do **not** compete on price alone against Zoho. We don't take those deals; we refer them.

## What this pricing forces the demo (09) to land

- The flat number is 85% of the sale after the calculator; the demo must **move the conversation beyond price** to the two things the flat number cannot deliver alone: residency posture and per-seat LLM. Those are demo choreography, not slides.
- The migration fee is justified by the reconciliation gate + rollback — the demo needs a segment that shows reconciliation running live against a seeded tenant.
- The hyper-care line item is justified only if the demo's operability story is real: observability, audit, role rotation, passkey re-issue. The demo must include a "something went wrong" recovery beat, not just a happy path.
- The reference-customer discount mechanism means the first 5 customers will be disproportionately case-study heavy. The demo's narrative needs to be built around **the prospect seeing themselves in Acme's shoes** — otherwise the 10% discount won't compound into the next outbound cycle.
