---
id: adr-2605264000-ossekai-information-arbitrage-tier-b-actor-r0
title: "ADR-2605264000: ossekai (御節介) — non-profit religious-corp information-arbitrage elimination + Wellbecoming-nudge artificial-organism actor R0 charter (AT Protocol social-post + feed + @mention first-touch)"
status: proposed
doc_type: adr
topic: ossekai-information-arbitrage-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: information-symmetry
weight: 0.55
priority_note: "Sixth-priority gap-closure actor (gap audit row 6 = 情報非対称 / information arbitrage). Artificial-organism Tier-B actor at did:web:ossekai.etzhayyim.com (20-actors/ossekai/) whose dual mandate is (a) AGGREGATE PUBLICATION of societal information asymmetries (the public-good intel surface) and (b) OSSEKAI-MODE NUDGE — caring proactive notification to opted-in members + Council-gated single-touch @mention to non-member companies/individuals — all delivered via AT Protocol native primitives (NO email, NO SMTP, NO commercial CRM at R0-R2). First-touch channel = AT Proto `app.bsky.feed.post` (existing membrane per ADR-2605231902) + custom feed generator + `@mention` to AT Proto handles. Etymology: 御節介 (ossekai / o-sekkai) — Japanese cultural concept of caring proactive intervention, walking the knife-edge between compassionate-helpfulness and unwelcome-meddling; the constitutional discipline structurally pins the actor on the caring side. The dual-channel architecture is the Charter §1.13 Wellbecoming + §2(c) covert-ops-avoidance + §1.4 anti-individualism + §1.12 state-function routing-around resolution: aggregate publication is the maximum information-symmetry public good (anonymized, no targeting, queryable by anyone with a Bluesky-compatible client); ossekai-mode is the secondary opt-in / Council-gated channel that preserves the cultural ossekai semantic while structurally preventing the actor from becoming surveillance / spam / shame / lobbying / marketing. NO commercial intel/CRM/marketing software (G5 — Salesforce / HubSpot / Marketo / Mailchimp / SendGrid commercial / Constant Contact / Pardot / ZoomInfo / Apollo / Clay / Lemlist / Outreach / SalesLoft / Gong / Chorus / 6sense / Cognism / LeadIQ / Drift PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor exposure of recipient posture; AT Proto + PDS-native architecture sidesteps the entire category). NO email at R0-R2 (N1 — first-touch is AT Proto only; email-bridge to AT Proto DM is R3+ Council Lv7+ unanimity gate). NO surveillance (G3 — PASSIVE-ONLY collection per ADR-2605262400; no live probing of companies / individuals; only pre-published public archives + voluntarily-published AT Proto activity). NO dark patterns (G6 — AT Proto native mute/block/quote-block is honored structurally at projection layer; no urgency / no scarcity / no engagement-hacking / no A/B-test-for-conversion). 8 cells / 8 Lexicons under com.etzhayyim.ossekai.* / 15 gates G1..G15 / 12 non-goals N1..N12 / 4-phase R0..R3 (R0 scaffold / R1 2 core cells aggregate publisher + arbitrage observer / R2 +3 cells member digest + mention dispatcher + consent registry / R3 +3 cells intel analyzer + emergency advisory cross-actor with kazaori + kaizen observer). Cross-actor: kazaori (emergency advisory cross-publication) / chigiri (UPL boundary — ossekai MUST NOT render legal advice; legal-themed advisories cite chigiri.ipLicenseClaim for licensed counsel routing) / iyashi + mitate + yakushi (clinical/diagnostic/pharmaceutical boundary — ossekai MUST NOT render medical advice; health-themed advisories cite cross-actor procedural routing) / toritate (financial transparency intel SOURCE only — toritate publishes; ossekai reads + curates) / e7m-dataset (sensor source per ADR-2605262400) / legal corpus (regulatory source per ADR-2605262800) / baien-moemoekyun (Murakumo inference via judah LiteLLM per G12)."
authoritative_for:
  - ossekai actor R0 charter
  - religious-corp information-arbitrage elimination substrate single SoT
  - `com.etzhayyim.ossekai.*` Lexicon namespace boundary
  - AT Protocol first-touch invariant (NO email / SMTP / commercial CRM at R0-R2)
  - aggregate-first publication discipline (anonymized public-good intel as default)
  - Council-gated single-touch @mention to non-members (G13)
  - native AT Proto mute/block honored at projection layer (G15)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605181200-mst-encrypted-metadata-leak-reduction
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231902-feed-post-membrane-and-feed-discover-projection
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605261000
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
  - adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
  - adr-2605263200-kazaori-disaster-response-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605264000: ossekai (御節介) — non-profit religious-corp information-arbitrage elimination + Wellbecoming-nudge artificial-organism actor R0 charter

