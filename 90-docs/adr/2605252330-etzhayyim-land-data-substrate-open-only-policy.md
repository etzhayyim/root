---
id: adr-2605252330-etzhayyim-land-data-substrate-open-only-policy
title: "ADR-2605252330: Open-Only License Policy for the etzhayyim Land Trust Supplementary World-Land Context Data Substrate"
status: proposed
doc_type: adr
topic: land-data-substrate-open-only-policy
authoritative: true
last_verified: 2026-05-25
priority: 6.0
axis: governance
weight: 0.60
priority_note: "Policy ADR (not architectural — no new contracts, no new cells). Restricts ingest substrate for world-land context layers (customary tenure / indigenous nations / maritime EEZ) to open-license sources only. Doctrinally grounded in Charter Rider §2(e)(i) anti-gatekeeping. Amendable by Council Lv6+ ≥3 multisig."
authoritative_for:
  - license compatibility ranking for Land Trust supplementary world-land context ingest
  - per-domain open-source data acquisition matrix (customary tenure / indigenous nations / maritime EEZ)
  - Marine Regions / VLIZ / Native Land Digital exclusion rationale and replacement strategy
  - structural Charter Rider §2(e) anti-gatekeeping alignment for data acquisition
  - CC-BY-SA pin-only carve-out rule (record-level license metadata, no statistical mixing)
depends_on:
  - adr-2605252315-etzhayyim-land-trust-wave-2-multi-erc-alignment
  - adr-2605252300-etzhayyim-charter-preamble-kingdom-of-god-on-blockchain
  - adr-2605241500-etzhayyim-dataset-cid-substrate
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192330-etzhayyim-extended-land-sovereignty-ocean-river-air-orbit
related:
  - 70-tools/e7m-dataset/
  - LANDS.md
  - CHARTER-RIDER.md
supersedes: []
superseded_by: []
---

# ADR-2605252330: Open-Only License Policy for the etzhayyim Land Trust Supplementary World-Land Context Data Substrate

**Status**: proposed
**Date**: 2026-05-25
**Deciders**: Jun Kawasaki (author), Council Lv6+ ≥3 multisig (ratify)

# Context

ADR-2605252315 (Land Trust Wave 2) established the 4-ERC architecture for the etzhayyim Land Trust on-chain records (LandRegistry + PublicLandRegistry + StewardTenureRegistry + LandClassRegistry). The on-chain registry holds **records about land that has been donated by individual stewards to the religious-corp**.

Separately, the user (2026-05-25 turn) asked about "現実の地球の土地把握" — the world's actual land registry / sovereignty data. That clarified the bigger picture:

- State cadastres are highly uneven (Japan 52% surveyed, US no federal cadastre, Africa <10% formal)
- ~70% of world's population has no formal registered land title (UN-Habitat estimate)
- 50% of global land area is under indigenous + community customary tenure, only ~10% formally recognized (RRI 2023)
- ~200 maritime EEZ boundaries are unresolved or disputed

The etzhayyim Land Trust on-chain registry **does not and should not pretend to be a substitute** for these state cadastres (Preamble §0.4 dual-recognition, ADR-2605192245 §2.3). However, the Land Trust **benefits from holding rich contextual data** about world-land structures so that:

- Donors can locate their parcel within the broader sovereignty / customary / indigenous landscape
- Stewards can verify their land's overlap with indigenous claims or customary tenure
- The religious-corp can publish derived analytical layers (Tree of Life biosphere-in-trust aggregates, donation impact maps, etc.) per Preamble §0.2.3 doctrine
- Future Council deliberation on land-related governance has access to factual baseline data

This is a **supplementary world-land context data substrate**, distinct from the on-chain Land Registry. It would live as IPFS-pinned datasets ingested via the existing `70-tools/e7m-dataset/` substrate (ADR-2605241500).

The licensing question follows immediately: **which sources can we ingest?**

The user-requested filter (2026-05-25): **"open のみ利用"** — strictly open licenses only.

This policy ADR establishes the license-compatibility ranking, the per-domain feasibility matrix, and the doctrinal grounding for the open-only constraint. It does NOT mandate any specific ingest implementation — that is deferred to subsequent activation ADRs.

