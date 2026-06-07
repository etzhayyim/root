---
id: adr-0066-magatama-organizer-shinka-shannon-bayes
title: "ADR-0038: Magatama Organizer — joucho Shinka × Shannon Optimization × Bayesian Evaluation"
status: accepted
doc_type: adr
topic: magatama-organizer
authoritative: true
last_verified: 2026-04-20
related:
  - adr-0034-agent-cron-goose-kotoba-direct
supersedes: []
superseded_by: []
---

# ADR-0038: Magatama Organizer — joucho Shinka × Shannon Optimization × Bayesian Evaluation

| Field | Value |
|---|---|
| Status | **Accepted** (implemented 2026-04-20) |
| Supersedes | — |
| Extends | ADR-0034 (agent-cron-goose-kotoba-direct) |
| Authors | jun + Claude Opus 4.7 |
| Depends on | murakumo v4.1.0 (LiteLLM gateway), goose cron wrapper, Kotoba/Datomic |

## Context

The magatama platform (`magatama.etzhayyim.com`) surfaces goose agent activity from
the Mac mini fleet. ADR-0034 wired goose runs into Kotoba/Datomic via the
`vertex_repo_commit` table with a deterministic cron wrapper. This left one
question open: **how should the platform pace itself as more agents and
recipes come online**?

Three prior signals were already in the system:

1. **joucho shinka heartbeat** (`magatama:magatama/shinka@1.0.0`) — a
   per-actor emotional cadence derived from mood and inbox buffer.
2. **goose cron wrapper** — reads `vertex_actor_shinka_state.cadence_ms`
   and throttles fires accordingly. The column was free-form.
3. **vertex_repo_commit** — append-only log of every successful goose run.

None of these has any notion of *repo-wide balance*, *recipe health under
uncertainty*, or *autonomous adaptation to load*. Without such a governor
the fleet drifts toward whichever recipe happens to be scheduled aggressively,
accumulating redundant signal and starving quieter recipes.

## Problem

Given an arbitrarily growing set of {agent DID × collection} recipes, decide
— every 5 minutes, without human input — how fast each recipe should fire,
which recipes should be archived, and how to balance load so that the fleet
produces *maximally informative* commit streams under a finite throughput
budget.

Formally: the organizer chooses a cadence vector **c** ∈ ℝ₊ⁿ that maximises

    J(c) = Σᵢ wᵢ · posteriorHealthᵢ(c)  +  λ · entropy(c)  −  μ · saturation(c)

subject to a fleet capacity constraint and a joucho-driven per-recipe floor.

## Decision

Introduce a **repo-wide organizer** inside the `magatama.etzhayyim.com` Worker
with three plug-in signals — Bayesian health, Shannon entropy, joucho cadence
— fused into a single cadence decision per recipe, plus an LLM-synthesised
narrative layer for humans. Persist the decision in
`public.vertex_actor_shinka_state (repo_did, collection)`; the goose cron
wrapper consumes it on the next tick.

### Components

```
 ┌─ signals ─────────────────────────────────────────────────────────────┐
 │  S1 Bayesian health        posterior = Beta(α+actual, β+expected−actual)│
 │  S2 Shannon entropy        H(c) = −Σ pᵢ log₂ pᵢ, pᵢ = runsᵢ / Σrunsⱼ   │
 │  S3 joucho shinka cadence  per-actor emotional baseline (lower bound)  │
 │  S4 fleet capacity         obs req/min ÷ capacity req/min = saturation │
 └───────────────────────────────────────────────────────────────────────┘
             ↓   (every 5 min)
 ┌─ organizer (CF Worker scheduled handler) ─────────────────────────────┐
 │  classify → {hot, normal, stale, silent, archived}                     │
 │  assign base cadence from priority class                               │
 │  if saturation > 1 → stretch non-hot cadences by saturation ratio      │
 │  respect joucho floor: cadenceᵢ = max(cadenceᵢ, jouchoFloorᵢ)          │
 │  auto-archive if silent > 7d (cadence=0 → wrapper skips)               │
 │  LLM narrative (Murakumo gemma3:1b, structured prompt, 120 tokens)     │
 └───────────────────────────────────────────────────────────────────────┘
             ↓
 ┌─ write plane ─────────────────────────────────────────────────────────┐
 │  vertex_actor_shinka_state  UPSERT (repo_did, collection)              │
 │  R2 magatama/plan-current.json + hourly history snapshots              │
 └───────────────────────────────────────────────────────────────────────┘
             ↓   (next crontab tick)
 ┌─ goose cron wrapper ──────────────────────────────────────────────────┐
 │  SELECT cadence_ms WHERE repo_did AND collection                       │
 │  0 → exit 0 (archived)                                                 │
 │  >0 → throttle fire against elapsed                                    │
 │  unset → fallback to crontab CADENCE_MS default                        │
 └───────────────────────────────────────────────────────────────────────┘
```

