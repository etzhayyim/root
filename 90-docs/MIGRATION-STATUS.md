# etzhayyim/root — on-chain migration status (audit 2026-06-02)

Substrate posture per ADR-2605172000 (RW-free) + ADR-2606011400 (on-chain-only).
This is a point-in-time classification of all `60-apps/` projects, resolving the
previously-opaque status of the ~312 apps that carry no `MIGRATION-TODO.md`.

**Total apps: 391.** Each is bucketed by: has a clean `rw-free/` reference impl?
has a `MIGRATION-TODO.md`? still imports prohibited substrate
(`createKyselyDb` / `kysely` / RisingWave / `HYPERDRIVE` / `stripe` / `viem` /
`@atproto/api`) in its non-`rw-free` source?

| Bucket | Count | Meaning |
|--------|------:|---------|
| **A — DONE** | 82 | has a `rw-free/` on-chain reference impl |
| **B — CLEAN** | 208 | no `rw-free`, no TODO, no prohibited imports — compliant or thin stub |
| **C — NEEDS-CODEMOD** | 16 | still imports prohibited substrate → the real active backlog |
| **D — TODO-PENDING** | 55 | has `MIGRATION-TODO.md` (seed copied, codemod pending) |
| **V — VENDOR-RESIDENT** | 27 | judged correctly gftd-resident (regulated-infra axis) — no migration |

**Real remaining scope ≈ 71 apps** (C + D = 16 + 55; the 8 Tier-2 commerce apps
celler/eigyo/minpaku/omise/real-estate/shopping/supplychain/yadoya already had
rw-free impls and are reconciled into Bucket A). Buckets A + B (260) need no
further substrate work. The open-* commodity-data backlog is **fully cleared** —
every open-* app now has an rw-free impl. The loop now proceeds over the
remaining C/D apps with a per-app judgment gate (etzhayyim-front vs
vendor-resident, per the Consensys pattern + 3-axis OR-test).

> **Nuance**: an app can be in A *and* C — the `rw-free/` package is the clean
> etzhayyim-compliant reimplementation, but the project's original (pre-migration)
> `src/` may still carry RW/Stripe code that a later cleanup removes. e.g. `cpc`,
> `common-crawl`, `sanctions`, `saiban`, `kami`. For these the
> on-chain path exists; the legacy src is residual cleanup, not a missing impl.
> (`auth` was an example here previously but is now Bucket V — vendor-resident,
> no on-chain path; see below.)

## Bucket A — DONE (82, has rw-free/)

6ir, aima (data layer; AI-compute stays gftd), air-sched,
analytics (mixed split — public catalog front), anime, bim, business-person, cad,
editor, gov (mixed split — public gov reference front), itonami, jp-fiscal,
kami (catalog: eng workbench + game worlds),
kenkyusha (research-knowledge; LLM compute stays gftd), kyber-qzzg06nh,
legal-entity (public corporate registry; PII in natural-person),
collector (mixed split — public OSINT front), completer,
fleamarket (mixed split — public C2C catalog front), flight-offer, ge,
animeka (mixed split — catalog front), blockchain, bpmn, bunken,
celler, common-crawl, cpc, crowdfunding, dns, ec, eigyo,
gameka, gtin, hakkou, hanrei, hospitality (mixed split — property/roster front),
houbun, houki, houshi, ipaddress, isbn, isin,
issn, ki, kiyo, koke, legal-corpus, manga, maps, minpaku, narou, ndc, nist,
ocel, okaimono, omise, open-airplane, open-apqc, open-banking, open-cofog,
open-denki, open-gas, open-isco, open-isic, open-jpn-gov, open-network,
open-ports, open-power, open-rail, open-swift, open-unispsc, open-water,
otakiage, real-estate, sbom, shopping, supplychain, threads,
threat-intelligence, tsukuru, yadoya, yoro

