---
id: adr-2606051200-hotaru-inp-iii-v-substrate-commons-r0
title: "hotaru 蛍 — III-V / InP substrate open-publication commons (Tier-B actor R0; the open-IP commons ADR-2605265500 §2's R4+ gate references — NOT a fab)"
status: proposed-pending-council-ratification
doc_type: adr
topic: hotaru-iii-v-inp-substrate-commons
authoritative: true
last_verified: 2026-06-05
priority: 6.2
axis: actor
weight: 0.62
priority_note: "Answers 「インジウムリン基盤の生成・製造に関わる actor は設計されているか」 (was: no). Sub-ADR of ADR-2605265500 (which PROHIBITS III-V manufacturing through R3). hotaru is NOT a fab — it is the open-publication III-V/InP substrate knowledge COMMONS that 2605265500 §2's R4+ re-evaluation gate is explicitly conditioned on ('open-source III-V wafer + epitaxy IP becomes available; currently no such commons exists'). Charter-clean by construction (nusa pattern): open-IP-only (G1) + design-only/not-fabricated (G2) + non-adjudicating-on-the-gate (G3). Fabrication remains PROHIBITED through R3, unchanged. ZERO invariant amendments."
authoritative_for:
  - "hotaru actor scope (III-V/InP substrate open-publication commons; design/datafication/simulation only)"
  - "the open-IP-only invariant for III-V process knowledge (:source-license practiceable-open set)"
  - "the design-only/not-fabricated invariant (:fabricated false through R3)"
  - "the commons-readiness index feeding the ADR-2605265500 §2 R4+ gate evaluation (non-adjudicating)"
depends_on:
  - adr-2605265500-concentrated-pv-d-gate-evaluation-r0
  - adr-2605242500-baien-ternary-silicon-and-tsukuru-fab-charter
  - adr-2605261100
  - adr-2606021200-himawari-solar-pv-manufacturing-r0
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605231525-server-side-signing-capability-boundary
related:
  - adr-2606012600-watatsuna-submarine-cable-resilience
supersedes: []
superseded_by: []
---

# ADR-2606051200: hotaru 蛍 — III-V / InP substrate open-publication commons (R0)

**Status**: proposed-pending-council-ratification
**Date**: 2026-06-05
**Deciders**: Jun Kawasaki (Founder, Seat 1) — pending Council ratification

# Context

A direct question: *「インジウムリン (InP) 基盤の生成・製造に関わる actor は設計されているか」*.

The honest pre-existing answer was **no** — and not by accident. The semiconductor actor ecosystem is
**silicon-only**: the iwakura/fuigo/tsukuru ternary logic-ASIC track (ADR-2605242500) and himawari
solar-grade c-Si PV (ADR-2606021200). Compound III-V semiconductors (InP, GaAs, GaN, …) were evaluated
once — in **ADR-2605265500 §2** (concentrated PV) — and III-V *manufacturing* was ruled **PROHIBITED
through R3**, because:

- MOCVD/epitaxy has ~3 commercial vendors globally, all vendor-IP-encumbered (incompatible with §1.6 中間排除);
- no open-publication III-V wafer + epitaxy IP **commons** exists;
- In/Ga/Ge sourcing carries Charter §2(g) supply-audit complexity (In/Ga are explicitly barred from
  hikari/himawari panel sourcing, §G2);
- ITAR/EAR export controls touch III-V semiconductor.

Crucially, ADR-2605265500 §2 left a door: **R4+ re-evaluation if "open-source III-V wafer + epitaxy IP
becomes available (currently no such commons exists)."** That precondition is a *thing that has to be
built*. Nobody is building it inside the religious-corp substrate. That is the gap hotaru fills.

So hotaru is designed the way **nusa** (ADR-2606039800) answered "大麻の解禁": **not** the prohibited
thing, but the charter-clean inverse, with the prohibited space **unrepresentable by construction**.

**Why 蛍 (firefly).** Silicon has an **indirect** bandgap and cannot emit light efficiently — that
physical fact is *why* the direct-bandgap III-V family exists: lasers, LEDs, photodetectors, photonic
ICs, the optoelectronics that run optical fibre and the submarine cables watatsuna 綿津綱 maps
(ADR-2606012600). hotaru is the light-emitting-crystal commons — the **direct**-bandgap sibling of the
iwakura/fuigo **indirect**-bandgap silicon track.

