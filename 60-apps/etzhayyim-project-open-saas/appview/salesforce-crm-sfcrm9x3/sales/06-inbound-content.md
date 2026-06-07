# Inbound content plan — open-salesforce

> Reverse-topo node 06 / 13. Back-solves 05 (discovery script). Each asset below is a URL the AE sends during or after discovery, or that the buyer finds via search before discovery ever happens. No "top 10 CRM tips" listicles; every piece is a load-bearing artifact for a real objection.

## Publishing principles
- **Primary surface**: `https://salesforce.opensaas.etzhayyim.com/` root docs + `/at/` deep-links to example records so every post can link to a *live* lexicon-shaped artifact.
- **Secondary surface**: `atproto.etzhayyim.com` blog (AT Record-native; every post is itself `app.bsky.feed.post` + a `com.etzhayyim.apps.opensaas.site.article` record, dog-fooding the protocol).
- **No gating** on technical content. Gate only the pricing calculator (email required) and the POC Agreement draft.
- **Language**: JP + EN for every pillar piece. JP first when the topic is APPI / Japan sovereignty; EN first when it's GDPR / federation.
- **Cadence**: 1 pillar / 2 weeks, 1 short / week. Sustained for 2 quarters before judging SEO pull.

## Pillar 1 — Content-addressed activity log (2500–3500 words, + live examples)

**URL**: `/docs/activity-log-content-addressed`
**Objection it answers**: Q2 "what killed alternatives" → Salesforce's audit log is mutable at the DB layer; open-salesforce isn't.
**Outline**:
1. What "audit log" means in Sales Cloud (rows in `FieldHistory` + Setup Audit Trail) and why a DBA with write access breaks both.
2. W Protocol commit = Merkle DAG + signed by the seat DID's key. Immutable by construction.
3. How the `derive` rule in `kotodama.jsonld` emits `com.etzhayyim.apps.opensaas.salesforce.activity` with `source=derived-stage-change`, and the commit CID is embedded. Link to a live record: `at://demo.opensaas.etzhayyim.com/com.etzhayyim.apps.opensaas.salesforce.activity/act-example`.
4. Regulator demo: export 7y of activity as OCEL 2.0 → Parquet on Iceberg, verifiable offline.
5. "Things Einstein forecasts can't explain and we can" — 3 worked examples.

## Pillar 2 — Per-seat LLM in the CRM (3000–4000 words, + 2-min video)

**URL**: `/docs/per-seat-llm-murakumo`
**Objection it answers**: Q4 "own-LLM plan" → Einstein GPT is a line item; Murakumo is a capability.
**Outline**:
1. Why "CRM AI" is the wrong frame (org-wide model, opaque prompt policy). Right frame: seat DID = agent DID, the seat invokes the model.
2. `kotodama.Invoke(did, method, params)` from inside an XRPC handler scoped to the seat DID. Code snippet, ≤30 lines.
3. Prompt privacy: Murakumo is a tenant-configurable fleet (`did:web:murakumo.etzhayyim.com:fleet:<tier>`). Swappable to OpenAI / Anthropic / in-house via one `ConfigPut`.
4. Worked flow: "Summarise this opportunity" in the CRM UI → LLM pulls `opportunity` + linked `activity` rows via `listPipeline` + `G().match(...)` → returns markdown. 2-min screen capture.
5. Cost model — per-invocation vs. per-seat-per-month Einstein GPT. Calculator link (Pillar 5).

## Pillar 3 — APPI + GDPR posture packet (downloadable PDF + HTML)

**URL**: `/docs/posture-appi-gdpr`
**Objection it answers**: Q5 "named regulation" + POC Track 2 gate. The customer's Security reviewer downloads this *before* the POC kicks off.
**Contents**:
- Tier-1 vs Tier-3 PII topology diagram — which fields are which, with lexicon file links.
- Art-17 / APPI §30 cascade purge flow: input → `POST /api/vault/purge` → Tier-3 delete + Tier-1 `emailHash` rotation → `activity(kind=note)` attestation. Signed JSON sample.
- Data-residency attestation format: `etzhayyim opensaas attest --tenant <did> --region <JPN|EUR>` output with colo IDs + RisingWave replica regions.
- Processor / Controller matrix aligning MSA §5 with APPI § and GDPR Art.
- Sub-processor list: Cloudflare (Worker + B2), RisingWave Cloud (PG + Hummock), Linode LKE (region-pinned), Cloudflare Vectorize. Named colos per region.
- Incident response timeline (72h notification).

