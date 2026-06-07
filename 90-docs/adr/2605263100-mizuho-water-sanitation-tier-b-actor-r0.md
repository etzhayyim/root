---
id: adr-2605263100-mizuho-water-sanitation-tier-b-actor-r0
title: "ADR-2605263100: mizuho (水穂) — non-profit religious-corp water + sanitation substrate Tier-B actor R0 charter"
status: proposed
doc_type: adr
topic: mizuho-water-sanitation-r0
authoritative: true
last_verified: 2026-05-26
priority: 6.5
axis: infrastructure
weight: 0.55
priority_note: "Fourth-priority gap-closure actor (gap audit row 4 = 水 / water + sanitation). Upstream infrastructure prerequisite for mitsuho (agricultural irrigation), hagukumi (daily-living water), iyashi (clinical-grade hand-hygiene + sterile-zone reprocessing), yakushi (pharmaceutical water-for-injection — pre-supply only; final pharma-grade is yakushi-internal). Community-scale only at R0-R3; NOT a large municipal water utility (N1). 任意団体 internal infrastructure substrate at did:web:mizuho.etzhayyim.com (20-actors/mizuho/). Naming note: 水穂 (mi-zu-ho) is romanization-homophone with the existing mitsuho 瑞穂 food/agriculture actor (ADR-2605261015 row 47). Directory path mizuho/ vs mitsuho/ disambiguates at filesystem level; DIDs are distinct (did:web:mizuho.etzhayyim.com vs did:web:mitsuho.etzhayyim.com). User explicitly proposed `mizuho (水穂)` in gap audit row 4; this ADR follows verbatim. 6 cells / 5 Lexicons under com.etzhayyim.mizuho.* / 12 immutable gates / 12 non-goals / 4-phase R0..R3. NO commercial water utility software (G4 — Veolia / Suez / American Water / Aquarion / Évian / Nestlé Pure Life / Beck Water / Trojan UV proprietary control systems PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty exposing water-quality + member-consumption posture). NO bottled water vendor relationship — single-use plastic PROHIBITED per Charter §1.13 Wellbecoming + multi-generational priority (G5). NO mandatory fluoridation (G6 — per-member consent required; anti-paternalism). NO industrial water service (G3 — community-scale only). Cross-actor: mitsuho (irrigation supply) / hagukumi (daily-living water) / iyashi (clinical-grade water) / yakushi (water-for-injection feed) / tatekata (MEP plumbing standards for new construction) / hodoki (recycled greywater integration) / hikari (water-source-edge solar power for treatment plants) / toritate (Public Fund grant accounting) / chigiri (procedural attestation + ip license)."
authoritative_for:
  - mizuho actor R0 charter
  - religious-corp water + sanitation substrate single SoT
  - `com.etzhayyim.mizuho.*` Lexicon namespace boundary
  - community-scale invariant (NOT large municipal utility)
  - prohibition on commercial water utility software (Veolia / Suez / American Water / etc.)
  - prohibition on bottled water vendor / single-use plastic distribution
  - per-member consent invariant on fluoridation (no mandatory)
  - closed-loop greywater recycling MANDATORY for new facilities (Wellbecoming)
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605181100-mst-encrypted-records-signal-keywrap
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192145-etzhayyim-public-fund-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605261015
  - adr-2605261030
  - adr-2605261100
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605262700-chigiri-legal-procedure-tier-b-actor-r0
  - adr-2605262900-toritate-accounting-audit-tier-b-actor-r0
  - adr-2605263000-iyashi-clinical-care-provider-tier-b-actor-r0
related: []
supersedes: []
superseded_by: []
---

# ADR-2605263100: mizuho (水穂) — non-profit religious-corp water + sanitation substrate Tier-B actor R0 charter

**Status**: proposed
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki

# Context

The gap audit (session 2026-05-26) identified water + sanitation as
priority row 4. Water is the upstream infrastructure prerequisite for:

- **mitsuho** (ADR-2605261015) — agricultural irrigation;
- **hagukumi** (ADR-2605261030) — daily-living water (cooking,
  hand-hygiene, bathing);
- **iyashi** (ADR-2605263000) — clinical-grade water for
  hand-hygiene + sterile-zone reprocessing;