### S1 — Bayesian health

For each recipe with assigned cadence `c`, the expected runs per hour are
`e = 3.6 × 10⁶ / c`. Let `a` be the observed runs in the last hour. With a
weakly-informative Beta(2, 2) prior the posterior mean is

    health = (2 + min(a, 2e)) / (4 + min(a, 2e) + max(0, e − a))

Recipes with `health < 0.3` are surfaced for investigation; `health < 0.1`
triggers "silent" reclassification. The cap at `2e` prevents a runaway hot
recipe from inflating its own health score past the intended pace.

Why Beta(2, 2)? Symmetric around 0.5, regularises small-sample recipes
toward "uncertain" rather than 0 or 1. Matches how we want stale recipes
with 0/0 observations to read — "unknown, not failed".

### S2 — Shannon entropy (uniformity)

Per repo, let `pᵢ` be the share of 24h runs contributed by collection `i`:

    H  = −Σ pᵢ log₂ pᵢ             # bits
    Hmax = log₂ N                   # N = distinct collections
    η    = H / Hmax                 # 0 = one-hot, 1 = uniform

`η` is the uniformity ratio. Low `η` means one collection dominates the
commit stream (informational redundancy — same signal repeated). The
organizer does not *force* uniformity (that would destroy legitimately
bursty recipes like mentionDrain), but it does surface `η` as a health
indicator and uses per-recipe Shannon contribution `shannonBits =
−pᵢ log₂ pᵢ` as a future-optimisation input.

### S3 — joucho shinka cadence floor

The existing `etzhayyim:magatama/shinka@1.0.0` WIT produces a per-actor
emotional baseline cadence based on mood + inbox buffer + follower KPI.
This stays the **floor**: the organizer's cadence is never set below
the joucho baseline, because emotional tempo is a legitimate signal the
organizer cannot override on numeric grounds alone.

Implementation (next iteration): the organizer will read
`vertex_actor_shinka_state.joucho_cadence_ms` (or an equivalent column
set by the shinka heartbeat worker) and enforce
`cadence = max(organizerCadence, jouchoFloor)` per recipe. Today the
floor is implicit via the `normal` class's 1h default matching typical
joucho baselines. Column addition is tracked as follow-up.

### S4 — Fleet capacity & cross-repo rebalancing

Fleet capacity = `FLEET_CAPACITY_REQ_PER_MIN = 10` (10 Ollama backends
× ~1 qwen3.5:9b warm req/min). Observed load = Σᵢ (60 s / cadenceᵢ) for
`cadence > 0`. If saturation > 1.0, all `normal` and `stale` recipes are
scaled by saturation (cadence × saturation), stretching them until load
fits. Hot recipes are preserved — by definition they are the intended
signal load. Archived recipes (cadence=0) do not count toward load.

The same mechanism generalises to multi-repo: summing across repos gives
cross-repo fairness. When `GOOSE_REPOS` grows beyond `yoro`, the organizer
naturally throttles across all of them. The `agent_origin` column from
ADR-0034 §Pending will replace the hard-coded repo list.

### Auto-archive semantics

Recipes silent for more than 7 days (`ARCHIVE_AFTER_SILENT_MS`) are
written with `cadence_ms = 0, priority = 'archived'`. The goose cron
wrapper, on reading `cadence=0`, logs `[archived] … skip` and exits
without firing. Archival is reversible: any fresh manual run (or ansible
re-deploy of the recipe) that produces a `vertex_repo_commit` row will
cause the next organizer tick to reclassify the recipe out of archived
into normal on the strength of recent evidence.

### LLM narrative (observability, not control)

Per organizer tick, a compact fact JSON (summary stats + top 6 recipes +
entropy + fleet) is sent to murakumo via the `MURAKUMO` service binding
(`x-magatama-verified: true` internal bypass; model `gemma3-1b`; 120
tokens; temperature 0.3). The resulting 2-sentence summary is stored in
`plan.narrative` and displayed on the dashboard. The narrative has **no
control authority** — it is a human-facing observability layer. Even if
the LLM output is wrong, the numeric decisions are unchanged.

## Data model

### `public.vertex_actor_shinka_state`

| column | type | role |
|---|---|---|
| `repo_did` | varchar | part of composite PK |
| `collection` | varchar | part of composite PK |
| `cadence_ms` | bigint | organizer decision — 0 = archived |
| `priority` | varchar | hot / normal / stale / silent / archived |
| `runs_24h` | integer | observed count |
| `last_run_ts_ms` | bigint | latest observed commit |
| `organizer_note` | varchar | human-readable rationale |
| `updated_ts_ms` | bigint | organizer tick timestamp |

