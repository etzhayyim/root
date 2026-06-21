---
id: adr-2606212030-kafun-ie-flow-energy-visualization
title: "ADR-2606212030: kafun 花粉 embeds ie-flow + energy-flow system-of-systems visualization"
status: accepted
doc_type: adr
topic: kafun-ie-flow-energy-visualization
authoritative: true
last_verified: 2026-06-21
priority: 5.5
axis: architecture
weight: 0.55
authoritative_for:
  - kafun 花粉 ie-flow embedding (20-actors/kafun/methods/ie_flow.cljc)
  - kafun energy-flow visualization (20-actors/kafun/viz/energy-flow.html)
depends_on:
  - adr-2606211712-kafun-pollen-remediation-actor
  - adr-2606211200-ie-flow-datomic-agent-lifecycle
related:
  - adr-2606211200-energy-order-protocol
  - adr-2606201200-ibuki-coscientist-entropy-react-loop
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
---

# ADR-2606212030: kafun 花粉 embeds ie-flow + energy-flow system-of-systems visualization

**Status**: accepted (2026-06-21)
**Scope**: `20-actors/kafun/methods/ie_flow.cljc`, `20-actors/kafun/viz/energy-flow.html`
**Deciders**: Jun Kawasaki

## Context

The founder asked, of the just-landed kafun actor (ADR-2606211712): **as an ie /
system-of-systems, how does this actor change the energy flow — visualize it.**

The repo already has the framework this question is asking for: **`etzhayyim.ie-flow`**
(ADR-2606211200) — the order calculus (entropy / order-index / net-gain /
agent-efficiency) that every actor embeds so the roster is a system of systems, on
the kotoba Datom log; and the **Energy Order Protocol** framing (ADR-2606211200,
PoUF: use information to put verifiable order onto energy-flow). What was missing for
kafun specifically: (1) the **embedding** of that shared calculus, and (2) a
**visualization** of the energy/order transformation kafun performs.

## Decision

Add **`kafun.methods.ie-flow`** — kafun embeds the SHARED `etzhayyim.ie-flow.metrics`
(not a fork) and renders a self-contained energy-flow visualization.

### The energy-flow model (what kafun does, in ie-flow terms)

kafun's substrate is the **花粉 burden**: scattered (散在) pollen-source pressure
across many cedar/cypress stands = high-entropy disorder imposed on humans. kafun's
gate is a **RECTIFIER (整流)**: it folds that scattered burden flow onto OUTCOMES —
concentrating realised **restoration** value onto the highest-burden, viable,
consented stands (`:reforest-priority`) and cleanly routing the rest to NAMED sinks.

- **EVENT** (per stand): `source` = the stand (a 花粉源), `target` = the verdict
  route, `volume` = pollen-burden (the scattered input flow), `value` =
  burden·route-factor·scale (the order rectified onto an outcome), `cost` = flat
  assessment compute, `risk` = 0 (assessment-only — kafun never actuates).
- **route-factor** = how much RESTORATION each verdict moves this cycle:
  `:reforest-priority` → viability (full); `:protected-selective` → 0.25 (gradual);
  `:await-*` → 0.05 (routed-but-pending on the L1-1 苗木 / consent bottleneck);
  `:refuse` → 0 (PROTECTIVE only — disorder prevented, shown structurally, not
  restoration-energy); `:monitor` → 0.02.
- **order-index** = 1 − H(value)/H(volume) = how much scattered pollen-disorder kafun
  rectified into prioritized restoration order. **η = exported ÷ consumed** = the
  order multiplier over kafun's cheap assessment cost (the 共生 axis).

### The visualization (`viz/energy-flow.html`)

A self-contained canvas Sankey, generated FROM the model (numbers inlined, no external
fetch), with four columns = the SoS pipeline:

```
花粉源 stands (散在 disorder) → kafun 整流 (rectifier) → verdict routes (order) → 下流アクター (SoS)
```

Ribbon width ∝ burden, colored by verdict. The verdict sinks feed the downstream
actors — `:reforest-priority` → **sanae** (planting robotics) + **inochi** (biosphere
restoration); `:await-sapling-supply` → **sanae** (無花粉苗木 L1-1); `:await-consent`
→ **musubi** (consent); `:protected-selective` → **inochi**; `:refuse` → **kamado**
(carbon transition); `:monitor` → kafun (re-observe). That downstream column is the
**system of systems**: kafun's output is another actor's input.

The header shows the order calculus: throughput, order-index, net-gain, η,
order-exported, actionable-now %, and the entropy drop H(before)→H(after).

### Measured result (synthetic R0 seed)

`order-index 0.320` (H 2.307→1.569), `η 6.58×`, `net-gain +133.9`, **non-parasitic** —
kafun cheaply converts scattered pollen-disorder into prioritized restoration order and
exports ~6.6× the order it consumes. 6 ie-flow tests / 22 assertions green (28 / 84 total).

## Consequences

- **+** kafun is now in the ie-flow system-of-systems roster (`registry.edn`), sharing
  the unforkable safety property (a predatory mechanism is structurally unrepresentable).
- **+** The founder's question is answered concretely + visually + data-backed: the viz
  is generated from the same metrics the tests assert, not hand-drawn.
- **+** assessment-only is preserved: the flow kafun moves is INFORMATION-energy (a
  prioritized map); physical forestry stays landowner + operator/Council.
- **−** The viz consumes the R0 synthetic seed; real stands are the ADR-2606211712 G7
  operator flip. The live `record!`/`beat!` to the per-actor kotoba flow ledger
  (`80-data/ie-flow/kafun/flow.kotoba.edn`, gitignored) is the heartbeat/operator step.
- **Follow-ups**: wire kafun's heartbeat (autorun) to also `record!` the flow events;
  Murakumo-narrated meta-review (G6); the co-scientist beat over the flow (an aligned
  kafun intervention catalog extension).

## References

- `20-actors/kafun/methods/ie_flow.cljc` (embedding + viz generator) + `test_ie_flow.cljc`
- `20-actors/kafun/viz/energy-flow.html` (generated, self-contained)
- ADR-2606211712 (kafun actor) · ADR-2606211200 (ie-flow lifecycle + Energy Order Protocol)
