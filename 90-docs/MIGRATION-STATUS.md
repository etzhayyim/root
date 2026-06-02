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
| **A — DONE** | 93 | has a `rw-free/` on-chain reference impl |
| **B — CLEAN** | 209 | no `rw-free`, no TODO, no prohibited imports — compliant or thin stub |
| **C — NEEDS-CODEMOD** | 0 | CLEARED — all build-targets resolved (rw-free or Bucket V); only legacy codemod-cleanup remains |
| **D — TODO-PENDING** | 54 | has `MIGRATION-TODO.md` (seed copied, codemod pending) |
| **V — VENDOR-RESIDENT** | 38 | judged correctly gftd-resident (regulated-infra axis) — no migration |

**Real remaining scope ≈ 54 apps** (C + D = 0 + 54; Bucket C build-targets CLEARED — the 8 Tier-2 commerce apps
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

## Bucket A — DONE (93, has rw-free/)

6ir, aima (data layer; AI-compute stays gftd), air-sched,
analytics (mixed split — public catalog front), anime, bim, business-person, cad,
editor, gov (mixed split — public gov reference front), itonami, jp-fiscal,
kami (catalog: eng workbench + game worlds),
kenkyusha (research-knowledge; LLM compute stays gftd), kyber-qzzg06nh,
legal-entity (public corporate registry; PII in natural-person), open-patent,
patent (public patent registry; PII in natural-person), pptx,
public-kafun-bokumetsu (pollen-eradication research),
saiban (mixed split — public court/judge reference; cases stay gftd),
sanctions (mixed split — public consolidated sanctions-list reference; screening stays gftd),
seibutsu (biodiversity taxonomy open-data; image→species identify stays gftd),
shigotoba (business-establishment registry + job-board open-data; summarize LLM stays gftd),
shinkansen (mixed split — public timetable/fare/operation reference; reservations stay gftd),
toshi-kozan (mixed split — public depot/material/safety reference; recovery pipeline stays gftd),
xlsx (document-editor — workbook/sheet/cell tree; formula engine + OOXML stay client-side),
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

## Bucket V — CONFIRMED VENDOR-RESIDENT (38)

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
- **open-kyber** — axes: **Custody + Settlement + Liability** (all three). Open
  Source ERP (Apache-2.0): accounting (GL/AP/AR), HR/payroll, procurement,
  inventory; multi-entity consolidation, IFRS/GAAP/JP-GAAP. Custody (payroll
  employee PII + private company financials) + Settlement (AP/AR money
  obligations + payroll + Stripe) + Liability (financial-reporting regulatory
  compliance + accounting fiduciary). The OSS *code* is separately public-eligible
  (mirrored); the running ERP *data layer* stays gftd.
- **open-ossekai** — axis: **Custody (PII Tier-3)**. L1/L2/L3 intelligence +
  Well-Becoming coaching (classification=pii-tier3): intelBrief / arbitrage /
  wellBecomingPlan. L3 jocho (情緒) emotional scoring of individuals across 5 axes
  + kyu/dan coaching, consent-gated per ADR-0018; L1 OSINT actor profiling.
  Sensitive personal psychometric PII — Tier-3 stays server-side (Preferences/
  E2E), never public AT records. Stays gftd.
- **os-messaging** — axes: **Custody + RisingWave**. Multi-platform messaging
  bridge (9 platforms: Discord/Telegram/Slack/LINE/WhatsApp/Matrix/Teams/WeChat/
  Kakao → etzhayyim agents): private user DMs (com.etzhayyim.convo.message) +
  platform webhook credentials + messaging-user DID resolution; peripheral
  public-open-channel crawler is RW-backed. Messaging is E2E/signal per root rules,
  never public AT records. The public-open-channel crawl could later be an
  etzhayyim-front feed, but the bridge + credentials stay gftd.
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
- **shinka** — axes: **RisingWave + compute (LLM inference orchestration)**. The
  actor-evolution scheduler (`shinka.etzhayyim.com`, `*/5min` cron): queries the
  stalest actors from `vertex_actor` (37K+ rows, RisingWave), resolves joucho
  (情緒) cadence, and drives **murakumo LLM inference** to repair profiles, run
  kyumei drills, and post socially on each actor's behalf; plus a PropagationJob
  queue (claimJobs/queueStats) and HistoricalEvent/PropagationEvent simulation
  state. Its records (ShinkaTask queue, coverage stats, kyumei results, job
  queue) are **internal orchestration telemetry**, not a consumer catalog — there
  is no product/open-data layer to front. Pure backend orchestration-compute over
  the platform actor graph. Stays gftd. (Social posts it emits land via the
  normal `app.bsky.feed.post` federation path, already on-substrate.)
- **tenso** — axis: **Custody (zero-knowledge E2E)**. Signal-Protocol secure file
  transfer (`tenso.etzhayyim.com`): X3DH + Double Ratchet wraps per-transfer
  AES-256-GCM file keys; chunked ciphertext blobs on B2; server stores ciphertext
  only. Collections (transferRequest / fileManifest / transferLog / accessControl)
  are **private per-transfer encrypted envelopes** between specific DIDs — wrapped
  keys + access-control, never public AT records. Same signal/vault/messaging
  family the root invariant keeps server-side (`signal:v1:{ciphertext}` field-
  encrypt, PDS pipethrough). No public catalog to front — surfacing the wrapped
  keys would violate the zero-knowledge invariant. Stays gftd.
- **voxelforge** — axes: **RisingWave + GPU generation-compute (+ Settlement,
  metered `sk_live_*` API)**. 3D design pipeline (text/image/CAD → mesh+voxel):
  a stateless L3 dispatcher CF Worker forwarding `generate` to the
  `mitama-voxelforge-pool` LangGraph Server, which calls RunPod 6000 Ada GPU
  (TRELLIS / ComfyUI 3D-Pack / CadQuery) and **writes artifacts to B2 +
  RisingWave directly**. The design/artifact metadata is a read-projection of RW
  run-state; `listArtifacts?actorDid=` is a private "my generation history" view,
  not a public reference. **Discriminator**: its records have NO authoritative
  external source — artifacts exist only because a GPU job ran, so `sourceUrl`
  would point at our own RunPod pod. Compute-output bookkeeping, not open-data
  (same family as `dougaka`, NOT a published-work catalog like animeka). Stays
  gftd. (Carry-forward test: can each record cite an authority that isn't our own
  pod/RW? No → (b).)
- **watashi** — axis: **Custody (private device-session + transport relay)**.
  Cross-platform input sharing (渡し): macOS↔Windows cursor/keyboard/clipboard
  sharing (Synergy/Universal-Control style) via a Rust OS-input agent + encrypted
  UDP transport (ChaCha20-Poly1305 / X25519) + a Cloudflare-D1 relay
  (`watashi-relay`, HMAC `SS_SIGNING_KEY`). Collections (peer / layout / session /
  clipboardSync / fileTransfer / audit_log) are **private per-user device-session
  + transport coordination state** — peer pairing, session tokens, clipboard &
  file-transfer payloads — not open-data (no external authority; carry-forward
  test fails). Screen-layout is Tier-3 user config → Preferences, not public
  records. Same encrypted-transport/relay family as `tenso`. Stays gftd.
- **webmk** — axes: **RisingWave + LLM generation-compute + Custody (client
  CRM/PII) + Settlement (ad-campaign)**. Web Marketing Proposal Agent: a
  LangGraph/Claude loop (research→competitors→strategy→copy→quality_gate→store)
  that generates marketing proposals, delivers them via Resend email, and
  optionally creates ad campaigns via `ads.etzhayyim.com`. Collections
  (`vertex_webmk_proposal` = LLM-generated strategy/copy/qualityScore,
  `vertex_webmk_client` = private client CRM name/website/industry + email target,
  `edge_webmk_campaign_link` = → ad campaignId) are **generated deliverables +
  private CRM data**, not open-data — a proposal's `sourceUrl` would point at our
  own Claude run (carry-forward test fails). Same generation-agent family as
  `voxelforge`. Stays gftd.
- **webya** — axes: **RisingWave + LLM generation-compute + Custody (hosted site
  content + custom-domain) + Liability/Settlement (website-hosting SaaS)**.
  Homepage-generation SaaS (ウェブ屋) for 士業 + 一般企業: a LangGraph loop
  (createSite/reviseSite) generates site HTML, `provisionDomain` sets up custom
  domains (CF for SaaS CNAME), and pages are served at edge via Hyperdrive SELECT
  on `vertex_webya_page.html_content`. Tables (`vertex_webya_site` /
  `vertex_webya_page` / `vertex_webya_domain`) are **generated client website
  content + client-domain hosting config** — webya HOSTS client production sites
  (availability/fulfillment liability + paid custom-domain provisioning). Not
  open-data — a site's authority is our own generation run (carry-forward test
  fails). Same generation + hosting family as `webmk`. Stays gftd.
