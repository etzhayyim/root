---
id: adr-2606022300-akashi-public-ad-disclosure-kotoba-actor-r0
title: "ADR-2606022300: 証 (akashi) — public ad-disclosure kotoba actor for platform ad libraries (R0)"
status: proposed
doc_type: adr
topic: akashi-public-ad-disclosure-actor
authoritative: true
last_verified: 2026-06-02
priority: 7.8
axis: actor-architecture
weight: 0.78
priority_note: "Names a new Tier-B actor for passive, source-cited ingestion of already-public advertising-transparency disclosures from platforms such as Meta/Facebook/Instagram, LINE, X/Twitter, Google/YouTube, TikTok, and regional ad libraries into kotoba EAVT. Sibling to danjo; bounded away from malak except for voluntary fraud/malware-ad evidence handoff."
authoritative_for:
  - new Tier-B actor `akashi` (public ad-disclosure transparency graph)
  - kotoba EAVT schema for platform / advertiser / creative / disclosure / targeting-summary / spend-range / impression-range / landing-page / snapshot
  - boundary between akashi (public ad disclosure) and malak (confidential cybercrime intelligence)
  - `com.etzhayyim.akashi.*` Lexicon namespace
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605301600-danjo-public-accountability-oversight-tier-b-actor-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
related:
  - adr-2605172000-malak-onion-frontier-ransomware-tracking
  - adr-2605131600-malak-orchestration-langgraph-pregel-langserve
  - adr-2605302130-himotoki-disclosure-request-tier-b-actor-r0
  - adr-2605312400-moushibumi-democratic-participation-concierge-tier-b-actor-r0
  - adr-2604281900-open-adnetwork-actor
  - adr-0084-yoro-ads-integration
supersedes: []
superseded_by: []
---

# ADR-2606022300: 証 (akashi) — Public Ad-Disclosure Kotoba Actor

**Status**: proposed
**Date**: 2026-06-02
**Deciders**: Jun Kawasaki

# Context

The repo already has advertising actors, but they answer different questions:

- `open-adnetwork` designs first-party ad serving, campaigns, impressions and
  revenue.
- `yoro-ads` and `advectors` design native sponsored posts / ad delivery.
- `danjo` observes public government records.
- `malak` handles confidential cybercrime intelligence and law-enforcement
  referral packages.

None of these is the actor for the question: "can we hold the publicly
disclosed ad libraries of Facebook / Instagram / LINE / X and similar
platforms as a kotoba database?"

That capability is useful, but constitutionally sensitive. Ad libraries often
include political or social-issue ads, advertiser identities, creative text,
media thumbnails, landing pages, rough spend / impression ranges, and sometimes
targeting disclosures. A careless implementation becomes political profiling,
commercial ad intelligence, or a target list. A correct implementation is a
passive transparency mirror over records that platforms have already chosen or
been legally required to publish.

# Decision

Create **`akashi`** (証), DID `did:web:akashi.etzhayyim.com`, namespace
`com.etzhayyim.akashi.*`, as a **Tier-B kotoba-native public ad-disclosure
actor** in **R0 scaffold**.

akashi is the advertising-disclosure sibling of danjo:

- danjo mirrors and cross-references public state output.
- akashi mirrors and cross-references public platform ad disclosures.
- both are passive, source-cited, non-adjudicating, open-method, and kotoba
  EAVT-native.

## Scope

akashi ingests only **already-public ad disclosure artifacts** from platform
transparency sources and stores them as content-addressed kotoba datoms:

- platform/source registry: platform, jurisdiction, disclosure surface, license
  / ToS posture, fetch cadence, robots / API constraints, retention windows.
- advertiser identity: disclosed page/account/business name, platform IDs,
  website/landing domains, jurisdiction, public verification markers.
- ad creative disclosure: text, media hash/CID, thumbnail hash, language,
  declared category, issue/political classification as disclosed by source.
- delivery disclosure: first seen / last seen, active/inactive status, rough
  spend range, rough impression range, regions, demographic or interest
  summaries where disclosed.
- landing-page evidence: URL, normalized domain, redirect chain summary,
  content hash, safety flags, collection timestamp.
- snapshot lineage: source URL/API endpoint, source record ID, fetched_at,
  payload hash, parser version, source terms revision, methodNote CID.

akashi does **not** serve ads, sell ad intelligence, rank voters, infer private
traits, or issue legal / criminal conclusions.

## Platform Source Registry

R0 reserves a source registry rather than hard-coding platform behavior:

| Source family | Examples | R0 stance |
|---|---|---|
| social ad libraries | Meta/Facebook/Instagram, X/Twitter, TikTok | passive public disclosure only; no logged-in scraping; source terms recorded per adapter |
| messaging / portal ad disclosures | LINE and regional transparency portals | public pages or official APIs only |
| search/video ad libraries | Google / YouTube political-ad transparency surfaces | public disclosed fields only |
| official regulator datasets | election-ad and DSA-style ad repositories where available | preferred when bulk/public export exists |