# Decision

Land **hotaru** as a Tier-B actor at **R0 = open-publication III-V/InP substrate knowledge commons +
readiness reporting**. **Design / datafication / simulation only. NO fabrication.** This ADR makes **zero
invariant amendments**; ADR-2605265500 §2's III-V manufacturing prohibition stands unchanged.

## §1 Scope — the substrate chain, open-publication only

hotaru datafies the **substrate** chain (生成 + 製造 of the wafer the device is later built on):

```
synthesis → bulk-growth (single crystal) → wafering → surface-prep (epi-ready)   ← hotaru scope
                                                              │
                                                              ▼
                                                  epitaxy / device stack-up        ← OUT of scope
                                                  (ADR-2605265500 §2 vendor-IP gap)
```

`:epitaxy` is recorded **only as a tracked gap**, never as a practiceable recipe.

## §2 The three structural invariants (charter-clean by construction)

Each invariant is enforced in **three places** — ontology schema `:db/allowed`, lexicon `enum`/`const`,
and code (`ValueError`/refusal) — exactly as nusa enforces `:thc-class`.

| # | Invariant | Gate | Enforcement |
|---|---|---|---|
| 1 | **Open-IP only** — `:iiiv.proc/source-license` ∈ {`:academic-oa` `:patent-expired` `:textbook-public` `:standard-public` `:own-rnd`}; `:vendor-proprietary`/`:patent-active`/`:trade-secret` **unrepresentable** | G1 | schema allowed-set + lexicon enum + `commons_ingest`/`analyze.py` raise |
| 2 | **Design-only / not-fabricated** — `:iiiv.crystal/fabricated` and `:iiiv.wafer/fabricated` `:db/allowed [false]`; a grown boule / manufactured wafer **unrepresentable** through R3 | G2 | schema allowed-`[false]` + lexicon `const false` + `screen_fabrication` raise |
| 3 | **Conflict-mineral sourcing** — In/Ga consumed requires `:in-sourcing` ∈ {`:recycled` `:conflict-free-attested`}; `:unverified` refused (inherits hikari/himawari §G2) | G4 | schema allowed-set + lexicon enum + `precursor_safety` refusal gate |

Invariant #1 is precisely what makes the graph **a commons** — the artifact ADR-2605265500 §2's R4+
gate references. A graph that could hold a proprietary recipe would not be one.

## §3 Non-adjudicating on the gate (G3)

hotaru **reports** how far the open commons is from the R4+ gate; it **does not decide or advocate** it.
`methods/analyze.py` computes a per-stage open-coverage index and a verdict
(`r4GateSatisfiable`), and `silenHotaruReview` (`fabricationProhibited const true`) confirms the
prohibition stands. Opening the gate is **Council Lv7+ unanimity** (stronger than the usual Lv6+,
because III-V is constitutionally gated through R3) — never an act of this actor.

## §4 Architecture — 5 Pregel cells + 6 lexicons + ontology

| Cell | Murakumo node | Role | Status |
|---|---|---|---|
| `commons_ingest` | dan | open-publication process-knowledge ingest + **open-IP license screen** | **coded** state machine (G1) |
| `bulk_crystal_design` | naphtali | LEC/VGF/VB boule growth design (+ thermal-field sim R1) | **coded** state machine (G2 `fabricated false` + G4) |
| `wafer_fab_design` | gad | saw/lap/CMP/surface epi-ready spec | **coded** state machine (G2 `fabricated false` + spec-sanity) |
| `precursor_safety` | asher | PH₃/In/Ga toxic + conflict-mineral + export-control **refusal gate** | **coded** state machine (G3/G4/G9/G11) |
| `commons_readiness` | issachar | per-stage coverage + maturity-score → R4+ gate input (non-adjudicating) | **coded** state machine (G3; logic mirrored in `analyze.py`) |

Lexicons `com.etzhayyim.hotaru.{processKnowledge, crystalGrowthDesign, waferSpec,
precursorSafetyAttestation, commonsReadinessReport, silenHotaruReview}`. Ontology
`00-contracts/schemas/iii-v-substrate-ontology.kotoba.edn`.

## §5 Empirical R0 result

