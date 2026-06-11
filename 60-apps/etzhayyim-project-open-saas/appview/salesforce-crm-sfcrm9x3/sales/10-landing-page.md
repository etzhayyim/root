# Landing page copy — open-salesforce

> Reverse-topo node 10 / 13. Back-solves 09 (demo): the page hands Security, RevOps, and the VP the next-click they each need so the demo is a formality, not a convince-step. Single URL `https://salesforce.opensaas.etzhayyim.com/`. Above-the-fold must load in <1s on 4G; three primary CTAs serve three primary personas; one secondary URL (`democo.opensaas.etzhayyim.com`) lets anyone self-serve the demo.

## H1 + subhead (above the fold, 6 seconds of attention)

**H1**: The Salesforce alternative your DPO signs off before your CRO does.

**Subhead**: open-salesforce is a CRM on AT / W Protocol. Tenant = DID. PII split between a Tier-1 federation-ready record and a Tier-3 residency-pinned vault. Seat = agent. Flat price, no per-seat, no Einstein GPT line item.

**Primary CTA (×3, side by side)**:
- **See a real record** → `/at/democo.opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.opportunity/opp-demo-q3`
- **Download posture packet (APPI + GDPR, PDF 14pp)** → `/docs/posture-appi-gdpr.pdf`
- **Run the TCO calculator** → `/pricing/calculator`

**Secondary CTA line**: "Or just log in to the public demo: [democo.opensaas.etzhayyim.com](https://democo.opensaas.etzhayyim.com/) — passkey-less guest mode, pre-seeded pipeline, auto-rolls back nightly."

## Section 1 — The three claims, each with a one-click proof

### Claim A: Convert a lead atomically, auto-log the activity
One click writes `account` + `contact` + `opportunity` + updated `lead` + derived `activity(kind=conversion)` in a single commit pipeline pass. Zero app-layer orchestration. No Flow, no Apex.

- **Proof link**: live record `/at/democo.opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.activity/act-demo-conv-001`
- **Micro-copy**: "Paste that URI into any AT Protocol client. The CRM isn't the only thing that can read it."

### Claim B: Your CRM data is where you say it is, and you can prove it
Run `etzhayyim opensaas attest --tenant <your-did> --region JPN` (or EUR) → signed JSON lists every CF colo, RisingWave replica, vault KMS region that touched your data in the last 7 days. Built for APPI §22-28, GDPR Art 44, and your next ISMAP / SOC2 audit.

- **Proof link**: example attestation `/docs/examples/attest-democo.json`
- **Micro-copy**: "If the attestation ever shows a region outside your Order Form, we owe you a credit."

### Claim C: LLM is a seat capability, not an add-on SKU
The seat DID (`did:web:<tenant>.opensaas.etzhayyim.com:seat:<role>-<nn>`) is itself the agent identity. `kotodama.Invoke(murakumoFleetDid, ...)` runs under that identity. Swap Murakumo for your own LLM (Azure OpenAI, Anthropic, in-house GPU) with one `ConfigPut`.

- **Proof link**: Pillar 2 deep-dive `/docs/per-seat-llm-murakumo`
- **Micro-copy**: "Your Einstein GPT line item is ¥6,000 / seat / month. Our LLM line item is ¥0."

## Section 2 — Who this is actually for

Three-column persona fit, each column ends in the CTA that persona needs.

| If you're… | We assume you care about… | Your next click |
|---|---|---|
| **VP Sales / CRO** | Renewal quote is up, Einstein add-on pushing another ¥6,000 / seat / month, seat/WAU ratio is 2:1 | TCO calculator |
| **RevOps / Salesforce admin** | Flow sprawl, Apex tech debt, field-level audit that your auditor doesn't trust | Interactive field map `/docs/map-salesforce-to-opensalesforce` |
| **CISO / DPO** | APPI re-opened per tenant, GDPR Art 44 transfer mechanism, Art-17 cascade deletion evidence | Posture packet PDF |

Each column has a 30-word mini-case ("A 720-seat logistics co. migrated in one weekend; reconciliation gate was a ±¥6,200 pipeline delta, signed off by Sunday 16:00.") — no logos until we have contractual rights.

## Section 3 — What moved off Salesforce, plainly

Tight, honest inventory. No "we're better at everything" bravado.

**Supported on day 1**: Account, Contact, Lead, Opportunity, Case, Activity, User/seat, pipeline reports, field history, basic email integration (SMTP), webhook-based integration to SAP / HubSpot / BI tools, WebAuthn auth.