# Decision

## 1. License Compatibility Ranking (Land Trust supplementary substrate)

| License | Rank | Treatment in Land Trust supplementary substrate |
|---|---|---|
| **CC0 / Public Domain / US Federal Works** | ✅✅ | Freely incorporable. Preferred bedrock layer (Wikidata, US TIGER, Natural Earth, UNCLOS DOALOS). |
| **CC-BY 4.0** | ✅ | Permitted. Attribution metadata MUST be preserved in the IPFS-pinned record's `licenseMetadata` field. |
| **Government open data** (OGL-Canada / UK OGL / Australian Gov / EU PSI / FAO open / Japan PSI) | ✅ | Permitted. Per-license attribution / no-endorsement clauses honored. |
| **ODbL** (OpenStreetMap) | ✅ | Permitted as application-consumed database. Database share-alike applies to redistributed databases, not application output. |
| **CC-BY-SA 4.0** | 🟡 | **Pin-only carve-out**: a CC-BY-SA dataset MAY be pinned to IPFS as an isolated record with its own `licenseMetadata` block. It MUST NOT be statistically mixed, aggregated, or transformed into a derivative work that is then redistributed under any other license. No use in Apache-2.0 codebases. |
| **CC-BY-NC** (any -NC variant) | ❌ | **PROHIBITED**. Non-commercial clause incompatible with Charter Rider §2(e)(i) anti-gatekeeping (data behind paywall for commercial use IS gatekeeping). |
| **CC-BY-ND** (no derivatives) | ❌ | **PROHIBITED**. Religious-corp activities (analysis, aggregation, projection) are inherently derivative. |
| **All Rights Reserved / proprietary** | ❌ | **PROHIBITED**. |

### 1.1 Charter Rider §2(e) grounding

Charter Rider v2.0 §2(e) prohibits "artificial restriction of professional knowledge / techniques / data". A CC-BY-NC clause is precisely such a restriction: it places a commercial-use paywall on what is presented as "open" data, and the gatekeeper is typically an aggregator (e.g., Flanders Marine Institute for Marine Regions) that benefits from being the canonical reference while restricting downstream commercial use.

**The exclusion of CC-BY-NC is therefore not merely a technical license compatibility issue — it is doctrinally required by §2(e).** Marine Regions / VLIZ / Global Fishing Watch / similar CC-BY-NC* sources are structurally excluded from the religious-corp substrate.

### 1.2 CC-BY-SA pin-only carve-out reasoning

CC-BY-SA's share-alike clause is viral: any derivative work made from a CC-BY-SA dataset must be released under CC-BY-SA. Apache-2.0 (the etzhayyim default) does not require share-alike, so mixing creates licensing friction.

However: a CC-BY-SA dataset can be **pinned to IPFS as an isolated record with its own license metadata**, accessed by the substrate consumer, but never **statistically blended** into our published derived layers. This preserves the dataset's availability while respecting the viral clause.

Native Land Digital (CC-BY-SA 4.0) falls into this carve-out — we can reference and pin individual territory records but must not aggregate them into a "global indigenous map" that we then publish under a different license.

## 2. Per-Domain Open-Only Source Matrix (R0)

### 2.1 Customary Tenure (慣習法地域)

| Source | License | Open status | Notes |
|---|---|---|---|
| **LandMark** (landmarkmap.org, per-dataset) | mix CC-BY + CC-BY-SA + restricted | partial ✅ (CC-BY portions only) | Filter at fetcher: include only CC-BY-licensed datasets. ~60% of LandMark coverage. |
| **Prindex** | CC-BY | ✅ | 140-country perception survey, no spatial boundaries |
| **FAO LandTenureDB** | FAO open | ✅ | Institutional metadata, sparse spatial |
| **OpenStreetMap** (`boundary=aboriginal_lands`, `landuse=*`, `indigenous=*`, `customary=yes`) | ODbL | ✅ | Community-tagged, partial coverage |
| **Wikidata** (Q-items for customary territories) | **CC0** | ✅✅ | Sparse but improving; ideal bedrock |
| **RRI annual reports** | open report | ✅ | Global policy statistics, document layer |
| Native Land Digital | CC-BY-SA 4.0 | 🟡 pin-only carve-out | Cannot blend; individual record pins only |