### B2 plan persistence

- `magatama/plan-current.json` — latest plan, replaced every 5 min
- `magatama/plan-history/{YYYY-MM-DDTHH}.json` — hourly snapshot for trend
  analysis (no cleanup policy yet — B2 $0.015/GB-mo; 8KB × 24 × 365 ≈ 70MB/y)

## Invariants

| Invariant | Why |
|---|---|
| organizer is **read-heavy, write-light** on RW | one UPSERT per recipe per 5 min; no continuous load |
| wrapper cadence query filters by `(repo_did, collection)` | composite PK prevents the "last-row-wins" bug we saw in initial impl |
| `cadence_ms = 0` means **archived, skip entirely** | distinct from "no override" (empty result → default CADENCE_MS) |
| LLM narrative never gates control flow | keeps the numeric plane deterministic |
| joucho floor wins over Shannon-optimal speedup | emotional pacing is a primary signal |
| saturation-driven stretch excludes `hot` | hot = intended signal; throttling it is an operator decision, not autonomic |

## Evaluation (Bayesian + Shannon)

The combined objective `J(c)` is evaluated per organizer tick and surfaced
on the dashboard:

- Per-recipe health (posterior mean) with colour-coded dot
- Per-repo Shannon η (uniformity) with Hmax comparison
- Fleet saturation bar (observed / capacity)
- LLM narrative summarising the above in natural language

No tuning knobs are exposed to users — the organizer self-selects within
the invariants above. This is the "autonomous growth topology" the design
aims at: new recipes appear in `vertex_repo_commit`, the organizer picks
them up on the next tick, assigns a class and cadence, and the wrapper
adjusts. Silent recipes archive themselves. Saturation triggers stretch.
No human intervention is required to reach steady state.

## Rejected alternatives

| Alternative | Why rejected |
|---|---|
| Single fixed cadence per recipe (crontab-only) | Can't adapt; doesn't encode activity priority |
| LLM-as-organizer (gemma/qwen decides cadence) | Non-deterministic, opaque, expensive per tick |
| Pure entropy maximisation (force uniform) | Destroys legitimately bursty recipes |
| Dual-writer (goose writes cadence + organizer writes cadence) | Write-path conflicts; CRDTs overkill |
| Reinforcement learning (reward model + policy) | Needs labelled feedback data we don't have |

## Consequences

### Positive

- Fleet paces itself as recipes come and go; operator sees heat-map rather
  than scheduling detail.
- Bayesian health gives small-sample tolerance (Beta prior).
- Shannon η is a single-number readout for "is this repo balanced?".
- Archived recipes auto-skip via `cadence=0`; no manual cron deletion
  needed. Resurrection is automatic on fresh commit.
- LLM narrative provides a human-readable layer on top of numerics,
  without gating control.
- Composite PK prevents the last-row-wins bug observed in the first
  deployment attempt.

### Negative / known trade-offs

- Organizer runs on a single CF Worker cron instance; no HA. Loss of the
  tick just means stale plan for an extra 5 min (wrapper falls back to
  `CADENCE_MS` default — graceful degradation).
- 7-day silent → archived heuristic is a hard-coded constant. When we have
  more varied recipes this may need per-agent tuning.
- `GOOSE_REPOS` is hard-coded pending the ADR-0034 `agent_origin` column
  for fully-declarative agent-origin filtering.
- Shannon η is computed on 24h counts — intrinsically window-biased.
  Recipes active earlier in the window count the same as recent ones.
- LLM narrative is gemma3:1b (fast but limited). Quality improves with
  gemma4:e4b but that costs ~10× latency per tick.

### Follow-ups (not in this ADR)

- `joucho_cadence_ms` column on `vertex_actor_shinka_state` populated by
  shinka heartbeat worker; organizer reads it as floor (S3 full
  implementation).
- `agent_origin` column on `vertex_repo_commit` + migration (drops
  hard-coded `GOOSE_REPOS`).
- Per-agent LLM narrative (not just per-plan) for long-running agents
  that have meaningful individual stories.
- Prometheus-style time-series export of health/η/saturation for external
  monitoring systems.

## References

- ADR-0034 — agent-cron-goose-kotoba-direct
- `50-infra/cloudflare/workers/magatama/src/worker.ts` — implementation
- `60-apps/etzhayyim-project-magatama/CLAUDE.md` — operator runbook
- `60-apps/etzhayyim-project-murakumo/ansible/roles/goose/templates/goose-cron-wrapper.sh.j2` — wrapper source of truth
- `public.vertex_actor_shinka_state` — RW table (composite PK
  `(repo_did, collection)`)
