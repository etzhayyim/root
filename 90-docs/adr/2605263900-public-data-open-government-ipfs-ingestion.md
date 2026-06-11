---
id: adr-2605263900-public-data-open-government-ipfs-ingestion
title: "ADR-2605263900: Global open-government-data ingestion (open-data portals / parliament / budget / procurement / statistics) via IPFS-pinned DataLad subdatasets — sibling of ADR-2605262400 + ADR-2605262800 + ADR-2605263800; powers ossekai (ADR-2605264000) information-arbitrage publication + toritate (ADR-2605262900) public-spending cross-reference + chigiri (ADR-2605262700) state-function-routing-around evidence base + manabi civic-literacy curriculum + baien-distill civic-reasoning specialist artifacts"
status: w1-impl-landed
doc_type: adr
topic: public-data-open-government-r0
authoritative: true
last_verified: 2026-05-27
priority: 6.0
axis: information-symmetry
weight: 0.55
priority_note: "Sibling of ADR-2605262400 (geo / netreg / routing / dns / web) + ADR-2605262800 (legal corpus) + ADR-2605263800 (corporate disclosure); adds the `gov/` bucket family: `open-data/<jurisdiction>/` (data.gov-class portals) + `parliament/<jurisdiction>/` (議事録 / Hansard / OEIL / Congressional Record) + `budget/<jurisdiction>/` (USAspending / national budget publications) + `procurement/<jurisdiction>/` (TED / SAM.gov / 政府調達情報) + `statistics/<source>/` (Eurostat / OECD.Stat / World Bank Open Data / IMF SDMX / UN data). Five sensor families register under `kotodama.organism.sensors.gov.*`: gov_open_data_sensor (per-jurisdiction open-data portal) / gov_parliament_sensor (per-legislature 議事録 / Hansard / OEIL) / gov_budget_sensor (per-jurisdiction budget + spending) / gov_procurement_sensor (per-jurisdiction tender notices + awards) / gov_statistics_sensor (per-IGO statistics: Eurostat / OECD / WB / IMF / UN). Most sources are Tier-A: open-government licenses dominate (US public-domain / UK OGL v3.0 / EU re-use Decision 2011/833 / FR Étalab v2.0 / JP CC-BY 4.0 政府標準利用規約 / DE Datenlizenz Deutschland Zero / Eurostat free re-use / OECD ToU free / World Bank CC-BY 4.0 / IMF open-data / UN free use). Tier-B for sources with attribution-mandatory restrictions or partial paywalls open-data portion only (`-tierB-` infix per ADR-2605263800 §2 G4). Tier-C explicitly EMPTY in W1: NO paid commercial government-intelligence platforms (GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro **CONSTITUTIONALLY PROHIBITED** per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor closed query-tracking exposes member civic-research posture). Special handling: (a) CN data — National Bureau of Statistics + State Council Bulletin + 中国政府网 — flagged Charter Rider §2(g) state-aligned scrutiny (ingested as authoritative-source-of-record but flagged as non-substitution for independent verification, mirroring ADR-2605262800 CN NPC handling); (b) parliament/议事録 contains member-personal-statements + sometimes citizen-petitioner names — pass-through per upstream publication rule + chigiri.data_privacy DSAR routing for any takedown request; (c) procurement contains awardee company names + bid amounts — pass-through (procurement transparency is the public-good reason for the publication regime). Passive-only (inherits ADR-2605262400 §7): NO live portal scraping at organism-tick time; bulk archives + bulk-API snapshots only. Powers ossekai (ADR-2605264000) aggregate-publication of state-function-routing-around evidence (per Charter §1.12; routing-around is structurally informed by publicly-recorded state activity) + toritate (ADR-2605262900) public-spending cross-reference (recipient-vendor anti-related-party check against gov procurement + tithe-recipient cross-juris regulatory check) + chigiri (ADR-2605262700) state-function-routing-around evidence base (when external state procedure is publicly recorded, chigiri.covenant_ceremony and chigiri.inheritance can cite it as substitution context) + manabi civic-literacy curriculum (parliament transcripts + budget breakdowns + procurement transparency = direct civic-literacy primary sources) + baien-distill civic-reasoning specialist artifacts (gov-civic-literacy-foundations-r1 + gov-budget-transparency-r1 + gov-parliament-procedural-r1 recipes)."
authoritative_for:
  - public-data open-government ingestion single SoT
  - `gov/` bucket family taxonomy (open-data / parliament / budget / procurement / statistics)
  - `kotodama.organism.sensors.gov.*` sensor family namespace
  - open-government license × tier × jurisdiction ladder
  - GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro commercial gov-intelligence terminal PROHIBITION (Charter Rider §2(e) + §2(c))
  - parliament / 議事録 publication-rule-honoring policy (NO unilateral re-identification, NO de-anonymization; chigiri.data_privacy DSAR routing)
  - CN gov data §2(g) state-aligned scrutiny flagging (parallel to ADR-2605262800 CN NPC treatment)
  - `com.etzhayyim.substrate.datasetPin` integration for gov bucket
  - gov training corpus recipes at `70-tools/baien-moemoekyun-train/recipes/gov/`
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
  - adr-2605263800-public-data-corporate-disclosure-ipfs-ingestion
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263900: Global open-government-data ingestion via IPFS-pinned DataLad subdatasets

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

