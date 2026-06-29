---
id: adr-2605265900-sng-methanation-sabatier-d-gate-evaluation-r0
title: "Synthetic natural gas (SNG / Sabatier methanation) from green H₂ + DAC CO₂ — D1..D5 evaluation R0 (sub-ADR of 2605263500; complementary to biomethane 2605263800)"
status: proposed-pending-council-ratification
doc_type: adr
topic: sng-methanation-sabatier-d-gate-evaluation
authoritative: true
last_verified: 2026-05-26
priority: 6.2
axis: constitutional
weight: 0.62
priority_note: "Sub-ADR of ADR-2605263500. Methanation (Sabatier: CO₂ + 4H₂ → CH₄ + 2H₂O at 250-400°C over Ni/γ-Al₂O₃) produces SNG chemically identical to biomethane (2605263800) but via electrochemical-thermochemical route. Verdict: SNG via Sabatier from religious-corp green H₂ (2605263600) + DAC CO₂ (2605264600) CONDITIONALLY PERMITTED with COMBINED biomethane+SNG aggregate cap ≤200 Nm³/day R3 (no scale creep beyond existing CH₄ ceiling). SNG from commercial CO₂ (industrial flue / NH₃ plant byproduct) ABSOLUTELY PROHIBITED."
authoritative_for:
  - "SNG methanation D1..D5 evaluation"
  - "Sabatier vs biomethane pathway selection criteria (Council Lv6+ quarterly review)"
  - "Combined CH₄-pathway aggregate cap discipline (biomethane + SNG unified to ≤200 Nm³/day)"
  - "Ni catalyst open-formula requirement"
  - "Cross-actor heat byproduct (~10 MJ/kg-CH₄ exothermic) routing"
depends_on:
  - adr-2605263500-energy-substrate-dependency-vs-substance-reframing
  - adr-2605263600-hydrogen-economy-d-gate-evaluation-r0
  - adr-2605263800-biomethane-d-gate-evaluation-r0
  - adr-2605264600-direct-air-capture-d-gate-evaluation-r0
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
  - adr-2605265000-district-heating-cooling-d-gate-evaluation-r0
  - adr-2605265800-high-temperature-heat-pump-d-gate-evaluation-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605264700-methanol-dme-synfuel-d-gate-evaluation-r0
supersedes: []
superseded_by: []
---

# ADR-2605265900: SNG Sabatier methanation — D1..D5 evaluation R0

**Status**: proposed-pending-council-ratification
**Date**: 2026-05-26
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council Lv7+ unanimity cascade

# Context

ADR-2605263800 covers biological biomethane (anaerobic digestion). Sabatier methanation (CO₂ + 4H₂ → CH₄ + 2H₂O; ΔH = -165 kJ/mol exothermic; Ni/Al₂O₃ catalyst 250-400°C) is a thermochemical-electrochemical route to identical CH₄ molecule. Pathways are functionally redundant downstream but have different upstream characteristics:

| Pathway | Feedstock | Cycle time | Footprint | Religious-corp fit |
|---|---|---|---|---|
| Biomethane AD (2605263800) | Religious-corp waste streams | 20-40 days | Moderate | ✓ already permitted |
| **Sabatier SNG** | Green H₂ + DAC CO₂ | Minutes | Compact | ✓ §1 conditional, complementary |

Sabatier is preferred when: biomethane feedstock exhausted / surplus H₂+DAC capacity / dispatchable production needed.

# Decision

## §1 Sabatier SNG — CONDITIONALLY PERMITTED

**COMBINED biomethane + SNG aggregate cap ≤200 Nm³/day religious-corp through R3** (NOT separate caps — prevents unconstrained CH₄ scale creep).

| Gate | Assessment |
|---|---|
| **D1** | ✓ Both feedstocks religious-corp-internal; reactor + catalyst + BOP religious-corp open-hardware |
| **D2** | ✓ No long-lived waste; Ni catalyst recyclable; short-cycle gases |
| **D3** | ✓ Closed-loop carbon (DAC CO₂ → CH₄ → combustion CO₂ → DAC re-capture) |
| **D4** | ✓ No fissile |
| **D5** | ✓ Reactor + Ni catalyst formula + control firmware Apache 2.0 + Rider |

