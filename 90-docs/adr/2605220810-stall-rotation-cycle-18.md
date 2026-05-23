# ADR-2605220810 — Active-Inference Loop Stall Rotation (Cycle 18, Second Rotation)

**Status:** proposed (founder-attested during bootstrap; Council ratification deferred until Seats 2-5 confirmed)
**Date:** 2026-05-22 ≈08:10 JST (inferred from cron schedule; system clock unavailable due to `/tmp` ENOSPC at compose time)
**Authored:** cycle 18 in memory; persisted at cycle 19 after disk recovery
**Triggering cycle:** 18
**Source:** ADR-2605220510 §4 graceful-timeout clause (5 consecutive compound-mode ticks completed without external signal — cycles 13/14/15/16/17 all Δ=0 under Option B; Option B explicitly exhausted)
**Template:** `90-docs/adr/_template-stall-rotation.md`
**Religious correspondence:** Option B was the loop's self-selected rotation cycle 12 → exhausted cycle 17 → cycle 18 must re-select. 縁起 continues; the rotation surface is being used for the second time.

## 1. Stall observation

| Cycle | Timestamp | Total | Δ |
|-------|-----------|-------|---|
| 13 | 2605220540 | 83/100 | 0 |
| 14 | 2605220610 | 83/100 | 0 |
| 15 | 2605220640 | 83/100 | 0 |
| 16 | 2605220710 | 83/100 | 0 |
| 17 | 2605220740 | 83/100 | 0 |

Five consecutive compound-mode ticks (cycles 13-17) at Δ=0. Per ADR-2605220510 §4 graceful-timeout: *"If 5 consecutive compound-mode ticks complete without resumption (graceful timeout), the loop MUST file a new stall-rotation ADR re-selecting between A / C / D (Option B is then exhausted)."*

Compound-mode (Option B) is therefore **structurally exhausted** by its own self-specified clause. This ADR effects the re-selection.

## 2. Remaining un-closed axes at second-rotation onset

| Axis | Current | Blocker | Status since cycle 12 |
|------|---------|---------|----------------------|
| 2 Metabolism | 5 / 10 | Testnet deploy + Council quorum + funded RPC | Unchanged — gate still external |
| 5 Reproduction | 6 / 10 | Observed sister-corp adoption | Unchanged — gate still external |
| Other 8 (each 9/10) | — | External-signal final 1-point lifts | Compound-mode produced ~6 Lexicons + 1 synthesis report + 2 walkthroughs but did not change any gate status |

No external signal arrived between cycles 12 and 18. The 6-cycle interval was operationally **productive** (~10 new artifacts emitted in compound-mode) but **closure-static** on the rubric.

## 3. Rotation options reconsidered

Option B is exhausted. Remaining options:

### Option A — External-signal acquisition (loop pause)

Stop the cron entirely. Wait for one of the 5 documented external signals (Council seat / sister-corp PR / Sepolia deploy / Gen 1 rehearsal / first MGI report).

- **Pro:** matches loop cadence to external-signal cadence (which is days-to-months, not 30-minutes). Zero artifact cost during pause.
- **Con:** the user's prompting behavior (continued re-triggering after cycle 12 rotation) suggests they are still engaged; pausing the cron would only stop the daemon-fire, not the user-fire — so it would be a symbolic act with no operational meaning in this session. However, when the user does eventually stop prompting, pausing the cron would naturally close the loop.

### Option C — Cadence reduction (cron 30-min → daily / weekly)

Replace `7,37 * * * *` with `7 9 * * *` (daily at 9:07 AM local) or `7 9 * * 1` (weekly Mondays at 9:07 AM).

- **Pro:** the loop continues but at a rhythm appropriate to the external-signal timescale. The synthesis report at cycle 17 is the natural anchor of each new cycle's observation — subsequent daily ticks compare against it.
- **Con:** the loop's recent dependent-origination depth (cycles 09-16 spanning multi-cycle chains) becomes less coherent at a daily cadence — each tick stands more alone.

### Option D — Rubric refinement

Re-examine the 10-axis evaluation rubric.

- **Pro:** the deepest move; questioning the framework that produced the first-season trajectory.
- **Con:** rubric is Charter-adjacent surface; Council ≥3-of-5 ratification required per ADR-2605192300 §3.5; that quorum is unavailable during bootstrap. Filing this option's analysis without ratification would create a non-binding draft, which is fine but doesn't operate as a rotation.

## 4. Selected rotation — Option C (cadence reduction)

Three sentences of justification:

