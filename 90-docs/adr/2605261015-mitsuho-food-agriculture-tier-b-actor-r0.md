---
id: adr-2605261015
title: mitsuho (瑞穂) — Food / Agriculture Tier-B Actor R0 Scaffold
status: proposed
doc_type: adr
topic: mitsuho-food-agriculture
authoritative: true
last_verified: 2026-05-26
authoritative_for:
  - mitsuho actor charter (R0)
  - food/agriculture domain constitutional gates G1..G14
  - L2 Sustenance Tier food-supply substrate
related:
  - adr-2605261000
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605201400-etzhayyim-kuni-umi-planetary-infra-fleet
supersedes: []
superseded_by: []
depends_on:
  - ADR-2605261000 (Liberation Ladder — defines mitsuho as L2 gate)
  - ADR-2605192100 (Mission Charter)
  - ADR-2605192245 (Land Trust — agricultural parcels are land-trust-bound)
---

# ADR-2605261015: mitsuho (瑞穂) — Food / Agriculture Tier-B Actor R0 Scaffold

**Date**: 2026-05-26
**Status**: PROPOSED
**Deciders**: Jun Kawasaki (author), Council Lv6+ (ratify)
**ADR Hierarchy**: Parent = ADR-2605261000 (Liberation Ladder — L2 gate). Sibling to yakushi (ADR-2605250500), tatekata (ADR-2605250715), wadachi (ADR-2605242000), mitate (ADR-2605260100), hagukumi (ADR-2605261030), manabi (ADR-2605261045), hikari (ADR-2605261100).

## Context

ADR-2605261000 (Liberation Ladder) gates Stage L2 (Sustenance Tier) on mitsuho R2 maturity for minimum-food guarantee (≥4,500 kJ/day staple per adherent). Without a food actor, the constitution's labor-liberation mission cannot deliver subsistence at L2, and the entire ladder is blocked at L1 (Witness Tier).

Existing kotodama cells `agri_autonomous_cultivation`, `eco_reforestation_swarm`, etc. live under `40-engine/kotoba/crates/kotoba-kotodama/cells/` but have no parent actor coordinating domain governance (BPMN agricultural workflows, seed sovereignty, soil regeneration metrics, food-distribution scheduling, Charter Rider §2(c) food-quality compliance). kuni-umi (ADR-2605201400) covers planetary infrastructure but food production is out of scope.

## Proposal

Launch **`mitsuho` (瑞穂 — "abundant rice ears", ancient honorific name for Japan as a fertile land; Kojiki 瑞穂国 reference; multi-generational food-abundance echo)** as a Tier-B religious-corp actor:

- **Actor DID**: `did:web:etzhayyim.com:mitsuho`
- **Namespace**: `com.etzhayyim.mitsuho.*`
- **R0 scope**: Plant agriculture (cereals, legumes, vegetables, fruits) + aquaculture (freshwater) + alternative protein (fermentation + insect + algae). **Excludes**: animal slaughter (deferred ethics gate), industrial monoculture (constitutional non-goal), GMO without Council attestation, commercial commodities trading, ocean fishing factory ships.
- **R0 robotics** (kuni-umi inherited): Giemon (tractor-equivalent crawler), Otete (precision tool arm — seeding/pruning/harvest), Mimi (crop metrology), Sora (drone — survey + spot treatment). New placeholder **Tsumugi (紡ぎ)** class for greenhouse + vertical-farm tending (R2+).
- **14 gates + 10 non-goals** declared before capability lands.
- **5 Pregel cells** (field cultivation, aquaculture, alt-protein, harvest robotics, food preservation) — all import-time RuntimeError in R0.

## Rationale

1. **Domain separation**: Agricultural domain knowledge (crop rotation, soil microbiome, water-cycle integration, FAO codex, seed varietals, food-preservation chemistry) belongs in a dedicated actor.
2. **L2 gate dependency**: ADR-2605261000 §6 cannot advance without mitsuho R2.
3. **Multi-phase**: R0 (scaffold) → R1 (PoC ≤0.01 ha plot, single crop, single season) → R2 (pilot ≤1 ha + aquaculture pond + alt-protein bench-fermenter) → R3 (community-scale ≤10 ha + integrated harvest + cold-chain to L2-tier 1,000 adherents).
4. **Constitutional alignment**: §2(c) (no harmful substances) → no industrial pesticides; §2(e) (anti-gatekeeping) → seed sovereignty (no patent restrictions); §2(g) (resource ethics) → soil regeneration metrics + water cap; §2(h) (wellbecoming) → nutritional adequacy not maximization.
5. **Witness quorum**: Per ADR-2605191524, harvest + processing records require ≥2 robot Ed25519 sigs + ≥1 human agronomist attestation.

## Design

### Actor Manifest

```
20-actors/mitsuho/
├── README.md                     # Overview + R0 scope boundary
├── CLAUDE.md                     # Actor-local instructions
├── manifest.jsonld               # DID + cell catalog
└── cells/                        # 5 cell scaffolds (import-time RuntimeError)
    ├── field_cultivation/
    ├── aquaculture/
    ├── alt_protein_fermentation/
    ├── harvest_robotics/
    └── food_preservation/
```