- **yorishiro** — axes: **Custody (per-user/org credential vault + session) +
  Liability (browser-automation agency) + Settlement (card/ad/cashback
  providers)**. Apify-inspired web-service browser-automation platform (依り代):
  a fleet of provider adapters that drive authenticated browser automation
  (Playwright Chromium pool, session persistence) or external APIs **on the
  user's behalf using stored credentials** — google/microsoft/aws/x/linkedin
  (browser), marqeta (card issuing), japanpost-enaiyo (certified legal mail),
  flyio (account closure), nuro (cashback), trafficstars (ad delivery).
  `provider-vault-provider` is a HashiCorp Vault storing **per-user/org
  credentials** (`secret/data/orgs/{org}/users/{user}/services/{service}/{key}`).
  Records are credential references + authenticated session/automation-run state
  — no external authority (carry-forward test fails), and it acts *as* the user
  on external regulated/financial services. Same credential-custody family as
  `auth`. Stays gftd.
- **yukkuri** — axes: **RisingWave + generation-compute (murakumo LLM/image/audio
  + kami render + ffmpeg) + B2 storage Custody**. AI ゆっくり実況 video generation:
  a multi-actor pipeline (scriptwriter→voiceL/R→character→illustrator→sfx→composer
  →editor→renderer→critic) that drives **murakumo** text/image/audio inference,
  `kokoro-ts` TTS, `kami-engine` headless render, and `ffmpeg-wasm` mux to produce
  mp4/webm. Tables (`vertex_yukkuri_video` / `generation` / `render` +
  `yukkuri.asset` intermediate outputs) are **compute-output bookkeeping** with
  final videos stored to B2 (SigV4-presigned). A video's authority is our own
  generation run, not external open-data (carry-forward test fails). Same
  generation-pipeline family as `voxelforge` / `dougaka` / `mangaka`. Stays gftd.