(51 incl. `ec`/`crowdfunding` (2026-06-02) and the 8 open-* commodity-data apps
— open-airplane/cofog/gas/network/ports/power/rail/swift — migrated through the
one-at-a-time loop; superset of the original audit's 43.)

## Bucket V — CONFIRMED VENDOR-RESIDENT (27)

Apps judged (per-app gate) to have a **regulated-infra primary function** that
correctly stays gftd vendor under the Consensys boundary + 3-axis OR-test. These
are NOT migrated; the etzhayyim front consumes them via consent-capability.

- **auth** — axis: **Custody** (+ identity-assurance liability). Primary function
  is credential / private-key / session custody: `vertex_gftd_auth_*` (WebAuthn
  passkey credentials, account secrets) in D1 AUTH_DB, `vertex_gftd_key_*`
  (private keys, revocation) in D1 KEYS_DB, session JWT issuance. Operator-
  producible secrets ⇒ stays gftd. NOTE: the *decentralized-identity primitives*
  it also touches — did:web / did:plc issuance + `vertex_gftd_identity` public
  governance — are etzhayyim-exclusive per ADR-2605211950 and tracked as separate
  relocate targets in `/CLAUDE.md` migrations, not as an rw-free registry here.
- **accounts** — axis: **Custody** (+ identity-assurance liability). The
  account-lifecycle worker (`accounts.etzhayyim.com`, ADR-0024 split of auth):
  linked auth methods, email/OAuth provider linking, session, `/manage` UI,
  actor.score. Same regulated-infra family as `auth` — handles linked
  credentials + email PII + sessions. Currently scaffold-only (route still
  served by the auth Worker). Stays gftd. The DID-linkage primitives are
  etzhayyim-exclusive (ADR-2605211950), tracked separately.
- **air-book** — axes: **Custody + Settlement + Liability** (all three). Airline
  reservations / ticketing: PNR (passenger name records = passport / itinerary /
  contact PII), ticket issuance, IATA **BSP settlement** (fiat money settlement
  between airlines and agents), passenger reprotection (duty-of-care liability).
  No clean public-catalog layer to split out (flight schedules belong to
  air-sched). Stays gftd.
- **air-cargo** — axes: **Settlement + Liability + Custody**. Airline cargo ops:
  cargo booking, air-waybill issuance, ULD assignment, claims processing, IATA
  **CASS cargo-account settlement** (fiat), cargo-security reporting. Same family
  as air-book. Shipment-tracking is only a thin read-view over the regulated
  AWB/settlement data (could later be surfaced etzhayyim-front via consent-
  capability, but the data is custodied gftd-side). Stays gftd.
- **air-crew** — axes: **Custody + Liability**. Airline crew management: roster
  publication, pairing construction, qualification tracking, fatigue assessment,
  duty-time recording, crew assignment/travel. Crew = employee PII (names, quals,
  duty hours, fatigue); duty-time/fatigue/qualification = FTL flight-safety
  regulatory compliance. No clean public layer (qualification records bind to
  named crew). Stays gftd.
- **air-dcs** — axes: **Custody + Liability**. Departure control system: passenger
  check-in, boarding-pass issuance, baggage acceptance/reconciliation, load-sheet
  computation, APIS transmission, turnaround. Custody (passenger PII + APIS
  government border data) + Liability (load-sheet weight-&-balance flight safety,
  baggage-reconciliation security). Stays gftd.
- **air-ffp** — axes: **Settlement + Custody + Liability**. Frequent-flyer program:
  enrollment, points accrual, redemption, tier, miles transfer, purchase
  processing, partner reconciliation. Custody (member loyalty PII) + Settlement
  (miles = redeemable financial instrument: purchase/transfer/partner
  reconciliation) + Liability (points = balance-sheet deferred-revenue). Stays
  gftd.
- **air-mro** — axes: **Liability + Settlement**. Maintenance / repair / overhaul:
  work orders, component tracking, airworthiness checks, technical occurrence
  reporting, reliability reports, spare-part ordering. The airline's own
  maintenance-execution + per-tail airworthiness evidence (safety-regulatory
  duty of care) + parts procurement settlement. No clean public layer — regulator-
  published ADs/SBs would be a separate open-data app, not this internal execution
  system. Stays gftd.
- **air-ops** — axes: **Liability** (+ minor Settlement). Flight operations /
  dispatch: flight-plan filing, dispatch briefs, NOTAM/weather, technical logs,
  fuel ordering, PIREP, flight monitoring. Flight-dispatch operational control is
  safety-regulatory (dispatch authority shares legal responsibility for the
  flight) + tech-log airworthiness; fuel procurement settlement. NOTAM/weather are
  consumed public feeds, not this app's product. Stays gftd.
- **air-sms** — axes: **Liability + Custody**. Safety Management System: safety
  report submission, risk assessment, IOSA findings, regulatory report filing,
  occurrence reporting, dangerous-goods screening, security alerts. Safety-
  regulatory compliance (IOSA/occurrence/dangerous-goods) + custody of
  confidential safety-reporter identity (just-culture protection) and security-
  sensitive data. Stays gftd.
- **air-yield** — axes: **Settlement + Liability**. Revenue management / pricing:
  fare-class publication, inventory adjustment, fare filing, overbooking, group
  bookings, dynamic pricing, revenue reporting, demand forecasting. Proprietary
  revenue optimization (pricing / fare filing / revenue accounting) + overbooking
  denied-boarding consumer-protection liability. The public fare-OFFER display
  belongs to flight-offer (consumer search), not this backend engine. Stays gftd.
- **business-edge** — axes: **Custody + Settlement + Liability** (all three). The
  developer-facing edge-compute PaaS control plane (multi-tenant KV/Graph/CDN/
  PubSub/Lock/Secrets/VirtualActor): tenant API-key + Secrets-primitive custody,
  usage metering→billing, multi-tenant WASM runtime SLA. This IS the gftd
  infra-vendor ("Infura") layer of the Consensys pattern — structurally cannot
  move etzhayyim-front. Stays gftd.
- **coverage** — axis: **RisingWave**. "World coverage monitor backed by
  RisingWave live materialized views" — capabilities domain-query + analytics, an
  HTTP SPA with no record-authoring AT collections. The app IS a read-model over
  RW streaming aggregation across the whole data graph (internal operational
  observability); there is no substrate record layer to migrate. Stays gftd.
  (Publishing periodic coverage snapshots as public records would be net-new, not
  a migration of this monitor.)
- **briefing** — axis: **Custody** (PII Tier 3). WebRTC multi-actor meeting /
  live-briefing platform (transcriber/translator/recorder/summarizer; KAMI spatial
  audio; C2ISR situational awareness): briefingRoom / briefingParticipant /
  briefingPosition + transcript / summary / recording. Meeting recordings +
  transcripts + participant identity + private real-time comms are Tier-3 PII
  (server-side Preferences, never public AT records). Stays gftd.
- **cloudflare-browser-render** — axis: **Infra compute** (CF-Workers-bound). CF
  Browser Rendering backend — serverless Playwright via CF Workers `browser`
  binding + Durable Object session affinity; the execution substrate for the
  `playwright` actor. session/artifact collections are ephemeral execution state
  (DO routing, rendered-output CID). Proprietary CF-compute service, not a product
  or AT-registry — same infra-vendor class as business-edge. Already in the
  "Substrate-boundary violation flagged" list. Stays gftd.
- **crypto-asset-freeze** — axes: **Custody + Liability**. Blockchain freeze LE
  coordination (LE-only, classification=confidential): incident / freezeRequest /
  forensicTrace / exchangeNotification. requestFreeze gated on
  performer.role=law-enforcement + court-order CID + LE-agency signature.
  Confidential criminal-investigation / court-order data (never federable) +
  regulated asset-freeze enforcement liability (due-process, FATF Travel Rule).
  Stays gftd.
- **cyber-drill** — axes: **Liability + Custody + Settlement** (all three; self-
  documented VENDOR-PRIVATE). OT-cybersecurity training (WebVR walkthroughs):
  NDA-signed customer training IP, customer-specific regulatory exposure (METI /
  消防法 / 高圧ガス保安法 / GHS) + proprietary OT topology, paid SaaS (Stripe/
  fiat). Explicitly NOT eligible for the etzhayyim/root open mirror (its own
  CLAUDE.md). The SDK it consumes (`@etzhayyim/kami-engine-sdk`) is separately
  public-eligible. Stays gftd.
- **deai** — axes: **Custody + RisingWave**. Dating/matching app + research-data-
  collection frontend (Spirit-in-Physics): startAssessment / submitResponse /
  getProfile / listMatches / sendMessage / createCheckin. Every collection is
  PII-bearing — psychometric assessment responses (sensitive), dating profiles,
  matches (relationship data), private DMs, research-participation data — and
  matching is RW-backed. No non-PII public-catalog slice (any of it on public AT
  records would expose PII). etzhayyim brand-front consumes via consent-
  capability; data custody stays gftd.
- **manimani** — axes: **Custody + kotobase**. Personal knowledge router (随に):
  drop a fragment → LLM classifies into the user's projects (knowledge/task/memo).
  Non-federable by design + Signal E2E PII + Gmail/PC ingest, on the kotoba/
  kotobase datomic backend (a gftd-function per the Consensys pattern). Personal
  private knowledge/Gmail content can't be public AT records. Stays gftd.
- **dougaka** — axis: **RisingWave + render compute**. Video-rendering (動画化)
  LangGraph pipeline (render + health graphs; com.etzhayyim.apps.dougaka.render)
  with RW-backed job state (RW_URL / vertex_). Pure GPU/render compute infra — no
  consumer catalog layer in the project (cf. animeka, where the generation compute
  stayed gftd and only the catalog migrated; dougaka is just the compute). Stays
  gftd.
- **fax** — axes: **Custody + Liability** (classification=confidential). FAX
  transmission agent — dispatches PDFs to E.164 numbers via Phaxio/Dropbox Fax;
  faxTx / inboundFax (refs lawfirm.brief, eyubin.postalItem). Confidential legal/
  regulatory correspondence (内容証明 / 労基署 / 裁判所; inbound faxes) +
  legal-document-transmission duty of care. Cannot be public AT records;
  integrates paid fax providers. Stays gftd.
- **hc** — axes: **Custody + Settlement + Liability** (all three). Human Computing
  Platform (gig work + micro-tasks + OEM provider registration): worker KYC
  identity + KYB factory verification + labor records (Custody), gig wage payment
  (Settlement), 労働基準法 labor-law compliance + employer/platform duty of care
  (Liability). KYC/KYB + wages + labor compliance = regulated-infra. Stays gftd.
- **intel** — axis: **Custody** (classification=CUI). Multi-INT fusion
  intelligence platform (30 INT disciplines): report / source / indicator /
  feedObservation / inferredCohort. CUI-classified intelligence + protected
  sources (HUMINT source identities) + inferred-cohort profiling/surveillance —
  controlled data, never public AT records. Same class as crypto-asset-freeze.
  Stays gftd.
- **jukyu** — axis: **RisingWave + graph-compute**. Global supply-demand
  System-of-Systems: normalizes domain-actor outputs, runs global Pregel
  propagation (K8s pod-side LangGraph), ranks company exposure, emits signals.
  A DERIVED analytical compute engine — not a source-of-truth catalog (domain
  actors remain SoT, many already migrated). Same class as coverage (RW
  read-model) / dougaka (compute). No standalone rw-free catalog. Stays gftd.
- **llm** — axes: **RisingWave + Settlement + Custody**. LLM inference gateway
  (/v1/chat/completions, routes to CF Workers AI / Murakumo GPU): inferenceRequest
  / inferenceResult / modelConfig. RW-backed inference-event logging + credits-
  gated paid compute (x-credits-did) + inference requests/results carry arbitrary
  user content. The platform's LLM inference SSoT is gftd-resident (ADR-2605211000,
  Vultr A16 GPU primary). Canonical infra-vendor compute layer. Stays gftd.
