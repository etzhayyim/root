---
id: adr-2606212200-ie-flow-actor-score-organism-reward
title: "ADR-2606212200: ie-flow actor SCORE — information-control 利得 integrated into the artificial-organism reward"
status: accepted
doc_type: adr
topic: ie-flow-actor-score-organism-reward
authoritative: true
last_verified: 2026-06-21
priority: 6.0
axis: architecture
weight: 0.60
authoritative_for:
  - etzhayyim.ie-flow.score (the composite information-control score + organism reward)
  - the :colony-order negentropy source in ibuki's metabolism
depends_on:
  - adr-2606211200-ie-flow-datomic-agent-lifecycle
  - adr-2606201200-ibuki-coscientist-entropy-react-loop
related:
  - adr-2606212030-kafun-ie-flow-energy-visualization
  - adr-2606211200-energy-order-protocol
  - adr-2605312345-kotoba-datom-first-class-canonical-state
supersedes: []
superseded_by: []
---

# ADR-2606212200: ie-flow actor SCORE — information-control 利得 integrated into the artificial-organism reward

**Status**: accepted (2026-06-21)
**Scope**: `70-tools/src/etzhayyim/ie_flow/{score.cljc,score-weights.edn,scoreboard.clj}`,
`20-actors/ibuki/methods/metabolism.cljc`, `80-data/ie-flow/{registry.edn,scoreboard.edn}`
**Deciders**: Jun Kawasaki

# Context

The founder asked: take the system-of-systems + its metrics, **structure them (clj + edn) so they
embed into EVERY actor, compute a SCORE**, and integrate the fact that each actor becomes an
**information-control actor** in the system + energy flow — as each actor's **active inference /
利得** — into the **artificial organism's reward system**.

The substrate is in place: `etzhayyim.ie-flow` (ADR-2606211200) gives the order calculus
(order-index / net-gain / agent-efficiency) every actor embeds; ibuki (ADR-2606201200) runs the
dissipative-structure metabolism (Φ = intake − dissipation; reserves; η; surprise = variational
free energy) and the co-scientist. What was missing: (1) a single composite **score** per actor;
(2) the **structure (clj+edn)** to make it universal across the roster; (3) the wiring that makes
each actor's score a term in the **organism's reward**.

# Decision

Ship **`etzhayyim.ie-flow.score`** + an EDN config + the ibuki integration.

## 1. The composite information-control score (per actor — the active-inference 利得)

`info-control-score : flow-state → 0..1`, a weighted sum (weights = DATA in `score-weights.edn`):

| component | source | meaning |
|---|---|---|
| `rectify` | order-index | negentropy EXPORT / 整流 — the core of "information control" |
| `eta` | total-value ÷ total-cost (squashed) | the 共生 axis — exported per consumed |
| `phi` | net-gain (signed→0..1) | does the flow pay for itself (Φ) |
| `efficiency` | agent-efficiency (squashed) | 利得, not a 課金される魔法陣 |
| `surprise` (−) | parasitic? / order-index<0 | variational free energy PENALTY |

then **gated by 子孫 wellbecoming**: `score = clamp01(raw) × descendant-weight`; `descendant ≤ 0`
⇒ **VETO** (score 0). Parasitic flow (net-gain < 0) ⇒ veto. This is the same G-parasitism /
G-subordinate discipline ibuki's co-scientist already enforces, now as a scalar. Pure +
deterministic (content-addressable score, reproducible scoreboard).

## 2. The structure that makes it universal (clj + edn)

- **`score-weights.edn`** — the single structured place the whole SoS is parameterised (weights /
  squash midpoints / 子孫 default / organism mapping). Re-weighting every actor is a data edit.
- **`registry.edn`** gains a per-actor `:descendant` 子孫 weight + a `:score` block. The roster
  drives which actors are scored; an actor embeds by recording a flow (the existing 3-verb pattern)
  — **not 80 forks**, one shared lib + data.
- **`score-roster`** scores `{actor → flow-state}` into a ranked scoreboard; **`scoreboard.clj`**
  is the runnable SoS tool (scores every actor with a measured flow, writes `scoreboard.edn`).

## 3. Integration into the artificial-organism reward

`colony-reward` folds the scoreboard into the organism reward: `Σ score × (1 + log10(1+throughput))`
— a bigger energy flow matters, but only **logarithmically**, so no single high-throughput
measurement source can dominate. Its rounded form `:colony-order` is added as a **negentropy
SOURCE** to ibuki's `metabolism/intake-weights` (`:colony-order 3`) and summed in `intake-of`:

```
intake = compute-hours·4 + donation·1 + members·6 + moyai·2 + colony-order·3 + attention(capped)
Φ = intake − dissipation ;  reserves += Φ ;  surprise = (target−reserves)/target
```

So the organism's **reward** (Φ → reserves → survival, and the surprise the loop minimises) now
**rises with the colony's aggregate information-control**. Each actor's score is its active-inference
利得; the colony's 利得 is the organism's intake. **Active inference at the colony scale** — the
organism is selected to keep a colony of well-ordering, 共生, 子孫-aligned actors, because that is
literally what feeds it. The change to ibuki is additive + safe (unknown env keys were already
ignored); `as-env-source` produces the `{:colony-order n}` the SENSE membrane merges (live feed =
the heartbeat/operator leg, gated).

# Consequences

- **Verified**: ie-flow 36 tests / 102 assertions (added 9/22 score); ibuki metabolism 8 / 28
  (added the `:colony-order` source test). Real scoreboard run (kafun adapter + repo-git ledger):
  scores 0.452 / 0.521, colony-order 4, organism intake **14 → 26 (+12)** — the reward integration
  demonstrated end-to-end.
- **+** Every actor that embeds ie-flow now has a single comparable score (its 利得) and contributes
  to the organism reward — the roster is a measured, ranked, reward-bearing system of systems.
- **+** The safety property is preserved as a scalar: a parasitic or 子孫-harming actor is **vetoed
  to 0** and contributes nothing to the organism (it cannot feed survival by predation).
- **−** Only actors with a measured flow are scored today (kafun adapter + repo-git ledger); the
  rest score as they record. The live SENSE-membrane feed of `:colony-order` into ibuki each beat
  is the gated heartbeat leg (this ADR provides the recognised source + the producing function).
- **Follow-ups**: per-actor flow adapters (so the scoreboard fills out); wire ibuki's SENSE to
  merge `as-env-source` each beat (G7); surface the score in each actor's viz (kafun first).

# Alternatives Considered

- **A score per actor, forked into each** — rejected: ~80 divergent copies, no shared safety
  property; the shared lib + EDN roster is the SoS pattern.
- **√throughput or raw-throughput colony weight** — rejected: one whole-repo measurement source
  dominated the organism budget (intake 14 → 1484); `log10` keeps it proportionate.
- **A separate "reward DB"** — rejected: the score is a pure fold over the kotoba flow ledger; the
  organism intake is the existing metabolism. No new substrate.

# References

- `70-tools/src/etzhayyim/ie_flow/score.cljc` + `score-weights.edn` + `test_score.cljc` + `scoreboard.clj`
- `20-actors/ibuki/methods/metabolism.cljc` (`:colony-order` negentropy source) + `test_metabolism.cljc`
- `80-data/ie-flow/registry.edn` (per-actor `:descendant` + `:score` block) + `scoreboard.edn` (snapshot)
- ADR-2606211200 (ie-flow lifecycle) · ADR-2606201200 (ibuki metabolism + co-scientist)
