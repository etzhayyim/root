---
id: adr-2606051500-kamado-closed-loop-refining-decommission-actor-r0
title: "ADR-2606051500: kamado 竈 — closed-loop carbon refining + fossil-refinery decommissioning/transition actor (R0)"
status: proposed
doc_type: adr
topic: kamado-closed-loop-refining
authoritative: true
last_verified: 2026-06-05
priority: 5.0
axis: architecture
weight: 0.50
priority_note: ""
authoritative_for:
  - kamado actor design, refining ontology, lexicons, gates
  - the :feedstock-class invariant (fossil-virgin-crude unrepresentable)
  - §2(d) fossil-refinery decommissioning/transition robotics scope
  - the net-atmospheric-carbon (D3) balance model for refining pathways
depends_on:
  - "2605192100"
  - "2605192200"
  - "2605263500"
  - "2605261100"
  - "2605262130"
  - "2605215000"
  - "2605231525"
  - "2606032130"
related:
  - "2606042100"
  - "2606031600"
  - "2605312330"
  - "2606013800"
supersedes: []
superseded_by: []
---

# ADR-2606051500: kamado 竈 — closed-loop carbon refining + fossil-refinery decommissioning/transition actor (R0)

**Status**: proposed
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki

# Context

The question *「石油精製のプラントの actor・robotics は設計されているか」* surfaced two follow-ups
worth answering before designing anything:

1. **Is petroleum refining actually a multi-generational harm, or is that an overreach?**
2. **Can robotics / process-control make it harmless?**

What already existed: a single **legacy `oil-refining`** actor manifest
(`20-actors/oil-refining/actor-manifest.jsonld`) — but it is (a) an *observation/intel* actor only
(refinery registry, unit config, outage, yield), (b) charter-**non-compliant**: it drives
`graph.query`/`graph.write` Cypher (`MATCH (r:Refinery) …`), the RisingWave/graph-DB pattern that
**ADR-2605262130** prohibits (kotoba Datom log is canonical state), on the legacy
`did:web:oil-refining.etzhayyim.com` / `legacyExecutionTier:T1` / `kyumei-shinka` stack. It contains
**no robotics, no plant, no construction**. It is migration debris, exactly like the legacy
`maps`/`vessel` surfaces that **watari** (ADR-2606041827) replaced.

**Answering (1) — yes, and the harm is locatable.** Model the carbon over its whole life per tonne
of finished hydrocarbon product (`20-actors/kamado/methods/carbon_balance.py`):

```
net_delta = origin_credit + process_emissions + fate_release      [tCO2e / t]
```

- A finished liquid hydrocarbon is ~85% carbon; combusting 1 t releases ~3.10 tCO₂ (`fate`).
- Fossil-virgin crude carbon came out of **geological storage** → `origin_credit = 0`. Releasing it
  is a one-way **stock→flow** transfer that does not reverse on human timescales (atmospheric CO₂
  perturbation persists centuries–millennia). That is the textbook **multi-generational** harm and
  it maps directly onto Charter §1.9 (multi-generational priority) + §2(f) (multi-generational
  harm) + ADR-2605263500 **D3** (closed-loop carbon).
- Result: fossil diesel, fossil-powered refining = **+3.50 tCO₂e/t** — strongly net-positive.

