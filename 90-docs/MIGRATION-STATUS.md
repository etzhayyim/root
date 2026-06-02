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
| **A — DONE** | 105 | has a `rw-free/` on-chain reference impl (git-authoritative: committed `rw-free/src/index.ts` count) |
| **B — CLEAN** | 209 | no `rw-free`, no TODO, no prohibited imports — compliant or thin stub |
| **C — NEEDS-CODEMOD** | 0 | CLEARED — all build-targets resolved (rw-free or Bucket V); only legacy codemod-cleanup remains |
| **D — TODO-PENDING** | 7 | has `MIGRATION-TODO.md` (seed copied, codemod pending) — all build-targets resolved (rw-free or V); remainder = legacy codemod-cleanup chores |
| **V — VENDOR-RESIDENT** | 85 | judged correctly gftd-resident (regulated-infra axis) — no migration |

**Real remaining scope ≈ 8 apps** (C + D = 0 + 8; Bucket C build-targets CLEARED — the 8 Tier-2 commerce apps
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

## Bucket A — DONE (105, has rw-free/)

> **Roster correction (2026-06-03)**: count is git-authoritative (committed
> `rw-free/src/index.ts` = 105). The prose list below previously named 6 phantom
> non-apps (`6ir`, `air-sched`, `analytics`, `bim`, `business-person`,
> `legal-corpus`) — empty dirs with only stray `node_modules`, no committed src,
> absent from both repos — now treated as resolved phantoms (see Bucket V note).
> Treat the prose names as indicative, not a 1:1 roster.

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
hrse (Bucket D; mixed split — public cyber-sec job-board catalog; freelancer PII + matching + billing stay gftd),
resource-flow (Bucket D; mixed split — public 2次ソース flow/emitter/anomaly data; detection + sankey compute stay gftd),
webpage (Bucket D; content-editor — space/page authoring + public published-page directory; no hosting/domains),
worlds (Bucket D; content-authoring — scene/asset/portal + public published-scene directory; no generation compute),
github (Bucket D; mixed split — public GitHub-data catalog repo/profile/issue/org-graph; private-repo sync + commit-analysis stay gftd),
live (Bucket D; mixed split — public live-room/schedule catalog; cheers/tipping + AI avatar generation stay gftd),
media-gamers (Bucket D; mixed split — public game catalog publisher/developer/title/chart; guide-gen LLM stays gftd),
news (Bucket D; mixed split — public news-aggregation source/article catalog; quality-eval + translation LLM stay gftd),
newsletter (Bucket D; mixed split — public newsletter-issue archive; subscriber list + email delivery + LLM gen stay gftd),
open-jpn-mynumber (Bucket D; public My Number reference-doc catalog — gov-published policy/spec/API docs; ingest compute stays gftd),
repository (Bucket D; ADR-0039 Repository-in-Graph — git object model blob/tree/commit/ref over Actor DID = first-party source code; FaaS build dispatch + execution stay gftd),
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

## Bucket V — CONFIRMED VENDOR-RESIDENT (85)

Apps judged (per-app gate) to have a **regulated-infra primary function** that
correctly stays gftd vendor under the Consensys boundary + 3-axis OR-test. These
are NOT migrated; the etzhayyim front consumes them via consent-capability.

> **Phantom non-apps removed from Bucket A roster (2026-06-03)**: `6ir`,
> `air-sched`, `analytics`, `bim`, `business-person`, `legal-corpus` were listed
> in the Bucket A prose roster as DONE but have **zero committed `rw-free/src`** —
> only stray `node_modules/` leftovers — and **no source in either repo**
> (etzhayyim/root nor the gftd.co.jp vendor repo). They are non-apps (the
> `gftdcojp` precedent). **Resolved = do NOT build; future batch fires skip them.**
> Count is git-authoritative: committed `rw-free/src/index.ts` = **105** (the
> header was under-counting by 1). The prose roster is indicative, not exhaustive.

- **accounts** — axis: **Custody**. Account-lifecycle management worker (ADR-0024,
  `accounts.etzhayyim.com`, scaffold-only / not deployed): linked auth methods,
  OAuth provider link/unlink (Google/Microsoft tokens), email binding, server-
  issued sessions, `actor.score`, `/manage` UI. Custodies third-party IdP tokens +
  email bindings + session credentials = auth-credential + identity PII custody.
  No catalog-shaped product surface to front (auth session/credential management
  does not map to a typed-record registry) ⇒ stays gftd. Sibling split-off of
  **auth**; the `/manage` UX could front (c) but there is no registry layer to
  build, so disposition = Bucket V. did:web/did:plc/passkey issuance stays
  etzhayyim-exclusive (in `auth`, tracked separately), not here.
- **air-book** — axes: **Custody + Settlement + Liability**. Airline reservations
  & ticketing: PNR creation (`createPnr`), booking confirmation, ticket issuance
  (`issueTicket`), seat assignment, ancillary services, cancellation/reprotection
  (`reprotectPassenger`), and BSP settlement (`settleBsp`). PNR = passenger PII
  custody; BSP/ticketing = IATA fiat settlement (merchant-of-record); ticketing +
  reprotection = fulfillment / 善管注意義務 liability. No public catalog to front
  (flight *search* is the separate `flight-offer`, already migrated) ⇒ stays gftd.
- **air-cargo** — axes: **Settlement + Liability + Custody**. Airline cargo
  operations: cargo bookings, air waybill issuance (`issueAirWaybill`), cargo
  acceptance (`acceptCargo`), ULD assignment, shipment tracking, claims
  (`processClaim`), cargo account settlement (`settleCargoAccount`), cargo
  security reporting (`reportCargoSecurity`). AWB = contract of carriage (freight
  charges + Montreal-Convention carriage liability); settleCargoAccount = fiat
  settlement; claims + acceptance = 善管注意義務 fulfillment liability; shipper/
  consignee + security reporting = custody/regulatory ⇒ stays gftd. No public
  open-data catalog to front.
- **air-crew** — axes: **Custody + Liability**. Airline crew management &
  scheduling: roster publication (`publishRoster`), pairing construction
  (`buildPairing`), qualification tracking (`trackQualification`), fatigue
  assessment (`assessFatigue`), crew assignment, crew travel, duty-time recording
  (`recordDutyTime`), notifications. Crew rosters / duty-time / fatigue (medical-
  adjacent) / qualifications = employee-labor PII custody; fatigue + duty-time +
  qualification = aviation safety / flight-time-limitation regulatory compliance =
  善管注意義務 fitness-to-fly liability ⇒ stays gftd. No public catalog to front.
- **air-dcs** — axes: **Custody + Liability**. Airline departure control system:
  check-in (`processCheckIn`), boarding-pass issuance (`processBoardingPass`),
  baggage acceptance/reconciliation (`acceptBaggage`/`reconcileBaggage`), load-
  sheet computation (`computeLoadSheet`), APIS transmission (`transmitApis`),
  turnaround tracking, departure control (`issueDepartureControl`). Passenger PII
  + APIS = passport/visa/border data sent to government authorities (custody +
  regulatory); load sheet = weight-&-balance flight-safety; baggage reconciliation
  = security; all = 善管注意義務 safety/border liability ⇒ stays gftd. No public
  catalog to front.
- **air-ffp** — axes: **Custody + Settlement + Liability**. Airline frequent-flyer
  program: member enrollment (`enrollMember`), points accrual (`accruePoints`),
  reward redemption (`redeemReward`), tier updates (`updateTier`), miles transfer
  (`transferMiles`), purchase processing (`processPurchase`), miles expiration
  (`expireMiles`), partner reconciliation (`reconcilePartner`). Member PII + miles
  balance = stored-value ledger custody; processPurchase = fiat MoR; reconcile-
  Partner = partner settlement; miles = deferred-revenue liability ⇒ stays gftd.
  No catalog method exists (no reward/partner inventory list) — the only member-
  facing records are the PII + stored-value balance that stay gftd; fabricating a
  reward catalog would be the invent-a-catalog trap. No frontable surface.
- **air-mro** — axes: **Liability + Custody**. Airline maintenance, repair &
  overhaul: work orders (`createWorkOrder`), component tracking (`trackComponent`),
  airworthiness checks (`checkAirworthiness`), tech-occurrence reporting
  (`reportTechOccurrence`), maintenance scheduling (`scheduleMaintenance`),
  reliability reports (`reportReliability`), spare parts (`orderSparePart`), ground
  equipment. Airworthiness + maintenance + occurrence/reliability reporting =
  aviation safety-critical regulatory compliance (EASA/FAA Part-145) = 善管注意義務
  airworthiness liability; component traceability = safety-critical regulated
  records custody (life-limited parts, certs of conformity) ⇒ stays gftd. Internal
  maintenance ops; no public catalog to front.
- **air-ops** — axis: **Liability** (+ operational-records Custody). Airline flight
  operations & dispatch: flight plan filing (`fileFlightPlan`), dispatch briefs
  (`createDispatchBrief`), NOTAMs (`fetchNotam`), weather briefings
  (`fetchWeatherBrief`), tech logs (`recordTechLog`), fuel orders (`orderFuel`),
  PIREPs (`submitPirep`), real-time flight monitoring (`monitorFlight`). Flight
  dispatch / ops control = safety-critical 善管注意義務 (dispatch shares legal
  responsibility for flight safety & legality) ⇒ stays gftd. NOTAM/weather are
  `fetch` of external-authority public feeds as dispatch inputs, not an owned
  catalog the app publishes — fabricating one would be the invent-a-catalog trap.
  No frontable surface.
- **air-sms** — axes: **Liability + Custody**. Airline safety management system:
  safety reports (`submitSafetyReport`), risk assessment (`assessRisk`), IOSA
  findings (`recordIosaFinding`), regulatory reports (`fileRegulatoryReport`),
  occurrence reporting (`reportOccurrence`), safety bulletins
  (`distributeSafetyBulletin`), dangerous-goods screening (`screenDangerousGoods`),
  security alerts (`handleSecurityAlert`). Aviation safety & security regulatory
  compliance (IOSA / ICAO-IATA DG / occurrence reporting) = 善管注意義務 liability;
  confidential safety/occurrence/security records (just-culture protected) =
  custody ⇒ stays gftd. Safety bulletins = internal crew distribution, not public
  open-data. No frontable surface.
- **air-yield** — axes: **Settlement + Liability**. Airline revenue management &
  pricing: fare class publication (`publishFareClass`), inventory control
  (`adjustInventory`), fare filing (`fileFare`), overbooking (`setOverbooking`),
  group bookings (`processGroupBooking`), dynamic pricing (`applyDynamicPrice`),
  revenue reporting (`generateRevenueReport`), demand forecasting
  (`forecastDemand`). Proprietary revenue-optimization engine = fiat-revenue /
  MoR-adjacent (Settlement); overbooking → denied-boarding compensation regulatory
  (EC261/DOT) = Liability ⇒ stays gftd. publishFareClass/fileFare are the
  write/decision side of the engine, NOT an open-data catalog — the consumer-
  facing fare-display catalog is the already-migrated `flight-offer`, which
  consumes this engine's output. No frontable surface here.
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
- **mangaka** — axes: **RisingWave + GPU generation-compute**. Manga generation
  studio pipeline (`mangaka.gftd.ai`): ComfyUI + USD cinematic page-atom pipeline
  (11+ generation graphs, quality pack, MangakaUSDScene custom nodes) producing
  manga pages via diffusion/LLM compute, artifacts to B2 + RW. Records have NO
  authoritative external source — a page exists only because a generation job ran
  (carry-forward test fails: `sourceUrl` would point at our own pod/RW). Compute-
  output bookkeeping, NOT a published-work catalog — the consumer-facing catalog
  front is the sibling `animeka` (in A); mangaka is the generation/studio side.
  Same generation-pipeline family as `voxelforge` / `dougaka` / `yukkuri`. Stays
  gftd. (Corrects a stale prose assertion that wrongly grouped mangaka with
  animeka as "already in A" — caught by a git-authoritative C/D truth-pass.)
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
- **harai** (Bucket D → V) — axes: **Settlement + Custody (financial ledger)**.
  Payment & Settlement Clearing Platform (払い): 8 methods — createPayment /
  settlePayment / refundPayment / transferFunds / getBalance / listTransactions /
  closeAccount. A payment-clearing balance + transaction ledger is **regulated
  financial state**, never a public AT registry (carry-forward test fails). Same
  financial family as `credits`: the on-chain settlement rail (USDC + ERC-4337,
  per its MIGRATION-TODO) is an **etzhayyim-EXCLUSIVE** primitive (ADR-2605211950
  relocate target), NOT an AT-PDS rw-free registry; the fiat/clearing/balance
  custody stays gftd. No rw-free built.
- **hub** (Bucket D → V) — axes: **Infra (API-gateway request routing) + Custody
  (endpoint/webhook config + secrets)**. Integration Hub & API Gateway Platform
  (`hub.gftd.ai`): 8 methods — registerEndpoint / listEndpoints / routeRequest /
  getRouteStatus / createWebhook / listWebhooks / testConnection / getMetrics.
  Records are **per-user/org integration plumbing** — registered endpoint URLs,
  webhook callback secrets, routing rules + live routing state + metrics — not a
  public directory (carry-forward test fails). `routeRequest` is live proxy
  compute. Same gateway/dispatcher-infra family. No rw-free built.
- **kaikei** (Bucket D → V) — axes: **Custody (confidential financial/tax books)
  + Liability (記帳/tax compliance, 善管注意義務) + Settlement (invoice/payment
  accounting)**. Accounting / bookkeeping platform (会計): thin-edge facade over
  pod-side accounting logic (journals / ledgers / invoices / tax / balances /
  financial reports). Accounting books are **confidential business financial
  data**, never public AT records (carry-forward test fails). Same financial
  family as `harai` / `credits`. No rw-free built.
- **keiei** (Bucket D → V) — axes: **Infra (k8s-resident C-suite orchestration
  LSP + leader election) + Custody (internal CxO audit ledger)**. C-suite role
  LSP (経営): an AI CxO management daemon (`pymagatama.keiei` / `KeieiServer`,
  `did:web:keiei.gftd.ai`, ADR-2605101200) — multi-replica k8s deployment with
  single-writer Lease leader-election, an append-only `CXO-LEDGER.md` decision
  audit, and JSON-RPC dispatch to C-suite roles. Internal management
  orchestration compute, not a consumer/catalog product (carry-forward test
  fails); records are internal governance audit. Root CLAUDE keeps the keiei
  daemon a distinct gftd-tied entity. Same internal-orchestration family as
  `shinka`. No rw-free built.
- **ops** (Bucket D → V) — axes: **Infra (process-automation orchestration /
  workflow execution) + Custody (per-org automation configs + process-run
  state)**. Operations Automation Platform (`ops.gftd.ai`): 8 methods —
  createProcessRun / updateProcessRun / listProcessRuns / getProcessRun +
  createAutomation / updateAutomation / listAutomations / getAutomation. Records
  are **per-org internal operational orchestration state** — automation
  (workflow) definitions + process-run history — not a public catalog
  (carry-forward test fails). Same internal-orchestration/dispatcher family as
  `keiei` / `hub`. No rw-free built.
- **resource-planner** (Bucket D → V) — axes: **Custody (per-user/org resource
  inventory + allocation plans) + Infra (Inngest event-driven plan-generation
  compute)**. Inngest event-driven resource planner (`rp.etzhayyim.com`): ingests
  resources scoped by user_id/org_id and generates optimal resource-allocation
  plans (KV `resource-planner-store`). Records are **private per-org operational
  planning data** — resource inventory + generated allocation plans — not public
  open-data (carry-forward test fails). Contrast `resource-flow` (PUBLIC 2次ソース
  of externally-authored flows → fronted): resource-planner is per-org private
  planning → stays gftd. No rw-free built.
- **resource-provider** (Bucket D → V) — axes: **Settlement (rewards for
  contributed resources) + Custody (contributed documents/images + location PII +
  GPU compute provisioning)**. etzhayyim Resource Provider Network: a
  decentralized system where users contribute resources (documents/images for
  RAG/training, GPU compute, location data) **in exchange for rewards**.
  Currently business-plan/spec-stage (`.jsonld` metadata only; Actor Development
  + Frontend pending). Reward-settling resource marketplace = regulated primary
  function (carry-forward test fails). Same family as `credits` / `harai`: any
  on-chain reward rail is an etzhayyim-exclusive relocate target (ADR-2605211950),
  NOT an rw-free registry; reward-settlement + data/compute custody stays gftd.
  No rw-free built.
- **robot** (Bucket D → V) — axes: **Liability (physical robot mission control +
  dropshipping fulfillment) + Custody (telemetry + shipping PII) + Settlement
  (dropshipping order processing)**. Robotics Control & Dropshipping Platform
  (`robot.gftd.ai`): 8 methods — workflowStart / workflowPlan / missionPlan /
  missionStatus / missionSimulate / telemetryIngest / processCatalog /
  fulfillmentClose. Two regulated halves: physical robot mission control + safety
  (telemetry custody) and dropshipping order fulfillment (MoR / shipping PII).
  Mission plans / telemetry / fulfillment orders are platform-operational/
  regulated, not open-data (carry-forward test fails); the "process catalog" is
  the fulfillment pipeline's internal catalog, not an external-authority
  registry. No clean public layer to front. No rw-free built.
- **scheduler** (Bucket D → V) — axes: **Infra (job/cron scheduling + execution
  engine) + Custody (per-user job definitions + run status)**. Job Scheduling
  Platform (`scheduler.gftd.ai`, "Codex Automations 風"): 8 methods — createJob /
  getJob / updateJob / deleteJob / listJobs / pauseJob / resumeJob / jobStatus,
  fired by a cron-tick MCP actor. Records are **per-user private scheduled-job
  definitions + run status** — internal scheduling config/state, not public
  open-data (carry-forward test fails). Same internal-orchestration/dispatcher
  family as `ops` / `hub` / `keiei`. No rw-free built.
- **shiharai** (Bucket D → V) — axes: **Settlement (executes payments — final
  submit) + Custody (payment credential vault + billing data) + Liability
  (browser-automation payment agency, 善管注意義務)**. 支払 Web 自動化 Actor
  (`shiharai.etzhayyim.com`): extracts billing emails (Gmail), drives Web payment
  pages via Playwright, and **executes the final submit** (actually completes
  fiat payments) using credentials wrapped through `vault.etzhayyim.com`
  (ephemeral, 60s). Records are private financial/credential automation state,
  not open-data (carry-forward test fails). Same family as `yorishiro`
  (browser-automation + credential agency) + `harai` (payment). No rw-free built.
- **tia** (Bucket D → V) — axes: **Custody (account-protection PII + monitored
  profiles + threat findings) + Infra/compute (LLM threat-intel analytics) +
  Liability (auto-takedown agency)**. Threat Intelligence & Analytics Platform
  (`tia.gftd.ai`): 8 methods — analyzeIntent / classifySignal / extractEntities /
  scoreRisk / generateSummary / lookupProfile / submitFeedback / getInsights;
  domain = Internet Account Protection (detect account-takeover/impersonation
  across social media via AI similarity, auto-contact platforms). Records are
  private surveillance/security analytics state + account-protection PII, not
  open-data (carry-forward test fails). Stays gftd.
- **web4** (Bucket D → V) — axes: **Settlement (GCC on-chain token + minter) +
  Infra/compute (distributed Web4 inference & expert network)**. Two regulated
  facets: (1) GCC Token & Minter — deployed Ethereum mainnet contracts (GCC
  FiatTokenV2_2, GCCMinter accepting ETH/USDC/USDT, Safe 2/3 multisig, Chainlink
  oracle); (2) Decentralized Web4 Inference & Expert Network (`web4.gftd.ai`):
  registerExpert / submitInference / getInferenceResult / getClusterStats — a
  distributed GPU-inference compute network. The GCC token/minter is an
  **etzhayyim-EXCLUSIVE on-chain primitive** (ADR-2605211950 relocate target; the
  same GCC `credits` references), NOT an AT-PDS rw-free registry; the
  inference/expert compute stays gftd. Records are platform compute-network state
  + on-chain contracts, not open-data (carry-forward test fails). No rw-free built.
- **wire** (Bucket D → V) — axes: **Settlement (wire transfers + balance ledger)
  + Custody (balance + transfer records + messages) + Liability (money-transfer
  善管注意義務)**. Wire Transfer & Messaging Platform (`wire.gftd.ai`): 8 methods —
  createTransfer / listTransfers / getTransfer / confirmTransfer / createMessage /
  listMessages / getBalance / getTransferHistory. Money-transfer infrastructure
  with a balance ledger + transfer confirmation/history (messaging = transfer-
  attached memos). Transfer records + balances are confidential financial state,
  never a public registry (carry-forward test fails). Same financial family as
  `harai` / `credits` / `shiharai`. No rw-free built.
- **yabai** (Bucket D → V) — axes: **Custody (AML/sanctions screened-entity data +
  IP access-surveillance logs) + Liability (AML/反社 risk scoring + enforcement,
  善管注意義務) + Infra/compute (risk-scoring UDF + threat-intel ingest)**. Risk
  Intelligence Platform (`yabai.etzhayyim.com`): AML / sanctions / 反社
  (anti-social forces) risk scoring + IP access filtering/WAF + cyber threat-intel
  (CVE/MITRE/malware/IOC/phishing/STIX/BGP/TLS, WHOIS/DNS/ASN/GeoIP). Tables
  include YabaiRisk / YabaiAlert / YabaiEnforcement / YabaiAuditLog +
  IntelAccessLog / IntelSession / IntelDevice / CfHttpRequestLog (surveillance
  access logs). Records are confidential compliance/surveillance state, not a
  public registry (carry-forward test fails). The public CTI catalog is already
  covered by the separate `threat-intelligence` app (Bucket A); yabai's distinct
  function is the AML/risk-scoring/enforcement/access-surveillance core. No
  rw-free built.
- **yatabase** (Bucket D → V) — axes: **RisingWave + Custody (tenant storage /
  graph / auth PII) + Settlement (Stripe billing) + Liability (BaaS hosting)**.
  Retail cloud graph DB + Supabase-style BaaS (`yatabase.etzhayyim.com`, codename
  io-yatabase: Cypher/Bolt/Realtime/PostgREST/GraphQL/Auth/Functions/Studio) —
  object storage + buckets + presigned URLs + **Stripe Customer Portal** billing
  + tenant auth/identity + recovery email; persistence on L4 RisingWave + L7
  LangServer. This is the **canonical "kotobase backend"** regulated-infra example
  named in root CLAUDE.md ("kotobase P1, 旧 yatabase を統合") — the gftd commercial
  BaaS data backend that etzhayyim apps consume via consent-capability. Never a
  public registry (carry-forward test fails). No rw-free built.
- **communicator** (Bucket D / ad-pixel → V) — axes: **Custody (Gmail/Outlook
  conversation memory + contacts + email PII) + Liability (agent-driven external
  comms on user's behalf, 善管注意義務) + Infra/compute (agent decision layer +
  emotional-analytics)**. Communication control plane orchestrating external
  Gmail/Outlook conversations with policy guardrails + conversation memory
  (integrates mailer / external-service-adapter / emotional-analytics); persists
  conversation state + follow-up actions, sends on the user's behalf (approval-
  gated for high-risk). Records are private per-user conversation state, not
  open-data (carry-forward test fails). Same messaging/comms-orchestration family
  as `mailer` / `microsoft` / `outreach`. No rw-free built.
