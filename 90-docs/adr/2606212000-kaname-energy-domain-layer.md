---
id: adr-2606212000-kaname-energy-domain-layer
title: "ADR-2606212000: kaname 要 — :energy domain layer (system-of-systems energy-flow)"
status: proposed
doc_type: adr
topic: kaname-energy-domain
authoritative: true
last_verified: 2026-06-21
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - kaname-energy-domain-layer
depends_on:
  - 2606172100
  - 2606212020
  - 2606211200
related:
  - 2606091800
  - 2605261100
supersedes: []
superseded_by: []
---

# ADR-2606212000: kaname 要 — :energy domain layer (system-of-systems energy-flow)

**Status**: proposed
**Date**: 2026-06-21
**Deciders**: Jun Kawasaki

# Context

kaname 要 (ADR-2606172100) is the cross-domain system-of-systems (SoS) leverage synthesizer:
it joins the mirror lineage into one multilayer (multiplex) graph and computes, on read, the
single structural position (the 要 / 律速段階) whose release most improves resilience across the
maximum number of domains. Its multiplex had **10 layers**: politics / religion / organization /
ideology / economy / ecology / security / wellbecoming / ai / information.

**Energy was absent as an explicit layer.** It appeared only operationally — inside hikari 光's
single-site microgrid design (ADR-2605261100), the Energy Order suite's flexibility/heat/compute
legs (ADR-2606211200), and implicitly folded into `:organization`/`:economy` concentration. So
kaname could not answer the SoS question the founder actually asked: *is energy-infrastructure
concentration or grid fragility a cross-domain 律速 — a leverage point that spans energy AND
economy AND organization at once?*

The gap had two halves:

1. **No energy-flow producer.** Until ADR-2606212020 (amime 網目), nothing modelled how ordered
   energy flows BETWEEN sites across a mesh; there was no committed energy concentration graph
   to join.
2. **No energy layer in kaname.** Even with an energy mirror, kaname's `domains` vector had no
   `:energy` member, so any energy 縁 would have been dropped or mis-filed.

This ADR closes the second half (amime ADR-2606212020 closes the first), making energy a
first-class SoS domain.

# Decision

Add `:energy` as the **11th domain layer** of kaname's multiplex, fed by amime 網目's committed
mesh output.

1. **`methods/sos.cljc`** — append `:energy` to `domains` (now 11; `D` = `(count domains)` = 11).
   No other math changes: `L = C·(V/D)·(1+B)·(1−open)`. Adding a domain that the existing
   synthetic seed does not populate rescales every `L` by 10/11 **uniformly** — so the **argmax
   (the 要) is invariant** (the substantive claim is unchanged; only the absolute magnitude
   shifts). The one kaname test asserting the exact seed `L` (11.7 → 10.6363…) is updated with a
   note; the argmax assertion (`要 = accred`) is untouched.

2. **`methods/join.cljc`** — register an `:amime` mirror adapter targeting
   `amime/out/energy-sos.kotoba.edn`, domain `:energy`, identity kind-map (amime already emits
   kaname-form `:concentrates`/`:depends-on` 縁). amime's mesh concentration — flow `:concentrates`
   onto importing loads; single-path import is a `:depends-on` SPOF — lifts straight into the
   `:energy` layer. **Running amime to (re)produce its output is the G7/Council-gated step;
   joining its committed output is what kaname does** (the same rule as for chie/tsumugi/…).

3. **`methods/coverage_report.cljc`** — add `:amime` to `expected-mirrors` so coverage honestly
   reports the energy mirror as joinable (unjoined until a run includes it).

4. **`tests/test_energy_join.cljc`** — a new suite proving the composition end-to-end: amime's
   committed `:energy` graph lifts into the `:energy` layer, every lifted 縁 is `:en/domain :energy`,
   and kaname computes leverage natively over it (the datacenter — the largest importer — is the
   energy-layer 要).

**Why a uniform rescale is acceptable (not a silent regression).** The versatility term `V/D` is
a *ratio*; growing the domain set is a legitimate model extension, not a bug. The discriminator
that matters — a node spanning MANY domains outranks a single-domain hoarder — is strengthened,
not weakened: an entity that now bears load in BOTH an `:energy` chokepoint and another domain
gains versatility and rises. The constitutional gates (G1 map-not-target, G2 opening-only,
G4 edge-primary, G5 no-thought-policing) are untouched.

# Consequences

- kaname can now surface an **energy-flow chokepoint as a cross-domain 要** when (and only when)
  a real entity reconciles across the `:energy` layer and another — e.g. a compute operator that
  is both an `:ai` concentrator and an `:energy` SPOF (datacenter import dependence). This is the
  SoS reading the founder asked for.
- **Composition is real and tested**, not aspirational: amime's committed mesh output is joined
  by exactly the same machinery (`read-graph`/`lift`/`reconcile-by-label`) as the existing
  mirrors. The two ADRs (2606212000 + 2606212020) are a producer/consumer pair.
- Full kaname suite stays green (39 tests / 157 assertions) after the `D` change.
- **No charter amendment.** This is an 実装/engineering extension of an existing observatory
  (Rider §2(e) intel-not-BI boundary unchanged; map-not-target, opening-only preserved).

# Alternatives Considered

- **Fold energy into `:economy`/`:organization` (status quo).** Rejected: it cannot express a
  node whose leverage comes specifically from energy-flow position spanning into other domains —
  the versatility signal is exactly what's lost.
- **Make `:energy` a separate kaname instance rather than a layer.** Rejected: the whole value of
  kaname is the *single* multiplex; a separate instance cannot reconcile a shared entity across
  energy and non-energy domains (no cross-layer versatility).
- **Keep `D` = 10 and special-case energy.** Rejected as dishonest math — if energy is a domain,
  it counts in `D`; hiding it to preserve a test value would be the regression, not the fix.

# References

- ADR-2606172100 (kaname 要 — cross-domain SoS leverage synthesizer)
- ADR-2606212020 (amime 網目 — multi-site energy mesh flow-network; the `:energy` producer)
- ADR-2606211200 (Energy Order Protocol suite — mio/tawami/okibi/toi/yudane/hikari)
- ADR-2606091800 (infra-robotics 3-layer substrate — hikari microgrid; chokepoint redundancy target)
- ADR-2605261100 (hikari 光 — single-site energy)