**Conditions**:

1. **Feedstock chain-of-custody MANDATORY**: per kg SNG ≈ 0.5 kg H₂ + 2.75 kg CO₂; `sngBatchAttestation` Lexicon cites source CIDs; mass-balance ≥95%
2. **Pathway-selection priority (Council Lv6+ ≥3 quarterly)**:
   - Biomethane primary (when waste feedstock available per 2605263800)
   - Sabatier when (a) waste exhausted OR (b) dispatchable/compact production needed OR (c) surplus H₂+DAC capacity ≥50%
   - **Never both pathways simultaneously at same facility** without Council per-facility justification
3. **Catalyst open-formula MANDATORY**: Ni/γ-Al₂O₃ industrial mainstream (public-domain since 1902 Sabatier+Senderens); Ru/Co/Mn promoters acceptable if open-formula. **Johnson Matthey HiFUEL R110 + other commercial proprietary catalysts PROHIBITED** (D5)
4. **Reactor**: fixed-bed tubular + heat-management cooling water mandatory (highly exothermic; ΔT control critical); slurry-bubble or fluidized-bed acceptable variants
5. **Operating conditions**: 250-400°C / 1-20 bar through R3; >350°C requires Council Lv6+ ≥3 per facility (carbon deposition + Ni-carbonyl formation risks)
6. **Use restriction**: religious-corp-internal energy substrate only (NO commercial sale; pipeline injection PROHIBITED through R3 per biomethane 2605263800 §1.7(b)); use cases = on-site CHP combustion / CNG vehicle fuel (cross-actor wadachi/sarutahiko R3+ separate ADR) / turquoise H₂ pyrolysis feedstock (2605263600 §3) / industrial process heat via HTHP (2605265800)
7. **Combustion-product water routing**: per kg SNG ≈ 2.25 kg H₂O; condensed → mizuho process water OR electrolyzer feedstock (closes water loop)
8. **Leak rate ≤1%** (CH₄ GWP100 28-34); quarterly OGI leak survey
9. **Storage**: ≤500 Nm³ per LANDS parcel; aggregate ≤2,000 Nm³ (parity with biomethane)
10. Annual `silenSngReview` Council Lv6+ ≥3

## §2 SNG from commercial CO₂ (industrial flue gas / NH₃ plant byproduct) — PROHIBITED

| Failing |
|---|
| D1 — commercial CO₂ off-take = vendor dependency |
| D3 — fossil-derived CO₂ recycling does NOT close atmospheric loop (carbon was geological) |
| Charter §2(d) — indirect new-fossil-extraction enablement |

ABSOLUTELY PROHIBITED on triple-independent grounds.

## §3 SNG from biomethane upgrading tail-gas CO₂ — PERMITTED variant

Biomethane upgrading (PSA/water-scrubbing/amine) strips CO₂ tail-gas at 90-99% purity. This CO₂ is already-atmospheric (closed-loop). Recycling biomethane tail-gas CO₂ → SNG tightens biomethane loop (recovers CO₂ that would otherwise vent).

Permitted as §1 variant with additional condition: upstream biomethane facility (2605263800 §1) must be religious-corp-owned. NOT permitted from commercial biomethane facility tail-gas (D1).

## §4 Exothermic heat-byproduct cross-actor pairing

Sabatier ΔH = -165 kJ/mol = ~10.3 MJ/kg-CH₄ heat released during synthesis. Valuable byproduct for cross-actor heat-network:

```
Sabatier reactor (250-400°C)
    ↓ heat-recovery cooling loop
ADR-2605265000 §1 4GDH/5GDH district network 80-150°C inlet
    ↓
    ├─→ industrial process steam ≤150°C
    ├─→ DAC §1 sorbent regen heat (CLOSES OUTER LOOP: DAC heat → Sabatier reactor heat → DAC regen)
    ├─→ biomethane digester thermophilic 55°C
    └─→ mitsuho greenhouse heating
```

At 200 Nm³/day (~143 kg/day SNG), heat byproduct ~1.4 GJ/day = ~17 kW continuous — meaningful low-grade heat budget.

## §5 Roadmap