- **external-service-adapter** (Bucket D / ad-pixel → V) — axes: **Infra
  (provider-native execution adapter) + Custody (provider credentials /
  integration config) + Settlement (affiliate-revenue paths)**. A thin adapter/
  integration layer that executes external-service API calls (commerce /
  communication / media) on behalf of other apps (e.g. `communicator` uses it for
  "provider-native execution"). No product surface — pure integration plumbing,
  not open-data (carry-forward test fails). Same adapter/integration-infra family
  as `yorishiro` / `hub`. No rw-free built.
- **facebook** (Bucket D / ad-pixel → V) — axes: **Custody (collected Facebook
  PII — profiles / friend-graph / posts / messenger, incl. third-party PII) +
  Liability (FB sync/scrape + messenger-bridge agency)**. Facebook Intelligence
  Platform (`facebook.etzhayyim.com`): capabilities facebook-sync /
  profile-collection / friend-graph / post-collection / messenger-bridge —
  ingests/mirrors a user's Facebook data into the platform. Collected social data
  is private personal PII (incl. friends'), not open-data (carry-forward test
  fails). Same provider/messaging family as `gmail` / `messenger` / `microsoft`.
  No rw-free built.
- **game-play-uploader** (Bucket D / ad-pixel → V) — axes: **Settlement
  (rewards/payouts for uploads + affiliate-revenue paths) + Custody (uploaded
  gameplay content + uploader PII + payout records) + Liability (campaign
  fulfillment + content hosting)**. A reward-paying upload-campaign pipeline
  (campaign / upload / reward via `ingest/game_play_uploader.py`): users upload
  gameplay content as marketing-campaign submissions and earn rewards. The uploads
  are settlement-entangled campaign submissions, not a curated external-authority
  catalog (carry-forward test fails; fronting them = the voxelforge invent-a-
  catalog trap). Same reward-marketplace family as `resource-provider`. No rw-free
  built.