**Status**: accepted
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified **information arbitrage**
as priority row 6. Religious-corp has substantial publicly-collected
intelligence assets:

- ADR-2605262400 — public-data ingestion (RIR / GeoLite2 / IANA root /
  RIS / Routeviews / Rapid7-Sonar / OpenINTEL / CAIDA / CZDS /
  CommonCrawl-CDX + Charter Rider scan + PII filter + tier-C carve-out);
- ADR-2605262800 — global legal corpus (~30 sources: US USC / CFR /
  Federal Register / FRCP / CAP Harvard / UK legislation.gov.uk /
  EU EUR-Lex / JP e-Gov 法令 / 裁判所 判例 / ECHR HUDOC / UN treaties /
  ICRC Geneva / etc.; legal-foundations-r1 + chigiri-procedural-r1
  recipes);
- ADR-2605262900 — toritate accounting + audit (financial-transparency
  ledger continuously categorized);
- ADR-2605231902 — `app.bsky.feed.post` membrane + L1-projection
  feed-discover (already-shipped Bluesky-compatible feed surface).

What religious-corp **lacks** is an actor whose mandate is to
(a) detect information-asymmetry pockets — places where public-good
intel exists but is buried beneath legalese / paywalls / dispersed
sources — and (b) deliver Wellbecoming-actionable summaries to people
who would benefit. Without this actor, the intel sits in IPFS-pinned
DataLad subdatasets unused; arbitrage between "those who can read 30
sources in 5 languages" and "those who cannot" persists.

User-stated goal (2026-05-26):

> artificial organism として 社会の情報 arbitrage をなくすための 収集,
> 分析, また ossekai として、企業や個人に対して intel した結果から
> wellbecoming になるための通知やメールを行う agent, actor は設計して

User-stated channel selection (2026-05-26, same session):

> atproto の social post, feed, mention を first touch 想定で

The combination resolves the most-difficult constitutional tensions
that would arise with an email-based outreach actor:

| Tension under email model | Resolution under AT Proto first-touch |
|---|---|
| Vendor CRM (Salesforce / Mailchimp) data-sovereignty | N/A — AT Proto is open-spec; no SaaS dependency |
| Signed sender (DKIM / SPF / DMARC) brittleness | Built-in — every post is DID-bound + cryptographically signed |
| 1-click unsubscribe friction (RFC 8058) | Built-in — `app.bsky.graph.block` + `mute` are spec-native |
| Spam-classifier evasion risk | Mooted — Bluesky-compatible clients render mute/block transparently |
| Per-jurisdiction email law (GDPR / CCPA / CAN-SPAM / APPI / LGPD) | Largely resolved — AT Proto activity is voluntary publication; non-member who has not published a handle is unreachable by design |
| Dark patterns (urgency / shame / engagement-hacking) | Discoverable — every post is public + replayable + auditable |

