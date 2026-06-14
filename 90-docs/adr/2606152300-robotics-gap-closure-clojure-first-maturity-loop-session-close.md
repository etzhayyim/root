---
id: adr-2606152300-robotics-gap-closure-clojure-first-maturity-loop-session-close
title: "ADR-2606152300: Robotics GAP-closure wave + Clojure-first maturity-loop — session close"
status: accepted
doc_type: adr
topic: robotics-gap-closure-session-close
authoritative: true
last_verified: 2026-06-15
priority: 5.0
axis: architecture
weight: 0.30
priority_note: "Session-close record for the robotics-coverage GAP wave (ADR-2606142000..2606142030) + the self-paced /loop maturity arc. Documents the merge-mid-loop split (PR #1740 merged at the handoff commit; the later 9 commits land via this closing PR) and registers the 4 actor ADRs in adr-index.edn (they were merged as .md but never indexed)."
authoritative_for:
  - robotics-coverage GAP-closure session outcome (4 Clojure-first actors, R0)
  - the Clojure-first (babashka-runnable) actor idiom + the robotics-coverage maturity scorecard
depends_on:
  - ADR-2606142000 (kuramori — reference Clojure-first actor)
  - ADR-2606142010 (soma)
  - ADR-2606142020 (madomori)
  - ADR-2606142030 (kudamori)
  - ADR-2606073001 (robotics remote-work coverage/GAP survey)
related:
  - ADR-2606032100 (labor-liberation robotics wave)
  - ADR-2605312345 (kotoba Datom = canonical state)
supersedes: []
superseded_by: []
---

# ADR-2606152300: Robotics GAP-closure wave + Clojure-first maturity-loop — session close

**Status**: accepted
**Date**: 2026-06-15
**Deciders**: Jun Kawasaki (founder, Council Lv7+ 1/1)

# Context

ADR-2606073001 §3/§4 named four open robotics coverage GAPs — warehouse 積み下ろし,
伐採 logging, 高所/façade window cleaning, and 下水道/confined-space cleaning — the last three
being precisely the occupations where teleoperation value is highest (the hazard is on-site
presence itself). This session closed all four, authored **Clojure-first** (the first working
babashka-runnable actor idiom in the repo; the prior Python→Clojure migration had left only
non-functional `port-failed` stubs), then drove their maturity via a self-paced `/loop` against
a measurable scorecard.

# Decision

Record the session outcome as authoritative.

**1. Four GAP actors authored (all 🟡 R0, Clojure-first, dividend-coupled, tazuna-teleoperable):**
- **kuramori 倉守** (ADR-2606142000) — warehouse intralogistics (AGV/AMR), the reference idiom;
  reuses niyaku's proven trapezoidal-profile + segment-conflict + LPT-dispatch core.
- **soma 杣** (ADR-2606142010) — forestry/logging (directional fell + bucking + extraction).
- **madomori 窓守** (ADR-2606142020) — façade/high-rise window cleaning (wind/fall-arrest +
  adhesion; G3 privacy-by-construction).
- **kudamori 管守** (ADR-2606142030) — sewer/confined-space cleaning (atmosphere entry gate +
  jetting; closes the in-pipe GAP mizuho's *treatment* scope left open).

Each encodes its on-site hazard as a *raising* safety gate (fall-zone exclusion · wind
work-stop + fall-arrest redundancy · confined-space atmosphere entry · pipe over-pressure).

**2. Clojure-first idiom + maturity scorecard.** Pure babashka-runnable Clojure (ns
`<actor>.methods.*`, classpath `20-actors`, self-exiting `clojure.test`), also
kotoba-pywasm-portable. `70-tools/robotics-coverage/maturity.clj` scores each actor across
measurable axes; `ecosystem.clj` verifies the cross-actor handoff chain references only real
actors (emits `CHAIN.md`).

**3. The /loop maturity arc (scorecard-driven).** Successive `/loop coverage, 成熟度を向上して`
iterations drove, in order: scorecard baseline → kuramori R1 batch-picking/congestion →
cross-actor handoff edges (niyaku→kuramori→todoke · soma→tatekata · madomori→tatekata ·
kudamori→mizuho) → per-actor occupation-coverage modules → **occupation-coverage 0→100%** (16
named sub-task GAPs closed as real methods) → **full-day `run-day` pipelines (pipeline-
integration 100%)** → cross-actor chain verifier → **`emit-day` (canonical Datom log captures
the full day)**. Final state: **4 actors · 165 deftests green · every scorecard axis 1.00**.

**4. Merge-mid-loop split (recorded for honesty).** PR **#1740** merged at the handoff commit
(`f78ff1a96f`), mid-loop. The subsequent **9 commits** (coverage→100%, run-day pipelines,
chain verifier, emit-day) were stranded on the branch; **this closing PR lands them** in main,
**registers the 4 actor ADRs in `adr-index.edn`** (they merged as `.md` but were never indexed),
and adds this session-close record.

# Consequences

**Positive** — the named-occupation robotics coverage map (ADR-2606073001) is now **closed
except the N1-excluded 採掘 (mining)**; the first working Clojure-first actor idiom is
established and replicated ×4; maturity is measurable and fully green; the cross-actor logistics
chain is verified.

**Limits / deferred (R1, gated)** — all four remain R0 (design + sim; no hardware, no real
actuation, no-server-key). The **cell-runtime `.solve()` execution layer** and higher-fidelity
physics are explicitly deferred to a **fresh branch off this merged main** (they are
architectural / Council-operator-gated, not loop-shaped). The self-paced `/loop` was stopped at
this close.

# Alternatives Considered

- **Keep pushing the loop into cell-runtime on the same PR** — rejected; #1740 was already a
  large, coherent unit and the cell-runtime is architectural. Cleaner as its own branch.
- **Leave the 9 stranded commits unmerged** — rejected; they are complete, tested, and valuable
  (occupation-coverage 100% + composition + canonical-log completeness).
- **Hand-author vs regenerate adr-index.edn** — hand-added the 4 entries to match schema (the
  docs-registry regen covered `docs.json`/`graph.jsonld` but not `adr-index.edn`).

# References

- ADR-2606142000 / 2606142010 / 2606142020 / 2606142030 (the 4 GAP actors)
- ADR-2606073001 (robotics remote-work coverage/GAP survey)
- ADR-2606032100 (labor-liberation robotics wave), ADR-2605312345 (Datom = canonical state)
- PR #1740 (initial wave, merged); this closing PR (stranded commits + index + close)