Every adapter must emit `sourcePolicySnapshot` before it can emit
`adDisclosureSnapshot`.

## kotoba EAVT Vocabulary

R0 reserves these predicate groups:

| Entity | Predicates |
|---|---|
| `:ad.platform/source` | `:platform/name`, `:platform/source-url`, `:platform/jurisdiction`, `:platform/access-mode`, `:platform/retention-window`, `:platform/terms-cid` |
| `:ad.disclosure/snapshot` | `:ad/source-record-id`, `:ad/source-url`, `:ad/fetched-at`, `:ad/payload-cid`, `:ad/parser-version`, `:ad/source-policy-cid` |
| `:ad.advertiser/entity` | `:advertiser/name`, `:advertiser/platform-id`, `:advertiser/page-url`, `:advertiser/verified-status`, `:advertiser/website-domain` |
| `:ad.creative/entity` | `:creative/text-cid`, `:creative/media-cid`, `:creative/media-hash`, `:creative/language`, `:creative/disclosed-category` |
| `:ad.delivery/disclosure` | `:delivery/started-at`, `:delivery/ended-at`, `:delivery/status`, `:delivery/spend-range`, `:delivery/impression-range`, `:delivery/region-summary` |
| `:ad.targeting/disclosure` | `:targeting/disclosed-age-range`, `:targeting/disclosed-gender`, `:targeting/disclosed-interests`, `:targeting/source-limited` |
| `:ad.landing/evidence` | `:landing/url`, `:landing/domain`, `:landing/redirect-summary-cid`, `:landing/content-hash`, `:landing/safety-flags` |
| `:ad.observation/method` | `:method/name`, `:method/version`, `:method/source-code-cid`, `:method/limits`, `:method/false-positive-notes` |

The graph is stored in kotoba only. No Kotoba/Datomic/Postgres/Lance projection is
authoritative.

## Cells

| Cell | Node | Phase | I/O |
|---|---|---|---|
| `akashi_source_registry` | reuben | periodic | curated public source registry -> `sourcePolicySnapshot` |
| `akashi_disclosure_fetch` | reuben | periodic | public source/API/bulk export -> raw payload CID + `adDisclosureSnapshot` |
| `akashi_normalize_creative` | reuben | continuous | snapshot payload -> advertiser / creative / delivery datoms |
| `akashi_landing_evidence` | gad | rate-limited | disclosed landing URL -> redirect/domain/hash evidence; no interaction beyond fetch |
| `akashi_cross_platform_link` | gad | continuous | advertiser/domain/creative hashes -> non-adjudicating `adDisclosureLink` |
| `akashi_transparency_report` | naphtali | periodic | aggregate trends -> `adTransparencyReport` |
| `akashi_malak_evidence_bridge` | gad | event-gated | explicit fraud/malware flags -> optional evidence package for malak; no automatic accusation |

## Lexicons

| Lexicon | Purpose |
|---|---|
| `sourcePolicySnapshot` | Public source description, access mode, ToS / robots / API constraints, parser version, collection cadence. Required before any source adapter runs. |
| `adDisclosureSnapshot` | One raw disclosure snapshot with source record ID, URL/API endpoint, fetched_at, payload CID/hash, parser version. |
| `advertiserIdentity` | Disclosed advertiser/page/account identity. No private identity inference. |
| `creativeDisclosure` | Text/media/category/lang/landing refs as disclosed or observed from the public ad artifact. |
| `deliveryDisclosure` | Active period, region, spend/impression ranges, targeting summaries where disclosed. |
| `landingEvidence` | Landing URL/domain/redirect/content-hash evidence. Does not click forms, log in, purchase, or bypass anti-bot controls. |
| `adDisclosureLink` | Non-adjudicating factual link: same landing domain, same disclosed advertiser, same creative hash, same source record lineage. |
| `methodNote` | Open, versioned adapter/parser/linkage method. |
| `adTransparencyReport` | Aggregate report. Named advertiser views only mirror already-public source naming and are Council-gated for sensitive categories. |
| `malakEvidenceCandidate` | Optional evidence package for malak when public ad disclosure intersects malware/phishing/fraud indicators. Requires human/Council review before malak intake. |

# Relationship To Malak

akashi is **not** a malak cluster. malak remains confidential, TLP:AMBER/RED,
case/referral oriented, and law-enforcement facing. akashi is public,
transparency-first, and non-adjudicating.

The only bridge is:

1. akashi observes a public ad disclosure.
2. landing evidence or creative content matches an already-public IOC,
   takedown notice, brand-abuse report, or malware/phishing indicator.
3. akashi emits `malakEvidenceCandidate` with source CIDs and
   `nonAdjudicatingNotice=true`.
4. malak may import it as OSINT evidence only after its own access audit and
   review gates.

