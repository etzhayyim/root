---
id: adr-2607081100-noroshi-device-design-reliability-qual-compliance-engine
title: "ADR-2607081100: noroshi — device_design + reliability_qual mature to coded cells; IEC 60825 ground-truth classification"
status: accepted
doc_type: adr
topic: noroshi-photonic-convergence-wave2
authoritative: true
last_verified: 2026-07-08
priority: 4.0
axis: architecture
weight: 0.30
priority_note: "closes a real coverage gap: 2 of noroshi's 6 cells had zero implementation (pure .edn scaffold); this pass makes them real, tested, and adds a genuine GR-468-SHAPE PASS/FAIL compliance engine"
authoritative_for:
  - noroshi-device-design-cell
  - noroshi-reliability-qual-cell
  - noroshi-iec60825-classification
depends_on:
  - 2606051600
related:
  - 2606032130
  - 2605231525
  - 2605215000
  - 2606072802
supersedes: []
superseded_by: []
---

# ADR-2607081100: noroshi — device_design + reliability_qual mature to coded cells; IEC 60825 ground-truth classification

**Status**: accepted
**Date**: 2026-07-08
**Deciders**: Jun Kawasaki

# Context

The question put to the substrate, in a prior session, was whether `cloud-itonami`/`kotoba-lang`
had any physical-device/EDA/manufacturing-process design for optical communication — the answer
surfaced `noroshi` (this actor) as the closest existing coverage, one layer down from the network-
topology work that prompted the question (`kotoba-lang/apn` + `cloud-itonami-isic-6110`, ADR-
2607084700 in the `com-junkawasaki/root` superproject). A follow-up asked to further mature
`noroshi` specifically, with a **PASS/FAIL compliance engine**.

Direct inspection (not assumption) found: of noroshi's 6 manifest cells, only `active_alignment`
was `:cell/coded true` — and even there, "coded" means the pure phase-transition state machine is
real and tested, while `.solve()` itself remains an R0 `RuntimeError` stub. The other 5 cells
(`link_budget`, `isac_waveform`, `sense_estimate`, `device_design`, `reliability_qual`) were **pure
`.edn` descriptors with zero implementation** — `:cell/entry` pointing at a `cell.py` file that does
not exist on disk, for any of them. `reliability_qual`'s own `.edn` docstring already named the
target compliance standard: "using the Telcordia GR-468 test SHAPE only ... names as neutral
vocabulary" — but no code anywhere computed a PASS/FAIL judgment against it. `device_design`'s own
`.edn` similarly described a design pipeline (NL intent → civilian-gate → open-EDA plan → emit) with
no implementation behind any node.

Research also found: the actor's own `methods/*.py` files were **already pruned** after a prior
py→cljc port wave (MATURITY.md item #3) — `.cljc` is the sole canonical implementation for the
`methods/` layer, though `cells/active_alignment`/`cells/fibre_loop` still keep a hand-synced
Python twin. The `com-junkawasaki/root` superproject's own CLAUDE.md independently confirmed this
direction: "newly authored operational code should be bb/cljc, not new `.py`" (kotoba wasm →
clojurewasm → cljs → nbb → jvm priority order) — and `etzhayyim/root`'s own CLAUDE.md states the
stronger, repo-wide rule directly: **"Do not author new first-party operational/daemon/heartbeat/
tooling scripts in Python or shell"** (ADR-2606072802 enforced-forward). No numeric GR-468 or IEC
60825 parameters existed anywhere in the repo to avoid duplicating or contradicting — this ADR's
thresholds are new, not a conflicting second source.

# Decision

### Decision 1: `reliability_qual` gets a real GR-468-SHAPE PASS/FAIL engine — representative, not verbatim

`methods/reliability-qual.cljc` judges four test types (thermal cycling, damp heat, mechanical
shock, fibre pull) against caller-supplied results. Every numeric acceptance threshold in
`default-suite` is tagged `:representative true` (G10) — assembled from commonly-published
engineering literature, explicitly **not** a verified citation to the licensed Telcordia GR-468-CORE
clause text. This mirrors the repo's own `nv-compat`/G1 "clean-room, names as neutral vocabulary"
discipline, now applied to a standards-compliance domain rather than an EDA-tool domain. An operator
qualifying a real device must replace `default-suite` with the actual licensed thresholds before the
judgment carries real regulatory weight — stated explicitly in the namespace docstring, not left
implicit.

A selected test with no submitted result FAILS (`:not-submitted`), never silently passes — the same
"no fabricated coverage" (G10/N4) discipline `telecom.facts`/`netops.facts` use in the
`com-junkawasaki/root` fleet for missing jurisdiction coverage, applied here to missing test
evidence.

### Decision 2: `device_design` gets a real civilian-gated EDA plan generator, delegating to `pic-layout`

`methods/device-design.cljc`'s `civilian-gate` refuses an unknown device kind (G1 — outside the
open-PDK vocabulary) or a non-civilian force-class (G3/N1) before any plan is built — the
device-design analogue of `methods/active-alignment`'s `enable-laser`. `design-plan` delegates
assembly-kind intents (`:cpo-module`/`:pic-link`) to the EXISTING `methods/pic-layout/transmitter-
plan` rather than reimplementing PIC layout a second time; a single discrete component gets a
minimal one-op placement plan, honest about scale (never inflating one part into a fake assembly).

