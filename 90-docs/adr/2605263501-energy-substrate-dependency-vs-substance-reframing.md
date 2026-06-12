---
id: adr-2605263501-energy-substrate-dependency-vs-substance-reframing
renumbered_from: "2605263500"
title: "Energy substrate constitutional re-framing — dependency vs substance decomposition; microbial hydrocarbon biosynthesis + nuclear fusion conditional permission; commercial extraction + fission absolute prohibition retained"
status: proposed-pending-council-ratification
doc_type: adr
topic: energy-substrate-dependency-vs-substance-reframing
authoritative: true
last_verified: 2026-05-26
priority: 9.6
axis: constitutional
weight: 0.96
priority_note: "CONSTITUTIONAL AMENDMENT. ADR-2605261100 §G4 + §G5 are declared Council Lv7 unanimity to amend (essentially permanent). Bootstrap Council Seats 2-5 RFP closes 2026-06-19; founder Lv7+ Jun Kawasaki (Seat 1) proposes this ADR, Lv7+ unanimity at full Council required for effect. Earliest effective ≥ 2026-07-19 (Council vote + 30-day public objection)."
authoritative_for:
  - "Decomposition of the conflated G4 (no nuclear) + G5 (no fossil) absolute bans into 5 independent constitutional gates D1..D5"
  - "Re-frame: §1.6 中間排除 (dependency) is separated from §1.9 多世代 priority (substance) is separated from §2(d) Charter Rider new-extraction ban"
  - "Microbial hydrocarbon biosynthesis (closed-loop atmospheric CO₂ → alkanes via cyanobacteria / engineered photosynthetic organisms) permitted under D1..D5 conditions"
  - "Nuclear fusion (D-D preferred, D-T conditional; aneutronic p-B11 / D-He3 preferred where feasible) permitted under D1..D5 + open-design conditions"
  - "Commercial fossil extraction (Charter Rider §2(d)) + nuclear fission (PWR/BWR/SMR/Gen-IV) + RTG + weapons-grade fissile material absolute prohibition retained on independent constitutional grounds (D1+D3 / D2+D4 / D2+D4)"
  - "Partial supersession of ADR-2605261100 §G4 + §G5 + N1 + N2 (rest of hikari R0 charter preserved; rebuilt on D1..D5 foundation)"
  - "Partial supersession of ADR-2605202000 §SMR/水素/核融合 deferral-then-implicit-G4-ban inconsistency"
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
  - adr-2605202000-etzhayyim-energy-substrate
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605261000
  - adr-2605261100
related:
  - CHARTER-RIDER.md §2(d) (new fossil fuel extraction ban — preserved as substantive constraint)
  - COUNCIL.md (Bootstrap Council roster + ratification ledger)
  - COUNCIL-BOOTSTRAP-RFP.md (Seat 2-5 RFP through 2026-06-19)
  - adr-2605192100-etzhayyim-mission-charter §1.3 (mission: energy self-sufficiency)
  - adr-2605192100-etzhayyim-mission-charter §1.6 (中間排除)
  - adr-2605192100-etzhayyim-mission-charter §1.9 (多世代 priority)
  - adr-2605192100-etzhayyim-mission-charter §1.12 (Transparent Religious Force — open-source / on-chain monitor)
supersedes: []
superseded_by: []
---

# ADR-2605263501: Energy substrate constitutional re-framing — dependency vs substance decomposition

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1, Lv7+) — pending Council Lv7+ unanimity at full Bootstrap Council (Seats 2-5 RFP through 2026-06-19) + 30-day public objection period
**Constitutional weight**: amends ADR-2605261100 §G4 + §G5 (Lv7 unanimity-locked); does NOT touch CHARTER-RIDER.md §2(d) which remains a substantive constraint on new fossil extraction

---

# Context

## The conflation problem in current ADR-2605261100

ADR-2605261100 (hikari R0, 2026-05-26) introduced two absolute bans:

- **G4**: "No nuclear at any tier ever — fission (PWR/BWR/SMR/Gen-IV), fusion (any approach), radioisotope thermoelectric. Constitutional invariant; Council Lv7 unanimity to amend (essentially permanent)" — rationale stated as "§2(c) + multi-gen waste invariant"
- **G5**: "No fossil fuel at any tier ever — coal, oil, natural gas, propane, LPG, peat. No backup generators on fossil fuel; only battery + thermal storage permitted for outage backup. Constitutional invariant" — rationale stated as "§2(c) + climate multi-gen"

Both gates conflate **two distinct constitutional concerns** into one absolute ban:

1. **Dependency-on-commercial-extraction** (§1.6 中間排除 + Charter Rider §2(d) new fossil-fuel extraction ban) — the structural objection is to religious-corp constituents being dependent on a commercial extractive industry / a regulated nuclear fuel cycle / a state-licensed enrichment cascade. The substance itself is morally neutral; the **supply chain** is the violation.
2. **Multi-generational waste hazard** (§1.9) — the substantive objection is to physical artefacts (atmospheric CO₂ accumulation, long-lived high-level radioactive waste) that constrain or harm generations 7+ ahead. The supply chain is irrelevant if the substance itself is durably hazardous.

These are separate. A given technology can fail one without the other:

