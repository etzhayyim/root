---
id: adr-2606035000
title: "Session close — labor-liberation OSS-robotics actor wave + Displacement Dividend + concurrent-tree recovery"
status: active
doc_type: adr
topic: session-close-labor-liberation-robotics-wave
authoritative: true
last_verified: 2026-06-03
authoritative_for:
  - session-close record for the labor-liberation robotics-actor wave (2026-06-03)
related:
  - adr-2606032100
  - adr-2606032130
  - adr-2605173100
  - adr-2605172000
supersedes: []
superseded_by: []
depends_on:
  - ADR-2606032100 (Robotics-Actor Wave)
  - ADR-2606032130 (Displacement Dividend)
---

# ADR-2606035000: Session close — labor-liberation OSS-robotics actor wave + Displacement Dividend + concurrent-tree recovery

**Date**: 2026-06-03
**Status**: ACTIVE (session-close record)
**Deciders**: Jun Kawasaki

## Context

Session goal: answer *「今の全世界カバレッジの actor 設計で、OSS・robotics になっていない領域を OSS+robotics にすると人類の労働解放が促進する、を ISIC/ISCO/UNSPSC で順位付けして」* and *「public fund として、従事者を robotics で置き換えた時に勤続年数に応じた income が分配されるよう設計して」*. Then a `/loop` maturation pass, and git persistence.

## Decision / what landed

### Design (committed + pushed)

- **ADR-2606032100** — Labor-Liberation Robotics-Actor Wave. Ranked the un-automated toil by Liberation Priority Score (LPS = headcount × misery × automatability × charter_fit × coverage_gap). The robotics gap maps almost entirely onto **ISCO major groups 6–9**; ISCO 1–4 is already software-liberated by the concierge/intel actors. Opened the top-3 zero-coverage / highest-misery actors at R0 and roadmapped #4–#12.
- **ADR-2606032130** — Displacement Dividend. Tenure-weighted (勤続年数) **in-kind** Basic High Income for workers freed by etzhayyim OSS-robotics, with **zero invariant amendments**: cash≡0 (N1), no-payroll, donation-only, conversion-gated all preserved. `w_i = ln(1+min(tenure,40)) × hazard`; `share` governs onboarding priority + a stage-capped 5-year-decay transition floor, never a cash split. Funded by the displacing actor's own surplus → donation → TitheRouter → per-cohort Public-Fund earmark.

### Actors (R0, funadaiku pattern; `.solve()`→RuntimeError; `:representative`)