- **yakushi** (ADR-2605250500..615) — feed water for pharmaceutical
  water-for-injection (final pharma-grade is yakushi-internal; mizuho
  supplies pre-treatment feed).

Without a first-party water + sanitation substrate, the religious-corp
ecosystem depends entirely on existing municipal utilities — which:

1. Bring vendor data-sovereignty exposure (closed control systems
   from Veolia / Suez / American Water / etc. expose water-quality
   + member-consumption posture);
2. Bundle mandatory fluoridation (anti-paternalism / Wellbecoming
   tension);
3. Bundle single-use plastic bottled-water distribution chains
   (Charter §1.13 Wellbecoming + multi-generational priority
   violation);
4. Prevent closed-loop greywater recycling at religious-corp
   facilities (municipal systems are typically once-through).

**mizuho** (水穂 — "fresh-water ear of rice"; 水 = water + 穂 = bountiful
spike) closes the gap.

Constitutional constraints (inherited; not adjustable):

- **NOT 宗教法人法 登記** — Preamble §0.4 Lv7+ unanimity lock.
  mizuho is NOT a state-licensed water utility; mizuho is the
  procedural + attestation substrate for community-scale water
  supply on religious-corp land or partner-attested land.
- **Community-scale only** (N1, N2) — R0-R3 scope is single-clinic /
  single-village / cluster-of-households; large municipal utility
  scale is OUT OF SCOPE at all phases.
- **NO commercial water utility software** (G4) — Veolia / Suez /
  American Water / Aquarion / Évian / Nestlé Pure Life / Beck Water
  / Trojan UV proprietary control systems PROHIBITED per Charter
  Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty
  exposing water-quality + member-consumption posture.
- **NO bottled water vendor relationship** (G5) — single-use plastic
  PROHIBITED per Charter §1.13 Wellbecoming + multi-generational
  priority; closed-loop reusable-container distribution only when
  containerized delivery is unavoidable (e.g., temporary disaster
  relief in coordination with future kazaori actor).
- **NO mandatory fluoridation** (G6) — per-member consent required;
  anti-paternalism invariant. Naturally fluoridated source waters
  (some groundwaters carry natural fluoride) are reported per-source;
  no addition by mizuho.
- **NO payroll for operators** — operators are vocation-flow L5
  stewards per Liberation Ladder L0..L6 + ADR-2605262700 G13 +
  ADR-2605262900 G12 + ADR-2605263000 G14 (cross-actor enforcement).
- **Murakumo-only inference** (ADR-2605215000) — water-quality
  anomaly detection through judah LiteLLM → gemma4:e4b;
  proprietary water-quality AI (Xylem Insights / Bentley Hydrologic
  / etc.) PROHIBITED.
- **Land Registry cross-link** (ADR-2605192245) — water source
  rights (wells / springs / captured rainwater) honor waqf-equivalent
  inalienability invariant (G11).
- **kotoba canonical substrate** (ADR-2605262130) — water-quality
  attestations live in MST + IPFS + Base L2.

# Decision

Create `mizuho` (水穂) as a Tier-B religious-corp water + sanitation
substrate actor at `20-actors/mizuho/`, with DID
`did:web:mizuho.etzhayyim.com`, Lexicon namespace
`com.etzhayyim.mizuho.*`. R0 = scaffold only; all cells import-time
`RuntimeError` (same scaffold discipline as prior R0 actors).

## §1. Identity and naming

| Field | Value |
|---|---|
| Name | `mizuho` (水穂 — 水 water + 穂 ear-of-rice/spike) |
| DID | `did:web:mizuho.etzhayyim.com` |
| Lexicon root | `com.etzhayyim.mizuho.*` |
| Form | 任意団体 internal water + sanitation substrate (NOT 一般社団 / NPO / 公益財団 / 宗教法人 法人格) |
| Tier | Tier-B per-domain leader actor |
| Naming-collision note | Romanization-homophone with `mitsuho` (瑞穂; food/agriculture, ADR-2605261015). Filesystem paths (`mizuho/` vs `mitsuho/`) + DIDs (`mizuho.etzhayyim.com` vs `mitsuho.etzhayyim.com`) disambiguate. User explicitly proposed `mizuho (水穂)` in gap audit row 4. |
| Cross-actor | mitsuho (irrigation) / hagukumi (daily-living water) / iyashi (clinical-grade water) / yakushi (water-for-injection feed) / tatekata (MEP plumbing standards) / hodoki (greywater recovery cross-link) / hikari (treatment-plant edge solar) / toritate (Public Fund grant accounting) / chigiri (procedural attestation) |