## Pillar 4 — Salesforce → open-salesforce field map (interactive HTML table + JSONL export)

**URL**: `/docs/map-salesforce-to-opensalesforce`
**Objection it answers**: Q6 + Q7 pre-work. Customer Salesforce admin can prep the migration before meeting us.
**Contents**:
- Full map table (extends Schedule C-1 from node 03): 200+ SF fields → lexicon paths.
- Per-row: Tier classification, default drop/port choice, rationale, example value transformation (e.g. `Account.AnnualRevenue=8200000000` → `annualRevenueJpyBand=u10b` + Tier-3 raw).
- "Paste your object-field list, get back a dry-run map" mini tool — runs entirely client-side, no upload, no PII leakage.
- Downloadable `map.jsonl` ready for `etzhayyim opensaas migrate --map`.

## Pillar 5 — Flat-price calculator (single-page web app)

**URL**: `/pricing/calculator`
**Objection it answers**: Q3 seat/WAU ratio. Customer drops in (a) current Salesforce ACV, (b) seats, (c) WAU, (d) Einstein add-on status, (e) data-residency region → gets a 3-year TCO delta vs. open-salesforce flat plan (filled in node 08).
**Gating**: email for the PDF export; calculator itself is public.
**Outputs**:
- 3-year spend chart.
- Payback period on migration fee.
- "Forward this to your CFO" link — landing URL pre-fills org name, seats, and a calendar booking link to the AE.

## Short-form cadence (weekly)

| Week | Format | Topic | Primary anchor |
|---|---|---|---|
| W1 | 300w blog | "What `createLead` rejects, and why that's the feature" | Pillar 3 |
| W2 | 600w blog | "The `listPipeline` MV — why streaming ≠ eventual-consistent in our stack" | Pillar 1 |
| W3 | 2-min video | `convertLead` in the UI, 3 records written atomically, one derived activity | Pillar 4 |
| W4 | 300w blog | "Why we don't let raw email into Tier-1" | Pillar 3 |
| W5 | 1200w blog | "Salesforce Flow → our `derive` rule: a port in 40 lines of JSONLD" | Pillar 4 |
| W6 | 600w blog | "Per-seat LLM auth: the seat DID, not an API key" | Pillar 2 |
| W7 | 2-min video | Art-17 purge rehearsal, live, against a seeded tenant | Pillar 3 |
| W8 | 300w blog | "What the `activity` derive rule emits on `closed-lost`, and what it doesn't" | Pillar 1 |

## Distribution beats (paid and owned)

- **AT Protocol firehose**: every pillar post is an AT Record; any follower (Bluesky / federated AppView) sees it. No ad spend on this channel.
- **Bluesky sponsored**: ¥`<seed budget>` / month targeting JP SaaS + EU sovereignty tags.
- **LinkedIn**: AE personal posts syndicate pillars to the ICP industries. Company page posts are throwaway.
- **Industry lists**: 3 niche newsletters (JP RevOps, EU CIO, APAC Sec) — paid sponsorships on pillar launches.
- **SEO targets**:
  - "Salesforce 代替 OSS" / "Salesforce 移行 APPI"
  - "CRM data residency EU self-hosted"
  - "Own LLM inside CRM"
  - "Salesforce renewal negotiation" (commercial-intent keyword, paid)

## Attribution

- Landing URLs use UTM + a short-form AT URI deep-link so the inbound AE can see the exact pillar that pulled the lead.
- Every form POST lands as `com.etzhayyim.apps.opensaas.salesforce.createLead` with `source=web-form` and `campaignId=<pillar-id>`.
- Weekly RevOps review: which pillar yielded which discovery-call green column in the qualification sheet.

## What this forces the outbound sequence (07) to do

- Outbound email must **link to the exact pillar** that matches the industry / regulation / renewal-quarter of the target — no generic "learn more" CTAs.
- Every sequence has a "send the APPI or GDPR posture packet" beat (step 2 or 3), because it's the highest-asymmetry ask: zero-cost to us, high-value to Security.
- The last beat of every sequence is the pricing calculator — because the AE wants to walk into discovery knowing what TCO the buyer has already simulated.
- Cadence timing is pegged to the target's **Salesforce renewal quarter**, derived from their fiscal year-end (public) — so outbound fires into the T-90..T-180 window the discovery script qualifies on.