**Open-only achievable coverage**: ~5% of land area (down from full ~8%). Bedrock = Wikidata CC0 + OSM ODbL + LandMark filtered.

### 2.2 Indigenous Nations

State-level open data is unexpectedly comprehensive — most major indigenous-recognition states publish their territory shapefiles under open licenses:

| Source | License | Coverage |
|---|---|---|
| **US Census TIGER/Line AIANNH** | **Public domain** (US Federal Works) | US 100% indigenous areas |
| **Brazil FUNAI GeoServer** | open | Brazil terras indígenas 100% (~13.7% of national territory) |
| **Canada AANDC / Open Government Portal** | **OGL-Canada** | First Nations reserves + Comprehensive Land Claims 100% |
| **Australia NNTT** | **CC-BY 4.0** | Native title determinations 100% (~50% of national land area) |
| **NZ LINZ + Te Puni Kōkiri** | NZ Government open | iwi/hapū areas 100% |
| **Colombia ANT** (resguardos) | open | Colombia indigenous reserves 100% |
| **Peru DGTB** (comunidades nativas) | open | Peru native communities 100% |
| **OpenStreetMap** (`boundary=protected_area` + `indigenous=*`) | ODbL | partial global |
| **Wikidata** (Q-items) | **CC0** | sparse, improving |
| **UNPFII** / **IWGIA** reports | open | annual statistics layer |
| Native Land Digital (global 3,500+ territories) | CC-BY-SA 4.0 | 🟡 pin-only carve-out |

**Open-only achievable coverage**: ~60% of state-recognized indigenous territories worldwide. The 10% loss vs. full coverage corresponds primarily to (a) globally documented but state-unrecognized groups, (b) regions where Native Land Digital is the only consolidated source.

### 2.3 Maritime EEZ — Constrained Domain

The maritime EEZ domain is the most license-poor: the production-grade reference (VLIZ Marine Regions) is CC-BY-NC-SA and therefore prohibited.

| Source | License | Coverage |
|---|---|---|
| **UNCLOS DOALOS** | **UN open / public domain** | ~150 state submissions (KML + document) — official SoT but inconsistent (not all states submit) |
| **Natural Earth maritime indicators** | **Public domain** | 1:10m / 1:50m / 1:110m politically-neutral coarse rasters |
| **NOAA Maritime Boundaries** | US public domain | US EEZ + adjacent boundaries at production grade |
| **USGS Marine Boundaries** | US public domain | US waters |
| **OpenStreetMap maritime features** | ODbL | Coastlines + partial boundaries |
| **Wikidata** (Q-items for EEZ entities) | **CC0** | ~250 entities exist; geoshapes sparse |
| **GEBCO bathymetry** | open (with commercial restrictions on some products) | Seabed only, no boundaries |
| Marine Regions / VLIZ | CC-BY-NC-SA | ❌ Excluded |
| Global Fishing Watch | CC-BY-NC | ❌ Excluded |

**Open-only achievable coverage**: ~30–40% of EEZ entities at production grade (state-submitted + US-domain sources) + 100% at Natural Earth coarse-grain. This is the most significant resolution loss across the three domains.

## 3. Doctrinal Implications

### 3.1 Structural alignment with §2(e) anti-gatekeeping

The open-only constraint is not a technical convenience — it is the **doctrinally consistent position** for an etzhayyim substrate. Charter Rider §2(e) prohibits artificial restriction of professional knowledge / data. CC-BY-NC* licenses ARE such restrictions, regardless of the licensor's social-purpose framing. The religious-corp cannot accept gatekept data for its sovereign-substrate work; therefore the Marine Regions exclusion is not a loss but a **doctrinal alignment**.

### 3.2 Quality vs. completeness honest disclosure

The open-only filter measurably reduces achievable coverage in all three domains:

