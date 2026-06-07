---
id: adr-2605263800-public-data-corporate-disclosure-ipfs-ingestion
title: "ADR-2605263800: Global corporate-disclosure ingestion (SEC EDGAR / EDINET / Companies House / GLEIF LEI / OpenCorporates / regional registries) via IPFS-pinned DataLad subdatasets — extends ADR-2605262400; powers ossekai (ADR-2605264000) information-arbitrage publication + toritate (ADR-2605262900) recipient-transparency cross-reference + chigiri (ADR-2605262700) legal-entity ID lookup + baien-distill financial-literacy specialist artifacts"
status: w1-impl-landed
doc_type: adr
topic: public-data-corporate-disclosure-r0
authoritative: true
last_verified: 2026-05-27
priority: 6.0
axis: information-symmetry
weight: 0.55
priority_note: "Sibling of ADR-2605262400 (geo / netreg / routing / dns / web) and ADR-2605262800 (legal corpus); adds the `corp/` bucket family: `registries/<jurisdiction>/` + `disclosures/<jurisdiction>/<form>/` + `lei/gleif/` + `cross-juris/opencorporates/`. Five sensor families register under `kotodama.organism.sensors.corp.*`: corp_registry_sensor (per-jurisdiction legal-entity registry) / corp_disclosure_sensor (per-jurisdiction periodic financial filings) / lei_sensor (GLEIF LEI + relationship records, global cross-juris key) / corp_ownership_sensor (UBO / parent-subsidiary / control-relationship graph) / corp_filing_event_sensor (8-K-class material-event filings, low-latency hot-path priority). Most sources are Tier-A: SEC EDGAR (US public-domain), EDINET (JP 金融庁 free-redistribution), Companies House (UK OGL v3.0), GLEIF LEI (CC0 1.0), SEDAR+ (CA accessible bulk), ASIC (AU paid-API — Tier-B only with paid metered access; bulk archives Tier-A where published), Unternehmensregister (DE accessible bulk), INFOGREFFE / RNCS (FR Étalab portions). Tier-B includes OpenCorporates global cross-juris aggregator (CC-BY-SA 4.0 partial — open-data fork + paid-API tier — only open-data subset admitted with `-tierB-` infix; SA propagates to derivative corpus tagging). Tier-C explicitly EMPTY in W1: NO paid commercial data terminals (Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon / FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro **CONSTITUTIONALLY PROHIBITED** per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor closed query-tracking exposes member investment-research posture); future Tier-C additions require separate ADR + Council Lv6+ ≥3. Special PII / market-abuse concern: corporate filings name officers + directors + significant shareholders + sometimes employees and counterparties. Published filings are public by nature, BUT this ADR adds a `corp_filing_pii_policy` per-jurisdiction that respects publication redaction rules (e.g., EU GDPR right-to-be-forgotten on company-officer historical filings; JP 個人情報保護法 + 金融商品取引法 redaction for non-public material-fact insiders pre-disclosure). Default = pass-through for jurisdictions where publication is unredacted-by-law; redaction layer applied where jurisdiction practice requires it. Passive-only (inherits ADR-2605262400 §7 invariant): NO live registry scraping at organism-tick time; only pre-published bulk archives + IPFS-pinned subdataset reads. Powers ossekai (ADR-2605264000) public-good arbitrage publication (aggregate-anonymized officer-network / cross-jurisdictional ownership-graph queries) + toritate (ADR-2605262900) recipient-transparency cross-reference (donor verification: corporate-donor LEI lookup + recipient-vendor anti-related-party check) + chigiri (ADR-2605262700) external-counsel routing (entity-identity verification before vendor-contract Rider scrutiny + ipLicenseClaim recipient validation) + baien-distill specialist financial-literacy artifacts (corp-financial-disclosure-foundations-r1 recipe + corp-ownership-graph-r1 recipe; manabi financial-literacy curriculum)."
authoritative_for:
  - public-data corporate-disclosure ingestion single SoT
  - `corp/` bucket family taxonomy (registries / disclosures / lei / cross-juris)
  - `kotodama.organism.sensors.corp.*` sensor family namespace
  - corporate-disclosure license × tier × jurisdiction ladder
  - Bloomberg/S&P/Refinitiv/FactSet/Moody's/D&B/Pitchbook/Crunchbase commercial terminal PROHIBITION (Charter Rider §2(e) + §2(c) substrate-boundary)
  - corporate-disclosure PII redaction policy (per-jurisdiction publication-rule honoring; NO unilateral re-identification, NO de-anonymization)
  - `com.etzhayyim.substrate.datasetPin` integration for corp bucket
  - corp training corpus recipes at `70-tools/baien-moemoekyun-train/recipes/corp/`
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605240200-unispsc-organism-kaizen-self-reflection
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605262100-baien-moemoekyun-r1-phase0-coding-train
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262400-public-data-organism-ipfs-ingestion
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262800-public-data-legal-corpus-ipfs-ingestion
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605264000-ossekai-information-arbitrage-tier-b-actor-r0
related: []
supersedes:
  - adr-2604291500-jp-corporate-financial-disclosure-ingest
  - 2605150000