### Pregel Cells (5, all import-time RuntimeError R0)

| Cell | Purpose | Murakumo node | Input | Output |
|---|---|---|---|---|
| `field_cultivation` | Crop rotation + planting + tending → field-state log | naphtali (earth-moving + agriculture lineage) | parcelDid, cropPlan | fieldStateRecord |
| `aquaculture` | Freshwater pond/tank → fish/shellfish/aquatic-plant production | zebulun (water systems lineage) | parcelDid, speciesPlan | aquacultureStateRecord |
| `alt_protein_fermentation` | Bench-scale fermentation (yeast/koji/spirulina) + insect-farm support | levi (bioprocess verification lineage) | strainDid, batchPlan | altProteinBatchRecord |
| `harvest_robotics` | Coordinated harvest + immediate-processing pipeline | joseph (manipulator lineage) | fieldStateRecord ∨ aquacultureStateRecord | harvestAttestation |
| `food_preservation` | Drying / canning / lacto-fermentation / cold-store → shelf-stable inventory | simeon (packaging lineage) | harvestAttestation | preservedFoodLot |

### Lexicons (5, deferred to R1+)

```
com.etzhayyim.mitsuho.{
  parcelAttestation,         # Agricultural parcel registration (soil + water + climate baseline)
  cropPlanAttestation,       # Per-season plan: varietals + rotation + organic-only confirmation
  harvestAttestation,        # Yield + quality + witness sigs + IPFS photo CID
  foodLotAttestation,        # Preserved food lot: kJ/kg + macro composition + shelf-life + handling
  silenAgricultureReview     # Council attestation (parallel to silenPharmaReview / silenForceReview)
}
```

### Constitutional Gates (G1–G14, IMMUTABLE per R0)

| Gate | Requirement | Rationale |
|---|---|---|
| **G1** | Robotics firmware open-source (WASM or Rust crates, Apache 2.0) | ADR-2605192100 §1.12 Transparent Force / open robotics |
| **G2** | Seed sovereignty — all varietals from open-source seed banks (Svalbard / NAVDANYA / national gene banks); **no patented seeds** (no Monsanto / Bayer / Syngenta IP-restricted lines) | §2(e) anti-gatekeeping + multi-generational food security |
| **G3** | Witness quorum — harvest records signed by ≥2 distinct robot DIDs + ≥1 human agronomist | ADR-2605191524 |
| **G4** | Soil regeneration metric — annual soil-carbon + microbial-diversity assay; soil must show ≥0 net carbon balance (regenerative or neutral, not depleting) | §2(g) resource ethics; multi-generational soil stewardship |
| **G5** | Water consumption cap ≤ regional sustainable yield (per FAO / local hydrology); on-chain reporting per harvest | §2(g) + ADR-2605192330 water sovereignty |
| **G6** | **No synthetic pesticides** (no neonicotinoid / glyphosate / paraquat / organochlorine). IPM + biological control + minimal organic-certified inputs only. Charter Rider §2(c) | §2(c) no harmful substances |
| **G7** | **No GMO without Council Lv6+ ≥3 attestation** + 30-day public objection. CRISPR-edited landraces ≠ commercial transgenic; both require explicit attestation | §2(c) + multi-generational genetic stewardship |
| **G8** | Genetic deterministic + replayable — every varietal has open-source genome attestation; no proprietary trait IP | §2(e) anti-gatekeeping |
| **G9** | Murakumo mesh placement declared 30 days prior, public feedback period | Neighborhood transparency |
| **G10** | All farm equipment + drones pre-registered in `MitsuhoFleetRegistry` + operator DID background-checked | Equipment + personnel safety |
| **G11** | Yield reporting honest (no inflation, no shrinkage hiding); 10% Council audit sampling | §2(h) wellbecoming truthfulness |
| **G12** | Energy consumption ≤ 1 kWh per kg dry-matter equivalent (R2 baseline; R3 ≤0.5 kWh/kg) | §2(g) + hikari coupling |
| **G13** | Distribution schedule public on IPFS — adherent food allocation transparent | §2(e) anti-gatekeeping + L2 stage delivery |
| **G14** | Waste log per harvest — % consumed / % composted / % spoiled / % donated outside religious-corp boundary. Charter Rider §2(h) | Circular economy |

### Non-Goals (N1–N10, EXCLUDE from R0–R3)