- **cowork** — axes: **Custody + RisingWave**. Internal "Claude Cowork" MCP bridge
  to Microsoft Graph (Mail/Teams/Files/Calendar/Users) + RW graph (read-only):
  mailDraft (email content), toolGrant (OAuth delegation credentials), syncJob.
  Corporate M365 PII + credential custody; gftd internal IT tooling (M365 =
  ingest-only per root CLAUDE.md). Stays gftd.
- **credits** — axes: **Settlement + Custody**. Credit ledger & public-fund
  routing (Earn→Purchase→Spend; 30% platform fee; 10% tithe to public-fund).
  Not an AT-registry target — a credit ledger is financial data (never public
  records) with authoritative state on-chain or fiat-MoR. Split: the fiat-
  purchase + platform-fee MoR + balance ledger stays gftd (Settlement/Custody);
  the on-chain GCC token + TitheRouter 10% tithe is an etzhayyim-EXCLUSIVE
  on-chain primitive (ADR-2605211950 relocate target — Base L2/Ethereum, NOT an
  AT-PDS rw-free registry). No rw-free built here.

## Bucket C — NEEDS-CODEMOD (16) — active backlog

Import vectors: `createKyselyDb` 29 · `HYPERDRIVE` 23 · RisingWave 18 ·
`kysely` 8 · `stripe` 4 · `@atproto/api` 0 · `viem` 0.