superseded_by: []
---

# ADR-2605263800: Global corporate-disclosure ingestion via IPFS-pinned DataLad subdatasets

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

Religious-corp has substantial public-good intelligence ambition
(ossekai ADR-2605264000 aggregate-anonymized publication + toritate
ADR-2605262900 financial transparency + chigiri ADR-2605262700 vendor
contract Rider scrutiny + manabi financial-literacy curriculum). All of
these consumers need **structured access to global corporate-disclosure
data** — periodic financial filings, legal-entity registries, beneficial
ownership graphs, and material-event filings.

The existing substrate covers:

- **ADR-2605262400** — geo / netreg / routing / dns / web public-data
  ingestion (DataLad + IPFS + passive-only + tier ladder framework);
- **ADR-2605262800** — global legal corpus ingestion (statutes / cases
  / treaties / procedures; sibling pattern this ADR mirrors);
- **ADR-2605262600** (ossekai) — publication front-end via AT Proto
  `app.bsky.feed.post` membrane + custom feed generator + @mention;
- **ADR-2605262900** (toritate) — on-chain accounting + audit substrate
  reading TitheRouter / Public Fund Safe / Council Safe;
- **ADR-2605262700** (chigiri) — legal procedure substrate (entity
  identity verification, vendor Rider scrutiny, ipLicenseClaim
  recipient validation).

**What is missing**: corporate-disclosure data is NOT ingested. The
pre-religious-corp commercial-fund era left several legacy scripts at
`70-tools/scripts/sec-edgar-disclosure-ingest.mjs` /
`gleif-bulk-ingest.mjs` / `lg-isin-listed-company-ingest-langserver.mjs`
plus ADR-2604291500 (jp-corporate-financial-disclosure) and
ADR-2605150000 (lg-isin-listed-company), but none of these were
migrated to the religious-corp substrate (Kotoba/Datomic/Postgres-bound,
not DataLad+IPFS; pre-Charter-Rider; pre-passive-only-discipline; no
sensor abstraction; no Tier ladder; no ossekai consumer wiring).

User-stated goal (2026-05-26):

> 全世界の公開企業, 全世界の政府情報などを ingest として
> atproto actor として設計はされている? datalad, ipfs に保存.

(This ADR addresses the corporate half; ADR-2605263900 addresses the
government half.)

# Decision

Adopt the ADR-2605262400 + ADR-2605262800 architecture pattern
(DataLad subdataset + IPFS-pin + passive-only discipline + tier ladder
+ sensor abstraction + cold-path corpus assembly) extended to the
`corp/` bucket family. The five legacy commercial-fund scripts are
**superseded** by this ADR and will be removed from `70-tools/scripts/`
in W4 (after sensor parity is verified).

## §1. Bucket taxonomy