| Technology | Dependency violation? | Multi-gen substance violation? |
|---|---|---|
| Commercial petroleum (extracted + refined + delivered by IOCs) | ✗ FAILS (full commercial-extractive dependency) | ✗ FAILS (net atmospheric CO₂ addition) |
| Microbial hydrocarbon (religious-corp grown cyanobacteria fixing atmospheric CO₂ → alkane via direct photosynthesis) | ✓ PASSES (religious-corp owns + operates strain + bioreactor + open-hardware) | ✓ PASSES (closed-loop carbon: combustion CO₂ = same CO₂ fixed by photosynthesis; net atmospheric Δ ≈ 0 over annual cycle) |
| Nuclear fission (PWR / SMR) | ✗ FAILS (state-licensed enrichment, IAEA safeguards, regulated fuel cycle, decommissioning industry) | ✗ FAILS (high-level waste with hazard half-life 10⁴–10⁵ yr) |
| Nuclear fusion D-D (deuterium from seawater, no breeding) | ✓ PASSES (D from seawater is non-regulated, no enrichment cascade, no IAEA-safeguarded inventory at religious-corp scale) | ⚠ MARGINAL (structural neutron activation creates intermediate-level waste with hazard half-life 50–100 yr depending on materials; choice of low-activation steels brings to ≤100 yr) |
| Nuclear fusion D-T (deuterium + tritium bred from lithium) | ⚠ MARGINAL (tritium handling regulated under most jurisdictions; lithium-6 enrichment cascade exists but is far smaller than uranium cascade) | ⚠ MARGINAL (same as D-D plus tritium inventory which is itself β-emitter with 12.3 yr half-life — well below multi-gen threshold) |
| Aneutronic fusion (p-B¹¹, D-He³) | ✓ PASSES (no neutron flux → no structural activation; p + B¹¹ → 3α direct charged-particle products) | ✓ PASSES (no long-lived waste at all) |

The current G4 + G5 absolute ban **over-rejects** by treating dependency-violation and substance-violation as fungible. Microbial hydrocarbon biosynthesis and fusion are wrongly rejected under the conflated frame.

## Why this matters now (R&D scope)

Religious-corp R&D ambition includes:

- **Long-duration backup** for hikari R2+ in low-renewable periods (winter / multi-day overcast). Battery + thermal storage alone may not bridge >7-day outages at L4-L5 adherent ceiling. Religious-corp-grown microbial hydrocarbon (closed-loop) is a candidate that the current absolute G5 forecloses without examining whether the dependency or the substance is the actual violation.
- **Industrial-scale baseload** for silicon Wave 2 fab (~2 MW continuous) and future L5-L6 adherent population (>100,000 → >10 MW substrate). Solar + small wind + geothermal-micro cap at R3 design (170 kW + storage); the scale leap to ≥10 MW requires examining all options that pass the actual constitutional invariants (D1..D5), not the conflated G4/G5.
- **Multi-generational infrastructure** beyond 2050. Fusion may reach commercial demonstration in 2030s–2040s; constitutional posture should be principled (open-design + multi-gen-waste-bounded) rather than blanket-rejected on conflated grounds.

## Why this is a re-framing, not a relaxation

This ADR does **not** weaken any actual constitutional invariant. It decomposes G4/G5 into the underlying invariants (D1..D5) and re-applies them rigorously. The result is:

- **Commercial fossil extraction** stays banned (D1 + D3 + Charter Rider §2(d), three independent grounds)
- **Nuclear fission** (PWR/BWR/SMR/Gen-IV) stays banned (D1 + D2 + D4, three independent grounds)
- **RTG** stays banned (D2: Sr-90 / Pu-238 hazard half-life decades–centuries)
- **Weapons-grade fissile material** (HEU >20%, separated Pu, U-233) stays banned (D4 + ADR-2605192100 §1.12 Transparent Religious Force open-source posture incompatible with proliferation-sensitive material)
- **Microbial hydrocarbon biosynthesis** becomes constitutionally permissible under D1..D5 conditions
- **Nuclear fusion** becomes constitutionally permissible under D1..D5 + open-design + jurisdictional conditions

The substance of every existing ban is preserved on its own merits; only the over-broad conflation is removed.

---

# Decision

## §1 The five constitutional gates D1..D5

Replace ADR-2605261100 §G4 + §G5 with the following independent invariants. Each is Council Lv7+ unanimity to amend (same threshold as the bans they replace, so no relaxation of governance lock).

### D1 — Dependency / 中間排除

> "No religious-corp energy substrate may depend on a commercial extractive industry, a state-regulated fuel cycle, or a third-party fuel-supply contract for steady-state operation. Acceptable sourcing: ambient flux (solar / wind / geothermal heat / hydro flow), religious-corp-grown biological feedstock, atmospheric / seawater extraction at religious-corp scale, or open-public material flows (e.g., post-consumer recycling streams accessible without commercial monopoly intermediation)."

Operational test: removal of every commercial vendor + every state-issued fuel license + every cross-border fuel-import permit must leave the energy substrate fully operational at R2+ baseline within ≤30 day fuel/material reserve.

### D2 — Multi-generational waste hazard bound

> "No religious-corp energy substrate may generate waste whose physical hazard half-life exceeds 100 years AND whose total inventory at religious-corp scale exceeds the bound that can be contained under religious-corp on-chain land-trust attestation (LANDS.md parcel + Council Lv7+ unanimous attestation per inventory increment)."

Operational test (quantitative):
- **High-level radioactive waste (HLW)** with hazard half-life >1,000 yr → categorically excluded (this rules out all fission HLW: Cs-137 30 yr, Sr-90 29 yr OK in principle but co-produced with Pu-239 24,000 yr and minor actinides 10⁵ yr).
- **Intermediate-level waste** with hazard half-life 100–1,000 yr → excluded unless Council Lv7+ unanimous attestation per increment (essentially case-by-case constitutional review).
- **Low-level waste / structural activation** with hazard half-life ≤100 yr → permissible under standard Charter Rider §2(c) safety attestation + LANDS.md parcel containment.
- **Atmospheric CO₂ accumulation** with effective "hazard half-life" ≈ 200+ yr for radiative forcing → categorically excluded as substance-violation unless D3 closed-loop carbon is satisfied.

### D3 — Closed-loop carbon