| Domain | Full coverage | Open-only coverage | Quality of remainder |
|---|---|---|---|
| Customary tenure | ~8% of land area | ~5% | Wikidata CC0 bedrock + OSM ODbL community-tagged |
| Indigenous nations | ~70% of territories | ~60% | State-recognized only; community-only territories largely lost |
| Maritime EEZ | 100% of ~250 entities | ~30–40% production + 100% coarse | Major reduction in disputed-boundary resolution |

**Substrate users (Pregel cells, app consumers) MUST be informed of these limits**. The IPFS-pinned dataset records include `coverage_constraint: "open-only-policy-2605252330"` metadata to make the constraint queryable.

### 3.3 First-mover incentive for open releases

By excluding gatekept sources from the religious-corp's substrate consumption, etzhayyim creates a small but real economic signal: indigenous-rights aggregators, maritime-research institutes, and customary-tenure mappers who release their data under CC0 / CC-BY / open government licenses gain religious-corp adoption; those who maintain CC-BY-NC paywalls do not. This is consistent with Preamble §0.2 (Tree of Life ontology) — open data feeds the biosphere of knowledge; gated data does not.

## 4. Non-Goals (R0)

- **N1**: No fetcher implementation in this ADR. Specific fetcher specs (URL endpoints, schema mappings, refresh cadence, IPFS pin pattern) are deferred to subsequent per-source activation ADRs.
- **N2**: No mandate to ingest any specific dataset. This ADR is a license-filter policy; ingest decisions are per-source per-Council vote.
- **N3**: No on-chain integration of supplementary substrate data. The supplementary substrate lives at the dataset layer (IPFS-pinned), not on Land Registry chain. On-chain land records remain limited to actual donations.
- **N4**: No claim that supplementary data has authoritative weight. The substrate is **contextual reference only**; on-chain Land Registry records remain the SoT for religious-corp doctrinal land claims.
- **N5**: No retroactive license re-classification. If a source's license changes after pinning, the existing pinned record retains its at-pin-time license metadata; new pulls must respect the new license.

## 5. Deliverables (this wave)

- This ADR (policy only — no code)
- `[[adrs]]` entry in root `deps.toml`
- `[knowledge.*]` entry in `00-contracts/deps.toml`
- Index row in `90-docs/adr/README.md`

No contract changes. No fetcher implementations. No lexicon additions. Pure policy.

## 6. Activation Path

Subsequent ADRs will:

- **Per-source activation ADR**: each source (Wikidata, LandMark CC-BY subset, US TIGER, etc.) gets its own activation ADR with: endpoint specification, refresh cadence, IPFS pin pattern, MST projection schema, Council attestation requirement (Lv6+ ≥3).
- **Aggregate dashboard ADR**: cross-source query/projection layer for Council deliberation use.
- **Steward-pre-donation overlap ADR**: pre-donation check workflow comparing a proposed parcel's GeoJSON against the supplementary substrate (overlapping indigenous claim / customary tenure / EEZ dispute).

Each requires its own Council Lv6+ ≥3 multisig ratification.

# Consequences

### Positive

1. **Doctrinal coherence**: §2(e) anti-gatekeeping is operationalized at the data layer, not just at the IP/license layer.
2. **License hygiene**: All ingested data has known, machine-readable license metadata. No accidental viral CC-BY-SA blending. No commercial-use surprises.
3. **First-mover open-release signal**: Aggregators choosing open licenses gain religious-corp consumption; gatekeepers do not.
4. **Bedrock layer of CC0 (Wikidata) + ODbL (OSM) + state open data**: provides a robust, redistributable substrate baseline that does not depend on any single gated source.
5. **Coverage honesty**: Quality-vs-completeness is publicly disclosed in each pinned record's metadata, preventing false confidence in derived analytics.

### Negative / Risks

