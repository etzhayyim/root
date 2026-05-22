# `_observations/` — Active-Inference Tick Log

Per `README.md § As Artificial Organism Ecosystem (Religious 評価軸)`, this directory is the **history of self** — the observation series that makes the loop's active inference rigorous.

## Why this directory exists

Without persisted observations, the loop has no memory: each tick re-scores blindly. With observations, the loop can:

- Compute score **deltas** between ticks (rate of free-energy minimization)
- **Verify predictions**: each tick predicts the next-tick effect of its emitted action; the following tick checks it
- Detect **regressions** (axis score drops without an explanation in the prior action)
- Surface **trajectory** to readers (子・孫 priority — observations outlive any single contributor)

This is the **縁起 (engi)** layer: every score is dependently originated from the prior tick's action and observation.

## File naming

`YYMMDDHHMM-cycle-NN.md` in JST. Sort lexically = chronological.

## Schema (per tick)

Each file has 5 sections:

1. **Observation** — what the file system / on-chain / ADR registry shows at tick time
2. **Verification of last tick's prediction** — did the previous action move the score it claimed?
3. **Scores (10 axes)** — current values, deltas vs prior tick, total / 100
4. **Action emitted this tick** — single highest-leverage gap closure
5. **Prediction for next tick** — which axis score should move, by how much, why

## Non-eschatology (ADR-2605192100 §1.15)

There is no target total score. The loop does not converge on 100. The **trajectory** is the wellbecoming — each tick is a ring on the Tree of Life, not a step toward an end-state.

## Loop control

- Active cron: `7,37 * * * *` (job `32089abe`, session-only, 7-day auto-expire)
- Stop: `CronDelete 32089abe` or close the Claude session