| Phase | Scope | Cap |
|---|---|---|
| **R0** | This ADR; `20-actors/hikari/cells/sng_sabatier/` path-reserved | None |
| **R1** | post-Council + 2605263600 H₂ R1 + 2605264600 DAC R1 + ≥1 catalysis-chemist on Council | Bench ≤5 Nm³/day fixed-bed pilot | 5 Nm³/day |
| **R2** | post-R1 + 30-day public + 1-yr safe operation + 5%-mass-balance | ≤50 Nm³/day + heat-recovery to district network OR biomethane digester | 50 Nm³/day |
| **R3** | post-R2 + Council Lv6+ ≥3 + combined biomethane+SNG ≤200 Nm³/day cap | Full §1 cap; pathway selection per quarterly review | combined ≤200 Nm³/day |

## §6 New Lexicons (R1+)

```
com.etzhayyim.hikari.{
  sngBatchAttestation,                # per-batch + H2 CID + DAC-CO2 CID + Ni catalyst lot + mass-balance
  sngStorageInventory,                # per-LANDS-parcel Nm³ + pressure + storage type
  sngPathwaySelectionRecord,          # Council Lv6+ ≥3 quarterly biomethane-vs-Sabatier allocation
  silenSngReview                      # annual Council Lv6+ ≥3
}
```

# Consequences

**Positive**:
- Dispatchable methane when biomethane waste-feedstock exhausted OR surplus H₂+DAC available
- Exothermic heat byproduct (~17 kW continuous at R3) closes outer DAC↔Sabatier loop + feeds district network
- Water byproduct closes water loop in green-H₂ pathway (electrolyzer feedstock OR mizuho process water)
- Ni catalyst non-proprietary mainstream; no vendor IP lock
- Combined cap with biomethane preserves CH₄ scale discipline

**Negative**:
- Highly exothermic — heat-management non-trivial
- Ni catalyst carbon-deposition + carbonyl formation requires >350°C avoidance + periodic regeneration
- Combined cap means SNG cannot expand beyond biomethane R3 — only displace
- Round-trip efficiency electricity → H₂ → CH₄ → combustion → electricity is poor (~25-30%)

# References

- ADR-2605263500 (parent D1..D5)
- ADR-2605263600 (H₂ feedstock)
- ADR-2605263800 (biomethane sibling; combined cap)
- ADR-2605264600 (DAC CO₂ feedstock; outer-loop pairing)
- ADR-2605264700 (methanol sibling synfuel)
- ADR-2605265000 (heat-network cross-actor)
- ADR-2605265800 (HTHP low-grade heat consumer)
- Sabatier P. + Senderens J.B. *Comptes Rendus* 134 (1902) — original public-domain reference
- IEA P2G (Power-to-Gas) — open-publication SNG tech state

---

## Amendment 2026-06-29 — promotion to standalone actor (ADR-2606290000)

The SNG pathway is **promoted from a path-reserved cell under `hikari`**
(`20-actors/hikari/cells/sng_sabatier/`, never scaffolded) **to a standalone
Tier-B actor `com-etzhayyim-sng`**, per ADR-2606290000, following the `kamado`
precedent (D-gate sub-ADR → standalone actor). Consequently:

- The `20-actors/hikari/cells/sng_sabatier/` path reservation (§5 R0 row) is
  **withdrawn**; hikari's 5 energy cells are unchanged.
- The four SNG lexicons (§6) are **re-namespaced** `com.etzhayyim.hikari.*`
  → `com.etzhayyim.sng.*` (`sngBatchAttestation`, `sngStorageInventory`,
  `sngPathwaySelectionRecord`, `silenSngReview`). The `hikari` namespace was
  never materialized, so there are no existing references to migrate.
- The D1–D5 verdict, the combined biomethane+SNG ≤200 Nm³/day cap, the
  open-Ni/γ-Al₂O₃ catalyst mandate, the green-H₂+DAC-CO₂-only feedstock
  chain, the commercial-CO₂ ABSOLUTE PROHIBITION, and the Council Lv6+≥3
  pathway-selection review are unchanged and are now enforced as the
  CarbonGovernor hard invariants of the standalone actor.

The status of this ADR remains `proposed-pending-council-ratification`; the
standalone-actor ADR-2606290000 is the implementation scaffold pending that
ratification.