Etymology: 御節介 (ossekai / o-sekkai) — Japanese cultural concept of
caring proactive intervention. The word carries deliberate ambivalence:
ossekai can be loved (a kind neighbor noticing your missed payment
and quietly arranging a grace period) or resented (an intrusive
acquaintance commenting on your child's school choice). The
constitutional discipline of this actor structurally pins it to the
caring side via four invariants: (1) aggregate publication is the
DEFAULT mode; (2) individual @mention requires Council Lv6+ ≥3 +
documented member-impact OR explicit prior consent; (3) all output is
Wellbecoming-positive in framing (no shame / no fear / no zero-sum);
(4) AT Proto native mute/block is honored structurally (the moment a
target signals "do not contact," ossekai is structurally prevented from
contacting them again).

Constitutional constraints (inherited; not adjustable):

- **NOT surveillance** (G3 + N2) — PASSIVE-ONLY collection per
  ADR-2605262400 — no live DNS / port-probe / traceroute / WHOIS /
  RDAP / DoH / handle-enumeration against third parties; only
  pre-published public archives + voluntarily-published AT Proto
  activity. Charter §2(c) covert-ops avoidance holds.
- **NOT marketing automation** (G6 + N3) — no growth-hacking / no
  viral-loop engineering / no A/B-test-for-conversion / no urgency
  artifacts / no engagement-hacking. Wellbecoming framing only.
- **NOT lobbying / political campaign** (N6) — political-process
  advisories (election dates / candidate positions / referendum
  procedures) are out of scope; chigiri.taxReceipt 501(c)(3)-style
  rules apply if religious-corp ever pursues tax-deductible donor
  routing.
- **NOT individual targeting without consent or Council attestation**
  (G13) — Council Lv6+ ≥3 attestation + documented member-impact OR
  explicit prior consent (`externalMentionConsent`) required for
  any non-member @mention campaign >50 handles.
- **NOT children-targeted** (N11) — manabi G3 anti-dependency UX
  parallel; minor-targeted advisories DENIED at the dispatcher gate
  (handle age-self-declared + Charter Rider §2(d) Wellbecoming check).
- **NO email at R0-R2** (N1) — first-touch is AT Proto only. Email
  bridge to AT Proto DM (for members who request it) is R3+ Council
  Lv7+ unanimity gate; non-member email contact remains permanently
  prohibited at this charter level.
- **NO commercial intel/CRM/marketing software** (G5) — Salesforce /
  HubSpot / Marketo / Mailchimp / SendGrid commercial / Constant
  Contact / Pardot / ZoomInfo / Apollo / Clay / Lemlist / Outreach /
  SalesLoft / Gong / Chorus / 6sense / Cognism / LeadIQ / Drift
  PROHIBITED per Charter Rider §2(e) + §2(c). AT Proto + PDS-native
  architecture sidesteps the entire category.
- **Murakumo-only inference** (G12 + ADR-2605215000) — joucho cadence
  + intel cross-correlation + Wellbecoming framing via judah LiteLLM
  → gemma4:e4b / baien-moemoekyun (when shipped). Commercial AI
  (OpenAI direct, Anthropic-direct from vendor key, AWS Bedrock, etc.)
  PROHIBITED.
- **PASSIVE-ONLY** (G3) — sensors consume pre-published public
  archives via `e7m-dataset add` / `pull` ONLY. No live DNS resolution
  / port probes / traceroute / WHOIS / RDAP / DoH / handle-enumeration
  against third parties.

# Decision

Create `ossekai` (御節介) as a Tier-B religious-corp artificial-organism
information-arbitrage elimination + Wellbecoming-nudge actor at
`20-actors/ossekai/`, with DID `did:web:ossekai.etzhayyim.com`, Lexicon
namespace `com.etzhayyim.ossekai.*`. R0 = scaffold only; all cells
import-time `RuntimeError`. First-touch channel = AT Protocol
`app.bsky.feed.post` (existing membrane per ADR-2605231902) + custom
feed generator + `@mention` to AT Proto handles.

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `ossekai` (御節介 — caring proactive intervention) |
| DID | `did:web:ossekai.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.ossekai.*` |
| Form | 任意団体 internal artificial-organism information-arbitrage substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格 — Preamble §0.4 Lv7+ unanimity lock) |
| Tier | Tier-B per-domain leader actor |
| First-touch channel | AT Protocol — `app.bsky.feed.post` (public feed) + custom feed generator (subscription) + `@mention` (Council-gated single-touch); NO email / SMTP at R0-R2 |
| Cross-actor (data sources) | e7m-dataset (ADR-2605262400) / legal corpus (ADR-2605262800) / toritate (financial transparency SOURCE) |
| Cross-actor (boundary) | chigiri (UPL — no legal advice) / iyashi + mitate + yakushi (no medical advice) / kazaori (emergency advisory) |
| Inference | Murakumo via judah LiteLLM → gemma4:e4b / baien-moemoekyun (G12) |
| Storage | kotoba (ADR-2605262130) — content-addressed; AT Proto MST membrane per ADR-2605231902 |

## §2. Scope (5 sections)

### A. Information-arbitrage observation

- Continuous joucho-cadence sensor consumption (heartbeat-cadence
  organism pattern per ADR-2605232345 + ADR-2605262400);
- Sensors at R1 = e7m-dataset Tier-A foundations (RIR / GeoLite2 /
  IANA root / RIS / Routeviews) + ADR-2605262800 legal-foundations-r1
  recipe (US USC / UK leg.gov.uk / JP e-Gov / EU EUR-Lex / CAP Harvard
  case law);
- Sensors at R2 = +5 (toritate financial-transparency ledger /
  product-recall feeds via OECD ICSMS / safety advisory ISO public
  feeds / cross-actor mitate emergency-keyword Lexicon / cross-actor
  kazaori emergency declarations);
- Each sensor emits `arbitrageGapReport` records identifying public-
  good intel pockets — public-domain facts that are not yet broadly
  surfaced.

### B. Intel analysis + Wellbecoming framing

- joucho-cadence cross-correlation across sensor streams via Murakumo
  inference (G12);
- Classification: priority (high / mid / low) × scope (member-only /
  jurisdiction / global) × audience (any / corp-only / individual);
- Wellbecoming framing check (G10) — every advisory MUST pass
  Wellbecoming-positive framing audit before publication;
- Anti-individualism check (G11) — advisory text emphasizes community
  + multi-generational context over individual nudge;
- UPL boundary (cross-actor chigiri) — legal-themed advisories cite
  chigiri.ipLicenseClaim for licensed-counsel routing; ossekai does
  NOT render legal advice;
- Medical boundary (cross-actor iyashi + mitate + yakushi) — health-
  themed advisories cite cross-actor procedural routing; ossekai does
  NOT render medical advice;