common-crawl (RW, legacy src), cpc (legacy src),
email-service-adapter (stripe),
open-kyber (stripe+RW),
open-ossekai, open-ot (RW), open-patent (RW),
os-messaging, patent (RW), pptx,
public-kafun-bokumetsu, saiban, sanctions, seibutsu, shigotoba, shinka,
shinkansen, tenso, toshi-kozan, voxelforge, watashi, webmk, webya, xlsx,
yorishiro, yukkuri

## Bucket D — TODO-PENDING (55, MIGRATION-TODO.md)

**TRANSFORM-pending (25)**:
gftdcojp,
harai, hrse, hub, kaikei, keiei, ops, resource-flow, resource-planner,
resource-provider, robot, scheduler, shiharai, tia, web4, webpage, wire, worlds,
yabai, yatabase

**Ad-pixel codemod complete (26)**: animeka*, briefing*, communicator,
email-service-adapter*, external-service-adapter, facebook, fax*,
game-play-uploader, github, gmail, live, mailer, mangaka, media-gamers, meet,
meeting-recorder, messenger, microsoft, microsoft-graph, news, newsletter,
ongakuka, outreach, phone, recap, ses, society6, x
(\* also in Bucket C — ad-pixel done but substrate codemod incomplete)

**Substrate-boundary violation flagged (6)**: cloudflare-browser-render, insatsu,
open-jpn-mynumber, playwright, repository, site