Religious-corp consumers need structured access to **global open-
government data** — open-data portals (data.gov class), parliament
transcripts (議事録 / Hansard / OEIL / Congressional Record), national
and supranational budget publications (USAspending / EU budget / each
nation's budget bulletins), public procurement notices and awards (TED
/ SAM.gov / 政府調達情報), and intergovernmental statistics (Eurostat /
OECD.Stat / World Bank Open Data / IMF SDMX / UN data).

The existing substrate covers:

- **ADR-2605262400** — geo / netreg / routing / dns / web ingestion
  framework;
- **ADR-2605262800** — global legal corpus ingestion (statutes /
  cases / treaties / procedures);
- **ADR-2605263800** — global corporate-disclosure ingestion (sibling
  this ADR mirrors);
- **ADR-2605264000** (ossekai) — publication front-end via AT Proto;
- **ADR-2605262900** (toritate) — accounting + audit substrate;
- **ADR-2605262700** (chigiri) — legal procedure substrate (esp.
  Charter §1.12 state-function routing-around).

**What is missing**: open-government data is NOT ingested. Without this
ADR, religious-corp lacks structured primary-source access to publicly-
recorded state activity. This is materially limiting for:

- ossekai aggregate-publication of state-function-routing-around
  evidence per Charter §1.12;
- toritate recipient-transparency cross-reference (vendor awarded a
  state procurement contract → cross-check against tithe-recipient
  vendor list);
- chigiri state-function-routing-around evidence base (when external
  state procedure is publicly recorded, religious-corp covenant /
  inheritance / withdrawal procedures can cite it as substitution
  context per Charter §1.12 routing-around discipline);
- manabi civic-literacy curriculum (parliament transcripts + budget
  breakdowns + procurement transparency are direct civic-literacy
  primary sources for L4 vocation-tier curriculum);
- baien-distill civic-reasoning specialist artifacts.

User-stated goal (2026-05-26):

> 全世界の公開企業, 全世界の政府情報などを ingest として
> atproto actor として設計はされている? datalad, ipfs に保存.

(ADR-2605263800 addressed the corporate half; this ADR addresses the
government half.)

# Decision

Adopt the ADR-2605262400 + ADR-2605262800 + ADR-2605263800
architecture pattern (DataLad subdataset + IPFS-pin + passive-only
discipline + tier ladder + sensor abstraction + cold-path corpus
assembly) extended to the `gov/` bucket family.

## §1. Bucket taxonomy