## Bucket C — NEEDS-CODEMOD (0) — active backlog CLEARED

> **False-positive removed**: `open-ot` (WASM-PLC OSS spec, Apache-2.0) was
> labelled "(RW)" but is spec + Rust crates only — no TS app, no AT collections,
> no prohibited-substrate imports in any code file. Nothing to migrate and no
> regulated function → reclassified to Bucket B (clean).


Import vectors: `createKyselyDb` 29 · `HYPERDRIVE` 23 · RisingWave 18 ·
`kysely` 8 · `stripe` 4 · `@atproto/api` 0 · `viem` 0.

**Build-targets CLEARED (2026-06-02).** Every Bucket C app that needed an
etzhayyim-front rw-free build has been resolved this loop: migrated
(6ir-batch + saiban / sanctions / seibutsu / shigotoba / shinkansen / toshi-kozan
/ xlsx) or judged (b) vendor-resident (shinka / tenso / voxelforge / watashi /
webmk / webya / yorishiro / yukkuri). The only entries that remain under the
"NEEDS-CODEMOD" label are **legacy codemod-cleanup**, NOT migration targets:

- `common-crawl` (RW, legacy src) — rw-free already exists; residual RW in
  non-`rw-free` src is a later cleanup.
- `cpc` (legacy src) — rw-free already exists; same.
- `email-service-adapter` (stripe) — codemod-only; also tracked in Bucket D.

These are mechanical import-removal chores on already-migrated/vendor apps, not
"front vs vendor" judgment calls. No rw-free build remains in Bucket C.

## Bucket D — TODO-PENDING (54, MIGRATION-TODO.md)

> **Phantom removed (2026-06-02)**: `gftdcojp` was listed but is **not an app** —
> no `60-apps/*-project-gftdcojp` dir exists. Throughout `deps.toml` it denotes
> the **vendor org identity** (the gftd.co.jp side of the Consensys boundary,
> repo `github.com/gftdcojp/ai-gftd-apps-gftdcojp`), not a migratable
> `etzhayyim/root` project. Nothing to migrate to etzhayyim-front; by definition
> gftdcojp IS the vendor side. Dropped from the backlog (TRANSFORM 25→24, D 55→54).

**TRANSFORM-pending (24)**:
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