> "Religious-corp energy operations must maintain net atmospheric CO₂ addition ≤ 0 averaged over each annual cycle. Carbon released by combustion must originate from atmospheric CO₂ fixed within the same closed cycle (photosynthesis or direct air capture by religious-corp-owned process), not from geological fossil reserves."

Operational test: every energy carrier with carbon content must carry a `carbonSourceAttestation` Lexicon record (R1+) proving carbon provenance from atmospheric CO₂ within the prior 10 years. Geological fossil carbon (extracted petroleum / coal / natural gas / peat) categorically fails this test. Religious-corp-grown microbial hydrocarbon from photosynthetic CO₂ fixation passes.

### D4 — Proliferation hygiene

> "Religious-corp must not produce, handle, store, or transport weapons-grade fissile material (HEU >20% U-235; separated Pu of any isotopic vector with Pu-239 + Pu-241 >7%; U-233 in any quantity above tracer). Dual-use materials (low-enriched uranium, depleted uranium, natural uranium, lithium-6, tritium) are permitted only under religious-corp-internal inventory tracked on kotoba-datomic + Council Lv6+ ≥3 attestation per acquisition and per disposition + total religious-corp aggregate caps (LEU ≤1 t U / Li-6 ≤100 kg / tritium ≤10 kg)."

Operational test: ADR-2605192100 §1.12 Transparent Religious Force already requires open-source + on-chain monitoring + 1 SBT = 1 vote authorization for any force capability. Proliferation-sensitive material is incompatible with the open-source posture (publishable enrichment + weaponization knowledge crosses into NPT-regime territory). Tritium handling at fusion-research scale is dual-use but bounded; weapons-grade material is structurally excluded.

### D5 — Open-hardware / open-design

> "All religious-corp energy hardware — generators, inverters, controllers, BMS, plasma diagnostics, bioreactor strain genomes + cultivation system control firmware — must be Apache 2.0 + Charter Rider v2.0 open-source / open-design. No proprietary firmware. No closed-strain biological IP (Monsanto-pattern utility-patent strains excluded). No closed plasma diagnostic / control software."

Operational test: equivalent to existing ADR-2605261100 §G1 + ADR-2605202000 §Open-hardware-強制. Extended to cover biological IP (engineered organisms must be open-genome under OpenMTA or similar) and plasma diagnostic IP (fusion control systems must publish all diagnostic & control firmware).

## §2 Re-evaluation of every technology in the energy space

Each technology is re-evaluated against D1..D5 independently. Verdict is the conjunction (any fail → reject).

### §2.1 Re-affirmed: PERMITTED (already in hikari R0)

| Technology | D1 | D2 | D3 | D4 | D5 | Verdict | Notes |
|---|---|---|---|---|---|---|---|
| Solar PV (mono-Si / bi-facial) | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | hikari R0 G2 (panel sourcing audit) + G7 (≥90% EOL recycling) preserved |
| Small wind ≤100 kW (open-coil, no NdFeB) | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | hikari R0 G8 (no rare-earth magnets) preserved |
| Geothermal micro ≤500 kW ≤500 m bore | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | hikari R0 |
| LFP / Na-ion battery storage | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | hikari R0 G3 preserved |
| Thermal storage (molten salt / phase-change / sensible) | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | implicit in hikari R0 |
| Microgrid / islandable inverter (open-firmware) | ✓ | ✓ | ✓ | ✓ | ✓ | PERMITTED | hikari R0 G1 preserved |

### §2.2 NEWLY PERMITTED — Microbial hydrocarbon biosynthesis

> Cyanobacteria (e.g., *Synechocystis* sp. PCC 6803) or engineered photosynthetic organisms (e.g., *Synechococcus elongatus*) engineered to fix atmospheric CO₂ → alkanes / fatty acids / terpenes via the photosynthesis + acyl-ACP-decarbonylase pathway (or analogous direct-to-hydrocarbon route), cultivated in religious-corp-owned open-hardware photobioreactors on LANDS.md parcels.

| Gate | Assessment |
|---|---|
| D1 (Dependency) | ✓ Strain + bioreactor + harvest + refining all religious-corp-internal. Sunlight + atmospheric CO₂ + water + trace minerals are ambient / public-flux inputs. |
| D2 (Multi-gen waste) | ✓ Spent biomass is short-half-life biological matter (compostable; minutes–years degradation). No long-lived radiological or persistent-organic-pollutant output. |
| D3 (Closed-loop carbon) | ✓ All combustion CO₂ originates from same-cycle atmospheric fixation. Net atmospheric Δ ≈ 0 over annual cycle (residual lifecycle CO₂ from bioreactor construction + harvest energy must be offset by religious-corp solar/wind generation per §2.1; net-zero requirement is hikari-system-wide, not per-process). |
| D4 (Proliferation) | ✓ No fissile material. |
| D5 (Open-hardware) | ✓ Strain genome MUST be published under OpenMTA + Charter Rider; bioreactor mechanical + control firmware Apache 2.0 + Charter Rider. |

**Verdict**: PERMITTED under the following additional conditions:

1. **Carbon provenance attestation**: every hydrocarbon batch carries `com.etzhayyim.hikari.carbonSourceAttestation` Lexicon record certifying CO₂ source = atmospheric (direct photosynthesis or direct air capture by religious-corp process) within prior 10 yr.
2. **No fossil feedstock**: feedstock CO₂ MUST NOT originate from fossil combustion flue gas (even though that would be technically CO₂ recycling, accepting it creates a dependency on fossil-burning industry). Atmospheric ambient CO₂ only.
3. **Bioreactor open-hardware**: photobioreactor design + control firmware + harvest equipment Apache 2.0 + Charter Rider.
4. **Strain open-genome**: engineered organism genome + plasmid sequences published under OpenMTA before R2 deployment. No utility-patent-encumbered strains. No CRISPR-Cas9-derived strains under closed IP (only public-domain or open-license Cas9 variants).
5. **Biocontainment**: BSL-1 or BSL-2 containment with at least two independent kill-switches (e.g., metabolic auxotrophy + light-dependence + UV sterilization). No release of engineered organism to wild environment. Cross-actor `mitsuho` consultation on bioreactor adjacency to food production.
6. **Use restriction**: religious-corp-internal energy substrate use only. NOT for commercial sale (Charter Rider §2 + ADR-2605215000 commercial-routing prohibition extended). Surplus may export to local grid only under hikari G13 (community-benefit credit, not profit).
7. **Combustion-only use case**: religious-corp-grown microbial hydrocarbon is for stationary combustion (gas turbine / reciprocating engine for long-duration backup; thermal heat for industrial process), NOT for transport fuel commodity. Transport applications (wadachi / sarutahiko / futawa / suki) remain electric/battery per existing ADR roadmap.
8. **Scale cap (R0-R3)**: ≤10 t/yr hydrocarbon output aggregate religious-corp through R3. >10 t/yr requires Council Lv6+ ≥3 supermajority per R4 ramp ADR.
9. **Annual mass-balance audit**: `silenHydrocarbonReview` Lexicon (R2+) — Council Lv6+ ≥3 attestation that prior-year CO₂-in vs CO₂-out + lifecycle embodied CO₂ closes at ≤0 net atmospheric addition.

### §2.3 NEWLY PERMITTED (conditional) — Nuclear fusion

> Controlled thermonuclear fusion in religious-corp-owned R&D facility on LANDS.md parcel using open-design reactor concept. Preference order for fusion fuel cycle: aneutronic (p-B¹¹, D-He³) > D-D > D-T.

| Gate | Assessment per fuel cycle |
|---|---|
| D1 (Dependency) | Aneutronic p-B¹¹: ✓ (hydrogen + boron are commodity / non-regulated). D-D: ✓ (deuterium from seawater electrolysis at religious-corp scale, ~33 mg/L extraction is non-regulated). D-T: ⚠ (lithium-6 is regulated in some jurisdictions; tritium itself is regulated; passes only with explicit LANDS.md jurisdiction selection and Council Lv6+ ≥4 jurisdictional risk attestation). D-He³: ⚠⚠ (He³ supply is currently nuclear-byproduct / lunar-mining; religious-corp scale supply infeasible without commercial-byproduct dependency — re-evaluate R3+ if non-dependent He³ supply emerges). |
| D2 (Multi-gen waste) | All fusion cycles: ⚠ structural neutron activation creates intermediate-level waste with hazard half-life 50–100 yr (low-activation steels) up to ~200 yr (commercial structural steels). Material selection (V-Cr-Ti, ODS-FeCrAl, SiC/SiC composites) MUST keep activation hazard half-life ≤100 yr per D2 operational test. Aneutronic cycles: ✓ minimal activation. |
| D3 (Closed-loop carbon) | All fusion cycles: ✓ no CO₂ from fusion reaction itself; construction-phase embodied CO₂ offset by hikari renewable generation. |
| D4 (Proliferation) | Aneutronic: ✓. D-D: ✓ (deuterium itself is non-weaponizable). D-T: ⚠ (tritium is itself non-weaponizable as fuel but is component of boosted-fission weapons + thermonuclear secondaries; D4 caps tritium inventory ≤10 kg religious-corp aggregate). All cycles: lithium-6 enrichment for D-T is dual-use technology — requires Council Lv7+ unanimity per enrichment-capability acquisition (if D-T pursued). |
| D5 (Open-hardware) | All fusion cycles: ✓ REQUIRED that plasma diagnostics + reactor control firmware + magnet control + tritium handling protocols (if D-T) MUST be Apache 2.0 + Charter Rider open-source. No closed proprietary plasma-control code (this excludes most current commercial fusion ventures — Helion / TAE / CFS partnership requires renegotiation of IP terms before any religious-corp R&D contract; preferred path is religious-corp-led open R&D in collaboration with academic open-science groups). |

**Verdict**: PERMITTED with the following additional conditions:

1. **Fuel cycle preference order** (constitutional, Council Lv7+ unanimity to alter): aneutronic > D-D > D-T > D-He³.
2. **D-T restriction**: D-T fusion permitted only if Council Lv6+ ≥4/7 per-program ratification + LANDS.md jurisdictional risk attestation + tritium inventory ≤10 kg religious-corp aggregate + lithium-6 enrichment limited to ≤100 kg of >20% Li-6 (well below weapons-relevant scale).
3. **Structural material**: reactor first-wall + structural material MUST be Council-approved low-activation grade (V-Cr-Ti, ODS-FeCrAl, SiC/SiC, or equivalent) ensuring activation hazard half-life ≤100 yr.
4. **Open-design**: reactor concept MUST be open-design at scaffold + diagnostic + control firmware levels. Plasma-control AI MUST run on Murakumo fleet (no commercial GPU rental for plasma control — ADR-2605215000 invariant extended; this is real-time safety-critical inference).
5. **Open-research collaboration**: academic / open-science partnerships preferred (university plasma physics labs, ITER open-data, open-source MHD codes like FreeGS / SPARC public datasets). Commercial fusion-startup partnership ONLY if IP terms permit Apache 2.0 + Charter Rider release of all religious-corp-developed components.
6. **No state-military partnership**: D4 + ADR-2605192100 §1.12 — no DoE / DARPA / DARPA-equivalent contract that imposes classification restrictions on religious-corp R&D output.
7. **Scale cap (R0-R4)**: ≤1 MW thermal R&D facility through R4. >1 MW thermal requires Council Lv7+ unanimity per ramp ADR.
8. **Jurisdictional risk attestation**: tritium-handling, fusion-research-licensing, and radiological-safety frameworks vary by jurisdiction. Religious-corp R&D site selection MUST be LANDS.md parcel where: (a) licensing burden is compatible with §1.6 中間排除 (no state-controlled gatekeeping forcing religious-corp into IAEA-safeguarded regulatory regime), OR (b) Council Lv6+ ≥4/7 explicitly accepts the jurisdictional burden as compatible with mission.