```
90-docs/baien/datasets/gov/
├── open-data/<jurisdiction>/<rev>/    # data.gov-class portal bulk archives
│   ├── usa/data-gov/                  # data.gov US federal catalog
│   ├── gbr/data-gov-uk/               # data.gov.uk
│   ├── fra/data-gouv-fr/              # data.gouv.fr
│   ├── jpn/data-go-jp/                # data.go.jp
│   ├── jpn/e-stat/                    # e-Stat 政府統計の総合窓口
│   ├── deu/govdata-de/                # govdata.de
│   ├── eu/data-europa-eu/             # data.europa.eu (EU Open Data Portal)
│   └── ...
├── parliament/<jurisdiction>/<rev>/   # 議事録 / Hansard / OEIL etc.
│   ├── usa/congress-gov/              # Congress.gov bulk
│   ├── gbr/hansard/                   # UK Hansard bulk
│   ├── eu/oeil/                       # European Parliament OEIL
│   ├── jpn/kokkai-kaigiroku/          # 国会会議録検索 bulk
│   ├── deu/bundestag-protokolle/      # Bundestag Plenarprotokolle
│   ├── fra/assemblee-nationale/       # Assemblée Nationale bulk
│   └── ...
├── budget/<jurisdiction>/<rev>/       # USAspending + national budget bulletins
│   ├── usa/usaspending-gov/           # USAspending.gov bulk
│   ├── eu/financial-transparency/     # EU Financial Transparency System
│   ├── jpn/yosan/                     # 予算書 publications
│   ├── gbr/treasury/                  # HM Treasury OSCAR
│   └── ...
├── procurement/<jurisdiction>/<rev>/  # tender notices + awards
│   ├── eu/ted/                        # TED (Tenders Electronic Daily)
│   ├── usa/sam-gov/                   # SAM.gov entity + contract data
│   ├── jpn/chotatsu-portal/           # 政府調達情報ポータル
│   ├── gbr/contracts-finder/          # UK Contracts Finder
│   └── ...
└── statistics/<source>/<rev>/         # IGO statistics
    ├── eurostat/                      # Eurostat SDMX
    ├── oecd-stat/                     # OECD.Stat SDMX
    ├── worldbank-open-data/           # World Bank Open Data
    ├── imf-sdmx/                      # IMF SDMX
    └── un-data/                       # UN data
```

Bucket boundary discipline matches ADR-2605262400 / ADR-2605263800
(each bucket = own DataLad subdataset; revision-level IPFS pin).

## §2. Data-source ladder (license × tier × jurisdiction × admissibility)