- **gmail** (Bucket D / ad-pixel → V) — axes: **Custody (private email PII +
  OAuth-token KEK custody) + Liability (email send/triage + messenger-bridge
  agency) + RisingWave**. Gmail Intelligence Platform (`gmail.etzhayyim.com`):
  syncs the user's emails/threads/contacts (email-triage / phishing-detection /
  contact-did-creation / messenger-email-bridge), sends outbound email, and
  custodies **OAuth refresh tokens** (D1 `GMAIL_DB` + KEK envelope, AES-256-GCM,
  server-side only); RisingWave-backed (`vertex_gmail_*`). Private personal email
  + credentials, not open-data (carry-forward test fails; contrast `github` =
  public open-data → fronted). Same provider/messaging family as `facebook` /
  `communicator` / `mailer`. No rw-free built.
- **mailer** (Bucket D / ad-pixel → V) — axes: **Custody (DID↔email binding +
  inbound/outbound email content + recipient PII) + Liability (email-delivery
  infra — Resend send + CF inbound routing, SPF/DKIM/DMARC, 善管注意義務) + Infra
  (platform email backend)**. DID-based email platform (`mailer.etzhayyim.com`,
  `performerType: system`): email-relay inbound gateway (CF Email Routing → MIME
  parse → PDS → convo), mailer-inbound (register/send/reply/forward), notify
  (multi-channel dispatcher), resend (Resend API backend). The canonical
  email-service backend apps consume (root CLAUDE: primary `mailer.gftd.ai`
  outbound/inbound). Email addresses/messages/bindings are private PII + infra
  state, not open-data (carry-forward test fails). No rw-free built.