```
90-docs/baien/datasets/corp/
├── registries/<jurisdiction>/<rev>/      # legal-entity registries
│   ├── usa/edgar-companies/              # SEC EDGAR company facts
│   ├── gbr/companies-house/              # UK Companies House bulk
│   ├── jpn/edinet-filers/                # JP EDINET 提出者
│   ├── deu/unternehmensregister/         # DE Unternehmensregister
│   ├── fra/rncs-infogreffe/              # FR RNCS/INFOGREFFE Étalab
│   ├── can/sedar-issuers/                # CA SEDAR+ issuers
│   ├── aus/asic-organisations/           # AU ASIC orgs bulk
│   └── ...
├── disclosures/<jurisdiction>/<form>/<rev>/   # periodic financial filings
│   ├── usa/10-K/                         # SEC annual report
│   ├── usa/10-Q/                         # SEC quarterly report
│   ├── usa/8-K/                          # SEC material-event filings
│   ├── usa/Form-4/                       # SEC insider transactions
│   ├── usa/13F/                          # SEC institutional holdings
│   ├── usa/S-1/ S-3/                     # SEC registration statements
│   ├── jpn/yuho/                         # JP 有価証券報告書
│   ├── jpn/hanki/                        # JP 半期報告書
│   ├── jpn/large-holding/                # JP 大量保有報告書
│   ├── gbr/annual-accounts/              # UK statutory accounts
│   ├── eu/transparency-directive/        # EU annual + half-year reports
│   └── ...
├── lei/gleif/<rev>/                      # GLEIF LEI canonical + relationships
│   ├── lei-l1/                           # LEI level-1 (entity reference)
│   ├── lei-l2/                           # LEI level-2 (relationship)
│   └── lei-cdf/                          # Common Data File concatenation
├── ownership/<source>/<rev>/             # UBO / parent-subsidiary graphs
│   ├── opencorporates-control/           # OpenCorporates control graph (Tier-B)
│   ├── usa-fincen-ubo/                   # US FinCEN BOI (post-2024 effective)
│   ├── eu-ubo-registers/                 # EU per-member-state UBO registers
│   └── ...
└── filing-events/<source>/<rev>/         # low-latency material-event stream
    ├── usa-edgar-rss/                    # SEC EDGAR RSS / Atom snapshots
    └── jpn-edinet-realtime/              # JP EDINET API snapshots
```

Bucket boundary discipline (per ADR-2605262400 G-pattern): each bucket
is its own DataLad subdataset; revision (`<rev>`) is a content-hash
directory rotated on each archive snapshot; IPFS-pin operates at the
revision level (every snapshot is its own immutable CID).

## §2. Data-source ladder (license × tier × jurisdiction × admissibility)

| Source | Jurisdiction | Coverage | License | Tier | Fetcher path-reserve | Bucket | Train? | Perceive? |
|---|---|---|---|---|---|---|---|---|
| **SEC EDGAR** companyfacts JSON + Submissions API archives | USA | ~10K public-traded + filers | public-domain (US gov work, 17 CFR 200) | **A** | `sec_edgar.py` (W1) | `corp/disclosures/usa/*/` + `corp/registries/usa/edgar-companies/` | yes | yes |
| **JP EDINET** XBRL bulk + Submissions metadata | JPN | ~4K filers (有報・大量保有) | 金融庁 free-redistribution (open-data utilization terms) | **A** | `jp_edinet.py` (W1) | `corp/disclosures/jpn/*/` + `corp/registries/jpn/edinet-filers/` | yes | yes |
| **UK Companies House** Free Company Data Product bulk + Confirmation Statement archive | GBR | ~5M companies | OGL v3.0 (Crown copyright open license) | **A** | `uk_companies_house.py` (W1) | `corp/registries/gbr/companies-house/` + `corp/disclosures/gbr/annual-accounts/` | yes | yes |
| **GLEIF LEI** Concatenated Files (CDF Level-1 + Level-2 + Relationship Records) | global | ~2.5M LEIs | **CC0 1.0** (Global Legal Entity Identifier Foundation public-domain) | **A** | `gleif_lei.py` (W1) | `corp/lei/gleif/` | yes | yes |
| **EU Transparency Directive** annual + half-year reports (per member-state OAM) | EU-27 | varies per member-state | per-member-state (most open / public) | **A** (per member-state) | `eu_oam_<cc>.py` (W3 per-state opt-in) | `corp/disclosures/eu/transparency-directive/` | yes (per-state) | yes |
| **CA SEDAR+** issuer profile bulk + continuous disclosure | CAN | ~10K issuers | Canadian Securities Administrators open-data ToU | **A** | `ca_sedar.py` (W2) | `corp/registries/can/sedar-issuers/` + `corp/disclosures/can/*/` | yes | yes |
| **AU ASIC** organisations registry bulk (data.gov.au extract) | AUS | ~3M orgs | data.gov.au CC-BY 4.0 | **A** | `au_asic.py` (W2) | `corp/registries/aus/asic-organisations/` | yes | yes |
| **DE Unternehmensregister** publication bulk (`unternehmensregister.de`) | DEU | ~1.6M entities | accessible bulk per InsO §1, BilMoG free-use | **A** | `de_unternehmensregister.py` (W2) | `corp/registries/deu/unternehmensregister/` | yes | yes |
| **FR INFOGREFFE / RNCS** open-data subset (Étalab portions only) | FRA | RCS extract subset | Étalab v2.0 (Licence Ouverte) | **A** | `fr_rncs_infogreffe.py` (W2) | `corp/registries/fra/rncs-infogreffe/` | yes | yes |
| **US FinCEN BOI** beneficial-ownership reports (post-CTA 2024 effective) | USA | ~32M reporting companies | per-FinCEN access regime (gov-only currently; W4 re-evaluate if public access opens) | **A** (when public) / **deferred** (currently) | `us_fincen_boi.py` (W4 / deferred) | `corp/ownership/usa-fincen-ubo/` | per-access | per-access |
| **OpenCorporates** open-data fork (NOT paid-API tier) | global cross-juris | ~200M entities | **CC-BY-SA 4.0** (open-data subset only) | **B** (`-tierB-` infix; SA propagates) | `opencorporates_opendata.py` (W3) | `corp/ownership/opencorporates-control/` | yes (SA-derivative) | yes |
| **SEC EDGAR RSS / Atom** filing-event stream snapshots | USA | live-event archive | public-domain | **A** | `sec_edgar_rss.py` (W3) | `corp/filing-events/usa-edgar-rss/` | yes | yes (high-cadence) |
| **JP EDINET API** filing-event snapshot loop | JPN | live-event archive | 金融庁 open-data utilization terms | **A** | `jp_edinet_api.py` (W3) | `corp/filing-events/jpn-edinet-realtime/` | yes | yes (high-cadence) |