## In-progress (2026-06-02)

- **Tier-2 commerce** (okaimono/ec on-chain pattern): ALL DONE (in A) —
  `crowdfunding` `ec` + the 8 (`shopping` `omise` `minpaku` `yadoya`
  `real-estate` `eigyo` `supplychain` `celler`) + `hospitality`.
  hospitality's rw-free is a property/roster mixed split; its residual RW in
  `scripts/sync-roster.ts` is legacy-cleanup (consumed via consent-capability),
  not a missing impl.

## Recommended sequencing

1. **Tier-2 commerce** (10) — okaimono/ec pattern; in progress.
2. **Bucket C open-* infra standards** (open-airplane/cofog/gas/network/ports/
   power/rail/swift/water etc.) — registry pattern like the Tier-1 standards
   (createKyselyDb → AT PDS), high-volume but mechanical.
3. **Bucket C RW data apps** (patent/jukyu/legal-entity/llm/deai/kenkyusha/...) —
   re-platform to kotoba datomic / AT PDS per ADR-2606011400 amendment 2026-06-01b.
4. **Bucket D non-commerce TODO seeds** (accounts/kaikei/keiei/hrse/...) — apply
   the 3-axis function-split per app (some are regulated → vendor function).
5. **Residual legacy-src cleanup** for Bucket A∩C apps (cpc/common-crawl/...).

Must-stay-vendor (NOT in scope, regulated): gambling / adult / payment-SaaS /
weapons-surveillance-finance / vendor cores — per vendor deps.toml
`phase5-vendor-deletion-248-projects-2026-05-23`.