### Decision 3: IEC 60825 gets a ground-truth classification function, not just a class-label pass-through

`methods/active-alignment.cljc`'s pre-existing `enable-laser` trusted a caller-supplied `laser_class`
string completely — it never checked that string against the laser's actual physical parameters.
This ADR adds `classify-laser-class` (power-mw + wavelength-nm → IEC 60825 class, via representative
AEL boundaries, G10) and wires `cells/active_alignment/state_machine.cljc`'s
`transition-verify-laser-safety` to independently recompute the class and refuse a claim that
UNDERSTATES the computed hazard — when `laser_power_mw`/`wavelength_nm` are supplied. This is the
same "ground-truth recompute, never trust the self-report" discipline
`netops.registry/route-endpoints-missing?` and `telecom.registry/e164-invalid-format?` use elsewhere
in this workspace (`com-junkawasaki/root`'s `cloud-itonami-isic-6110`/`cloud-itonami-isic-6190`),
now applied to a laser-safety class claim. **Backward compatible**: the two new fields are optional;
every pre-existing caller (including every pre-existing test) supplies neither, so the check is
skipped and behavior is unchanged — verified by re-running the full 183-test pre-existing baseline
unmodified before adding new tests, then again after.

### Decision 4: deliberately depart from the "state machine never calls methods/" precedent — for these two cells only

`active_alignment`'s and `fibre_loop`'s existing state machines never call their `methods/` sibling
core — they accept a pre-computed numeric result (e.g. `coupling_loss_db`) as a state-dict input
field. This pass's two state machines (`cells/device_design/state_machine.cljc`,
`cells/reliability_qual/state_machine.cljc`) DELIBERATELY call `methods/device-design`/
`methods/reliability-qual` directly. A real compliance-judgment ENGINE — not merely a job-lifecycle
gate around an externally-supplied number — was the explicit ask this pass answers; keeping the old
precedent would have meant re-stubbing the exact thing requested.

### Decision 5: no new Python (`cell.py`) — cljc only

Unlike `active_alignment`/`fibre_loop` (which keep a hand-synced `cell.py` + `state_machine.py`
twin), this pass ships `cells/device_design/` and `cells/reliability_qual/` as `.cljc` only. This
follows `etzhayyim/root`'s own repo-wide rule (ADR-2606072802: no new first-party `.py`/`.sh`
operational code) rather than the older dual-language pattern that predates that rule. `.edn`
descriptors were updated to match (`:cell/entry` → `cell.cljc`, `:cell/handler` → a namespace-
qualified Clojure symbol string rather than a Python class name).

### Decision 6: schema/ontology/manifest co-evolution, and the pre-existing tests that had to change

`reliability_qual.edn`'s own declared kotoba writes (`:qual/id :qual/suite :qual/acceptance`) had
**no matching attributes in `kotoba/schema.edn`** before this pass — a pre-existing gap, not
something this ADR introduces. `:qual/*` attributes were added to both `kotoba/schema.edn` and the
SSoT ontology (`00-contracts/schemas/photonic-convergence-ontology.kotoba.edn`) — required in
lock-step, since `methods/test_consistency.cljc`'s `test-ontology-attributes-equal-schema-idents`
strictly equates the two key sets. `manifest.edn` marks both cells `:cell/coded true`, which broke
the pre-existing `test-exactly-one-coded-cell-and-it-is-active-alignment` assertion by design (three
coded cells now, not one) — that test was renamed and its assertion updated to the new three-element
set, rather than left failing or worked around. `test-every-manifest-cell-exists-as-descriptor-or-
coded-dir`'s coded-check also only looked for `cell.py`; extended to accept `cell.cljc` too (else it
would have failed for both new cells given Decision 5).

