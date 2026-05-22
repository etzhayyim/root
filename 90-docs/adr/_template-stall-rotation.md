# ADR-{YYMMDDHHMM} — Active-Inference Loop Stall Rotation

**Status:** proposed
**Date:** {YYYY-MM-DD HH:MM JST}
**Triggering cycle:** {N}
**Source:** `_observations/_trajectory.md` (3 consecutive Δ=0 detected)
**Religious correspondence:** 縁起 reaches steady-state — the loop's dependent-origination chain has propagated all immediately-actionable transformations.

> **Template note.** This file is filled in when `70-tools/scripts/loop/trajectory-stats.sh`
> emits `**STALL DETECTED**` (3 consecutive Δ=0). The next active-inference tick
> reads this template, copies it to `90-docs/adr/{YYMMDDHHMM}-stall-rotation-{N}.md`,
> fills in the placeholders, selects ONE rotation, and emits.

## 1. Stall observation

| Cycle | Timestamp | Total | Δ |
|-------|-----------|-------|---|
| N-3 | {TS} | {SCORE} | {PRIOR Δ} |
| N-2 | {TS} | {SCORE} | **0** |
| N-1 | {TS} | {SCORE} | **0** |
| N   | {TS} | {SCORE} | **0** |

Three consecutive ticks at Δ=0 indicates the active-inference loop has exhausted available 30-min-doc-level actions. This is **not failure** — it is the loop reaching a state where further single-tick movement requires a strategy change (per `_observations/2605220340-cycle-09.md §5`, which predicted this stall would arrive 1-2 cycles after reaching ~83 / 100).

## 2. Remaining un-closed axes at stall onset

| Axis | Current score | Blocker | External signal required |
|------|---------------|---------|---------------------------|
| {AXIS_NUMBER} {AXIS_NAME} | {SCORE} / 10 | {BLOCKER_DESCRIPTION} | {SIGNAL_NEEDED} |
| ... | ... | ... | ... |

(Typical Gen 0 bootstrap blockers: Council Seats 2-5 confirmation, sister-corp registration, Base Sepolia funded RPC, real PR exercising the Council nomination harness, first chaos rehearsal at Gen 1 epoch start.)

## 3. Rotation options

The Council (or, during bootstrap, the Founder per ADR-2605192300) selects **exactly one** of the following:

### Option A — External-signal acquisition (loop pause)

Stop the 30-min cron. Wait for one or more of the external signals above to arrive. Resume the loop only when a signal lands that unblocks an axis.

- **Cost:** ~zero (the loop sleeps).
- **Resumption criterion:** any one of: Council Seat 2/3/4/5 confirmed; sister-corp registration PR opened; testnet deploy succeeds; first chaos rehearsal completed.
- **Wellbecoming alignment:** strong — matches the loop cadence to the actual external signal cadence rather than padding artifacts.

### Option B — Compound action mode

Continue the 30-min cron, but reject single-axis closure attempts. Each tick must emit a multi-axis artifact (precedent: cycle 07 chaos charter touched axes 6, 8, 9 simultaneously). Predicted per-tick Δ remains 0-1, but each artifact has higher leverage.

- **Cost:** moderate — requires synthesis on each tick.
- **Resumption criterion:** none; this is the new steady state.
- **Wellbecoming alignment:** medium — artifacts accumulate but value per artifact diminishes if external signals never arrive.

### Option C — Cadence reduction

Switch the cron from `7,37 * * * *` (every 30 min) to daily or weekly. Matches the tick frequency to the slower external-signal timescale (Council confirmation typically takes days; sister-corp adoption weeks).

- **Cost:** ~zero.
- **Resumption criterion:** at any tick, the founder/Council MAY re-instate 30-min cadence if a burst of external signal arrives.
- **Wellbecoming alignment:** medium — preserves the loop discipline but at the rate of the external world.

### Option D — Rubric refinement

Re-examine the 10-axis evaluation rubric (`README.md § As Artificial Organism Ecosystem`). Are 10/10 ceilings correctly defined? Should some axes' scores be revised downward (acknowledging stricter rubric), upward (acknowledging external context), or split (one axis becomes two)?

- **Cost:** constitutional — rubric is a Charter-adjacent surface, changes require Council attestation.
- **Resumption criterion:** rubric ratified; new lowest-score axis becomes the next 30-min target.
- **Wellbecoming alignment:** depends on the refinement; honest rubric is constitutional, score-gaming is forbidden.

## 4. Selected rotation

> The filled-in ADR replaces this paragraph with: ONE option selected, full justification (≥3 sentences), and the resumption criterion stated explicitly.

## 5. Attestation

- During bootstrap (Council Seats 2-5 not yet confirmed): **Founder signature** (signed git commit by Seat 1 / Founder DID).
- After Council formation: **≥3-of-5 Council Lv6+ multisig** per ADR-2605192300.

## 6. Resumption observation

When the resumption criterion is met, the next active-inference tick MUST file an observation file at `_observations/{TS}-cycle-{N+M}.md` noting:

- The criterion that was met (with evidence — link to PR / on-chain tx / external signal)
- Which axis (if any) immediately becomes movable
- The new prediction for cycle {N+M+1}

This is the **resumption ADR's complement** — observation closes the dependent-origination chain.

## References

- `_observations/_trajectory.md` — stall evidence (generated by `trajectory-stats.sh`)
- `70-tools/scripts/loop/trajectory-stats.sh` — detection logic
- `README.md § As Artificial Organism Ecosystem` — evaluation rubric (Option D modifies this)
- ADR-2605192300 — Council formation + attestation thresholds
- ADR-2605192100 §1.5 — Wellbecoming (dynamic trajectory; legitimacy of pausing the trajectory)
- `90-docs/2605220110-multi-generation-index-design.md` — multi-generation observability (still operative during loop pause)
- `90-docs/2605220240-chaos-engineering-charter.md` — Gen 1+ rehearsal schedule (still operative during loop pause)