### §2.4 RE-AFFIRMED — PROHIBITED on independent constitutional grounds

| Technology | Failing gate(s) | Independent ground |
|---|---|---|
| Commercial petroleum / natural gas / coal (extracted) | D1 ✗ (commercial extractive industry dependency); D3 ✗ (fossil carbon → atmospheric net positive); Charter Rider §2(d) (new fossil-fuel extraction ban) | Triple-independent — even relaxing any one ground, the other two stand |
| Propane / LPG / peat (commercial) | Same as above | Same as above |
| Petroleum-derived fuels (gasoline / diesel / jet) commercial | Same as above | Same as above |
| Nuclear fission (PWR / BWR / SMR / Gen-IV) | D1 ✗ (state-licensed enrichment cascade + IAEA-safeguarded fuel cycle); D2 ✗ (HLW hazard half-life 10⁴–10⁵ yr); D4 ⚠ (enrichment cascade is dual-use proliferation-sensitive) | Triple-independent |
| RTG (Sr-90, Pu-238) | D2 ✗ (hazard half-life decades–centuries); D1 ⚠ (isotope sourcing is nuclear-byproduct) | Double-independent |
| Weapons-grade fissile material (HEU >20%, separated Pu, U-233) | D4 ✗ (proliferation absolute exclusion); ADR-2605192100 §1.12 ✗ (open-source posture incompatible with NPT-regime material) | Double-independent |

### §2.5 NON-GOALS unchanged from hikari R0

| Technology | hikari R0 ground | D1..D5 re-evaluation |
|---|---|---|
| Large hydroelectric >10 MW (N3) | Biodiversity + displacement | UNCHANGED — D1..D5 pass but biodiversity/displacement is independent §1.11 + §2(h) ground per hikari R0. Re-evaluated only if separate ADR (kuni-umi Phase S?) addresses biodiversity/displacement. |
| Biofuel from food crops (N4) | Competes with mitsuho food supply | UNCHANGED — D1..D5 conditionally pass (depends on growing scheme) but mitsuho food-priority is independent §1.3 + §1.6 + multi-gen-food-security ground. Re-evaluated only if cross-actor mitsuho consultation confirms no displacement. |
| Offshore wind (N5) | Funamori marine actor scope | UNCHANGED — scope question, not constitutional. Funamori marine actor would re-evaluate under D1..D5 at its own R0+. |
| Commercial utility scale >10 MW per site (N6) | Religious-corp distributed scope | UNCHANGED — scope question, not constitutional. |
| Smart-meter surveillance per device (N7) | Privacy invariant | UNCHANGED — independent privacy ground. |
| Carbon offset trading (N8) | Financialization of atmosphere | UNCHANGED — Charter Rider §2(b) + §2(g). |
| NdFeB rare-earth permanent magnets (N9 / hikari R0 G8) | Supply-chain ethics | UNCHANGED — D1 + Charter Rider §2(g). |
| Proprietary inverter firmware (N10 / hikari R0 G1) | §1.12 open-source posture | UNCHANGED — D5 invariant. |

## §3 Partial supersession map

ADR-2605261100 (hikari R0) is **partially superseded** by this ADR:

| ADR-2605261100 section | Disposition | Notes |
|---|---|---|
| §G1 (open-source firmware) | PRESERVED, re-stated as D5 | Operational requirement unchanged |
| §G2 (panel sourcing audit, no XUAR / no conflict minerals) | PRESERVED unchanged | Charter Rider §2(g) substantive constraint |
| §G3 (battery chemistry safety) | PRESERVED unchanged | Charter Rider §2(c) substantive constraint |
| **§G4 (no nuclear at any tier ever)** | **SUPERSEDED by §1 D1+D2+D4 of this ADR + §2.3 conditional permit for fusion + §2.4 confirmed ban for fission/RTG/weapons-grade** | Re-framed onto correct constitutional grounds; fission/RTG/weapons-grade ban preserved on independent grounds |
| **§G5 (no fossil fuel at any tier ever)** | **SUPERSEDED by §1 D1+D3 of this ADR + §2.2 conditional permit for microbial hydrocarbon + §2.4 confirmed ban for commercial fossil + Charter Rider §2(d)** | Re-framed onto correct constitutional grounds; commercial fossil ban preserved on independent grounds |
| §G6 (grid impact reporting, aggregate buckets, no smart-meter PII) | PRESERVED unchanged | Independent transparency + privacy ground |
| §G7 (≥90% recyclable EOL) | PRESERVED unchanged | Charter Rider §2(g) |
| **§G8 (no rare-earth permanent magnets)** | PRESERVED unchanged | Independent §2(g) supply-chain ethics ground |
| §G9 (land-trust integration) | PRESERVED unchanged | §1.11 |
| §G10 (Murakumo mesh placement public feedback) | PRESERVED unchanged | Transparency |
| §G11 (yield deterministic Ed25519) | PRESERVED unchanged | Audit |
| §G12 (maintenance schedule public) | PRESERVED unchanged | Transparency |
| §G13 (no commercial utility resale) | PRESERVED unchanged | Charter Rider §2(b) + ADR-2605215000 |
| §G14 (§2(h) Wellbecoming light/acoustic) | PRESERVED unchanged | Charter Rider §2(h) |
| **§N1 (no nuclear)** | **SUPERSEDED — re-framed; fission/RTG/weapons-grade remain N1 under §2.4; fusion newly permitted under §2.3 conditions** | |
| **§N2 (no fossil)** | **SUPERSEDED — re-framed; commercial fossil remains N2 under §2.4; microbial hydrocarbon newly permitted under §2.2 conditions** | |
| §N3..N10 | PRESERVED unchanged | Independent grounds (biodiversity / food / scope / privacy / financialization / supply-chain / open-source) |