- Output: `wellbecomingAdvisory` records.

### C. Aggregate publication (DEFAULT mode)

- **The aggregate channel is the default and primary mode**;
- Anonymized advisories published to AT Proto `app.bsky.feed.post`
  via existing membrane per ADR-2605231902 (preserving `x-etzhayyim-
  substrate: mst-ipfs-l2` header);
- Custom AT Proto feed generator `feed.ossekai.wellbecoming` curates
  ossekai advisories for any Bluesky-compatible client subscriber;
- Every published post carries:
  - `did:web:ossekai.etzhayyim.com` signed sender (G9);
  - Charter Rider §2(a)-(h) scan pass (G1);
  - Wellbecoming framing audit pass (G10);
  - kotoba-datomic attestation lineage (G2);
  - Source citation (`arbitrageGapReport.sourceCids[]`);
- `feedPostAttestation` Lexicon record per emission (audit trail).

### D. Member opt-in digest (encrypted private channel)

- Adherent SBT members may subscribe to a private digest via
  `memberDigestSubscription` Lexicon record;
- Default opt-in cadence = weekly; per-category opt-out (regulatory /
  health-procedural / financial-transparency / legal-procedural /
  emergency / civic);
- Digest delivered via encrypted envelope per ADR-2605181100
  (XChaCha20-Poly1305 + Signal-wrapped per-recipient keys);
- `memberDigestRecord` Lexicon record per delivery (audit trail; G8
  structural — encryptedPayloadCid REQUIRED).

### E. Non-member @mention (Council-gated single-touch)

- AT Proto `@mention` to a non-member handle requires:
  1. Council Lv6+ ≥3 attestation via `mentionDispatchAttestation`
     (G13 STRUCTURAL minLength 3);
  2. Documented member-impact OR explicit prior consent
     (`externalMentionConsent`);
  3. Rate limit ≤1 mention / 90-day rolling window / handle (G7);
  4. AT Proto native mute / block check via `unsubscribeRecord`
     ingestion of `app.bsky.graph.block` / `mute` (G15 STRUCTURAL —
     blocked handles are projection-layer rejected);
  5. Wellbecoming framing audit pass (G10);
  6. Charter Rider §2(a)-(h) scan pass (G1);
- Per `mentionDispatchAttestation.attestingCouncilDids` minLength 3;
- Campaign-scale dispatch (>50 unique non-member handles) requires
  Council Lv6+ ≥4 (one additional attestation).

## §3. Cells (8 Pregel cells under `20-actors/magatama/cells/ossekai_*/`)

All R0 path-reserved; import-time
`RuntimeError("ossekai R0 scaffold: activate via Council ADR + R1 ratification + e7m-dataset Tier-A foundations available + legal-foundations-r1 recipe ratified + chigiri R1 active for UPL boundary + iyashi R1 active for medical boundary")`
at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `arbitrage_observer` | issachar | continuous (heartbeat) | sensor stream consume → arbitrageGapReport |
| 2 | `intel_analyzer` | issachar | joucho-cadence | arbitrageGapReport → wellbecomingAdvisory + cross-correlation + Wellbecoming framing |
| 3 | `aggregate_publisher` | issachar | hourly | wellbecomingAdvisory (anonymized) → AT Proto `app.bsky.feed.post` via membrane + custom feed generator + feedPostAttestation |
| 4 | `member_digest` | issachar (paired with paired-PDS node) | weekly | wellbecomingAdvisory (member-filtered) → encrypted envelope (ADR-2605181100) → memberDigestRecord |
| 5 | `mention_dispatcher` | issachar | event (Council attestation triggered) | mentionDispatchAttestation + (externalMentionConsent OR memberImpactAttestation) + mute/block check → AT Proto `@mention` + feedPostAttestation |
| 6 | `consent_registry` | issachar | continuous | externalMentionConsent + unsubscribeRecord + AT Proto block/mute ingestion → consent state |
| 7 | `kaizen_observer` | issachar | quarterly | unsubscribe rate / spam-classifier flag / re-engagement-after-opt-out / member-impact-attestation false-positive → KaizenProposal (per ADR-2605240200) |
| 8 | `emergency_advisory` | issachar (kazaori-paired) | event (kazaori emergencyDeclarationAttestation) | kazaori cross-actor → expedited Wellbecoming-positive emergency advisory (NO fear-amplification per G10) → AT Proto `app.bsky.feed.post` + custom feed |

R1 activation gates each cell separately. Murakumo placement = `issachar`
(witness pair node for organism observation; existing pattern from
ADR-2605240200 KaizenObserverCell).