No akashi output creates a threat actor, opens a case, drafts police reports,
or issues a fraud/crime conclusion by itself.

# Constitutional Gates

- **G1 Passive-only** — only public disclosure pages, official APIs, or public
  bulk exports. No logged-in scraping, no sockpuppets, no credentialed access,
  no dark-pattern interaction.
- **G2 Source-provenance mandatory** — every datom points to source URL/API,
  fetched_at, payload hash/CID, source record ID where available, and
  parser/method version.
- **G3 Non-adjudicating** — no claim that an ad is illegal, fraudulent,
  manipulative, or electioneering beyond source-disclosed categories. Use
  `nonAdjudicatingNotice=true` on links/reports.
- **G4 No political profiling** — do not build voter/person cohorts, persuasion
  scores, supporter/opponent graphs, or per-person political-interest records.
- **G5 No target lists** — aggregate-first reporting; named advertiser views
  only mirror source-public names and are severity/category gated.
- **G6 Open method** — all parsers, normalizers and linkers publish methodNote.
  No closed scoring.
- **G7 ToS / robots / API respect** — adapter cannot run unless the
  `sourcePolicySnapshot` allows the intended access mode.
- **G8 No ad SDK / no tracking pixel** — akashi never loads Meta Pixel, GA4 ad
  integration, third-party ad SDKs, or affiliate/tracking code.
- **G9 No commercial ad-intel product** — no paid targeting terminal, no
  advertiser lead-gen resale, no competitor-intel SaaS.
- **G10 Public-record minimization** — keep the source-disclosed facts and
  content hashes; do not infer private natural-person data.
- **G11 Murakumo-only inference** — any language/category normalization uses
  Murakumo only; no vendor LLM APIs.
- **G12 Transparent Religious Force discipline** — observation and transparent
  publication only. No coercive action or covert operation.
- **G13 Malak bridge review** — `malakEvidenceCandidate` is evidence only,
  never an accusation; malak import requires malak gates.

# Non-Goals

- NOT an ad network, auction exchange, DSP, SSP, or campaign manager.
- NOT a replacement for platform moderation or regulator enforcement.
- NOT a political persuasion or electioneering tool.
- NOT a voter/person profiling system.
- NOT a commercial ad-intelligence SaaS.
- NOT a scraping farm or anti-bot bypass system.
- NOT a malware/fraud adjudicator; malak handles reviewed CTI separately.
- NOT a DSAR / personal-data request actor; himotoki handles consent-bound
  disclosure requests.

# Consequences

Positive:

- The missing "public ad disclosure -> kotoba database" actor is explicitly
  named and bounded.
- The design reuses danjo's public-record discipline and kotoba EAVT pattern.
- malak integration exists without collapsing public transparency into
  confidential cybercrime operations.

Trade-offs:

- Platform-specific adapters must remain conservative and may be disabled when
  source terms change.
- R0 avoids exact field parity claims across platforms; the canonical model
  preserves source-limited disclosure instead of pretending all platforms reveal
  the same data.

# R0 Design-Maturity Addendum — 2026-06-02

The R0 design scaffold has been matured to its design cap without enabling live
collection.

Delivered artifacts:

- actor manifest/README plus coverage and maturity ledgers under
  `20-actors/akashi/`
- ten `com.etzhayyim.akashi.*` Lexicon records
- source catalog and source-policy review registry
- source-policy approval transaction schema with a fixture-only example and
  rollback-to-disabled requirement
- seven `20-actors/magatama/cells/akashi_*` cell scaffolds that raise at import
  until ADR-2606022300 R1 activation gates are attested
- fixture-only regulator bulk parser, lexicon-shape validator, dry-run CLI,
  dry-run golden summary, optional-field fixture, and negative fixtures
- closure fixtures for `adDisclosureLink`, `adTransparencyReport`, and
  `malakEvidenceCandidate`

Verification:

- `test_akashi_invariants.py` has 18 passing invariants.
- The dry-run CLI emits `networkAccess=false`, `writes=false`, and
  `totalRecords=15`.
- Parser output validates against the akashi Lexicons.
- Negative fixtures prove malformed disclosure records and malak-imported
  closure records are rejected at R0.

Still not enabled:

- no live adapter
- no platform API/page collection
- no scraping, login, sockpuppet access, or anti-bot bypass
- no source is marked `covered-r1`
- no malak import; akashi emits candidate-only evidence only

# References

- [danjo public-accountability actor](2605301600-danjo-public-accountability-oversight-tier-b-actor-r0.md)
- [malak onion frontier ransomware tracking](2605172000-malak-onion-frontier-ransomware-tracking.md)
- [malak orchestration](2605131600-malak-orchestration-langgraph-pregel-langserve.md)
- [kotoba storage substrate](2605262130-kotoba-storage-substrate-unification.md)
- [open-adnetwork actor](2604281900-open-adnetwork-actor.md)
- [yoro ads integration](0084-yoro-ads-integration.md)