`analyze.py` on the `:representative` seed (6 materials / 26 open processes / 3 crystal designs / 2 wafer
specs / 8 precursors; InP + GaAs + GaSb + InSb carry full open substrate chains (4/5 bulk-substrate
materials), InGaAs is epitaxial-only (correctly excluded), GaN bulk tracked as an explicit gap
(HVPE/ammonothermal, never claimed mature) — surfaced by the gap register):

- **substrate commons READY** — 4/4 stages (synthesis / bulk-growth / wafering / surface-prep) have ≥1
  `:open-mature` process (LEC InP from Mullin 1968 textbook-public; VGF/HB from expired patents; CMP
  from SEMI public standards; wet-etch surface from open-access);
- **epitaxy GAP** — present only as `:gap` maturity (single-layer fundamentals are open, device-grade
  stack-up is vendor-proprietary → not in the commons);
- **R4+ gate satisfiable from the commons alone = `False`** → III-V **fabrication stays PROHIBITED
  through R3**, unchanged. The binding gap is **epitaxy/device**, not substrate growth.

**53 tests green**: `methods/test_analyze.py` (25 — incl. `:vendor-proprietary` → `ValueError`,
`:fabricated true` → `ValueError`, In/Ga detection, R4+ gate not satisfiable, maturity-score +
per-material chain-completeness) + `cells/test_state_machines.py` (28 — all 5 cells' state machines:
open-IP screen, G2/G4 growth + wafer design refusals, precursor refusal gate, G3 non-adjudication, both
directions).

## §6 Gates (11, immutable) + non-goals (6)

G1 open-IP-only · G2 design-only/not-fabricated · G3 non-adjudicating-on-the-gate · G4 conflict-mineral-
sourcing · G5 no-server-key · G6 Murakumo-only · G7 sourcing-honesty · G8 outward-gated (**Lv7+**) ·
G9 export-control-honest · G10 civilian-only · G11 process-safety.

N1 no military/fire-control/weapons-seeker III-V · N2 NOT a fab (fabrication prohibited through R3) ·
N3 no vendor-proprietary recipe ingest/reverse-engineering · N4 not the silicon iwakura/himawari track ·
N5 no In/Ga without clean sourcing · N6 does not decide/advocate the R4+ gate.

## §7 Roadmap

| Phase | Scope | Gate |
|---|---|---|
| **R0** (this ADR) | Ontology + 6 lexicons + 5 cells (all 5 coded state machines) + analyzer (maturity-score + per-material chain-completeness) + InP & GaAs seed chains. Commons readiness reporting. 53 tests green. No runtime/sim/live-kotoba. | ADR-2606051200 (PROPOSED) + ADR-2605265500 §2 inherited |
| **R1** post-Council | Expand open commons (`:open-emerging` → `:open-mature`); bulk-growth thermal-field sim (kami-genesis); honest epitaxy-gap map. Design/sim only. | + ≥1 compound-semiconductor crystal-growth engineer on Council advisory |
| **R2** post-R1 | Simulation-validated substrate process designs; export-control/jurisdiction attestation framework; commons readiness as standing input to the 2605265500 R4+ evaluation. NO fabrication. | + ADR-2605265500 R4+ evaluation reopened by Council Lv7+ |
| **R3** deferred | RESERVED — reachable only if the ADR-2605265500 R4+ gate OPENS. Fabrication is out of hotaru R0..R2 by construction. | ADR-2605265500 R4+ gate (Council Lv7+ unanimity) |

## §8 R0 maturation log (2026-06-05 session)

R0 was hardened over an 8-iteration self-paced session (all changes design-only; zero invariant
amendments; fabrication never implemented). Trajectory:

1. Scaffold landed (ontology + 6 lexicons + 5 cells, 2 coded + 3 `RuntimeError` stubs) — 22 tests.
2–3. All 3 remaining stubs → coded state machines (`bulk_crystal_design` G2/G4, `wafer_fab_design`
   G2/spec, `commons_readiness` G3) + maturity-score metric — all 5 cells coded.
4–5. Analyzer metrics (per-material maturity-weighted score, precursor safety + export-control/G9,
   substrate-material coverage) + seed expanded InP → InP/GaAs/GaSb chains + `:iiiv.material/form`
   (bulk-substrate vs epitaxial-only, so InGaAs is correctly excluded, not a gap).