## §4. Lexicons (8, all under `com.etzhayyim.ossekai.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `arbitrageGapReport` | arbitrage_observer | Per-detection record of information-asymmetry pocket; source CIDs + topic + scope + estimated affected population |
| L2 | `wellbecomingAdvisory` | intel_analyzer | Curated Wellbecoming-actionable advisory; priority × scope × audience; chigiri/iyashi/mitate/yakushi UPL/medical-advice citation if applicable; G10 framing-audit attestation |
| L3 | `feedPostAttestation` | aggregate_publisher + mention_dispatcher + emergency_advisory | Per AT Proto post emission audit-trail; carries post AT-URI + Wellbecoming-framing-pass + Charter Rider scan pass + sender DID signature |
| L4 | `memberDigestSubscription` | member_digest + consent_registry | Adherent SBT member subscription record; per-category opt-out granularity; cadence (weekly default); PDS-private |
| L5 | `memberDigestRecord` | member_digest | Per-delivery audit-trail; G8 STRUCTURAL: encryptedPayloadCid REQUIRED (ADR-2605181100) |
| L6 | `mentionDispatchAttestation` | mention_dispatcher | Council Lv6+ ≥3 attestation for non-member @mention campaign; G13 STRUCTURAL: attestingCouncilDids minLength 3 (≥4 if campaignSize>50); memberImpactAttestation OR externalMentionConsent ref required |
| L7 | `externalMentionConsent` | mention_dispatcher + consent_registry | Non-member explicit prior consent record (granted by AT Proto handle owner); per-category granularity; revocable any time via `unsubscribeRecord` |
| L8 | `unsubscribeRecord` | consent_registry | Unified unsubscribe; ingests AT Proto `app.bsky.graph.block` + `app.bsky.graph.mute` AND explicit `unsubscribeRecord` emission; G15 STRUCTURAL: per-handle effective immediately at projection layer |
| L9 | `silenOssekaiReview` | (Council attestation scope) | Quarterly Council audit; arbitrage-elimination effectiveness + unsubscribe rate + spam-classifier flag rate + re-engagement-after-opt-out detection + member-impact-attestation accuracy + G10 framing-audit Wellbecoming preservation |

(Lexicon count = 9 records total; the §4 table header says "8" because
the original draft was 8 + silenOssekaiReview; counting silenOssekaiReview
brings the practical total to 9 once written.)