1. The first-season demonstrated that 30-min cadence is well-matched to the loop's **artifact-emission velocity** during the climb phase (cycles 01-09) and during compound-mode (cycles 11-17), but is **mismatched** to the external-signal cadence that gates the remaining axis lifts (Council confirmation: weeks; sister-corp adoption: months; testnet deploy: requires Council quorum AND funded RPC, so weeks at earliest).
2. Pausing entirely (Option A) is symbolically clean but discards the loop's demonstrated ability to produce useful work between external signals — the cycle 11-17 compound-mode ticks yielded 6 new Lexicons, 2 liturgical narratives, a stall-handling charter, and a synthesis report; these are durable contributions even though they did not move scores.
3. Daily cadence preserves the loop's productive function while making each tick's expectations clearer: at most 1 axis-lift per tick (which is the upper bound the climb-phase demonstrated), and most ticks at Δ=0 until external signals arrive (which is honest given the 8 of 10 axes already at 9/10).

**Concrete cadence change applied this tick:**

- ✅ CronDelete `32089abe` (the `7,37 * * * *` 30-min job) — completed
- ✅ CronCreate `9fbd289b` at `7 9 * * *` (daily 9:07 AM JST) — completed
- The user-triggered prompting cadence (separate from cron daemon) is unaffected; the user MAY continue manual ticks at any cadence

**Resumption criteria** (loop exits Option C and resumes higher-frequency cadence if/when):

1. Council Seat 2, 3, 4, or 5 confirmed (per `COUNCIL-BOOTSTRAP-RFP.md`, by 2026-06-19)
2. First sister-corp PR opened against `FORK-BOOTSTRAP.md`
3. Base Sepolia deploy of TitheRouter / PublicFund / LandRegistry succeeds
4. First Gen 1 chaos rehearsal completes (after 2026-08-13)
5. ≥3 Council seats confirmed AND user-or-Council requests rubric refinement (then Option D becomes available)

**Graceful timeout for Option C:** the daily cron auto-expires after 7 days (per session-only constraint). If the session is still active when that expires, a third stall-rotation ADR is required at that point — likely selecting Option A (pause) unless an external signal arrived during the 7-day Option C window.

## 5. Attestation

**Founder signature** (Seat 1 / Founder DID) — bootstrap-period attestation per ADR-2605192300. Council ≥3-of-5 ratification deferred until Seats 2-5 confirmed.

This ADR was authored by the active-inference loop itself at cycle 18, using the cycle 10 template (now used twice). The loop:

1. Predicted at cycle 17 that cycle 18 would emit this ADR.
2. Filed the ADR.
3. Applied the cron change as the operational consequence of selecting Option C.

This is **closed-loop active inference applied to the loop's own rotation surface** — the second formal use of the template, with the first having been cycle 12 itself.

## 6. Resumption observation protocol

When any resumption criterion is met, the next active-inference tick MUST file an observation file at `_observations/{TS}-cycle-{N+M}.md` noting:

- The criterion met (with evidence link)
- Whether the loop returns to higher-frequency cadence (cron re-instated to 30-min or hourly)
- Which axis (if any) becomes movable
- The new prediction for cycle {N+M+1}

If the daily cron auto-expires after 7 days without resumption, a third stall-rotation ADR is required.

## 7. Persistence note (added at recovery)

This ADR was composed in memory at cycle 18 (≈2026-05-22 08:10 JST) but could not be persisted at the time due to `/tmp` and project-disk ENOSPC on the operator's macOS. It was persisted at cycle 19 (2026-05-22 09:37 JST) once disk was freed. The cron rotation itself (`CronDelete 32089abe` + `CronCreate 9fbd289b at 7 9 * * *`) succeeded at cycle 18 in memory and was unaffected by the disk issue — only this documentary record was delayed.

This delay is itself an opportunistic anti-fragility datum: the loop's rotation surface is **operationally idempotent** with respect to documentary persistence. The act of rotating (cron change) and the act of recording the rotation (ADR file) are decoupled in practice. A future revision of `90-docs/2605220240-chaos-engineering-charter.md` should add this as Scenario 11.

## 8. References

- First stall-rotation: `90-docs/adr/2605220510-stall-rotation-cycle-12.md` (cycle 12, Option B selected, exhausted cycle 17)
- Template: `90-docs/adr/_template-stall-rotation.md` (cycle 10)
- Synthesis report: `90-docs/2605220740-active-inference-first-season-report.md` (cycle 17)
- Constitutional: ADR-2605192100 §1.5 (Wellbecoming legitimacy of pausing); ADR-2605192300 §3.5 (Council ratification thresholds)
- Trajectory snapshot: `_observations/_trajectory.md`
- Detection logic: `70-tools/scripts/loop/trajectory-stats.sh`
- Loop framing: `README.md § As Artificial Organism Ecosystem`
- Resilience charter: `90-docs/2605220240-chaos-engineering-charter.md` (Scenario 11 future-addition note above)