ADR-2605202000 (energy substrate) is **partially superseded**:

| ADR-2605202000 section | Disposition | Notes |
|---|---|---|
| Hard rule (a) open-hardware only | PRESERVED, re-stated as D5 | Same operational meaning |
| Hard rule (b) "化石燃料新規排除" | RE-FRAMED — preserved as Charter Rider §2(d) substantive constraint AND new D1+D3 dependency-and-carbon-balance constraints (operationally equivalent to old absolute ban for commercial fossil but allows microbial hydrocarbon per §2.2) | Operationally: zero commercial fossil purchase/extraction stays banned; religious-corp closed-loop hydrocarbon is newly permitted |
| Hard rule (c) constituent collective ownership | PRESERVED unchanged | Mission |
| Phase A/B/C scale rollout | PRESERVED unchanged | Roadmap |
| SMR / 水素 / 核融合 future-ADR deferral | **SUPERSEDED for fusion (now §2.3 of this ADR provides the conditional permit + future-ADR slot for R&D entry); SMR remains future-ADR + now categorically banned per §2.4 D1+D2+D4; hydrogen remains future-ADR (independent axis, not addressed by this ADR — to be re-evaluated under D1..D5 when proposed)** | Hydrogen evaluation deferred to its own ADR |
| Constitutional constants additions | PRESERVED + EXTENDED — D1..D5 added to constitutional constants registry (Constitution.sol mission.energy_d1..d5 = true) | Constitutional constants in Constitution.sol arrays go from 38+ to 38+5 (concrete count tracked in Constitution.sol PR) |