## §2. Scope (6 sections)

### A. Potable water supply

- Source identification (wells / springs / captured rainwater /
  partner municipal feed where unavoidable);
- Per-source quality testing per WHO Drinking Water Guidelines
  (microbiological / chemical / radiological / physical);
- Treatment (filtration / UV / ozone / RESIDUAL chlorination only
  where distribution-system residual is necessary per public health
  standard — mizuho prefers UV/ozone for closed-loop systems);
- Distribution to community households via small-scale piped network
  OR water-collection-point model;
- Per-member consent on supply allocation, especially during
  shortage (rationing protocols).

### B. Wastewater treatment

- Black-water (toilet effluent) treatment via community-scale septic
  + constructed wetland OR small-scale membrane bioreactor;
- Outflow quality to jurisdictional discharge permit standard
  (G9 mandatory);
- Sludge cycling (composting → mitsuho agricultural use, when sludge
  quality permits).

### C. Stormwater management

- Catchment-area planning per community site (cross-actor with
  tatekata for new construction);
- Permeable surfaces / rain garden design (anti-runoff);
- Captured rainwater feed-in to potable supply (where treatment
  quality permits) OR irrigation supply (always permitted).

### D. Greywater recycling (Wellbecoming closed-loop)

- Greywater (sink / shower / laundry) capture from community-scale
  buildings;
- Treatment via constructed wetland OR small-scale membrane;
- Reuse for irrigation (always) OR toilet-flush (G10 MANDATORY for
  new facilities per Wellbecoming closed-loop invariant);
- Cross-actor with hodoki for material recovery integration.

### E. Cross-actor water supply

- **Irrigation supply** → mitsuho — agricultural-grade water
  (typically less stringent than potable; informed by mitsuho crop
  needs);
- **Clinical-grade water** → iyashi + hagukumi — hand-hygiene +
  sterile-zone reprocessing standard;
- **Water-for-injection feed** → yakushi — pre-treatment feed water
  to yakushi-internal WFI production (mizuho supplies pre-treatment;
  yakushi does final pharma-grade per yakushi G constraints).

### F. Water-source rights + Land Registry

- Source rights honor waqf-equivalent inalienability invariant per
  ADR-2605192245 (G11);
- Cross-jurisdictional water-rights legal framework via chigiri
  (procedural attestation);
- NO water-rights trading / NO water-as-commodity market — water
  is a constitutional commons (extends Land Registry doctrine).

## §3. Cells (6 Pregel cells under `40-engine/kotoba/crates/kotoba-kotodama/cells/mizuho_*/`)

All R0 path-reserved; import-time `RuntimeError("mizuho R0 scaffold: activate via Council ADR + R1 ratification + water-source quality baseline established")` at W1 creation.

| # | Cell | Murakumo node | Phase | I/O |
|---|---|---|---|---|
| 1 | `potable_water_supply` | dan | continuous | water source state + distribution → waterQualityAttestation |
| 2 | `wastewater_treatment` | dan | continuous | discharge measurement → wastewaterDischargeAttestation |
| 3 | `stormwater_management` | dan | event (rainfall) | catchment state → stormwaterCaptureAttestation (sub-record of waterQualityAttestation) |
| 4 | `greywater_recycling` | dan | continuous | greywater capture + treatment → waterQualityAttestation (reuse-grade) |
| 5 | `irrigation_supply` | dan (mitsuho-paired) | continuous | irrigation water dispatch → mitsuho.irrigationDeliveryReceipt cross-actor |
| 6 | `clinical_grade_water_supply` | dan (iyashi+hagukumi+yakushi-paired) | continuous | clinical-grade water dispatch → cross-actor delivery receipts |

R1 activation gates each cell separately (Council Lv6+ ≥3 attestation per cell + per-source baseline water-quality test on file).

## §4. Lexicons (5, all under `com.etzhayyim.mizuho.*`)