| Source | Coverage | License | Tier | Fetcher path-reserve | Bucket | Train? | Perceive? |
|---|---|---|---|---|---|---|---|
| **US data.gov** dataset catalog + CKAN harvest | USA federal | public-domain (US gov work, 17 CFR 200) | **A** | `us_data_gov.py` (W1) | `gov/open-data/usa/data-gov/` | yes | yes |
| **UK data.gov.uk** CKAN bulk | GBR | **OGL v3.0** (Crown copyright open) | **A** | `uk_data_gov_uk.py` (W1) | `gov/open-data/gbr/data-gov-uk/` | yes | yes |
| **JP data.go.jp + e-Stat** | JPN | **CC-BY 4.0** (政府標準利用規約 2.0) | **A** | `jp_data_go_jp.py` + `jp_estat.py` (W1) | `gov/open-data/jpn/{data-go-jp,e-stat}/` | yes | yes |
| **EU data.europa.eu** Open Data Portal CKAN | EU + member-states | **EU re-use Decision 2011/833** (free re-use) | **A** | `eu_data_europa_eu.py` (W2) | `gov/open-data/eu/data-europa-eu/` | yes | yes |
| **FR data.gouv.fr** CKAN bulk | FRA | **Étalab v2.0** | **A** | `fr_data_gouv_fr.py` (W2) | `gov/open-data/fra/data-gouv-fr/` | yes | yes |
| **DE govdata.de** CKAN bulk | DEU | **Datenlizenz Deutschland Zero v2.0** | **A** | `de_govdata_de.py` (W2) | `gov/open-data/deu/govdata-de/` | yes | yes |
| **US Congress.gov** bulk (bills + roll-call votes + member info) | USA | public-domain | **A** | `us_congress_gov.py` (W1) | `gov/parliament/usa/congress-gov/` | yes | yes |
| **UK Hansard** bulk (Commons + Lords) | GBR | OGL v3.0 | **A** | `uk_hansard.py` (W1) | `gov/parliament/gbr/hansard/` | yes | yes |
| **JP 国会会議録検索** bulk | JPN | 国会 公開 (free use as official record) | **A** | `jp_kokkai_kaigiroku.py` (W1) | `gov/parliament/jpn/kokkai-kaigiroku/` | yes | yes |
| **EU OEIL** legislative observatory bulk | EU | EU re-use Decision 2011/833 | **A** | `eu_oeil.py` (W3) | `gov/parliament/eu/oeil/` | yes | yes |
| **DE Bundestag Plenarprotokolle** bulk | DEU | Datenlizenz Deutschland Zero | **A** | `de_bundestag.py` (W3) | `gov/parliament/deu/bundestag-protokolle/` | yes | yes |
| **FR Assemblée Nationale** + Sénat bulk | FRA | Étalab v2.0 | **A** | `fr_assemblee.py` (W3) | `gov/parliament/fra/assemblee-nationale/` | yes | yes |
| **US USAspending.gov** bulk award + recipient + sub-award | USA | public-domain | **A** | `us_usaspending.py` (W2) | `gov/budget/usa/usaspending-gov/` | yes | yes |
| **EU Financial Transparency System** bulk | EU | EU re-use | **A** | `eu_financial_transparency.py` (W3) | `gov/budget/eu/financial-transparency/` | yes | yes |
| **EU TED** (Tenders Electronic Daily) bulk + eForms | EU + EEA | EU re-use Decision 2011/833 | **A** | `eu_ted.py` (W2) | `gov/procurement/eu/ted/` | yes | yes |
| **US SAM.gov** entity + contract data bulk | USA | public-domain | **A** | `us_sam_gov.py` (W2) | `gov/procurement/usa/sam-gov/` | yes | yes |
| **JP 政府調達情報ポータル** bulk | JPN | 政府標準利用規約 2.0 | **A** | `jp_chotatsu.py` (W3) | `gov/procurement/jpn/chotatsu-portal/` | yes | yes |
| **UK Contracts Finder** bulk | GBR | OGL v3.0 | **A** | `uk_contracts_finder.py` (W3) | `gov/procurement/gbr/contracts-finder/` | yes | yes |
| **Eurostat** SDMX bulk | EU | Eurostat free re-use | **A** | `eu_eurostat.py` (W1) | `gov/statistics/eurostat/` | yes | yes |
| **OECD.Stat** SDMX | OECD | OECD ToU (free re-use) | **A** | `oecd_stat.py` (W2) | `gov/statistics/oecd-stat/` | yes | yes |
| **World Bank Open Data** | global | **CC-BY 4.0** | **A** | `worldbank_open_data.py` (W1) | `gov/statistics/worldbank-open-data/` | yes | yes |
| **IMF SDMX** Data Services | global | IMF open-data ToU | **A** | `imf_sdmx.py` (W2) | `gov/statistics/imf-sdmx/` | yes | yes |
| **UN Data** (UNSD + various IGO) | global | UN free use | **A** | `un_data.py` (W3) | `gov/statistics/un-data/` | yes | yes |
| **CN 中国政府网 + NBS** bulk | CHN | per-source (state-aligned) | **A** with **§2(g) flag** | `cn_gov_data.py` (W4) | `gov/open-data/chn/government-net/` + `gov/statistics/cn-nbs/` | yes (with §2(g) flag) | yes (with §2(g) flag) |

Tier-C explicitly EMPTY in W1-W4: NO paid commercial gov-intelligence
platforms (GovWin IQ / Bloomberg Government / Politico Pro / E&E News
Pro / FiscalNote / CQ Roll Call Pro) **CONSTITUTIONALLY PROHIBITED**
per Charter Rider §2(e) + §2(c). Same admission discipline as
ADR-2605263800 §2.

## §3. Sensor abstraction (`kotodama.organism.sensors.gov.*`)

New module path: `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/sensors/gov/base.py`.

```python
# Protocol definition (excerpt; full type-checked impl lands in W1)

from typing import Protocol, TypedDict, Literal

class GovObservation(TypedDict):
    source: str                     # e.g. "us_data_gov" / "uk_hansard" / "eu_eurostat"
    jurisdiction: str               # ISO-3 OR supra ("EU", "OECD", "UN", "WB", "IMF")
    facet: Literal[
        "open-data", "parliament", "budget", "procurement", "statistics"
    ]
    dataset_id: str                 # per-source canonical ID
    published_at_utc: str           # ISO-8601 UTC
    payload_cid: str                # IPFS CID of normalized JSON payload (annex preserved)
    tier: Literal["A", "B"]         # Tier-A or Tier-B (NO Tier-C in W1-W4 per §2)
    state_aligned_flag: bool        # True iff CN-class source (§2(g) scrutiny per ADR-2605262800)
    internal_only: bool             # True iff tier=="B" with SA-propagation; or state_aligned_flag=True
    pii_redacted: bool              # True iff per-juris redaction policy applied (see §5)

class GovSensor(Protocol):
    def latest_pin(self) -> str: ...
    def hot_sample(self, pin_cid: str, n: int = 8) -> list[GovObservation]: ...
```

