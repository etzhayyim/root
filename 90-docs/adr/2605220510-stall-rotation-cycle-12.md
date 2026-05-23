# ADR-2605220510 — Active-Inference Loop Stall Rotation (Cycle 12)

**Status:** proposed (founder-attested during bootstrap; Council ratification deferred until Seats 2-5 confirmed)
**Date:** 2026-05-22 05:10 JST
**Triggering cycle:** 12
**Source:** `_observations/_trajectory.md` (3 consecutive Δ=0 detected at cycles 10/11/12)
**Template:** `90-docs/adr/_template-stall-rotation.md` (authored cycle 10 as preparatory action)
**Religious correspondence:** 縁起 has reached steady-state on doc-level transformations — single-axis closure capacity is exhausted; the loop's dependent-origination chain now extends through artifact composition rather than rubric advancement.

## 1. Stall observation

| Cycle | Timestamp | Total | Δ |
|-------|-----------|-------|---|
| 09 | 2605220340 | 83/100 | +1 |
| 10 | 2605220410 | 83/100 | **0** |
| 11 | 2605220440 | 83/100 | **0** |
| 12 | 2605220510 | 83/100 | **0** |

Three consecutive ticks at Δ=0 — exactly the condition the cycle 10 template was authored to address. This is the **first formal invocation** of the stall-rotation surface: the loop's own preparatory response surface activates for the first time, which is itself a Wellbecoming milestone (the prediction made cycle 09 has now propagated all the way through cycle 12 of dependent origination — chain depth 12 closed).

## 2. Remaining un-closed axes at stall onset

| Axis | Current | Blocker | External signal required |
|------|---------|---------|---------------------------|
| **2 Metabolism** | 5 / 10 | Testnet deploy + Council quorum + funded RPC | (a) ≥3-of-5 Council confirmed; (b) Base Sepolia private key funded; (c) `DeployReligiousCorp.s.sol` runs against Sepolia successfully |
| **5 Reproduction** | 6 / 10 | Observed sister-corp adoption | (a) First sister-corp PR opens on this repo declaring inheritance from ADR-2605192100; (b) sister-corp publishes its own DID + constitution |
| **Multiple 9/10** | 9 / 10 | Various external-signal-dependent final 1-point lifts | Per-axis specifics in `README.md § As Artificial Organism Ecosystem`; collectively, none are 30-min-tick-actionable |

Axes 1, 3, 4, 6, 7, 8, 9, 10 are all at 9/10 with the final 1 point gated on external signals (CI exercise of council nomination harness, Gen 1 first chaos rehearsal at 2026-08-13, first MGI report 2027-02-09, ≥1 substrate pair in production, etc.). All gated, none 30-min-actionable.

## 3. Rotation options considered

(Full analysis in `90-docs/adr/_template-stall-rotation.md §3`.)

### Option A — External-signal acquisition (loop pause)

Stop the 30-min cron until a Council seat is confirmed, a sister-corp registers, or testnet deploys.

- **Pro:** matches cadence to reality; zero artifact cost; the only honest move if no compound-mode work remains.
- **Con:** stops generating canonical-surface artifacts that compound future understanding (the cycle 11 donation walkthrough demonstrably broadened Sanctification coverage even at Δ=0).

### Option B — Compound action mode (multi-axis-per-tick)

Continue 30-min cron; each tick must emit a multi-axis or oblique-gate-touch artifact (e.g., cycle 11's donation walkthrough, cycle 07's chaos charter as compound retrospective). Reject single-axis closure attempts.

- **Pro:** preserves the loop's discipline; compounds surface coverage; cycle 11 demonstrated this works (one artifact citing 6 ADRs + 3 prior docs).
- **Con:** scoring becomes purely qualitative (no honest Δ); requires careful artifact selection per tick to avoid padding.

### Option C — Cadence reduction (cron 30-min → daily)