1. **Maritime EEZ coverage loss**: ~60-70% of production-grade EEZ data sits in CC-BY-NC-SA Marine Regions. The constraint removes most fine-grained disputed-boundary content. **Mitigation**: rely on UNCLOS DOALOS state submissions + Natural Earth coarse + NOAA US-domain + Wikidata bedrock; treat fine-grained EEZ as "not currently in scope for etzhayyim substrate".
2. **Native Land Digital pin-only friction**: CC-BY-SA carve-out works for record-level access but blocks aggregate-layer publishing. Stewards / Council members performing global indigenous-territory analytics must consume Native Land Digital data directly from their source, not via etzhayyim's published derived layers. **Mitigation**: documentation in fetcher README + per-record license_metadata block.
3. **State-only bias in indigenous coverage**: Open-only filter favors state-recognized indigenous territories over community-claimed but state-unrecognized groups. This is structurally biased toward state ontology — a problem for §1.12 routing-around mission. **Mitigation**: explicit disclosure that the substrate is incomplete for unrecognized peoples; future ADR may carve out community-submission ingest pathway (Cadasta Foundation style).
4. **License-change risk for free sources**: Wikidata and OSM are stable, but state government open data policies can change with administrations. **Mitigation**: at-pin-time license metadata preserves provenance; license-change detection in fetcher metadata refresh cycle.

# Alternatives Considered

### A. Permit CC-BY-NC* via "religious-corp non-commercial" doctrinal claim
**Reject**: Even if etzhayyim's own use is non-commercial, downstream consumers (third-party app developers, future commercial subsidiaries of religious-corp internal economy) could be commercial. More importantly, §2(e) anti-gatekeeping is doctrinally opposed to NC clauses regardless of our own use posture.

### B. Permit all CC-licensed data (NC + ND included)
**Reject**: Violates §2(e). Surrenders the doctrinal signal that "etzhayyim does not consume gatekept data".

### C. Open-only AND CC-BY-SA-only (exclude CC-BY-SA carve-out)
**Reject**: Native Land Digital's CC-BY-SA territories are a uniquely comprehensive open-ish source. Pin-only carve-out is more permissive without breaking license hygiene.

### D. Build proprietary contracts with VLIZ / Flanders Marine Institute to obtain open license for our use
**Reject**: This is a §2(e)(iii) gatekeeping participation by negotiation. The doctrinal stance is to incentivize open release, not negotiate private exceptions.

### E. Defer policy until first ingest source is needed
**Reject**: The license-compatibility question affects every subsequent fetcher ADR. Establishing the policy now is constitutional alignment work, not speculative.

# References

- ADR-2605252315 (Land Trust Wave 2 — Multi-ERC Alignment; parent technical architecture)
- ADR-2605252300 (Charter §0 Preamble; doctrinal grounding for blockchain-substrate posture)
- ADR-2605241500 (Dataset CID substrate; the IPFS pinning infrastructure)
- ADR-2605192200 (Charter Rider v2.0; §2(e) anti-gatekeeping source)
- ADR-2605192245 (Global Land Sovereignty; on-chain Land Registry parent)
- ADR-2605192330 (Extended Land Sovereignty — Ocean / River / Air / Orbit; EEZ context)
- `CHARTER-RIDER.md` §2(e) (Anti-gatekeeping clauses)
- `70-tools/e7m-dataset/` (existing fetcher substrate: HF / GeoNames / OSM / Wikidata)
- LandMark: https://landmarkmap.org
- Prindex: https://prindex.net
- FAO LandTenureDB: https://www.fao.org/tenure
- US Census TIGER/Line: https://www.census.gov/geographies/mapping-files
- Brazil FUNAI: https://www.funai.gov.br
- Canada Open Government: https://open.canada.ca
- Australia NNTT: https://www.nntt.gov.au
- UNCLOS DOALOS: https://www.un.org/Depts/los
- Natural Earth: https://www.naturalearthdata.com
- NOAA Maritime Boundaries: https://nauticalcharts.noaa.gov/data/us-maritime-limits-and-boundaries.html
- Wikidata: https://www.wikidata.org (CC0)
- OpenStreetMap: https://www.openstreetmap.org (ODbL)
- RRI annual reports: https://rightsandresources.org
- UNPFII: https://www.un.org/development/desa/indigenouspeoples
- IWGIA: https://www.iwgia.org