W1 implementations (path-reserved, code lands in W1 deliverable):
- `gov_open_data_sensor` — per-jurisdiction open-data portal reads
- `gov_parliament_sensor` — per-legislature transcript reads
- `gov_budget_sensor` — per-jurisdiction budget + spending reads
- `gov_procurement_sensor` — per-jurisdiction tender + award reads
- `gov_statistics_sensor` — per-IGO statistics reads

## §4. Training corpus recipes (cold path)

New directory: `70-tools/baien-moemoekyun-train/recipes/gov/`.

| Recipe | Sources | License-mix | Train-tier | Consumer |
|---|---|---|---|---|
| `gov-civic-literacy-foundations-r1.toml` | Eurostat + WB + OECD + US Congress.gov + UK Hansard + JP 国会会議録 | all Tier-A | publishable artifact | manabi L4 civic-literacy curriculum |
| `gov-budget-transparency-r1.toml` | USAspending + EU FTS + UK Treasury + JP 予算書 | all Tier-A | publishable artifact | ossekai aggregate-publication + toritate cross-ref |
| `gov-procurement-transparency-r1.toml` | EU TED + US SAM.gov + UK Contracts Finder + JP 政府調達 | all Tier-A | publishable artifact | toritate vendor anti-related-party check |
| `gov-parliament-procedural-r1.toml` | US Congress.gov + UK Hansard + EU OEIL + JP 国会会議録 + DE Bundestag + FR Assemblée | all Tier-A | publishable artifact | chigiri state-function-routing-around evidence base |
| `gov-statistics-foundations-r1.toml` | Eurostat + OECD + WB + IMF + UN data | all Tier-A | publishable artifact | baien-distill civic-reasoning specialist |

## §5. PII / publication-redaction policy

Parliament transcripts + procurement awards contain member personal
statements, citizen-petitioner names, awardee company names, bid
amounts, sometimes individual contractor names. Pass-through default
(publication is the public-good reason these regimes exist), with the
following exceptions:

| Source class | Publication rule | Religious-corp policy |
|---|---|---|
| Parliament transcripts | named (members, witnesses, citizen-petitioners) | pass-through |
| Procurement awards | named (awardee companies, often individual contractors) | pass-through (transparency-regime reason) |
| Budget recipients | named (recipient orgs, sometimes individuals on subaward) | pass-through |
| Open-data portal datasets | varies per-dataset | honor upstream dataset license + any embedded redaction tags |
| **General** | GDPR / CCPA right-to-be-forgotten requests on parliament historical record | DSARs route through **chigiri.data_privacy** cell to upstream publisher, NEVER unilateral religious-corp removal |

PII filter (`pii_filter.py` per ADR-2605262400 §6) runs as defense-in-
depth (emails / E.164 / postal addresses / WHOIS-style free-text). CN
data carries `state_aligned_flag=True` per §2(g) (parallel to
ADR-2605262800 CN NPC handling): ingested as authoritative source of
record (citizens have right to see state-aligned data) but
non-substitution doctrine — religious-corp does NOT treat CN gov data
as independently verified; downstream consumers (ossekai, manabi) MUST
display the flag in any derived publication.

## §6. Passive-only network discipline (inherits ADR-2605262400 §7)

Prohibited:
- N1. Live data.gov / data.gov.uk / data.gouv.fr / data.go.jp portal scraping
- N2. Live Congress.gov / Hansard / 国会会議録 per-document scraping
- N3. Live USAspending / EU FTS / SAM.gov / TED per-query API hits
- N4. Live Eurostat / OECD.Stat / WB / IMF / UN per-indicator API hits
- N5. Any active probe against gov-tagged hosts

Permitted: pre-published bulk archives + bulk-API snapshots (e.g.,
Eurostat full SDMX dataset dump on documented cadence) via the
declared fetcher modules, with cadence respecting upstream rate-limit +
robots.txt + ToU. Per-source acceptance flag at
`~/.etzhayyim/source-acceptance/<source>.toml` MUST be present before
fetch will run (per ADR-2605262400 W3 acceptance pattern).

