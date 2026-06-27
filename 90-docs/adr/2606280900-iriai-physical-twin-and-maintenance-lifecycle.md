---
id: adr-2606280900-iriai-physical-twin-and-maintenance-lifecycle
title: "ADR-2606280900: iriai 入会 — physical-simulation twin + operations/maintenance lifecycle (+ 道路)"
status: accepted
doc_type: adr
topic: iriai-twin-maintenance
authoritative: true
last_verified: 2026-06-28
priority: 5.5
axis: architecture
weight: 0.55
priority_note: "Closes the upkeep gap: iriai's :maintain verdict was a placeholder. Adds a real-physics degradation twin + an ops/maintenance lifecycle (safety-floor first) + the road lifeline. SIM/compute-only R0."
authoritative_for:
  - iriai-twin-maintenance
  - lifeline-asset-degradation-simulation
  - lifeline-operations-maintenance-lifecycle
depends_on:
  - "2606272200  # iriai lifeline-commons (infra + 資金 + 管理)"
  - "2605262130  # kotoba storage substrate (no RisingWave)"
  - "2605312345  # kotoba Datom log = first-class canonical state"
related:
  - "2606091800  # infra-robotics 3-layer operational substrate (twin → WASM → device-loop)"
  - "2606101430  # infra-robotics R1 device-in-the-loop (real droop/anti-islanding WASM)"
  - "2605201400  # kuni-umi (build/commission/decommission robotics fleet)"
  - "2606042100  # tazuna (teleop fleet — inspection/repair)"
  - "2605261215  # hodoki (ELV/asset disassembly + materials recovery)"
  - "2605252400  # kanayama (circular metallurgy — recover renewed-asset materials)"
  - "2605250715  # tatekata (construction — road builder)"
  - "2605312700  # kizashi (non-invasive sensing — real condition telemetry, R1)"
  - "2606051800  # mitooshi (probabilistic forecasting — predictive maintenance)"
  - "2606032130  # Displacement Dividend (crews the upkeep, cash≡0)"
supersedes: []
superseded_by: []
---

# ADR-2606280900: iriai 入会 — physical-simulation twin + operations/maintenance lifecycle (+ 道路)

**Status**: accepted
**Date**: 2026-06-28
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

ADR-2606272200 landed **iriai 入会** — the lifeline-commons SoS umbrella (infra + 資金 + 管理).
But its steady-state `:maintain` verdict was a **placeholder**: the system could decide to *build*
a lifeline and *fund* it, but had no model of the deployed asset's **physical condition over time**
and no **operations/maintenance lifecycle** — which is, in reality, the bulk of running utilities.
The question this ADR answers is the user's: *how does this actually keep electricity/water/gas/
telecom **and roads** running — physical simulation, operations, and maintenance — over decades?*

The repo already proved the implementation pattern on the electric microgrid (ADR-2606091800/
2606101430): a clj/cljc **:representative twin** whose WASM control artifact runs **device-in-the-
loop** under Wasmtime, with a certified IEC 61508/61511 PLC as the field SSoT. This ADR brings that
**digital-twin discipline up into iriai** for the *condition* timescale (years of degradation), so
maintenance is condition-based + predictive instead of a fixed calendar guess.

# Decision

Add two layers to `20-actors/iriai/` (clj-native, kotoba-Datom, gated, tested), plus the **road**
(道路) lifeline. **SIMULATION + DESIGN ONLY** — iriai never actuates a tool or dispatches a crew.

## 1. `methods/twin.cljc` — physical-simulation digital twin (物理シミュレーション)

Each DEPLOYED asset carries a physical state that degrades. The twin advances it with a **real
engineering model per lifeline** and reports condition (0..1) + remaining-useful-life (RUL, years)
+ operating margin + a structural safety flag:

| lifeline | model | safety floor |
|---|---|---|
| **electric** (transformer) | IEEE C57.91 thermal aging: load → hot-spot θh → `FAA = exp(15000/383 − 15000/(θh+273))` → loss-of-life | θh > 140 °C OR loss-of-life ≥ 1 |
| **water** (main) | Hazen-Williams roughness decline `C(t)=C0−k·t` → hydraulic capacity | C ≤ 60 (unusable) |
| **gas** (main) | wall-thickness corrosion `w(t)=w0−cr·t` → leak-probability | leak-prob > 0.7 OR w ≤ wmin |
| **telecom** (fibre) | attenuation creep `α(t)=α0+β·t` vs link budget | budget exhausted (margin ≤ 0) |
| **road** (pavement+bridge) | PCI deterioration `PCI(t)=PCI0−a·t^b` + bridge load-rating | PCI < 25 OR load-rating < 1.0 |

`project` runs the twin **ahead** of reality (advance age by Δt) so maintenance is **preventive** —
see the failure before it happens. This is the active-twin discipline, the same shape as
mitooshi's leak-free forecasting. SIM ONLY (G5): `:iriai.twin/energize` / `:iriai/actuate` are
unrepresentable.

## 2. `methods/maintain.cljc` — operations/maintenance lifecycle (運用メンテナンス)