**Replaced, not ported**: Salesforce Flow → `derive` rule in `kotodama.jsonld` (JSONLD, not a designer GUI yet — on roadmap Q3); reports → `listPipeline` + tenant-scoped SQL on RisingWave MV; AppExchange → capability workers registered per tenant DID.

**Out of scope (today, honestly)**: Apex custom code, Visualforce UI, Lightning App Builder, Sales Cloud Einstein forecasting. If your org relies on these, we'll say so on the discovery call.

**Roadmap (next 2 quarters, dated, not vague)**: Flow-designer UI (Q3), Einstein-equivalent forecasting via Murakumo fleet fine-tune (Q4), Apex-lite extensibility via WASI capability WIT (Q4 preview).

## Section 4 — Pricing (flat, public, calculator-backed)

- **Sovereign** ¥3,600,000 / year flat — 500–5,000 employees, 1 region, up to Murakumo `m2`.
- **Sovereign Plus** ¥7,200,000 / year flat — upper mid-market / regulated, 3 regions, up to Murakumo `m4`.
- **Enterprise** from ¥14,400,000 / year — global, >60M records.
- **Community** ¥0 — self-host. Full source, full lexicons.

3-yr prepay → 15% off year 1. Reference-customer logo → additional 10% off year 1. No egress fee at any tier.

**CTA**: "Run the 3-year TCO against your current Salesforce quote" → calculator.

## Section 5 — FAQ (written in the voice of the buyer, not the vendor)

- **"Can I host this myself?"** Yes. `etzhayyim deploy` to your Cloudflare account; point your own RisingWave cluster; keep your DID on your own DNS. We can still operate it for you if the Order Form says so.
- **"What happens if etzhayyim the company disappears?"** Your tenant DID, your records, your Worker, your vault keys are all yours. The Community SKU is the permanent fallback; the lexicons are CC-BY-4.0, the code is AGPL-3.0 with a permissive commercial grant for operators.
- **"Can we move back to Salesforce if it doesn't work?"** Yes. Export every record in AT Protocol JSON + Iceberg Parquet on 30 days' notice. No egress fee.
- **"Do you support our SSO?"** SAML + OIDC on the tenant's Auth Worker; WebAuthn passkey is the seat-level primary. No password fallback.
- **"Can we use a different LLM?"** Any HTTP-invocable LLM fleet can be bound via one `ConfigPut`; OpenAI / Anthropic / Azure / your GPU cluster all fit.
- **"How does federation work?"** Tenant DID records are federable AT records. You can opt out per collection. Most customers opt out for `case` and opt in for `activity(kind=stage-change)` (anonymised).
- **"Where's the pricing catch?"** Soft caps on records, regions, integrations are published on `/pricing`. Beyond those → Enterprise SKU, no surprise invoice.

## Section 6 — Proof (load-bearing footer)

- Link to the lexicon repo: `https://github.com/etzhayyim/open-saas/tree/main/00-contracts/lexicons/com/etzhayyim/apps/opensaas/salesforce`.
- Link to the Cloudflare Worker source and `kotodama.jsonld`.
- Link to the atproto.etzhayyim.com public firehose — anyone can verify our own dogfooding (we run open-salesforce internally).
- Link to the `listPipeline` spec JSON.
- Sub-processor list, uptime history, most recent incident post-mortem.

## Analytics + lead capture

- Every form on the page → `POST /xrpc/com.etzhayyim.apps.opensaas.salesforce.createLead` with `source=web-form` and `campaignId=<section-id>`.
- Calculator CTA emits a synthetic lead with `scoreBand` derived from calculator inputs; RevOps sees the scoreBand distribution in `listPipeline` without seeing the raw PII (it's hashed before the XRPC).
- Posture-packet download gated by email, hashed before persistence, raw email goes to Tier-3 vault directly (dogfood).

## What this landing page forces the messaging pillars (11) to commit to

- A single sentence per pillar that **survives being quoted out of context** by a buyer's VP forwarding the page to Security.
- Pillars must map 1:1 to the three primary CTAs (record, posture, calculator) — otherwise the page loses copy-narrative alignment.
- The "flat price" pillar cannot be hedged with "*starting at*" or "call for quote" — because the page's Section 4 already publishes the number.
- The "seat = agent" pillar has to be the defensible differentiator against the "we use OpenAI" category — Messaging needs to specify the one-sentence distinction.
- Messaging has to commit to a **no-logo-lying** rule: Section 2 mini-cases become logo blocks only when a customer has signed Order Form §logo rights, never before.