## §7. Wave delivery plan

| Wave | Sources / fetchers / sensors | Estimated duration |
|---|---|---|
| **W0** = this ADR + 5 sensor path-reserves + 5 recipe templates + deps.toml + README | this commit | — |
| **W1** = US data.gov + UK data.gov.uk + JP data.go.jp + e-Stat + US Congress.gov + UK Hansard + JP 国会会議録 + Eurostat + World Bank + 5 sensors + `gov-civic-literacy-foundations-r1` + `gov-statistics-foundations-r1` recipes + §5 PII policy first cut + 2 new Kaizen rules R14 (stale-gov-pin) + R15 (parliament-cadence-drift >30d for active legislatures) | 4-5 days |
| **W2** = EU data.europa.eu + FR data.gouv.fr + DE govdata.de + OECD.Stat + IMF SDMX + USAspending + EU TED + US SAM.gov | 4-5 days |
| **W3** = EU OEIL + DE Bundestag + FR Assemblée + EU FTS + JP 政府調達 + UK Contracts Finder + UN Data + `gov-budget-transparency-r1` + `gov-procurement-transparency-r1` + `gov-parliament-procedural-r1` recipes + ossekai aggregate-publication wiring + toritate cross-ref wiring | 5-7 days |
| **W4** = CN 中国政府网 + NBS with §2(g) flag enforcement + cross-actor wiring (manabi civic-literacy curriculum L4 + chigiri state-function-routing-around evidence base + baien-distill civic-reasoning specialist) | 5-7 days |

## §8. Gates (12)

- **G1**. Charter Rider §2 scan on every ingested dataset
- **G2**. `replicationMin: 2` IPFS-pin on every revision
- **G3**. Per-jurisdiction publication-redaction policy honored (§5)
- **G4**. CN-class sources carry `state_aligned_flag=True` (§2(g) parallel to ADR-2605262800)
- **G5**. Murakumo-only inference (ADR-2605215000)
- **G6**. No-active-probe lint deny-list (data.gov / portal / parliament / budget / procurement / statistics live APIs forbidden; bulk-download utilities allowed)
- **G7**. `hot_sample` determinism
- **G8**. Recipe-in-git + per-recipe lock file
- **G9**. False-positive ≤5% / 24h on Charter Rider scan
- **G10**. `datasetPin` PDS record mandatory per published revision
- **G11**. Per-source acceptance flag present before fetch will run
- **G12**. Vendor-commercial-gov-intel-terminal deny-list lint (GovWin IQ / Bloomberg Government / Politico Pro / E&E News Pro / FiscalNote / CQ Roll Call Pro imports + API hostnames forbidden at lint time)

## §9. Non-goals (12)

- **N1**. NOT a GovWin IQ / Bloomberg Gov / Politico Pro / FiscalNote replacement (CONSTITUTIONALLY PROHIBITED per Charter Rider §2(e))
- **N2**. NOT live-portal client (passive-only per §6)
- **N3**. NOT a lobbying-target generator (G3 publication-rule-honoring; aggregate-only ossekai publication)
- **N4**. NOT a political-campaign tool (religious-corp is non-political per Charter §1.12 routing-around — state-function substitution, not state-political-engagement)
- **N5**. NOT a paywall-bypass tool (only sources with open bulk archives admitted)
- **N6**. NOT a citizen-de-anonymization service (G3; DSARs route through chigiri.data_privacy)
- **N7**. NOT a state-surveillance enabler (passive-only; aggregate-anonymized publication discipline; ossekai G3 honors mute/block)
- **N8**. NOT a substitute for licensed policy or legal advice (UPL-equivalent boundary; manabi curriculum is literacy-only; chigiri.ipLicenseClaim routes to licensed counsel)
- **N9**. NOT a vendor-LLM inference path (Murakumo-only per G5)
- **N10**. NOT a substrate engine replacement (kotoba per ADR-2605262130 remains canonical)
- **N11**. NOT a treat-CN-gov-data-as-independently-verified pretense (§2(g) flag + state-aligned non-substitution doctrine per ADR-2605262800)
- **N12**. NOT cross-religious-corp federation (per-religious-corp deployment)