Reads the twin (condition/RUL/safety) + the asset's maintenance schedule (inspect/service
intervals, mid-life refurbish, last-done) and routes the asset through the lifecycle —
**SAFETY FLOOR FIRST** (an unsafe asset is never deferred for cost):

```
verdict ∈ {:decommission :renew :corrective-repair :refurbish :preventive-service :inspect :ok}
  1. safety :unsafe AND RUL ≤ 0   → :decommission      (end-of-life + unsafe)
  2. safety :unsafe                → :corrective-repair (immediate, cost-independent)  ← SAFETY FLOOR
  3. RUL ≤ 0                        → :decommission
  4. condition < 0.25 OR RUL < 3yr  → :renew             (replace; old → hodoki/kanayama recycle)
  5. condition < 0.50              → :corrective-repair
  6. mid-life, not refurbished     → :refurbish
  7. service interval due          → :preventive-service
  8. inspect interval due          → :inspect
  9. else                          → :ok
```

Each verdict routes to an **executor** (kuni-umi build/commission · tazuna teleop inspection ·
giemon repair arm · noroshi fibre splice · hodoki disassembly + kanayama material recovery) and
imputes **OpEx** onto the **§1.16 non-profit rails** — **cash ≡ 0 to the consumer** (upkeep is
never billed, G2; the Displacement-Dividend cohort, ADR-2606032130, crews it). DESIGN ONLY:
actuation-class `:intent`; live upkeep is the executor's cell under **Council Lv7+ + operator-DID
+ member-sig** (G5).

## 3. Road (道路) — the fifth lifeline

`:road` joins as a first-class commons lifeline (essentiality 0.65; producer = tatekata
construction + the kuni-umi robotics fleet). Roads carry a pavement-PCI + bridge-load-rating twin
and the full maintenance lifecycle (an under-rated bridge in good surface condition is a
SAFETY-FLOOR corrective, not a deferred one). Road *coverage*-cells (who has road access) are a
trivial R2 add; the **maintenance** of roads — the user's emphasis — is fully modelled here.

## Gates

- **G9 maintenance-safety-floor** (NEW): an unsafe asset's verdict MUST be `:corrective-repair` or
  `:decommission` — never deferred (test-enforced; mirrors mizuho chlorination clamp + kamado purge
  gate + kafun refuse-precedes-routing).
- **G5** extends to twin/maintenance: `:iriai.twin/energize` / `:iriai.maint/dispatch-crew` /
  `:iriai.maint/actuate` unrepresentable; all `:intent`.
- **G2** extends: `:iriai.maint/consumer-bill` / `:iriai.maint/tariff` unrepresentable (upkeep is
  §1.16 in-kind, never billed).

# Consequences

- **R0 landed**: `methods/twin.cljc` + `methods/maintain.cljc` + 11 deployed-asset seed (5 lifelines
  incl. road, spanning every maintenance verdict + 2 safety-floor cases) + ontology/manifest/lexicon
  extension. **iriai suite now 54 tests / 394 assertions green** (was 40/311); the heartbeat folds
  infra+fund+manage+**twin+maintain** into one content-addressed tx (715 datoms on the seed beat,
  chain verifies).
- The physical-simulation answer to "how does it actually run + get maintained": the twin gives the
  condition timescale, the lifecycle gate gives the upkeep decisions, the robotics/teleop actors
  execute under Council — and the certified PLC + device-in-the-loop (ADR-2606101430) remains the
  field SSoT for the millisecond control timescale.
- **R1+ (G7-gated)**: real asset-condition telemetry (kizashi non-invasive sensing → condition);
  producer-twin device-in-the-loop coupling (the infra-robotics WASM device-loop); predictive
  maintenance via mitooshi; road coverage-cells; fleet registration + live kotoba-engine bridge.
- Live actuation + actual crew dispatch stays the producer/executor actors' under Council Lv7+,
  never iriai.

# Alternatives Considered

- **A fixed maintenance calendar (no physics).** Rejected: calendar maintenance over-services healthy
  assets and misses degraded ones; the real-physics twin lets upkeep be condition-based + predictive,
  and makes the safety-floor a property of the model, not a schedule.
- **A separate maintenance actor.** Rejected: condition + upkeep are the same SoS commons as coverage
  + funding + governance (one region's transformer is the asset behind its electric coverage); folding
  twin+maintain into iriai keeps one heartbeat and one ledger.
- **Modelling individual crews/workers.** Rejected on charter grounds (Rider §2(c) / Wellbecoming
  §1.13): no per-person attribute exists; executors are actors, OpEx is aggregate.

# References

- `20-actors/iriai/methods/{twin,maintain}.cljc` + `methods/test_{twin,maintain}.cljc`
- `20-actors/iriai/kotoba/seed.edn` (deployed-asset rows) + `ontology.iriai.edn` (twin/maint attrs + negative space)
- `00-contracts/lexicons/com/etzhayyim/iriai/{assetCondition,maintenanceVerdict}.json`
- infra-robotics twin→WASM→device-loop: ADR-2606091800 / 2606101430
- executors: kuni-umi (2605201400) · tazuna (2606042100) · hodoki (2605261215) · kanayama (2605252400) · tatekata (2605250715)