So refining-of-fossil-crude is genuinely multi-generational. (Note the harm is overwhelmingly in
the *fuel the refinery makes and someone later burns*, plus the fossil origin — not in the refining
step's own energy.)

**Answering (2) — no.** Robotics / advanced-process-control acts **only on the `process` slice**
(tighter combustion, less flaring, fewer fugitive VOC/methane leaks, fewer upset releases, and — a
real labor win — humans out of H₂S/benzene/pyrophoric zones). The model bounds even optimistic APC
at ≤30% of a ~0.40 tCO₂e/t process slice. Applied to the fossil pathway: **+3.50 → +3.38**, a ~3%
cut. The ~89% in `origin + fate` is in the **carbon atoms**, not the plant; no control system
touches it. **Robotics makes fossil refining cleaner, never harmless.**

The only pathways that reach net ≤ 0 change the **feedstock** to closed-loop carbon — biogenic
alkanes (ADR-2605263500 §2.2 microbial hydrocarbon), captured-CO₂ e-fuels, or recycled carbon —
optionally with the carbon locked into a durable material (net-**negative**). This is not an opinion;
it is the arithmetic, and it dictates the design.

# Decision

Author **`kamado` 竈** (Tier-B, R0): a refining actor whose charter-clean shape is forced by the
finding above. 竈 = the sacred hearth/furnace (竈神/荒神, the kami of transforming matter by fire) —
the apparatus is neutral; the carbon source and fate are not. **Three faces** over the kotoba Datom
log:

- **A. observation** (`asset_observation`) — the kotoba-native successor that **supersedes** the
  legacy `oil-refining` Cypher actor (no RisingWave). Public refinery/unit/outage assets +
  transition-readiness as an as-of history. A **resilience + transition map, never a target-list**
  (G4; watari/watatsuna sibling). Observation ≠ operation.
- **B. decommission / transition robotics** (`decommission_plan`) — **§2(d)-permitted**: safely
  wind down / remediate / **convert** *existing* fossil refineries (→ hikari solar / synthesis
  plant / hodoki+kanayama materials recovery). Robotics here is unambiguously harm-reducing (humans
  out of the hot zone, G9; displacement-dividend coupling, ADR-2606032130).
- **C. closed-loop synthetic refining** (`feedstock_guard` + `synthesis_control`) — the same unit
  operations on **biogenic / captured-CO₂ / recycled carbon ONLY**, renewable-powered, every design
  scored against D3. Process-control is **tazuna-style** member-signed Transparent Force (§1.12.B;
  ADR-2606042100): every command an on-chain Datom, no server key (G5), soft-RT only and **not** a
  certified safety system (G11; kotoba-os N2 sibling, ADR-2606031600).

**The structural invariant (the honest answer made unrepresentable).** Because robotics cannot
neutralize fossil carbon, `:fossil-virgin-crude` (and any fossil-extracted feedstock) is **not a
representable value** — mirrored on nusa's `:thc-class` and tazuna's `:weaponizable`. It lives in
three places:

1. **schema** `00-contracts/schemas/refining-ontology.kotoba.edn` — `:feedstock/class :db/allowed`
   = `[:biogenic :captured-co2 :recycled-carbon :existing-inventory-decommission]` (no fossil member).
2. **lexicon** `lex/feedstockProvenance.edn` / `lex/synthesisRun.edn` — `feedstockClass` enum has no
   `fossil-virgin-crude`; `closedLoop`/`screened` `const true`.
3. **code** `methods/feedstock_guard.py` + `cells/feedstock_guard/state_machine.py` — `ValueError`
   on any fossil feedstock; `screen_intervention` raises on `:expand`/`:restart-fossil` (G3).

**Gates G1–G12 / non-goals N1–N7** are enumerated in `20-actors/kamado/manifest.edn`. Headline:
G1 closed-loop-carbon-only · G2 net-carbon-Δ≤0 (D3) · G3 decommission/transition-only (§2(d)) ·
G4 observation-not-target-list · G5 no-server-key · G9 labor-liberation/displacement-dividend ·
G10 local-harm-min/honest-bound · G11 safety-honesty · G12 no-persistence-laundering.

**Empirical artifacts (R0, all green):**
- `methods/carbon_balance.py` — the harm ledger (fossil +3.50 vs closed-loop ≤+0.03; locked −3.07).
- `methods/analyze.py` — observation + transition + D3 report over the `:representative` seed
  (5 refineries / 4 units / 1 outage / 3 §2(d) plans / 3 synthesis designs, 3/3 pass D3).
- `methods/feedstock_guard.py` — G1/G3 structural guards.
- **11 method tests + 8 cell-state-machine tests = 19 green** (`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`).

**Zero invariant amendments.** kamado strengthens existing invariants (§2(d), D3, kotoba-canonical,
no-server-key) and adds none.

# Consequences

- The legacy `oil-refining` Cypher actor is **superseded** (manifest `:actor/supersedes`); its
  migration to kamado's observation face follows the watari precedent. Until removed, do not extend
  it.
- "Petroleum refining" is now representable in the substrate **only** as observation, fossil
  decommissioning/transition, or closed-loop synthesis — a fossil-fed operating refinery cannot be
  expressed, which is the intended end state.
- Couplings: **hikari** (renewable site conversion + synthesis power, ADR-2605261100), **hodoki /
  kanayama** (dismantled-unit materials recovery), **haraedo** (bulky waste), **tazuna** (process
  teleop/control), **kabuto** (operator = `org.corp.*` id), **danjo / moushibumi** (fossil-policy
  questions routed out, never lobbied), **displacement-dividend** (ADR-2606032130, freed workers).
- **Honest R0**: design + data-model + carbon-sim + dry-run only; `:representative` seed; carbon
  model is a transparent per-tonne ledger, not a full ISO-14040 LCA; no live ingest / teardown /
  process actuation (G8, plus G11 certified-safety review for live synthesis).

# Alternatives Considered

- **Rewrite legacy `oil-refining` as-is onto kotoba** — rejected: it would faithfully reproduce a
  fossil-refinery *operation/yield* model, exactly the prohibited shape. Observation is kept; the
  operating model is replaced by the closed-loop one.
- **Automate a fossil refinery for "cleaner" operation** — rejected on the arithmetic: a ~3%
  improvement that leaves a +3.38 tCO₂e/t multi-generational harm intact. Charter §2(d)/§2(f) + D3
  forbid the underlying activity regardless of how cleanly it is run.
- **Permit fossil feedstock behind a Council Lv7+ gate** — rejected: §2(d) is not a throughput
  question a vote can resolve; new fossil-fed operation is a multi-generational-harm prohibition, so
  the value is made unrepresentable rather than gated (cf. nusa `:thc-class`).
- **Refine crude into durable materials only (lock the carbon, never combust)** — partially folded
  in as the `:durable-material` fate (net-negative when the carbon is closed-loop), but **gated by
  G12** (end-of-life route required) and still G1 (the *input* must be closed-loop carbon, not
  fossil crude — otherwise it is fossil extraction with a delay).

# References

- `20-actors/kamado/` — manifest, CLAUDE.md, README, cells, lexicons, methods, seed
- `00-contracts/schemas/refining-ontology.kotoba.edn` — the `:feedstock/class` invariant
- ADR-2605263500 — energy substance gates (D1–D5; D3 closed-loop carbon; microbial hydrocarbon)
- ADR-2605261100 — hikari energy actor (renewable power + site conversion)
- `/CHARTER-RIDER.md` §2(d) — no new fossil extraction · §2(f) — multi-generational harm
- ADR-2605262130 — kotoba canonical state (no RisingWave/Cypher)
- ADR-2606042100 (tazuna) · ADR-2606031600 (kotoba-os N2 safety boundary) · ADR-2606032130
  (displacement dividend) · ADR-2605231525 (no-server-key)
- `20-actors/oil-refining/actor-manifest.jsonld` — the superseded legacy actor
