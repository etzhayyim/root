---
id: adr-2606022600
renumbered_from: "2606022600"
title: "ADR-2606022601: Session close — R0-actor coverage sweep (funadaiku/sarutahiko) + organism-axis affiliation convention"
status: active
doc_type: adr
topic: session-close-r0-actor-coverage-sweep-and-organism-axis-convention
authoritative: false
last_verified: 2026-06-02
priority: 4.0
axis: process
weight: 0.40
priority_note: "session-close record; continuation of ADR-2606022400"
authoritative_for: []
related:
  - adr-2606022400-session-close-himawari-r1-adr-and-coverage-maturation
  - adr-2606013400-funadaiku-zero-emission-cargo-shipbuilding-r0
  - adr-2605252500-sarutahiko-heavy-truck-manufacturing-r0
  - doc-2606022500-organism-axis-affiliation-convention
  - adr-2605221411-etzhayyim-artificial-organism-ecosystem
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606022400 (prior session-close — this continues the maturity+coverage sweep)
---

# ADR-2606022601: Session close — R0-actor coverage sweep (funadaiku/sarutahiko) + organism-axis affiliation convention

**Date**: 2026-06-02
**Status**: ACTIVE (documentation-only session closure)
**Deciders**: Jun Kawasaki

## Context

Continuation after ADR-2606022400. The operator picked the offered next steps
**"1, 2, 3, 4"** — extend the maturity+coverage sweep to sibling R0 manufacturing
actors, finish funadaiku's voyage-energy coverage, pivot one topo-sort Layer-0 item,
and record it all. Work spans funadaiku, sarutahiko, and the three already-matured
actors. (A concurrent background /loop continued committing to the shared dev branch
throughout; one commit had to be retried after a git-lock race — no work lost.)

## Decision (what shipped)

1. **sarutahiko coverage (was 0 tests) — `4a3ccadd1`.** `cells/test_state_machines.py`
   (3 tests), generic over all 9 cells via dataclass introspection (each cell has its
   own `<X>State` dataclass + `<x>_state` key + enum `Phase`, seeded from required
   fields): every state machine transitions INIT→…→100% with valid enum phases +
   monotone-distinct completionPct; a cell-set drift guard; **plus the constitutional
   G7 powertrain fuel-guard** (accepts `H2-fuel-cell`, rejects `pure-diesel`). All 9
   `state_machine.py` 0→**100%**. The R0 `.solve()` RuntimeError gate is **preserved** —
   the tests never call `solve()`, so Council ADR-2605252515 activation is not bypassed.

2. **funadaiku voyage-energy completion — `4a3ccadd1` (with `1ca59aee7`).** Added
   `test_main_writes_report_and_edn_artifacts`; `methods/voyage_energy.py` 78→**99%**
   (only the `__main__` guard remains). The G13/N5 zero-emission invariant (fossil=0,
   wind+solar+H₂≈100%, green-H₂>0, Admiralty cube law) stays empirically locked.

3. **Organism-axis affiliation convention (Sanctification axis #10) — `2ef0ea5ec`.**
   Root README's standing action "propagate organism-axis affiliation to 39 first-party
   package READMEs" was advanced via an **SSoT convention doc**
   (`90-docs/2606022500-organism-axis-affiliation-convention.md`) defining the one-line
   `**Organism axis**:` declaration + the 10-axis table + an incremental propagation
   checklist — so the 39-README rollout is a drift-free mechanical edit, not 39
   inventions. Applied the line to the **first 3-actor slice** (himawari / funadaiku /
   sarutahiko, all Axis 2 — Metabolism 代謝/産霊); remaining ~36 packages are the
   documented follow-up.

## Consequences

- Three R0 actors' real logic (state machines + voyage model) is regression-locked
  without touching their constitutional `.solve()` activation gates.
- The Sanctification 39-README task is now a single-line, single-SSoT mechanical
  follow-up that any session can extend one package at a time.
- **Honest caveats**: coverage measured via an uncommitted local `coverage` venv;
  every actor's `cell.py` Pregel wrapper stays import-smoke-only because this env's
  langgraph is broken by a pydantic/pydantic-core version mismatch (documented in each
  CLAUDE.md); funadaiku/sarutahiko have no `[[modules]]` entry in deps.toml, so only the
  ADR registry is updated here.

## Alternatives Considered

- **Blindly edit all 39 READMEs for the Sanctification axis.** Rejected — high
  collision risk with the active background /loop, and it would hard-code a 39-package
  convention without an SSoT. The convention-doc + 3-actor proof slice is safer and
  makes the rest mechanical.
- **Implement the gated `.solve()` bodies to lift cell.py coverage.** Rejected —
  that would bypass the R0 constitutional activation gates (Council per-actor R1 ADRs);
  testing the langgraph-free real logic is the charter-respecting path.

## References

- `90-docs/2606022500-organism-axis-affiliation-convention.md` — Sanctification SSoT
- `90-docs/adr/2606022400-session-close-himawari-r1-adr-and-coverage-maturation.md` — prior close
- `20-actors/funadaiku/` + `20-actors/sarutahiko/` — CLAUDE.md test sections updated
- Commits: `1ca59aee7` (funadaiku) · `4a3ccadd1` (sarutahiko + funadaiku main) · `2ef0ea5ec` (organism axis)