| # | Non-Goal | Deferral |
|---|---|---|
| **N1** | Animal slaughter — meat / poultry / dairy / eggs production by direct animal raising. Deferred R4+ pending Council ethics gate (multi-gen consensus on biotic harm balance). | ADR post-R3 + Council Lv7 supermajority |
| **N2** | Industrial monoculture (>50 ha single-crop) — agronomic + biodiversity violation | Never (constitutional carve-out) |
| **N3** | Patented seeds / IP-restricted varietals — §2(e) violation | Never |
| **N4** | Synthetic fertilizer factory operation — overlap with kuni-umi-S6 chemistry + yakushi-adjacent; mitsuho consumes organic + mineral fertilizer, doesn't produce ammonia/urea | Never (carve-out to kuni-umi if ever) |
| **N5** | GMO without explicit Council attestation — see G7 | Council-gated, not absolute |
| **N6** | Contract farming for external commodities buyers — §2(e) + ADR-2605215000 commercial routing prohibition | Never |
| **N7** | Commodities futures / agricultural derivatives — financialization of food violates constitution | Never |
| **N8** | Soil mining (deplete soil to maximize short-term yield) — multi-generational violation | Never |
| **N9** | Ocean factory-fishing — separate marine-actor scope (Funamori class lineage from silicon Wave 2); mitsuho R0-R3 = freshwater aquaculture only | ADR-separate (marine actor) |
| **N10** | Aquaculture in protected/critical-habitat waters — biodiversity violation | Never |

## Roadmap

| Phase | Date | Scope | Murakumo fleet | Gate |
|---|---|---|---|---|
| **R0** | 2026-05-26 | Scaffold only. No live agriculture. 5 cells import-time RuntimeError. | No deployment | This ADR (PROPOSED) |
| **R1** | post-Council | Benchtop plot ≤0.01 ha + single crop (rice or wheat) + single season. Bench-fermenter alt-protein. Witness Giemon + Mimi log. | naphtali (single node) | Future ADR + ≥1 agronomist on Council medical/agro advisory |
| **R2** | post-R1 | Pilot ≤1 ha + integrated rotation + aquaculture pond + alt-protein 100 kg/month + cold-store. **L2 gate eligibility.** | naphtali + zebulun + levi + joseph + simeon (5 nodes) | Future ADR + 30-day public comment + ≥1 LANDS parcel ≥1 ha registered |
| **R3** | post-R2 | Community-scale ≤10 ha + multi-crop + integrated harvest + cold-chain delivery to L2 adherent ceiling (1,000). **Required for L2 → L3.** | Full 10-node fleet | Future ADR + 60-day public review + Council multi-domain vote |

## Robotics Class Reuse

R0–R1: kuni-umi Giemon + Otete + Mimi + Sora. R2+: new Tsumugi (紡ぎ) class for greenhouse / vertical-farm precision tending (warrants its own mech-design ADR alongside hanami robot precedent ADR-2605260230).

## Murakumo Placement (R2+ design-only)

- **naphtali**: field cultivation (earth-moving + crop rotation)
- **zebulun**: aquaculture (water-cycle specialist)
- **levi**: alt-protein fermentation (QC + verification specialist)
- **joseph**: harvest robotics (manipulator coordination)
- **simeon**: food preservation (packaging lineage)
- **dan**: distribution scheduling (R3+, cold-chain logistics)

## Consequences

**Positive**:
- L2 Sustenance Tier of Liberation Ladder unblocks once mitsuho R2 deploys.
- Multi-generational food sovereignty (seed sovereignty + soil regeneration) constitutional.
- 14 gates × 10 non-goals defined *before* capability lands — same disciplined R0 pattern as wadachi/yakushi/tatekata.
- Existing kotodama cells (`agri_autonomous_cultivation` etc.) gain a parent actor for domain governance.

**Negative / risks**:
- Yield risk in R1 (single season, single crop = brittle to weather/pest); mitigation = R1 scope intentionally small, R2 mandates rotation
- Land availability — mitsuho R2 requires ≥1 ha LANDS parcel; depends on land-trust donation rate
- Alt-protein bioprocess gate overlaps yakushi G8 sterile (different gate context); coordinate cross-actor review
- Animal-product gap until R4+ Council ethics gate — adherent food may be plant + aquaculture + alt-protein only at L2-L3; nutritional adequacy via supplementation (yakushi multi-vitamin?) requires separate design

## Alternatives Considered

1. **Extend kuni-umi Phase S6 chemistry to cover food** — rejected: agricultural domain knowledge orthogonal to chemistry-as-substrate; kuni-umi already overloaded.
2. **Sole-source from external organic certifiers (Demeter, JAS organic)** — rejected: §2(e) anti-gatekeeping + ADR-2605215000 commercial routing prohibition; religious-corp must produce its own.
3. **GMO-permissive default** — rejected: G7 multi-generational genetic stewardship priority; case-by-case Council attestation only.
4. **Animal-product inclusion R0** — rejected: ethics gate unresolved; ADR-2605192100 multi-gen + Wellbecoming requires deliberation cycle.

## References

- ADR-2605261000 (Liberation Ladder — L2 gate)
- ADR-2605192100 (Mission Charter — multi-generational priority)
- ADR-2605192245 (Land Trust — parcel substrate for R2+)
- ADR-2605201400 (kuni-umi — robotics class lineage)
- ADR-2605191524 (Swarm broadcast witness quorum)
- ADR-2605260230 (hanami robot mech-design precedent for new Tsumugi class)