6. InSb chain (4/5 bulk full chains) + the **3-places invariant machine-checked** (schema `:db/allowed`
   ≡ lexicon `enum`/`const` ≡ code sets — anti-drift).
7. **Gap register** (enumerates every missing material+stage + the structural epitaxy gap — the core
   deliverable toward the R4+ gate) + GaN bulk represented as an explicit honest gap.
8. **Seed schema-conformance gate** (`analyze.py` validates every datom against the ontology
   `:db/allowed` SSoT, refuses to run on a non-conformant seed).

End state: 6 materials / 26 open processes / 8 precursors; **53 tests green** (25 methods + 28 cells);
substrate commons READY, epitaxy GAP, R4+ gate not satisfiable from the commons alone (unchanged). The
next meaningful maturation (bulk-growth thermal-field simulation, live kotoba materialization, Council
submission) is **R1 work, gated on Council Lv6+/operator** — outside design-only autonomous iteration.

# Consequences

**Positive**:
- Closes the honest gap surfaced by the question — InP/III-V substrate now has a designed actor, in the
  only charter-clean shape available.
- **Builds the exact artifact** ADR-2605265500 §2's R4+ gate is waiting on (an open-source III-V wafer IP
  commons), turning a static prohibition into a measurable, progressable one.
- The empirical finding is itself useful: it isolates **epitaxy/device** (not substrate growth) as the
  binding vendor-IP gap — sharpening any future R4+ debate.
- Reuses the nusa charter-clean-by-construction pattern + the himawari/hikari §G2 conflict-mineral gate;
  zero new substrate, zero invariant amendments.

**Negative / honest limits**:
- R0 is design + datafication + an analyzer over a **bounded `:representative` seed** — not a literature
  harvest of the real open-publication corpus, not a growth simulation, not live kotoba materialization.
- "Substrate commons READY" is a seed-level finding (the stages have *a* canonical open process each), not
  a claim that a fab could be stood up — fabrication remains prohibited and out of scope regardless.
- Process figures (EPD, bandgap, lattice constants) are `:representative` and need primary-source
  verification (G7) before any outward use.
- ITAR/EAR posture is recorded but not a substitute for the jurisdictional-risk attestation ADR-2605265500
  §2 requires at R4+.

# Alternatives Considered

- **Build a real InP fab actor (生成・製造 literally)**: rejected — directly violates ADR-2605265500 §2
  (III-V manufacturing PROHIBITED through R3). Would require a Council Lv7+ amendment this ADR does not seek.
- **Author only a re-evaluation proposal for ADR-2605265500 (no actor)**: rejected as insufficient — the
  R4+ gate is conditioned on a *commons existing*; a proposal that merely argues for the gate without
  building the commons cannot satisfy its own precondition. hotaru builds the commons; a future ADR can
  cite hotaru's readiness when arguing the gate.
- **Fold InP into the silicon iwakura/tsukuru track**: rejected — III-V compound substrate (direct
  bandgap, MOCVD/LEC, In/Ga/P precursors) is a distinct material system from Si logic ASIC; conflating
  them would hide the §2 prohibition and the conflict-mineral gate (N4).
- **Permit substrate growth but not epitaxy at R0**: rejected — substrate *growth* is still III-V
  *manufacturing*; ADR-2605265500 §2 prohibits it through R3. hotaru stays design/sim only until the gate.

# References

- ADR-2605265500 (Concentrated PV — III-V manufacturing PROHIBITED through R3; R4+ gate this actor serves)
- ADR-2605242500 (baien ternary silicon + tsukuru fab — indirect-bandgap silicon sibling track)
- ADR-2606021200 (himawari solar-Si PV — §G2 conflict-mineral In/Ga ban inherited)
- ADR-2605261100 (hikari energy — §G2 conflict-mineral source of the In/Ga bar)
- ADR-2606039800 (nusa — the charter-clean-by-construction / unrepresentable-prohibited-space pattern)
- ADR-2606012600 (watatsuna submarine cables — the optical-fibre/photonics consumer of InP substrates)
- ADR-2605215000 (Murakumo-only inference) · ADR-2605231525 (no-server-key)
- ADR-2605192100 (Mission Charter — §2(a) force-separation, §1.6 中間排除) · ADR-2605192200 (Charter Rider)