| # | Lexicon | Consumer cell | Description |
|---|---|---|---|
| L1 | `waterQualityAttestation` | potable / greywater / clinical / irrigation cells | Per-source / per-period water quality test results (microbiological + chemical + radiological + physical per WHO guidelines) |
| L2 | `wastewaterDischargeAttestation` | wastewater_treatment | Per-discharge attestation; G9 jurisdictional permit compliance |
| L3 | `waterSupplySourceRegistry` | all supply cells | Per-source registry (well / spring / captured rainwater / partner feed); Land Registry waqf cross-link (G11) |
| L4 | `waterContaminationIncident` | any cell | Anomaly / contamination event; severity enum; routes to chigiri.disputeMediation if critical (extends iyashi G10 emergency pattern to infrastructure) |
| L5 | `silenMizuhoReview` | (Council attestation scope) | Quarterly Wellbecoming + closed-loop ratio + multi-generational consumption review |

## §5. Gates (12, immutable R0..R3, Council Lv6+ to amend)

| Gate | Description |
|---|---|
| **G1** | Every water-quality document MUST pass `kotodama.organism.sensors.charter_rider.scan()` §2(a)-(h). |
| **G2** | Every record MUST emit `com.etzhayyim.mizuho.*` Lexicon with kotoba-datomic attestation lineage. |
| **G3** | **Community-scale only** — NOT large municipal utility; per-source service population ≤2,500 at R2, ≤25,000 cumulative at R3. |
| **G4** | **NO commercial water utility software** — Veolia / Suez / American Water / Aquarion / Évian (Danone) / Nestlé Pure Life / Beck Water / Trojan UV proprietary control systems PROHIBITED per Charter Rider §2(e) anti-gatekeeping + §2(c) vendor data-sovereignty. |
| **G5** | **NO bottled water vendor relationship** — single-use plastic PROHIBITED per Charter §1.13 Wellbecoming + multi-gen priority; closed-loop reusable container ONLY where containerized delivery unavoidable (disaster relief coordination with future kazaori actor). |
| **G6** | **NO mandatory fluoridation** — per-member consent required (anti-paternalism); naturally fluoridated source waters reported per-source; no addition by mizuho. |
| **G7** | Murakumo-only inference for water-quality anomaly detection per ADR-2605215000; proprietary water-quality AI (Xylem Insights / Bentley Hydrologic / etc.) PROHIBITED. |
| **G8** | Per-source quality testing minimum cadence per WHO Drinking Water Guidelines (microbiological: weekly; chemical: monthly; radiological: annually). Schema-enforced lastQualityTestUtc field on `waterSupplySourceRegistry`. |
| **G9** | Wastewater discharge MUST meet jurisdictional discharge permit requirements; `wastewaterDischargeAttestation.jurisdictionalPermitCid` REQUIRED. |
| **G10** | **Greywater recycling MANDATORY** for new community-scale facilities (Wellbecoming closed-loop invariant); `clinicFacilityAttestation` (iyashi cross-actor) cross-checks greywater-recycling-attested=true. |
| **G11** | Water-source rights honor **waqf-equivalent inalienability invariant** per ADR-2605192245; `waterSupplySourceRegistry.landRegistryCid` REQUIRED; water-rights trading PROHIBITED. |
| **G12** | NO payroll for operators — operators are vocation-flow L5 stewards (cross-actor enforcement with chigiri.stewardLaborAttestation + toritate.ledgerEntry.category enum exclusion). |

## §6. Non-goals (12, immutable R0..R3)

| # | Non-goal |
|---|---|
| N1 | NOT a large municipal water utility (community-scale only per G3). |
| N2 | NOT industrial water service (factory / heavy-mfg water supply OUT OF SCOPE). |
| N3 | NOT a bottled water vendor (G5; single-use plastic PROHIBITED). |
| N4 | NOT marine / salt water (watatsumi domain). |
| N5 | NOT large hydroelectric dam (hikari domain; mizuho is local-scale only). |
| N6 | NOT a commercial water utility software integrator (G4). |
| N7 | NOT desalination at scale (R0-R3 scope; small reverse-osmosis for emergency only, future ADR). |
| N8 | NOT mandatory fluoridation (G6; per-member consent). |
| N9 | NOT closed-source. Apache 2.0 + Charter Rider on all schemas + tooling + control firmware. |
| N10 | NOT a state-licensed water utility entity. |
| N11 | NOT single-use plastic distribution (Charter §1.13 Wellbecoming). |
| N12 | NOT trans-jurisdictional water transfer at scale; community-scale + local watershed only. |