# Consequences

- Closes the "physical device/EDA/manufacturing" gap the originating question identified, one layer
  further than the prior session's `kotoba-lang/apn` work: `noroshi` now has real, tested code for
  device-design planning and reliability-qualification judgment, not just a network-topology model
  one layer up.
- The GR-468/IEC-60825 thresholds are the first numeric compliance parameters in this actor —
  honestly scoped as representative (G10), matching every other "no measured silicon exists" claim
  this actor already makes for its physics simulations.
- `active_alignment`'s laser-safety gate is now strictly stronger for callers who supply physical
  parameters (a real safety improvement — a self-reported class can no longer silently understate
  hazard when the underlying power/wavelength are available) while remaining 100% behavior-preserving
  for callers who don't.
- Coded-cell count: 1 → 3 of 6. The remaining 3 (`link_budget`, `isac_waveform`, `sense_estimate`)
  are unchanged pure `.edn` scaffolds — a known, honestly-tracked gap (MATURITY.md), not silently
  implied to be done.
- `.solve()` is unchanged on every cell, including the two matured this pass — still R0 stubs
  pending Council ADR ratification (G8). No live chamber, no live laser measurement exists at any
  point in this change.
- Full suite: 183 → 233 tests (627 → 751 assertions), 0 failures/errors, including every pre-
  existing test file (three of which — `test_consistency`, `test_governance`, `test_active_alignment`
  — required edits to stay accurate, not to be worked around).

# Alternatives Considered

- **Full Telcordia GR-468-CORE clause-level reproduction.** Rejected: the standard is a licensed,
  paid document; reproducing its verbatim numeric tables without a verified license would violate
  this workspace's sourcing-honesty discipline (G10) and likely the standard's own copyright. The
  SHAPE-only framing (test categories + PASS/FAIL structure as open vocabulary, representative
  numbers, explicit operator-must-replace disclaimer) was the repo's own pre-existing framing for
  this cell, adopted rather than invented.
- **A precise, standards-accurate IEC 60825 classifier (wavelength-and-exposure-time-dependent AEL
  tables, 1M/2M sub-classes).** Rejected for the same reason, plus scope: the ask was a PASS/FAIL
  compliance engine, and a simplified representative model that is HONEST about its simplification
  is more defensible than a falsely-precise one. `representative-ael-mw`'s docstring states this
  explicitly.
- **Keep the "state machine never calls methods/" precedent** (pass results in as opaque numbers,
  same as `active_alignment`). Rejected — see Decision 4; it would have produced another
  job-lifecycle-only stub, not the compliance engine actually requested.
- **Add `cell.py` twins to match `active_alignment`/`fibre_loop`.** Rejected per Decision 5 — the
  newer repo-wide no-new-Python rule (ADR-2606072802) postdates and supersedes that older dual-
  language pattern for first-party operational code.
- **Leave `test-exactly-one-coded-cell-and-it-is-active-alignment` failing, or delete it.** Rejected:
  the test encodes a real, useful invariant (coded cells are exactly a known, intentional set); it
  was updated to the new correct set rather than removed or left red.

# References

- `20-actors/noroshi/methods/reliability_qual.cljc`
- `20-actors/noroshi/methods/device_design.cljc`
- `20-actors/noroshi/methods/active_alignment.cljc` (`classify-laser-class` addition)
- `20-actors/noroshi/cells/reliability_qual/` , `20-actors/noroshi/cells/device_design/`
- `20-actors/noroshi/MATURITY.md` (iteration record, 2026-07-08)
- ADR-2606051600 (noroshi master ADR)
- `com-junkawasaki/root` ADR-2607084700 (`kotoba-lang/apn` + `cloud-itonami-isic-6110` — the
  network-topology layer this photonic-chip layer sits beneath)