- **meet** (Bucket D / ad-pixel → V) — axes: **Custody (Google OAuth credentials +
  private meeting metadata/participants/transcripts PII) + Liability (Meet
  sync/agency)**. Google Meet integration (`meet.etzhayyim.com`): "Google Meet
  OAuth and sync" via `ingest/gworkspace_lite.py` (Google Workspace lite ingest)
  — syncs the user's private Meet data (meetings/participants/transcripts) with
  Google OAuth. Private Google-Workspace data + credentials, not open-data
  (carry-forward test fails). Same provider family as `gmail` / `microsoft` /
  `facebook`. No rw-free built.
- **meeting-recorder** (Bucket D / ad-pixel → V) — axes: **Custody (meeting
  audio/video + E2E-encrypted transcripts, PII Tier 3) + Liability (consent-gated
  recording on user's behalf, recording-consent compliance) + RisingWave + B2**.
  User-delegated meeting recorder for Teams / Meet / Zoom: joins meetings on the
  user's behalf (consent-gated ES256 JWT), captures audio/video + transcript,
  whisper transcription (Murakumo MLX); media chunks in B2, transcripts
  **Signal-encrypted** (`signal:v1:`), authoritative graph in RisingWave.
  Collections (recordingChunk / transcriptSegment) are zero-knowledge E2E
  sensitive meeting content (same family as `tenso` / vault / signal), never a
  public registry (carry-forward test fails). No rw-free built.
- **messenger** (Bucket D / ad-pixel → V) — axes: **Custody (private channel/DM/
  thread messaging PII) + Liability (message delivery/retention)**. GFTD Messenger
  (`messenger.etzhayyim.com`): real-time team-messaging platform (Slack/Discord
  style) — channels + direct messages + thread replies, message persistence via
  sql graph ORM. Messaging/conversation stays server-side per root CLAUDE
  (`chat.bsky.convo.*` / PDS pipethrough), not a public AT registry; DMs are
  private, channels team-scoped (carry-forward test fails). Same messaging/
  conversation family. No rw-free built.
- **microsoft** (Bucket D / ad-pixel → V) — axes: **Custody (M365 app-token
  credential + draft/sent mail content + recipient PII) + Liability (Mail.Send /
  Teams-post on the org's behalf, policy-gated)**. Microsoft 365 / Graph
  integration (`microsoft.etzhayyim.com`): a write facade (microsoft-send) —
  sendMail / sendDraft / listDrafts (Mail.Send app-only, internal=direct /
  external=auto-draft) + Teams channel posting; acquires M365 app tokens. Private
  email + M365 credentials, not open-data (carry-forward test fails). Same
  provider/messaging family as `gmail` / `mailer` / `meet`. No rw-free built.
- **microsoft-graph** (Bucket D / ad-pixel → V) — axes: **Custody (M365 Graph
  credentials + accessed Teams/SharePoint/Outlook private data PII) + Infra (Graph
  API access gateway + change-event pub/sub)**. Microsoft Graph Integration: app
  service for accessing M365 data (Teams / SharePoint / Outlook) via Graph API,
  unified HTTP endpoints + change events. Provider-access gateway over private org
  data + credentials, not open-data (carry-forward test fails). Same M365 provider
  family as `microsoft` / `gmail` / `meet`. No rw-free built.
- **ongakuka** (Bucket D / ad-pixel → V) — axes: **generation-compute (murakumo
  audio inference / Mac fleet for AI music) + B2 storage Custody**. AI Music
  Generation (音楽家, `ongakuka.etzhayyim.com`): Suno-class — lyrics + style prompt
  → vocals + accompaniment / stems via `murakumo:inference/audio` (DiffRhythm/YuE
  MLX + JP-lyrics LoRA), artifacts to B2. A generated track exists only because a
  generation job ran (source = our own audio-inference run) — compute-output
  bookkeeping, not an external-authority catalog (carry-forward test fails;
  fronting = the voxelforge invent-a-catalog trap). Same generation-pipeline
  family as `voxelforge` / `yukkuri` / `dougaka`. No rw-free built.
- **outreach** (Bucket D / ad-pixel → V) — axes: **Custody (prospect Tier-3 PII +
  outreach sequences) + Liability (outreach email-send / anti-spam compliance) +
  Infra/compute (LangGraph research/drafting LLM)**. Sales Outreach Automation
  (`outreach.etzhayyim.com`): LangGraph loop (research_prospect → draft_opening →
  quality_gate → store_step) — prospect email/title/company = **PII Tier 3**
  (ADR-0018); integrations ads / resend / gmail / m365. Private CRM/PII +
  outreach steps, not open-data (carry-forward test fails). Same family as
  `webmk` (marketing-CRM agent). No rw-free built.
- **phone** (Bucket D / ad-pixel → V) — axes: **Custody (call history + contacts
  PII) + Liability (PSTN telephony / telecom + call routing) + Settlement
  (per-minute charges) + Infra (AWS Connect)**. Browser-based phone calling
  platform (`phone.etzhayyim.com`) powered by AWS Connect: WebRTC softphone, call
  control (dial/answer/hold/transfer/DTMF), call history, contact management,
  inbound/outbound PSTN. Private telephony PII + telecom infra, not open-data
  (carry-forward test fails). No rw-free built.
- **recap** (Bucket D / ad-pixel → V) — axes: **Liability (copyright/fair-use) +
  Custody (B2 media + download history) + Infra/compute (yt-dlp + LLM
  summarization)**. Multi-Platform Media Download Agent (`recap.etzhayyim.com`):
  downloads video/audio from YouTube/TikTok/X/NicoNico/etc via yt-dlp, with
  transcript + LLM summarize, download (URL → B2 blob + AT record), getInfo,
  listDownloads. Scope = **社内研究・教育用途 (fair-use only)**, arbitrary public
  download prohibited. Downloaded media is fair-use-restricted third-party
  copyrighted content (not redistributable open-data); summaries are LLM output
  (carry-forward test fails). No rw-free built.
- **ses** (Bucket D / ad-pixel → V) — axes: **Custody (SES案件 Tier-3 PII,
  non-federable) + Liability (staffing/contract business) + Infra/compute (email
  ingest + LLM extraction)**. NOT AWS SES — a **SES (システムエンジニアリング
  サービス, IT-staffing) 案件・状況 ingest pipeline** (`ses.etzhayyim.com`, Tier T3,
  **Non-federable**): ingests SES staffing deals/projects + status from private
  email (Outlook/Exchange) → LLM extraction → graph. Confidential business
  staffing data (client/engineer/rate/contract), explicitly non-federable, not
  open-data (carry-forward test fails). No rw-free built.
- **society6** (Bucket D / ad-pixel → V) — axes: **Custody (per-constituent
  Well-Becoming scores + Kyu/Dan ranks = personal trust/evaluation PII) +
  Infra/compute (5-axis scoring + cross-app behavioral aggregation)**. NOT the
  print-on-demand marketplace — the **Well-Becoming Kyu/Dan rank system**
  (`society6.etzhayyim.com`, the DID Trust Score cluster): scores constituents
  across 5 axes (engagement/competence/contribution/growth/resilience, from
  cross-app behavioral data) → martial-arts kyu/dan rank (calculateScore /
  promoteRank). Per-person evaluation/trust PII, computed (carry-forward test
  fails — no external authority); the COFOG open-data layer is already migrated
  separately as `open-cofog` (Bucket A). No rw-free built.
- **x** (Bucket D / ad-pixel → V) — axes: **Custody (collected X profiles +
  follower-graph + tweets + private timeline = social PII / surveillance
  aggregation) + Liability (X sync/scrape, ToS)**. X (Twitter) Intelligence
  Platform (`x.etzhayyim.com`): x-sync / profile-collection / follower-graph /
  tweet-collection / timeline-analysis — collects/mirrors X data. Unlike `github`
  (public open-source, redistributable open-data → fronted), X data is ToS-
  restricted and collecting individuals' follower-graphs + personalized timelines
  is social-PII surveillance (carry-forward test fails). Same Intelligence-
  Platform family as `facebook`. No rw-free built.
- **insatsu** (Bucket D / substrate-boundary → V) — axes: **Custody (print jobs +
  recipient mailing-address PII) + Settlement (quote/pricing + partner dispatch/
  payment) + Liability (print+mail fulfillment, 善管注意義務 + delivery)**. Print-mail
  fulfillment platform (印刷, `insatsu.etzhayyim.com`): printPartner (print shops +
  methods digital/offset/inkjet) + printMailJob — quotePrintMailJob (price across
  eligible partners) → submit with recipient address → dispatch to a downstream
  partner actor (e.g. 日本郵便 for JPN). The printPartner registry is fulfillment-
  network config (our dispatch partners), not external-authority open-data
  (carry-forward test fails). Same commerce-fulfillment pattern as `okaimono`
  (MoR/fulfillment stays gftd). No rw-free built.
- **playwright** (Bucket D / substrate-boundary → V) — axes: **Infra
  (browser-automation execution primitives) + Custody (session state + vault
  credential injection)**. Browser automation primitives actor
  (`playwright.etzhayyim.com`): 11 XRPC primitives (navigate/click/screenshot/…),
  called by BPMN serviceTasks as a generic capability; execution on local Mac
  daemon / cf-browser (delegates to `cloudflareBrowserRender`), credentials via
  `vault://` ephemeral, session state in D1. Pure execution infra — no product
  surface, not open-data (carry-forward test fails). Same family as
  `cloudflare-browser-render` (V) / `yorishiro` / `hub`. No rw-free built.
- **site** (Bucket D / substrate-boundary → V) — axes: **Infra + Custody + Liability**.
  Site Intelligence Platform / "Internet Clone Gateway" (`site.etzhayyim.com`): the
  SOLE external web-fetch gateway (all apps' external fetch/crawl must route through
  it — direct HTTP fetch prohibited), a 100B-scale hierarchical DID page archive,
  crawl/fetch/frontier pipeline, bulk ingest (Aozora/Gutenberg/NDL/CommonCrawl),
  WET/WAT/WebP output, and LLM text/visual embedding + semantic search. The
  "frontable" page catalog cannot peel off: a 100B-scale RisingWave + IPFS-pinned
  archive cannot have AT PDS as its canonical store — the catalog IS the archive IS
  the infrastructure (no separable layer; building one = invent-a-catalog /
  physically impossible at scale). Sole-fetch-gateway shared-infra dependency + RW +
  IPFS pinning (both regulated-infra axes) + screenshot/full-content storage
  (DMCA/GDPR/robots liability) + embedding compute ⇒ stays gftd whole. Precedent =
  `common-crawl` (legacy codemod, never built rw-free), not `github`. No rw-free.

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

## Bucket D — TODO-PENDING (7, MIGRATION-TODO.md)

> **Phantom removed (2026-06-02)**: `gftdcojp` was listed but is **not an app** —
> no `60-apps/*-project-gftdcojp` dir exists. Throughout `deps.toml` it denotes
> the **vendor org identity** (the gftd.co.jp side of the Consensys boundary,
> repo `github.com/gftdcojp/ai-gftd-apps-gftdcojp`), not a migratable
> `etzhayyim/root` project. Nothing to migrate to etzhayyim-front; by definition
> gftdcojp IS the vendor side. Dropped from the backlog (TRANSFORM 25→24, D 55→54).

**TRANSFORM-pending (0)** — RESOLVED. All names (gftdcojp / harai / hrse / hub /
kaikei / keiei / ops / resource-flow / resource-planner / resource-provider /
robot / scheduler / shiharai / tia / web4 / webpage / wire / worlds / yabai /
yatabase) have been migrated (A) or judged vendor-resident (V). Only the
**ad-pixel codemod (26)** + **substrate-boundary (6)** sublists remain in Bucket D.

**Ad-pixel codemod complete (un-resolved tail)** — RESOLVED (all 28 classified):
every ad-pixel app is migrated (A) or judged vendor-resident (V). The (a)/(c)
fronts were github / live / media-gamers / news / newsletter; the (b) vendor-
resident were communicator / external-service-adapter / facebook /
game-play-uploader / gmail / meet / meeting-recorder / messenger / microsoft /
microsoft-graph / ongakuka / outreach / phone / recap / ses / society6 / x
(plus animeka already in A [catalog front]; mangaka → V [generation/studio side,
compute]; briefing already in V; email-service-adapter/fax
legacy codemod-only).

**Substrate-boundary violation flagged** — ALL RESOLVED: cloudflare-browser-render (V), insatsu (V), open-jpn-mynumber (A), playwright (V), repository (A — Repository-in-Graph git object model = first-party source code → front; FaaS build dispatch + execution stay gftd), site (V — Internet Clone Gateway: sole web-fetch gateway + 100B-scale RW/IPFS archive + embedding compute; Infra+Custody+Liability, no separable frontable layer).

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