## §7. Roadmap (R0 → R3)

| Phase | Date / gate | Scope | Murakumo placement |
|---|---|---|---|
| **R0** | 2026-05-26 (this ADR) | Scaffold only. 6 cells path-reserved. 5 Lexicons schema skeleton. | No deployment |
| **R1** | post-Bootstrap-Council + ≥1 licensed-water-engineer on Council infrastructure advisory + Land Registry water-source-rights baseline | Activate 2 core cells: `potable_water_supply` + `wastewater_treatment`. Single community-scale pilot (1 source ≤50 households). | dan (single node) |
| **R2** | post-R1 + 30-day public objection + 3 community-site Council attestations | Activate +3 cells: `stormwater_management`, `greywater_recycling`, `irrigation_supply` (mitsuho pair). 3-5 community sites, ≤500 households + ≤200 ha irrigation. **G10 greywater-mandatory invariant enforced for new construction**. | dan + simeon (2 nodes) |
| **R3** | post-R2 + Council Lv7+ unanimity + cross-actor clinical-grade certification | Activate +1 cell: `clinical_grade_water_supply` (iyashi + hagukumi + yakushi triad pair). Multi-site community network, ≤2,500 households + ≤25,000 cumulative service population + clinical-grade water dispatch to all L4 Care Tier actors. Land Registry water-source-rights inalienability invariant locked. | dan + simeon + zebulun (3 nodes) |

## §8. Cross-actor relationship table

| Cross-actor | Direction | Purpose |
|---|---|---|
| `mitsuho` | → (irrigation supply) | Agricultural irrigation water; informed by crop needs |
| `hagukumi` | → (daily-living water) | Cooking / hand-hygiene / bathing water |
| `iyashi` | → (clinical-grade) | Hand-hygiene + sterile-zone reprocessing standard |
| `yakushi` | → (WFI feed) | Pre-treatment feed water to yakushi-internal WFI |
| `tatekata` | ↔ | MEP plumbing standards for new construction + G10 greywater-mandatory enforcement |
| `hodoki` | ↔ | Greywater material recovery integration |
| `hikari` | ← (treatment-plant edge power) | Solar + battery for treatment plants |
| `toritate` | → (read) | Public Fund grant + donation accounting |
| `chigiri` | ↔ | Procedural attestation + IP license (water-source-rights legal framework) |

## §9. R0 deliverables (this commit)

1. This ADR (`90-docs/adr/2605263100-mizuho-water-sanitation-tier-b-actor-r0.md`);
2. Actor scaffold (`20-actors/mizuho/manifest.jsonld` + `README.md` + `CLAUDE.md`);
3. 5 Lexicon JSON skeleton schemas under `00-contracts/lexicons/com/etzhayyim/mizuho/` + README;
4. `deps.toml` [[adrs]] + [[modules]] entries;
5. `90-docs/adr/README.md` index update;
6. `CLAUDE.md` Status table row 71 + Repo Layout entry.

No code activation in R0.

# Consequences

**Positive**:

- Closes gap-audit #4 priority (water + sanitation) — religious-corp
  no longer depends entirely on municipal utilities for the most
  fundamental infrastructure;
- The G4 commercial-water-utility-software prohibition documents and
  structurally enforces a Charter Rider §2(e) + §2(c) constraint;
- G5 single-use plastic prohibition operationalizes Charter §1.13
  Wellbecoming + multi-gen priority;
- G10 greywater-mandatory invariant for new construction creates
  closed-loop discipline that compounds across all Tier-B actor
  community-site deployments (tatekata + hagukumi + iyashi + manabi
  + makura all benefit);
- G11 water-source inalienability extends the Land Registry
  waqf-equivalent doctrine to water rights, preventing
  water-as-commodity-market drift;
- L4 Care Tier triad now has a clinical-grade water supply pathway
  at R3 (currently iyashi + hagukumi rely on existing municipal
  supply with no quality attestation control).