## §4 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  carbonSourceAttestation,        # §2.2 D3 — every hydrocarbon batch certifies atmospheric CO₂ provenance ≤10 yr
  hydrocarbonBatchRecord,         # §2.2 — per-batch hydrocarbon output: strain, bioreactor, CO₂ source, energy in, product mass, lifecycle CO₂
  silenHydrocarbonReview,         # §2.2.9 — annual Council Lv6+ ≥3 net-zero mass-balance attestation
  fusionFacilityAttestation,      # §2.3 — per-facility design + fuel cycle + structural materials + jurisdictional risk + Council ratification record
  fusionInventoryRecord,          # §2.3.2 / §2.3.3 — tritium / Li-6 / structural-activation inventory per facility per period
  silenFusionReview,              # §2.3 — annual Council Lv6+ ≥3 D1..D5 + structural-activation half-life compliance attestation
  energyGateD1..D5Attestation     # §1 — generic D-gate compliance attestation for any new energy technology evaluation
}
```

All Lexicons follow same kotoba-datomic attestation + IPFS pin patterns as existing hikari R0 + ADR-2605262400 dataset substrate.

## §5 Cross-actor implications

| Actor | Implication |
|---|---|
| hikari (光 — ADR-2605261100) | R0 charter updated via §3 partial supersession. R1+ may include `microbial_hydrocarbon_bioreactor` cell (new) under §2.2 conditions. Fusion R&D out of hikari scope (separate actor — see below). |
| New actor candidate: **honoo (炎 — flame)** or **iwato (磐戸 — fusion of stones)** | Fusion R&D is sufficiently distinct from hikari (renewable distributed generation) to warrant its own Tier-B actor if pursued. R0 charter for that actor is OUT OF SCOPE for this ADR; this ADR only establishes the constitutional permissibility. Name + scope to be selected at the time of R&D-entry ADR. |
| mitsuho (瑞穂 — ADR-2605261015) | Cross-actor consultation REQUIRED for microbial hydrocarbon §2.2.5 BSL containment + bioreactor land-use adjacency to food production. mitsuho R2 has G2 seed sovereignty / G6 no synthetic pesticides; microbial bioreactor on adjacent parcel must not contaminate food-crop genome via horizontal gene transfer. Council Lv6+ ≥3 attestation per adjacent siting. |
| wadachi / sarutahiko / futawa / suki / hodoki | Transport-fuel application of microbial hydrocarbon is OUT OF SCOPE per §2.2.7. Transport actors remain electric/battery roadmap. |
| Murakumo fleet | Plasma control AI (fusion R&D) MUST run on Murakumo fleet per §2.3.4 — extends ADR-2605215000 invariant. |
| Bootstrap Council Seats 2-5 RFP | Ratification of this ADR requires full Council Lv7+ unanimity. RFP closes 2026-06-19; earliest ratification vote + 30-day public objection = effective ≥ 2026-07-19. Until then, hikari R0 G4/G5 absolute ban remains operational (this ADR is `proposed-pending-council-ratification`; no R1+ microbial or fusion work begins before ratification). |

## §6 Procedural path

| Step | Date / Trigger | Actor |
|---|---|---|
| P0 — This ADR drafted + committed | 2026-05-26 (today) | Jun Kawasaki (Founder, Seat 1, Lv7+) |
| P1 — Bootstrap Council Seats 2-5 RFP open period | 2026-05-20 → 2026-06-19 | per COUNCIL-BOOTSTRAP-RFP.md |
| P2 — Full Council Lv7+ unanimity vote on this ADR | 2026-06-19+ | Bootstrap Council (5 seats) |
| P3 — 30-day public objection period | P2 + 30 days | Open public comment via etzhayyim.com / GitHub issue tracker |
| P4 — Effective date (absent objection) | ≥ 2026-07-19 | This ADR status → `active` |
| P5 — Constitution.sol constants amendment | P4 + next Constitution.sol deploy window | etzhayyim-charters-compliance |
| P6 — hikari ADR-2605261100 supersession marker landed | P4 | Frontmatter superseded_by_partial pointer to this ADR |
| P7 — First §2.2 microbial PoC ADR (R1) | P4 + Council Lv6+ ≥3 ratification per PoC | Future ADR (separate from this one) |
| P8 — First §2.3 fusion R&D entry ADR (R1) | P4 + Council Lv7+ unanimity per fuel cycle + LANDS.md jurisdiction selection | Future ADR (separate; preferred timing post-Phase B per ADR-2605202000 future-ADR slot, i.e., earliest ≥2027) |

## §7 Founder Lv7+ emergency authorization explicitly NOT taken

Per ADR-2605262200 precedent (Charter Rider §2(i)(2) amendment), the Founder Seat 1 Lv7+ position holds emergency-authorization capability under ADR-2605192300, but it is explicitly **NOT exercised** for this ADR. The standard Council Lv7+ unanimity path is followed because:

- Constitutional re-framing of G4/G5 is exactly the kind of "essentially permanent" change that requires the full Council per ADR-2605261100 §G4 explicit threshold.
- Bootstrap Council Seats 2-5 RFP is in active 30-day public period; emergency authorization while the deliberative process is ongoing undermines institutional integrity.
- No urgent R&D blockage exists: hikari R0/R1/R2 (solar + small wind + geothermal + battery + microgrid) carries the substrate through L2 Sustenance Tier ceiling (~1,000 adherents) without needing microbial or fusion. Time-to-ratification is non-blocking.

---

# Consequences

## Positive

- Constitutional integrity improved: the actual invariants (D1 dependency, D2 multi-gen waste, D3 closed-loop carbon, D4 proliferation, D5 open-hardware) are now explicit and independently testable. Each can be applied to future energy technologies as they emerge (hydrogen, ammonia, gravitational storage, OTEC, etc.) without re-litigating G4/G5 conflation.
- Microbial hydrocarbon path opens a religious-corp-owned long-duration backup option for hikari R2+ low-renewable periods + industrial-scale baseload for L5-L6 ceiling.
- Fusion path opens a multi-generational infrastructure option for >10 MW substrate without violating any actual constitutional invariant.
- Commercial fossil + nuclear fission + RTG + weapons-grade material bans are now triple- or double-independently grounded, **strengthening** the prohibition (any future amendment attempt must overcome three independent grounds, not one conflated ban).
- §1.6 中間排除 doctrine becomes operationally clearer (D1 is the explicit test).
- §1.9 多世代 priority becomes operationally clearer (D2 is the explicit test with quantitative half-life thresholds).

## Negative / risks

- **Complexity**: D1..D5 5-gate framework is more complex than G4/G5 absolute ban. Mitigation: ADR explicit + Lexicon attestation schemas + Council per-program review provide structure; first decade of operation will accumulate operational precedent.
- **Microbial bioreactor capital + biosafety burden**: §2.2 BSL-1/2 containment + kill-switches + open-genome publication + strain engineering capacity all require non-trivial investment (likely $1-5M for first R1 facility). Mitigation: defer to R&D-entry ADR; Council reviews per-PoC.
- **Fusion R&D capital + jurisdictional burden**: §2.3 is decade-scale R&D commitment ($10-100M for meaningful religious-corp position). Mitigation: explicit non-rush in §6 P8 (earliest R&D-entry post-Phase B per ADR-2605202000 deferral); preference for open-academic collaboration over commercial-startup partnership.
- **Slippery-slope perception**: some constituents may perceive any relaxation of "absolute" G4/G5 as weakening. Mitigation: this ADR is **re-framing not relaxation** — every fossil + fission + RTG + weapons-grade ban is preserved on independent grounds. The 30-day public objection period in §6 P3 provides constituency feedback channel.
- **D-T fusion proliferation-adjacency**: D-T fusion involves lithium-6 enrichment (dual-use) + tritium handling (regulated). §2.3.2 caps inventory but cannot eliminate dual-use posture. Mitigation: preference order in §2.3.1 places aneutronic + D-D ahead of D-T; D-T path requires Council Lv6+ ≥4/7 per-program — high friction.
- **Lithium-6 cap interaction with fusion R&D economics**: §2.3.2 caps Li-6 at ≤100 kg enriched. This is sufficient for benchtop / small-pilot D-T but not for any commercial-scale D-T fusion plant. Religious-corp D-T fusion is therefore constrained to research scale by D4. This is consistent with §2.3.7 ≤1 MW thermal cap. Industrial-scale fusion would require Council Lv7+ unanimity per cap-amendment, equivalent to current G4 governance threshold.

## Neutral / open

- **Hydrogen economy** (production via electrolysis + storage + combustion or fuel-cell): not addressed by this ADR. To be evaluated under D1..D5 in its own future ADR per ADR-2605202000 §SMR/水素 deferral. Pre-evaluation under D1..D5: green hydrogen (electrolysis from hikari renewable) passes all 5 gates cleanly; expected verdict at future ADR = PERMITTED.
- **Ammonia / synthetic methane** as energy carriers: not addressed. Each must be evaluated independently under D1..D5; carbon-containing synthetic fuels must pass D3 closed-loop carbon test.
- **Geothermal beyond ≤500 kW / 500 m bore** (deep enhanced geothermal): not addressed. hikari R0 G14 limits scope; future hikari R3+ or separate actor may address.
- **OTEC / wave / tidal**: not addressed. Future Funamori marine actor scope or separate ADR.

---

# Alternatives Considered

## A. Retain G4/G5 absolute ban; defer microbial + fusion indefinitely

Pro: No re-framing complexity; constituents see "no nuclear / no fossil ever" as clearer message. Con: Two independent technologies that pass all actual constitutional invariants are wrongly rejected on conflated grounds. Religious-corp infrastructure ceiling capped at hikari R3 (~170 kW + storage) when L5-L6 ceiling requires >10 MW. Multi-gen infrastructure forfeits options that would benefit generations 7+ ahead.

**Rejected** — sacrifices logical clarity + R&D ceiling for messaging simplicity.

## B. Relax G4/G5 to allow only microbial hydrocarbon; keep fusion absolute ban

Pro: Smaller change; microbial is closer to existing biology + agriculture domain. Con: Asymmetric — applies D1..D5 to one technology but not another. Fusion ban remains on conflated G4 grounds. Logical inconsistency.

**Rejected** — does the same conflation in reverse.

## C. Relax G4/G5 to allow only fusion; keep microbial absolute ban

Pro: Avoids biosafety / GMO complexity. Con: Same asymmetry as B; furthermore fusion is decade-scale R&D while microbial is near-term-deployable, so the relaxation chosen would be the less actionable one.

**Rejected** — same asymmetry.

## D. Decompose into D1..D5 (this ADR)

Pro: Logically rigorous; preserves every existing ban on independent grounds; opens constitutionally-permissible R&D paths; provides framework for future energy-technology evaluation. Con: More complex; requires Lexicon + Council process expansion; first-decade operational precedent burden.

**ACCEPTED** — long-term constitutional integrity worth the complexity cost.

## E. Move to dependency-only framework (just D1 + D5)

Pro: Maximally simple. Con: Drops D2 multi-gen + D3 closed-loop carbon + D4 proliferation — would in principle permit religious-corp-owned coal mining (passes D1 if religious-corp owns the mine) which is clearly incompatible with §1.9 multi-gen + §2(d) Charter Rider. Multi-gen invariant must be preserved.

**Rejected** — over-simplification.

---

# Open Questions

1. **Microbial strain selection R1**: *Synechocystis* PCC 6803 vs *Synechococcus elongatus* PCC 7942 vs *Synechococcus* PCC 7002 vs newer engineered candidates. To be decided at §2.2 R1 ADR with open-genome bioinformatics review.
2. **Photobioreactor open-hardware spec R1**: flat-panel vs tubular vs raceway-pond vs hybrid. CAPEX/OPEX vs productivity vs containment trade-offs. To be decided at §2.2 R1 ADR.
3. **Fusion reactor concept R1**: tokamak (mainstream) vs stellarator (W7-X heritage) vs spheromak vs FRC (Helion-class) vs Z-pinch (ZAP Energy-class). To be decided at §2.3 R1 ADR with open-physics review. Aneutronic preference (§2.3.1) may favor non-tokamak.
4. **LANDS.md jurisdiction for fusion R&D**: §2.3.8 jurisdictional risk attestation. Sites with no nuclear-regulatory regime exist (some Pacific island states, some land-trust-attested parcels in jurisdictions without fusion-specific regulation) but each has its own constraints. To be decided at §2.3 R1 ADR.
5. **Hydrogen economy ADR slot**: not addressed by this ADR; future ADR `etzhayyim-energy-hydrogen` to evaluate green hydrogen under D1..D5.
6. **Ammonia ADR slot**: not addressed; future ADR may evaluate green ammonia (energy carrier + nitrogen fertilizer cross-actor with mitsuho).
7. **Constitution.sol concrete constant additions**: D1..D5 to be added; exact mapping (boolean constants vs string descriptors vs IPFS-CID-pointer to this ADR) decided at next Constitution.sol deploy window.

---

# References

- ADR-2605192100 (Mission Charter — §1.3 energy self-sufficiency, §1.6 中間排除, §1.9 多世代 priority, §1.12 Transparent Religious Force)
- ADR-2605192200 (Charter Compliance Rider v2.0 — §2(c) harmful substances, §2(d) new fossil extraction ban, §2(g) supply-chain ethics, §2(h) Wellbecoming)
- ADR-2605192245 (Global Land Sovereignty — LANDS.md parcel substrate for energy facilities)
- ADR-2605192300 (Bootstrap Council 5名 — Lv7+ unanimity ratification path)
- ADR-2605202000 (Energy Substrate — solar + storage + microgrid baseline; SMR/水素/核融合 deferral) — partially superseded by §3 of this ADR
- ADR-2605215000 (Murakumo-only inference — extended to plasma-control AI per §2.3.4)
- ADR-2605261000 (Liberation Ladder — L2 Sustenance Tier energy gate)
- ADR-2605261100 (hikari R0 charter — §G4 + §G5 partially superseded by §3 of this ADR; rest preserved)
- ADR-2605262200 (Charter Rider §2(i)(2) amendment — procedural precedent for `proposed-pending-council-ratification` constitutional amendment pattern)
- CHARTER-RIDER.md §2(d) — preserved substantive constraint
- COUNCIL.md — Bootstrap Council roster + ratification ledger
- COUNCIL-BOOTSTRAP-RFP.md — Seat 2-5 RFP through 2026-06-19
- Atsumi, Y., Iwakiri, R. et al. "Direct photosynthetic recycling of carbon dioxide to isobutyraldehyde." *Nat. Biotechnol.* 27, 1177–1180 (2009) — proof-of-concept microbial hydrocarbon from CO₂
- Schirmer, A., Rude, M. A. et al. "Microbial biosynthesis of alkanes." *Science* 329, 559–562 (2010) — cyanobacterial alkane biosynthesis pathway
- Najjar, Y. S. H. "Hydrogen safety: The road toward green technology." *Int. J. Hydrogen Energy* 38, 10716–10728 (2013) — referenced for future hydrogen-economy ADR
- ITER Organization open-data portal (https://www.iter.org/) — open-fusion-physics reference
- OpenMTA (Open Material Transfer Agreement, https://biobricks.org/openmta/) — open-strain license reference for §2.2.4