Tier C and Tier D are **explicitly EMPTY in W1-W4**: NO paid commercial
data terminals (Bloomberg Terminal / S&P Capital IQ / Refinitiv Eikon /
FactSet / Moody's Orbis / D&B Hoovers / Pitchbook / Crunchbase Pro)
**CONSTITUTIONALLY PROHIBITED** per Charter Rider §2(e) anti-gatekeeping
+ §2(c) covert-ops vendor concern. Future Tier-C admission requires
separate ADR + Council Lv6+ ≥3 + concrete public-good justification +
vendor-data-sovereignty alternative-source-impossibility attestation.

## §3. Sensor abstraction (`kotodama.organism.sensors.corp.*`)

New module path: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/corp/base.py`.

```python
# Protocol definition (excerpt; full type-checked impl lands in W1)

from typing import Protocol, TypedDict, Literal

class CorpObservation(TypedDict):
    source: str                     # e.g. "sec_edgar" / "gleif_lei"
    jurisdiction: str               # ISO-3 (e.g. "USA", "JPN", "GBR") OR "GLOBAL"
    entity_lei: str | None          # GLEIF LEI 20-char; None if non-LEI-bearing
    entity_local_id: str            # per-juris ID (e.g. SEC CIK, EDINET 提出者 ID, UK CRN, JP 法人番号)
    form_type: str | None           # e.g. "10-K" / "8-K" / "yuho" / "annual-accounts"
    filed_at_utc: str               # ISO-8601 UTC
    payload_cid: str                # IPFS CID of normalized JSON payload (annex preserved)
    tier: Literal["A", "B"]         # Tier-A or Tier-B (NO Tier-C in W1-W4 per §2)
    internal_only: bool             # True iff tier=="B" with SA-propagation flag set on derivative
    pii_redacted: bool              # True iff per-juris redaction policy applied (see §5)

class CorpSensor(Protocol):
    def latest_pin(self) -> str: ...
    def hot_sample(self, pin_cid: str, n: int = 8) -> list[CorpObservation]: ...
```

W1 implementations (path-reserved, code lands in W1 deliverable):
- `corp_registry_sensor` — per-jurisdiction legal-entity registry reads
- `corp_disclosure_sensor` — per-jurisdiction periodic filing reads
- `lei_sensor` — GLEIF LEI canonical + relationship cross-juris key
- `corp_ownership_sensor` — UBO / parent-subsidiary / control graph
- `corp_filing_event_sensor` — material-event hot-path priority sensor
  (8-K / 大量保有報告書 / similar; higher cadence; ossekai-facing)

## §4. Training corpus recipes (cold path)

New directory: `70-tools/baien-moemoekyun-train/recipes/corp/`.

| Recipe | Sources | License-mix | Train-tier | Consumer |
|---|---|---|---|---|
| `corp-financial-disclosure-foundations-r1.toml` | SEC EDGAR + JP EDINET + UK Companies House + GLEIF LEI | all Tier-A | publishable artifact | baien-distill financial-literacy specialist |
| `corp-ownership-graph-r1.toml` | GLEIF L2 + OpenCorporates open-data + EU UBO registers | Tier-A + Tier-B-SA | derivative SA-licensed artifact (`-tierB-` infix) | manabi cross-jurisdictional-control curriculum |
| `corp-material-event-stream-r1.toml` | SEC EDGAR RSS + JP EDINET API snapshots | Tier-A | publishable artifact | ossekai aggregate publication |
| `corp-officer-network-r1.toml` | SEC EDGAR + UK Companies House + JP EDINET officer fields | Tier-A | publishable artifact w/ §5 PII redaction | manabi corporate-governance + ossekai aggregate-anonymized |

## §5. PII / publication-redaction policy (per-jurisdiction)

Corporate filings name officers / directors / significant shareholders /
sometimes employees and counterparties. Published filings are public by
nature — religious-corp does NOT re-identify, NOT de-anonymize, NOT
aggregate beyond what upstream publishes. Policy is **publication-rule-
honoring** per-jurisdiction:

| Jurisdiction | Publication rule | Religious-corp policy |
|---|---|---|
| USA (SEC) | named in filings (officers, ≥10% holders, directors) | pass-through (unredacted, upstream publishes named) |
| GBR (Companies House) | named (officers, PSCs) | pass-through |
| JPN (EDINET) | named (役員 + 大量保有提出者) | pass-through |
| EU (member-state OAMs) | varies — DE/FR/IT often pseudonymize lower-tier; AT/BE/NL pass-through | per-member-state honor upstream |
| CAN (SEDAR+) | named (officers, insiders Form 13) | pass-through |
| AUS (ASIC) | named (directors, secretaries) | pass-through |
| Cross-juris (OpenCorporates) | aggregator of above | honor upstream-tagged redaction |
| **General** | GDPR right-to-be-forgotten requests on company-officer historical filings | DSARs route through **chigiri.data_privacy** cell to upstream publisher, NEVER unilateral religious-corp removal |

PII filter (`pii_filter.py` per ADR-2605262400 §6) still runs as
defense-in-depth — emails, E.164 phone numbers, postal addresses, free-
text comment fields are redacted **on the redacted view** (annex bytes
preserved for forensic auditability). Charter Rider §2 scan runs after.

## §6. Passive-only network discipline (inherits ADR-2605262400 §7)

Religious-corp organisms MUST NOT perform live registry scraping at
organism-tick time. Specifically prohibited:

- N1. Live SEC EDGAR full-text search hitting the live API
- N2. Live Companies House individual-company API queries
- N3. Live EDINET 縦覧 page scraping
- N4. Live GLEIF concatenated-file API hits per-LEI
- N5. Live OpenCorporates API hits (free-tier OR paid-tier)
- N6. Live SEDAR+ / ASIC / DE / FR per-company queries

Permitted: pre-published **bulk archives only**, fetched via the
declared fetcher modules, with cadence respecting upstream rate-limit +
robots.txt + ToU. Per-source acceptance flag at
`~/.etzhayyim/source-acceptance/<source>.toml` MUST be present before
fetch will run (per ADR-2605262400 W3 acceptance pattern).

## §7. Wave delivery plan

| Wave | Sources / fetchers / sensors | Estimated duration |
|---|---|---|
| **W0** = this ADR + 5 fetcher path-reserves + 5 sensor path-reserves + 4 recipe templates + deps.toml + README + 5 legacy-script supersession marker | this commit | — |
| **W1** = SEC EDGAR + JP EDINET + UK Companies House + GLEIF LEI fetchers + 4 sensors + `corp-financial-disclosure-foundations-r1` recipe + §5 PII policy first cut + 2 new Kaizen rules R12 (stale-filing-pin) + R13 (entity-LEI-coverage drop >5%/30d) | 3-4 days |
| **W2** = SEDAR+ + ASIC + Unternehmensregister + INFOGREFFE fetchers + per-juris adapter for `corp_disclosure_sensor` | 3-4 days |
| **W3** = SEC EDGAR RSS + JP EDINET API filing-event sensors + OpenCorporates open-data fork Tier-B + `-tierB-` infix enforcement + `corp-material-event-stream-r1` recipe + ossekai aggregate-publication wiring | 4-5 days |
| **W4** = EU OAM per-member-state opt-in fetchers + US FinCEN BOI deferred-or-enable + 5 legacy-script removal from `70-tools/scripts/` after sensor parity verified + cross-actor toritate recipient-transparency cross-reference integration | 5-7 days |

## §8. Gates (12)

- **G1**. Charter Rider §2 scan on every ingested filing (incl XBRL textBlocks + officer fields)
- **G2**. `replicationMin: 2` IPFS-pin on every revision
- **G3**. Per-jurisdiction publication-redaction policy honored (§5); no unilateral re-identification
- **G4**. Tier-B SA-derivative `-tierB-` infix on any corpus including OpenCorporates open-data
- **G5**. Murakumo-only inference (ADR-2605215000)
- **G6**. No-active-probe lint scans imports/calls (deny-list: SEC EDGAR live-API client, Companies House live-API client, EDINET 縦覧 scraper, OpenCorporates API client, GLEIF live-API; allow: bulk-download utilities only)
- **G7**. `hot_sample` determinism (same pin_cid + same n → same observation IDs)
- **G8**. Recipe-in-git (every `corp/*/r*.toml` recipe + `<sha256>` lock file committed)
- **G9**. False-positive ≤5% / 24h on Charter Rider scan (else cell halts + R8 Kaizen escalation)
- **G10**. `datasetPin` PDS record mandatory per published revision (`com.etzhayyim.substrate.datasetPin`)
- **G11**. Per-source acceptance flag present (§6) before fetch will run
- **G12**. Vendor-commercial-terminal deny-list lint (Bloomberg Terminal / S&P CapIQ / Refinitiv / FactSet / Moody's Orbis / D&B / Pitchbook / Crunchbase Pro imports + API hostnames forbidden at lint time)

## §9. Non-goals (12)

- **N1**. NOT a Bloomberg Terminal / S&P CapIQ / Refinitiv / FactSet replacement (commercial terminal substitution out of scope and CONSTITUTIONALLY PROHIBITED by Charter Rider §2(e))
- **N2**. NOT live-registry API client (passive-only per §6)
- **N3**. NOT a credit-rating agency replacement (no rating issuance; rating issuance is regulated activity — out of scope)
- **N4**. NOT an insider-trading detection or short-selling target generator (G3 publication-rule-honoring; aggregate-only ossekai publication; no individual-targeting)
- **N5**. NOT a market-making or trading-signal generator (religious-corp is non-profit; no trading activity per Charter §1.3)
- **N6**. NOT a paywall-bypass tool (only sources with open bulk archives admitted)
- **N7**. NOT a UBO de-anonymization service (G3; DSARs route through chigiri.data_privacy)
- **N8**. NOT a corporate-espionage substrate (passive-only; aggregate-anonymized publication discipline)
- **N9**. NOT a substitute for licensed financial advice (UPL-equivalent boundary; manabi curriculum is literacy-only, chigiri.ipLicenseClaim routes to licensed counsel for actionable opinions)
- **N10**. NOT a vendor-LLM inference path (Murakumo-only per G5)
- **N11**. NOT a substrate engine replacement (kotoba per ADR-2605262130 remains canonical storage substrate)
- **N12**. NOT cross-religious-corp federation (per-religious-corp deployment; cross-deployment data sharing is separate ADR)

# Consequences

## Positive

- ossekai (ADR-2605264000) gains a structured global-corporate
  intelligence surface for aggregate-anonymized public-good publication
  (officer networks, cross-jurisdictional ownership graphs, material-
  event timelines) without surveillance or covert-ops.
- toritate (ADR-2605262900) gains a recipient-transparency cross-
  reference path: corporate-donor LEI lookup before tithe-receipt
  emission, anti-related-party check on vendor disbursement.
- chigiri (ADR-2605262700) gains entity-identity verification before
  vendor-contract Rider scrutiny + ipLicenseClaim recipient validation.
- manabi gains a Tier-A financial-literacy corpus (corp-financial-
  disclosure-foundations-r1 recipe) for L4 vocation-tier curriculum.
- baien-distill gains a financial-literacy specialist artifact path.
- Legacy commercial-fund era scripts (`sec-edgar-disclosure-ingest.mjs`
  + `gleif-bulk-ingest.mjs` + `lg-isin-listed-company-ingest-langserver
  .mjs`) are explicitly superseded and removed in W4 (eliminating
  pre-Charter-Rider / pre-passive-only / RW-bound legacy code).
- ADR-2604291500 (jp-corporate-financial-disclosure) and
  ADR-2605150000 (lg-isin-listed-company) are formally superseded
  (frontmatter `supersedes`).

## Negative

- Storage cost: post-W4 estimated ≈ 60-80 GB per fleet node (SEC EDGAR
  ~30 GB / EDINET ~10 GB / UK Companies House ~15 GB / GLEIF ~5 GB /
  others ~15-20 GB). Within Murakumo fleet capacity.
- US FinCEN BOI is currently gov-only-access; W4 re-evaluation required
  if public access opens (separate sub-ADR if data becomes available).
- OpenCorporates Tier-B SA-propagation tags downstream corpus, limiting
  some derivative-artifact distribution flexibility.

## Risks

- Per-jurisdiction publication-redaction policy drift: upstream
  publication rules can change (e.g., GDPR amendments, EU UBO register
  access restrictions per 2022 CJEU C-37/20 + C-601/20). Mitigation:
  R8 Kaizen rule (charter-fail-rate >5% / 24h) + per-jurisdiction
  silenReview cycle on policy changes + chigiri.data_privacy
  notification on publication-rule change detection.
- Vendor-commercial-terminal lint G12 must include hostnames + import
  patterns + SDK package names; deny-list maintenance overhead.

# Alternatives Considered

1. **Single global aggregator** (OpenCorporates paid-API tier OR
   Moody's Orbis OR D&B). Rejected: CONSTITUTIONALLY PROHIBITED per
   Charter Rider §2(e) anti-gatekeeping + §2(c) vendor closed query-
   tracking exposes member investment-research posture.
2. **Live-API client only (no bulk archive ingestion)**. Rejected:
   violates ADR-2605262400 §7 passive-only discipline.
3. **Keep legacy commercial-fund scripts as-is**. Rejected: RW-bound,
   pre-Charter-Rider, pre-passive-only, no sensor abstraction; would
   leave religious-corp consumers (ossekai, toritate, chigiri, manabi)
   without a substrate-compliant path.
4. **Per-actor private fetchers (no shared sensor abstraction)**.
   Rejected: violates the ADR-2605262400 + ADR-2605262800 sibling-
   pattern principle (single SoT for public-data ingestion).

# References

- ADR-2605262400 — Public-data ingestion (parent pattern)
- ADR-2605262800 — Global legal corpus ingestion (sibling)
- ADR-2605264000 — ossekai information-arbitrage actor (downstream consumer)
- ADR-2605262900 — toritate accounting + audit (downstream consumer)
- ADR-2605262700 — chigiri legal procedure (downstream consumer)
- ADR-2605262130 — kotoba storage substrate
- ADR-2605241500 — Dataset CID substrate (DataLad + IPFS)
- ADR-2605262100 — G13 fleet-internal NC carve-out precedent
- ADR-2605215000 — Murakumo-only inference invariant
- ADR-2605192200 — Charter Rider v2.0
- ADR-2604291500 — JP corporate financial disclosure ingest (superseded by this ADR)
- ADR-2605150000 — LG ISIN listed company ingest LangServer (superseded by this ADR)
- SEC EDGAR data documentation: https://www.sec.gov/edgar (data licensing 17 CFR 200)
- JP 金融庁 EDINET: https://disclosure.edinet-fsa.go.jp
- UK Companies House Free Data: https://download.companieshouse.gov.uk
- GLEIF concatenated files: https://www.gleif.org/en/lei-data/gleif-concatenated-file
- OpenCorporates open-data: https://opencorporates.com/info/open-data