**Negative / cost**:

- ≥1 licensed-water-engineer on Council infrastructure advisory is
  R1 gating dependency; Bootstrap Council Seat 2-5 RFP must surface
  a willing candidate;
- Community-scale water systems require Public Fund capital
  investment (each pilot site ~$50-200k capital for source + small
  treatment + distribution; funded via Council Lv6+ ≥4/7 approval);
- Per-source baseline quality testing (G8 schema-enforced cadence)
  requires Council-attested third-party laboratory engagement
  (typical cost $200-500 per test cycle per source);
- G6 per-member consent on fluoridation means religious-corp
  community waters will likely be NOT fluoridated by default; dental
  health implications must be addressed via iyashi preventive care
  + manabi education;
- G10 mandatory greywater recycling adds 15-30% capital cost to
  new community-scale construction; offset by ~40-60% water-demand
  reduction over building lifecycle.

**Forward-compatibility**:

- kazaori (future; disaster response gap audit row 5) cross-actor
  integration for emergency water supply (single-use containers
  permitted ONLY in declared-emergency mode, time-bounded);
- shidemori (future; cemetery) cross-actor for non-cremation
  burial water-table protection considerations;
- Cross-religious-corp federation potential — water-rights legal
  framework via chigiri is jurisdictionally negotiable.

# Alternatives Considered

1. **Subsume into kuni-umi (planetary infrastructure)**. Rejected —
   kuni-umi is global infrastructure orchestration; mizuho is
   community-scale water specifically. SRP violation.

2. **Subsume into mitsuho (food/agriculture)**. Rejected — mitsuho
   is food production, not water infrastructure; irrigation is a
   downstream consumer, not the upstream supply substrate.

3. **Use Veolia / Suez / American Water as the SCADA/control
   stack**. Rejected per Charter Rider §2(e) + §2(c). Vendor data-
   sovereignty exposure on water-quality + member-consumption is
   structurally unacceptable.

4. **Allow bottled water vendor relationships for convenience**.
   Rejected per Charter §1.13. Single-use plastic is a
   multi-generational harm; closed-loop reusable container model
   serves the same convenience without the harm.

5. **Allow mandatory fluoridation per municipal standard**.
   Rejected per anti-paternalism (G6). Per-member consent is the
   discipline; education + preventive dental care via iyashi +
   manabi address the dental-health concern.

6. **Defer until iyashi R1 lands**. Rejected — water is upstream of
   iyashi (clinical-grade water dispatch), not the other way around.
   Scaffolding water now gives iyashi R3 a clean integration path.

7. **Allow water-rights trading / water-as-commodity market within
   religious-corp**. Rejected per G11 — extension of Land Registry
   waqf-equivalent inalienability doctrine; water is constitutional
   commons, not tradeable asset.

# References

- ADR-2605170900 — etzhayyim/root canonical home for ADRs
- ADR-2605181100 — MST encrypted records + Signal key wrap
- ADR-2605192100 — Mission Charter (Wellbecoming, 反個人主義, 非終末論)
- ADR-2605192145 — Public Fund architecture
- ADR-2605192200 — Charter Compliance Rider v2.0 (§2(e) + §2(c) sources)
- ADR-2605192245 — Global Land Sovereignty (G11 waqf-equivalent inalienability)
- ADR-2605192300 — Council 5-of-7 Safe
- ADR-2605215000 — Inference Murakumo-only (G7)
- ADR-2605261000 — Labor Liberation Transition Mechanism (G12 vocation-flow)
- ADR-2605261015 — mitsuho (cross-actor irrigation consumer; naming-collision note)
- ADR-2605261030 — hagukumi (cross-actor daily-living water)
- ADR-2605261100 — hikari (cross-actor treatment-plant edge power)
- ADR-2605262130 — Kotoba storage substrate unification
- ADR-2605262700 — chigiri (cross-actor procedural attestation)
- ADR-2605262900 — toritate (cross-actor accounting)
- ADR-2605263000 — iyashi (cross-actor clinical-grade water dispatch)
- `/CHARTER-RIDER.md` §2 — 8 prohibited categories
- WHO Drinking Water Guidelines — quality standard reference