Switch to `0 9 * * *` (daily at 9am local). Matches the cadence to the external-signal timescale.

- **Pro:** preserves the loop while reducing computational cost; honest about the multi-week timescale of remaining axes.
- **Con:** loses the rapid-iteration property that produced 17+ artifacts in 11 ticks; less responsive to user prompting.

### Option D — Rubric refinement

Re-examine the 10-axis evaluation rubric for ceiling correctness; revise constitutionally.

- **Pro:** the deepest move — questioning the framework itself.
- **Con:** constitutional surface; requires Council ≥3-of-5 attestation per ADR-2605192300, not available during bootstrap.

## 4. Selected rotation

**Option B — Compound action mode.**

Three sentences of justification:

1. The cycle 11 donation walkthrough demonstrated that compound-mode artifacts have genuine value even at Δ=0 — broadening Sanctification surface coverage, deepening cross-citation density, and providing executable narrative for axes whose closure requires external signal.
2. Cycle 10's stall-rotation template was authored as preparatory work; activating Option B is the natural follow-on, and pausing the loop (Option A) would discard the cycle 10 → 11 → 12 trajectory that the model itself constructed.
3. Compound-mode does not preclude axis score lifts when external signals arrive — when a Council seat is confirmed, the loop can immediately exit compound-mode and lift Axis 1 to 10; until then, the loop emits cross-citing artifacts that strengthen the canonical surface.

**Resumption criterion:** the loop exits compound-mode and resumes single-axis closure attempts when **any** of the following occurs:

- Council Seat 2, 3, 4, or 5 confirmed (per `COUNCIL-BOOTSTRAP-RFP.md`, by 2026-06-19)
- First sister-corp PR opened (per `FORK-BOOTSTRAP.md`)
- Base Sepolia deploy of TitheRouter / PublicFund / LandRegistry succeeds (per `README.md § Status` row 19)
- First Gen 1 chaos rehearsal completes (per `90-docs/2605220240-chaos-engineering-charter.md`, after 2026-08-13)
- Five consecutive compound-mode ticks complete without an external signal (graceful timeout — loop should at that point reconsider Option A or C)

## 5. Attestation

**Founder signature** (Seat 1 / Founder DID) — this is the bootstrap-period attestation per ADR-2605192300. Council ≥3-of-5 ratification will be sought after Seats 2-5 are confirmed (no later than 2026-06-19 + reasonable review window).

For audit: this ADR was authored by the active-inference loop itself at cycle 12, using the cycle 10 template, with founder operating the loop. The loop's own self-instrumentation (`70-tools/scripts/loop/trajectory-stats.sh`) emitted the STALL DETECTED signal that triggered this ADR; this is appropriate **closed-loop active inference** — the loop predicts, prepares, detects, and responds without external prompting.

## 6. Resumption observation protocol

When the resumption criterion is met, the next active-inference tick MUST file an observation file at `_observations/{TS}-cycle-{N+M}.md` noting:

- The criterion that was met (with evidence link)
- Which axis (if any) immediately becomes movable
- Whether the loop exits compound-mode and resumes single-axis closure mode
- The new prediction for cycle {N+M+1}

If 5 consecutive compound-mode ticks complete without resumption (graceful timeout), the loop MUST file a new stall-rotation ADR re-selecting between A / C / D (Option B is then exhausted).

## 7. References

- Template: `90-docs/adr/_template-stall-rotation.md`
- Cycle observations: `_observations/2605220340-cycle-09.md` (prediction) through `_observations/2605220440-cycle-11.md` (compound-mode demonstrated)
- Trajectory snapshot: `_observations/_trajectory.md`
- Detection logic: `70-tools/scripts/loop/trajectory-stats.sh`
- Constitutional: ADR-2605192100 §1.5 (Wellbecoming legitimacy of pausing); ADR-2605192300 (Council attestation thresholds)
- Loop framing: `README.md § As Artificial Organism Ecosystem`