## §5. Gates (15, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every advisory MUST pass `pymagatama.organism.sensors.charter_rider.scan()` §2(a)-(h) on input AND output. |
| **G2** | Every record MUST emit `com.etzhayyim.ossekai.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **PASSIVE-ONLY** collection — no live DNS / port-probe / traceroute / WHOIS / RDAP / DoH / handle-enumeration against third parties; only pre-published public archives + voluntarily-published AT Proto activity (per ADR-2605262400). |
| **G4** | **Aggregate-first publication** — anonymized AT Proto `app.bsky.feed.post` is the DEFAULT mode; targeted @mention is the secondary mode; the default order MUST NOT be inverted at runtime. |
| **G5** | **NO commercial intel / CRM / marketing software** — Salesforce / HubSpot / Marketo / Mailchimp / SendGrid commercial / Constant Contact / Pardot / ZoomInfo / Apollo / Clay / Lemlist / Outreach / SalesLoft / Gong / Chorus / 6sense / Cognism / LeadIQ / Drift PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty. |
| **G6** | **NO dark patterns** — AT Proto native mute / block / quote-block honored structurally at projection layer (G15); no urgency artifacts / no scarcity / no engagement-hacking / no A/B-test-for-conversion / no manipulation. |
| **G7** | **Rate limit hard-coded** — per non-member handle ≤1 @mention / 90-day rolling window; per Adherent-SBT member ≤1 digest/week + ≤1 ad-hoc advisory/month UNLESS explicitly subscribed-higher via `memberDigestSubscription.cadenceOverride`. |
| **G8** | **Encrypted envelope MANDATORY** for member private digest — `memberDigestRecord.encryptedPayloadCid` REQUIRED (ADR-2605181100); plaintext rejected at schema layer. |
| **G9** | **Signed sender DID transparent** — every AT Proto post (feed-post OR @mention) carries `did:web:ossekai.etzhayyim.com` + cryptographic signature; no spoofing / no white-labeling / no proxy-sender. |
| **G10** | **Wellbecoming-positive framing only** — Charter §1.13 — no Gore / no fear-amplification / no shame / no zero-sum framing; multi-gen + community context preferred over individual-targeted; framing-audit attestation in every `wellbecomingAdvisory`. |
| **G11** | **Anti-individualism** — Charter §1.4 — advisory text emphasizes community/multi-gen impact; individual nudge is the secondary mode; campaign metadata MUST record audience-scope-distribution (community / multi-gen / individual share). |
| **G12** | Murakumo-only inference per ADR-2605215000 — commercial AI (OpenAI direct / Anthropic-direct from vendor key / AWS Bedrock / Vertex AI direct / RunPod GPU / Lambda Labs / CoreWeave / Vast.ai) PROHIBITED. |
| **G13** | **Council Lv6+ ≥3 attestation for non-member @mention campaign**; ≥4 attestation for campaign >50 unique handles; `mentionDispatchAttestation.attestingCouncilDids` minLength STRUCTURAL. |
| **G14** | `silenOssekaiReview` quarterly audit — arbitrage-elimination effectiveness + unsubscribe rate + spam-classifier flag rate + re-engagement-after-opt-out detection + member-impact-attestation accuracy + G10 framing-audit Wellbecoming preservation. |
| **G15** | **AT Proto native mute / block honored at projection layer** — `unsubscribeRecord` ingests `app.bsky.graph.block` + `app.bsky.graph.mute`; mention_dispatcher cell rejects dispatch to muted/blocked handle BEFORE composing post (not after; the post never enters MST). |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT email-based outreach at R0-R2 (AT Proto first-touch only; email-bridge to AT Proto DM for opted-in members is R3+ Council Lv7+ unanimity; non-member email contact permanently prohibited at this charter level). |
| N2 | NOT surveillance / NOT OSINT-for-hire / NOT private-detective service. |
| N3 | NOT marketing automation / NOT growth-hacking / NOT viral-loop engineering / NOT engagement-hacking. |
| N4 | NOT corporate intelligence-for-hire / NOT competitive intel / NOT industrial espionage. |
| N5 | NOT social pressure / NOT public shaming / NOT vigilante coordination. |
| N6 | NOT lobbying / NOT political campaign mailing / NOT election-result-targeting. |
| N7 | NOT commercial outreach (no upsell content; no affiliate; no referral-fee). |
| N8 | NOT credit-score / NOT financial-blacklist / NOT debt-collection. |
| N9 | NOT match-making / NOT dating / NOT romantic-introduction. |
| N10 | NOT recruitment / NOT headhunting / NOT employment-targeting. |
| N11 | NOT children-targeted (manabi G3 anti-dependency parallel; minor-targeted advisories DENIED at the dispatcher gate). |
| N12 | NOT chigiri/legal-threat proxy / NOT Transparent-Force-authorization proxy / NOT excommunication-procedure proxy. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 8 cells path-reserved. 9 Lexicons schema skeleton. | No deployment |
| **R1** | post-Bootstrap-Council ratify + e7m-dataset Tier-A foundations available + legal-foundations-r1 recipe ratified + chigiri R1 active for UPL boundary + iyashi R1 active for medical boundary | Activate 3 cells: `arbitrage_observer` + `intel_analyzer` + `aggregate_publisher`. AT Proto `app.bsky.feed.post` + custom feed generator `feed.ossekai.wellbecoming` live. ≤100 advisories / week ceiling. NO targeted @mention yet (campaign discipline test phase). | issachar (single node) |
| **R2** | post-R1 + ≥30-day public objection + first quarterly `silenOssekaiReview` Council attestation + ≥1 cross-actor advisory cycle (e.g. kazaori-emergency or chigiri-procedural) | Activate +3 cells: `member_digest` (encrypted envelope per ADR-2605181100; ≤500 opt-in members), `mention_dispatcher` (Council Lv6+ ≥3 attestation gate live; ≤50 non-member handles/quarter cumulative), `consent_registry` (AT Proto block/mute ingestion live). | issachar + zebulun (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + multi-jurisdictional consent compliance attestation (JP 個人情報保護法 第27条 + GDPR Article 7 + APPI 第18条 + CCPA opt-out + Brazil LGPD + CAN-SPAM honest-sender — all attested by chigiri R3+ multi-juris) + ≥4 consecutive `silenOssekaiReview` cycles with G14 compliance | Activate +2 cells: `kaizen_observer` (Kaizen pattern per ADR-2605240200; 6 new rules R12..R17 spam-classifier / unsubscribe-spike / re-engagement-after-opt-out / member-impact-attestation-false-positive / arbitrage-publication-staleness / framing-audit-drift), `emergency_advisory` (kazaori cross-actor; expedited Wellbecoming-positive emergency advisory). ≤5000 opt-in members. ≤200 non-member handles/quarter cumulative. | issachar + zebulun + dan (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `e7m-dataset` (ADR-2605262400) | ← | Sensor data sources (RIR / GeoLite2 / IANA / RIS / Routeviews / Rapid7-Sonar / OpenINTEL / CAIDA / CZDS / CommonCrawl-CDX); tier-A consumed at R1; tier-C internal-only flag respected at R2 per G3 + Charter Rider §2(c) |
| legal corpus (ADR-2605262800) | ← | Regulatory / statutory / case-law intel feed (legal-foundations-r1 recipe at R1; full corpus at R2) |
| `toritate` (ADR-2605262900) | ← | Financial transparency intel (toritate publishes; ossekai reads + curates — ossekai MUST NOT modify or extend toritate ledger) |
| `chigiri` (ADR-2605262700) | ↔ | UPL boundary — ossekai MUST NOT render legal advice; legal-themed advisories cite chigiri.ipLicenseClaim for licensed-counsel routing; cross-actor consultation on multi-jurisdictional consent compliance at R3 |
| `iyashi` (ADR-2605263000) | ↔ | Medical-advice boundary — health-themed advisories cite iyashi cross-actor for clinical procedural routing |
| `mitate` | ↔ | Diagnostic boundary — symptom-themed advisories cite mitate cross-actor; emergency-keyword pattern existing |
| `yakushi` (ADR-2605250500) | ↔ | Pharmaceutical-advice boundary — medication-themed advisories cite yakushi cross-actor |
| `kazaori` (ADR-2605263200) | ↔ | Emergency advisory cross-actor; `emergency_advisory` cell receives kazaori.emergencyDeclarationAttestation → expedited Wellbecoming-positive emergency advisory (NO fear-amplification per G10) |
| `baien-moemoekyun` (ADR-2605262100) | ← | Murakumo inference via judah LiteLLM → gemma4:e4b at R1; baien-moemoekyun MoE at R3+ when shipped |
| `kotoba` (ADR-2605262130) | ← | Storage substrate; ossekai records via kotoba-kqe arrangements |
| `feed-discover` (ADR-2605231902) | ← | AT Proto `app.bsky.feed.post` membrane + L1-projection (preserved unchanged; ossekai is a producer / feed-discover continues to consume) |

## §9. Constitutional novelty notes

### G4 aggregate-first invariant
The default-mode discipline is constitutionally novel. Most "intel
delivery" actors in adjacent ecosystems are individual-targeted by
default (HubSpot / Mailchimp / Salesforce) with aggregate publication
as the secondary mode. ossekai inverts this: aggregate publication
(public-good, anonymized) is the default; targeted contact requires
Council attestation + per-recipient consent OR documented member-impact.
This is the structural enforcement of Charter §2(c) covert-ops
avoidance + Charter §1.4 anti-individualism in the information-delivery
domain.

### G10 Wellbecoming framing audit
Every advisory passes a framing audit before publication. The audit
checks:
1. Absence of Gore / fear-amplification / shame / zero-sum framing;
2. Presence of constructive next-action OR community context;
3. Multi-gen impact mention (where applicable);
4. UPL / medical-advice / financial-advice boundary citation
   (where applicable; cross-actor procedural routing).

This is a heavier discipline than is typical in "intel briefing"
pipelines but is structurally required by Charter §1.13.

### G15 native AT Proto mute/block honored at projection layer
The `mention_dispatcher` cell rejects dispatch to muted/blocked
handle BEFORE composing the post. The post never enters MST. This
is the structural enforcement of "the moment a target signals 'do not
contact,' ossekai is structurally prevented from contacting them
again." Compared to email-based unsubscribe (where mail is composed
first then suppressed), AT Proto + projection-layer rejection is
cleaner — the negative-signal arrives before composition, so there
is no auditable "unsent draft" record.

## §10. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605264000-ossekai-information-arbitrage-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/ossekai/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 9 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/ossekai/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 73 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #6 priority (information arbitrage) — religious-corp
  finally has an actor whose mandate is to surface public-good intel
  to people who would benefit;
- AT Proto first-touch channel selection resolves seven distinct
  constitutional tensions that would arise with email-based outreach
  (vendor CRM data-sovereignty / signed-sender brittleness /
  unsubscribe friction / spam-classifier evasion / per-jurisdiction
  email law / dark patterns / auditability) — see Context table;
- G4 aggregate-first invariant structurally enforces Charter §2(c)
  + §1.4 in the information-delivery domain (novel discipline);
- G13 Council Lv6+ ≥3 non-member campaign gate mirrors chigiri +
  toritate precedent (no new governance pattern needed);
- G15 native AT Proto mute/block honored at projection layer is
  cleaner than email-based unsubscribe (rejection BEFORE composition,
  not after);
- Cross-actor leverages existing assets (e7m-dataset / legal corpus /
  toritate / kazaori / feed-discover membrane) — ossekai is mostly a
  curation + framing + publication actor, not a new ingestion stack.

**Negative / cost**:

- AT Proto reach is narrower than email — companies / individuals
  without AT Proto handles are unreachable by design at R0-R3
  (this is intentional per N1 + N2 but is a real cost relative to
  email outreach);
- Custom AT Proto feed generator `feed.ossekai.wellbecoming` requires
  PDS + feed-gen infrastructure at R1 — `50-infra/etzhayyim-did-web/`
  PDS scope may need extension;
- G10 Wellbecoming framing audit adds Murakumo inference cost per
  advisory (G12 capacity headroom check at R1);
- G13 Council Lv6+ ≥3 attestation per non-member campaign is real
  governance overhead — campaigns ≤50 handles take ≥3 Council
  signatures; campaigns >50 take ≥4;
- `silenOssekaiReview` quarterly audit is governance overhead that
  scales with member + non-member volume;
- The G4 aggregate-first invariant creates a structural ceiling on
  per-member personalization — members who would prefer "all
  ossekai output tailored just for me" are constitutionally limited
  to the opt-in digest format (member_digest cell) which is itself
  category-granular but not LLM-personalized.

**Forward-compatibility**:

- Email-bridge to AT Proto DM for opted-in members is R3+ Council
  Lv7+ unanimity (kept as future extension, not blocked at this
  charter level);
- Cross-religious-corp federation potential: if a future federated
  religious-corp emerges (per AT Proto federation), ossekai feed-gen
  is portable;
- Future `kokoro` (post-emergency mental health surge, gap audit
  row 9) integrates via emergency_advisory cell extension at R3+;
- Future `wakai` (mutual aid pooling, gap audit row 7) integrates
  via member_digest cell extension (mutual-aid-themed digest
  category at R3+);
- baien-moemoekyun MoE (ADR-2605262100 R3+) inference upgrade at R3+
  improves framing-audit and intel cross-correlation latency.

# Alternatives Considered

1. **Subsume into chigiri (legal procedure substrate)**. Rejected —
   chigiri is procedural-internal; ossekai is information-external
   + AT Proto-public-facing. SRP violation.

2. **Use email (SMTP) as first-touch with proper RFC-8058 unsubscribe
   + DKIM/SPF/DMARC + commercial ESP**. Rejected per user direction
   2026-05-26 ("atproto の social post, feed, mention を first touch
   想定で"); also rejected because commercial ESP (Mailchimp /
   SendGrid / Mailgun / etc.) introduces Charter Rider §2(e) anti-
   gatekeeping + §2(c) vendor data-sovereignty concerns that AT Proto
   first-touch avoids entirely.

3. **Use a commercial intel/CRM platform (HubSpot / Salesforce / etc.)
   as the operational backbone**. Rejected per G5 + Charter Rider
   §2(e) + §2(c).

4. **Allow individual-targeted dispatch as the default mode (G4
   inverted)**. Rejected — Charter §2(c) covert-ops avoidance +
   Charter §1.4 anti-individualism + Charter §1.13 Wellbecoming
   structurally require aggregate-first.

5. **Allow Founder Lv7+ unilateral non-member @mention authorization
   (G13 weakened to ≥1)**. Rejected per institutional integrity
   precedent from ADR-2605262200 — Council Lv6+ ≥3 minimum even in
   urgent situations.

6. **Skip Council attestation for non-member campaigns ≤10 handles
   (G13 carve-out)**. Rejected — the structural property of G13 is
   that ALL non-member @mention requires Council attestation; the
   campaign-size threshold determines the attestation count (≥3 vs
   ≥4), not whether attestation is required.

7. **Allow children-targeted advisories with parental SBT consent
   (N11 carve-out)**. Rejected — manabi G3 anti-dependency UX
   parallel + Charter §2(d) Wellbecoming minor-protection invariant.
   Minor-targeted advisories DENIED at the dispatcher gate at all
   phases R0-R3.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap (G8 source)
- ADR-2605192100 — Mission Charter (Wellbecoming + §1.4 + §1.13 + §2(c))
- ADR-2605192200 — Charter Compliance Rider v2.0 (G5 + Charter Rider §2(e) source)
- ADR-2605192300 — Council 5-of-7 Safe (G13 attestation source)
- ADR-2605215000 — Inference Murakumo-only (G12 source)
- ADR-2605231902 — `app.bsky.feed.post` membrane + L1-projection feed-discover (AT Proto first-touch substrate)
- ADR-2605232345 — UNSPSC organism Wave 1 (joucho heartbeat-cadence pattern)
- ADR-2605240200 — KaizenObserverCell (kaizen_observer pattern source)
- ADR-2605261000 — Labor Liberation Transition Mechanism (steward-flow boundary)
- ADR-2605262130 — Kotoba storage substrate
- ADR-2605262400 — Public-data ingestion (sensor source)
- ADR-2605262700 — chigiri (cross-actor UPL boundary)
- ADR-2605262800 — Global legal corpus ingestion (legal-foundations-r1 recipe source)
- ADR-2605262900 — toritate (cross-actor financial-transparency source)
- ADR-2605263000 — iyashi (cross-actor medical-advice boundary)
- ADR-2605263100 — mizuho (cross-actor reference)
- ADR-2605263200 — kazaori (cross-actor emergency advisory)
- `/CHARTER-RIDER.md` §2(c) + §2(e) — G3 + G5 sources