# Consequences

## Positive

- ossekai (ADR-2605264000) gains aggregate-publication evidence base
  for state-function-routing-around discourse per Charter §1.12.
- toritate (ADR-2605262900) gains procurement cross-reference path
  (recipient-vendor anti-related-party check via gov procurement +
  cross-juris regulatory-recipient check via open-data registries).
- chigiri (ADR-2605262700) gains structured state-function-routing-
  around evidence base — covenant_ceremony / inheritance / withdrawal
  procedures can cite publicly-recorded state procedure when claiming
  Charter §1.12 routing-around substitution context.
- manabi gains a Tier-A civic-literacy primary-source corpus
  (parliament + budget + procurement + statistics).
- baien-distill gains civic-reasoning specialist artifact path.
- ossekai + toritate + chigiri + manabi all unblocked on the
  "what does the state actually publish?" question — currently a gap.

## Negative

- Storage cost: post-W4 estimated ≈ 200-300 GB per fleet node (parliament
  transcripts and Eurostat full SDMX dominate; ~150 GB statistics +
  ~80 GB parliament + ~30 GB budget + ~20 GB procurement + ~20 GB
  open-data portal metadata). Within Murakumo fleet capacity but
  largest gov ingestion of any religious-corp ADR.
- CN data §2(g) flag requires every downstream consumer to honor +
  display the flag in published output (additional UI + projection
  surface burden on ossekai + manabi).

## Risks

- Per-jurisdiction publication-rule drift (e.g., GDPR amendments
  affecting parliament historical-record retention). Same mitigation
  as ADR-2605263800: R8 Kaizen rule + per-juris silenReview cycle +
  chigiri.data_privacy publication-rule-change notification.
- Vendor-commercial-gov-intel-terminal lint G12 deny-list maintenance
  overhead (similar to ADR-2605263800 G12).

# Alternatives Considered

1. **Use a commercial gov-intel aggregator** (FiscalNote / Bloomberg
   Government / Politico Pro). Rejected: CONSTITUTIONALLY PROHIBITED
   per Charter Rider §2(e) + §2(c).
2. **Live-portal API only (no bulk archive ingestion)**. Rejected:
   violates ADR-2605262400 §7 passive-only.
3. **Skip CN data entirely (exclude §2(g)-flagged sources)**.
   Rejected: information-symmetry public-good requires that
   state-aligned data be ingested with proper flagging; exclusion would
   create asymmetric coverage favoring Western-jurisdiction perspectives.
4. **Treat parliament + budget + procurement as separate ADRs**.
   Rejected: same ingestion + tier + sensor pattern across all four
   gov facets; single ADR simpler and matches ADR-2605262400 +
   ADR-2605262800 sibling-pattern principle.

# References

- ADR-2605262400 — Public-data ingestion (parent pattern)
- ADR-2605262800 — Global legal corpus ingestion (sibling, also CN §2(g) precedent)
- ADR-2605263800 — Global corporate-disclosure ingestion (sibling)
- ADR-2605264000 — ossekai information-arbitrage actor (downstream consumer)
- ADR-2605262900 — toritate accounting + audit (downstream consumer)
- ADR-2605262700 — chigiri legal procedure (downstream consumer)
- ADR-2605262130 — kotoba storage substrate
- ADR-2605241500 — Dataset CID substrate (DataLad + IPFS)
- ADR-2605215000 — Murakumo-only inference invariant
- ADR-2605192200 — Charter Rider v2.0
- ADR-2605192100 — Mission Charter §1.12 state-function routing-around
- US data.gov: https://www.data.gov
- UK data.gov.uk: https://www.data.gov.uk (OGL v3.0)
- JP data.go.jp + e-Stat: https://www.data.go.jp + https://www.e-stat.go.jp
- EU data.europa.eu: https://data.europa.eu
- US Congress.gov bulk: https://www.congress.gov/help/using-data-offsite
- UK Hansard: https://hansard.parliament.uk
- Eurostat: https://ec.europa.eu/eurostat
- World Bank Open Data: https://data.worldbank.org (CC-BY 4.0)
- IMF SDMX: https://data.imf.org
- USAspending.gov: https://www.usaspending.gov
- EU TED: https://ted.europa.eu
- US SAM.gov: https://sam.gov