| Actor | Domain | ISIC / ISCO / UNSPSC | Defining gate | Coded cell |
|---|---|---|---|---|
| **sanae 早苗** | field agriculture (LPS #1) | A01 / 6111,9211 / 70 | G9 regenerative / herbicide-free | autonomous_weeding (5/5) |
| **hataori 機織** | garment (LPS #2) | C13-14 / 7531 / 53 | G9 fair-labor-provenance + G2 | finishing_packing (6/6) |
| **kiyome 清め** | cleaning (LPS #3) | T,N81 / 9112 / 76 | G9 privacy-by-construction | surface_cleaning (7/7) |

Each ships one coded reference cell that enforces its constitutional gate in **executable code** (herbicide rejection / dividend-coupling / on-device-privacy). The **G2 displacement-dividend coupling gate** is the wave-defining invariant: no actor may displace human labour live without a funded tenure-weighted cohort.

### Dividend artifacts

- `00-contracts/lexicons/com/etzhayyim/give/displacementTenureAttestation.json` (cash field `const 0`)
- `50-infra/etzhayyim-chain-contracts/src/DisplacementDividend.sol` (R0 revert-stub + `payoutToSubject` tripwire → always reverts)
- `50-infra/etzhayyim-public-fund/displacement/allocate.py` reference allocator
- `20-actors/_conformance/test_lexicon_consts.py` cross-actor lexicon-const guard

**Tests 39/39 green**: allocator 10 · LPS 7 · sanae 5 · hataori 6 · kiyome 7 · conformance 4.

### `/loop` maturation (2 iterations before STOP)

Self-paced `/loop` (15-min cron) ran two maturations — hataori `finishing_packing` and kiyome `surface_cleaning` coded cells (13 tests) — then was **stopped** (`CronDelete`) on discovering the work-tree wipe (below). The matured cells are part of the committed wave.

### git persistence

- Branch `feat-labor-liberation-robotics-wave` + tag `labor-liberation-robotics-wave` → **pushed to `origin`** (commits `5ee50d0141` wave + `7d331e70b5` deps.toml registration + this close). Durable on GitHub.

## Meta-findings (honest)

1. **Concurrent shared working tree.** Multiple sessions operated in the same checkout simultaneously; branch switches + resets to `main` **wiped this session's untracked work twice**. Recovery: regenerated everything from conversation context, committed to a dedicated branch, pinned with a tag, and pushed. **Lesson: each parallel session needs its own `git worktree`** — the root cause of the churn. All this session's durable work was made on an isolated worktree off the pinned branch.
2. **Robotics coverage is ~0% real.** The 3 actors are R0 design/governance scaffolds; no kinematics/perception/manipulation/controllers. The real engine (`kami-engine`: kami-genesis solver, kami-autodrive GNC) is a submodule **not populated in this tree** (partial/foreign checkout at `40-engine/kami-engine` blocked a clean init; the actual solver crates are absent). What exists repo-wide is physics *simulation* (factory/voyage sims) + vehicle GNC — no hardware, no sim-to-real.
3. **Active inference exists but is unwired to robotics.** Genuine Friston discrete-POMDP AIF lives in `pymagatama/primitives/rl_active_inference.py` (variational + expected free energy) and the `etzhayyim-organism` Axis 4 — but it is lexical/symbolic agent reasoning, not motor control, and the labor-liberation actors do not call it. Wiring it into the R1 cell solvers (POMDP + small on-device generative models, aligned with Murakumo-only + baien edge-target) is the principled R1 path.
4. **Kotoba/Datomic-free reaffirmed.** Per owner directive + ADR-2605172000: the legacy `60-apps/etzhayyim-project-recap/` (psycopg/Kotoba/Datomic, with the `rw_…` placeholder credential class of ADR-2605173100) was **excluded then removed** from the tree. The credential is a documented placeholder (real RW root already rotated, ADR-2605173100 §61/§18) — no rotation needed. A clean manako/unspsc subset was committed+pushed separately on `feat/sumitsubo-cad-interop`.

## Consequences

The labour-liberation mission now has an explicit **two-layer roster shape** (ISCO 1–4 = software/knowledge actors, ISCO 6–9 = robotics actors) with the top robotics gaps opened and a reusable G2 coupling gate ensuring automation funds the humans it frees. The robotics *body* is unbuilt — R1 begins with `kami-engine` re-init → run one cell (e.g. 草薙 weeding) on kami-genesis physics + `rl_active_inference` POMDP.

## Next session starting point

1. `rm -rf 40-engine/kami-engine && git submodule update --init --recursive 40-engine/kami-engine` (when the tree is quiet — destructive on the partial dir).
2. R1 PoC: wire sanae `autonomous_weeding` cell solver to kami-genesis + `rl_active_inference`.
3. Open ADR-2606032100 #4–#5 (kamado food-service, kuramori warehouse).
4. Use isolated `git worktree` per session to avoid the contention that wiped work this session.

## References

- ADR-2606032100 (Robotics-Actor Wave) · ADR-2606032130 (Displacement Dividend)
- ADR-2605173100 (GitGuardian RW credential incident — placeholder finding)
- ADR-2605172000 (RW-free substrate) · ADR-2605215000 (Murakumo-only inference)
- ADR-2605261000 (Liberation Ladder) · ADR-2605301020 (Basic High Income)
