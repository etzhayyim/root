---
id: adr-2605240000-unispsc-organism-fleet-mass-deploy
title: "ADR-2605240000: UNSPSC organism fleet — 18,342 mass-deploy via sharded fleet cell on Murakumo"
status: proposed
doc_type: adr
topic: unispsc-organism-fleet
authoritative: true
last_verified: 2026-05-24
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Wave 2 of ADR-2605232345 — fans the reference UnispscOrganism out to all 18,342 codes via per-shard fleet cells on joseph/issachar/dan, mirroring the existing UnispscAgentExecutorCell sharding. Each fleet cell ticks ~5K organisms per heartbeat; classify graphs remain lazy-imported per the existing LRU pattern."
authoritative_for:
  - UnispscOrganismFleetCell sharding contract (mirrors UnispscAgentExecutorCell)
  - per-node organism count + tick cadence capacity math
  - replacement of UnispscOrganismC10101500Cell single-organism cell
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - 2605171300
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
supersedes:
  - cells.UnispscOrganismC10101500Cell  # subsumed by UnispscOrganismFleetCell shard-0
superseded_by: []
---

# ADR-2605240000: UNSPSC organism fleet — 18,342 mass-deploy via sharded fleet cell

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

ADR-2605232345 built the `UnispscOrganism` wrapper + Python heartbeat-cadence
port and wired one reference instance (c10101500 / Live Animal) into the
fleet. Phase 3-4 of that ADR explicitly deferred the mass-deploy of the
remaining 18,341 codes on capacity grounds.

This ADR closes that gap. The reference wrapper is already shard-agnostic;
what's missing is (a) a cell type that hosts **many** organisms per Pod /
launchd process, and (b) a placement that mirrors `UnispscAgentExecutorCell`
so each organism is co-located with its classify graph.

The user's original question — _"is each actor at `…/profile/did:web:…`
operating as an artificial ecosystem organism?"_ — becomes _yes_ for all
18,342 codes after this ADR lands and the cell is applied.

## Capacity math

Per `00-contracts/actor-registry/unispsc.json`:

| Shard | Node | Segments | Codes |
|---|---|---|---|
| shard-0 | joseph | 10-29 | 4,597 |
| shard-1 | issachar | 30-44 | 8,541 |
| shard-2 | dan | 45-60 | 5,204 |
| **Total** | | | **18,342** |

(`shard-1` is heaviest by ~85% — same skew as the executor cell.)

Per-tick cost on a Mac mini (Apple Silicon, 16-32 GB):

- `resolve_heartbeat_cadence(...)` is a constant-time computation over
  a `JouchoScores` (5 ints), an `InboxBuffer` (≤100 commits + ≤50
  reactions), and a `CadenceState` (6 ints + ≤20 recent-post entries).
  Wall-clock ~10-30 μs in interpreted Python.
- Most ticks are no-op because cooldowns suppress action. With a 5-min
  tick interval and a neutral-mood post cooldown of 2 hours, only every
  24th tick triggers a post.
- Graph compile is one-time per code and shared with `UnispscAgentExecutorCell`
  via lazy import. Memory pressure is bounded by an LRU (default 4096
  organisms in cache, organism-side; classify graphs are bounded by the
  executor cell's own LRU).

Per-shard wall-clock for a full sweep tick:

| Shard | Codes | Tick cost (μs/code × codes) | At 5-min interval |
|---|---|---|---|
| shard-0 | 4,597 | ~60-140 ms | <0.05% CPU |
| shard-1 | 8,541 | ~110-250 ms | <0.1% CPU |
| shard-2 | 5,204 | ~70-160 ms | <0.06% CPU |

Memory ceiling (organism cache LRU 4096 × ~2 KB state) ≈ 8 MB per shard.
Graph LRU is shared with executor (already 4096-bounded). Network: no
network calls in default tick (joucho is local provider; follower stub
returns []). When MST writes land (per ADR-2605232345 §Phase 5/6 and
ADRs 2605240015 + 2605240030), tick cost rises by 1 PDS RPC per
post-emitting tick — still <1% CPU.

**Conclusion: 18,342 organisms fit comfortably on the existing 3-shard
joseph/issachar/dan placement. No new hardware needed.**

# Decision

## New cell: `UnispscOrganismFleetCell`

Add a `lan-api`-trigger cell to `50-infra/murakumo/fleet.toml` that:

1. Reads `00-contracts/actor-registry/unispsc.json`, filters by shard
   segment range (matches `UnispscAgentExecutorCell.SHARD_RANGES`).
2. On startup, lazy-instantiates `UnispscOrganism` per code via the
   existing `for_code()` constructor (uses LRU cache, capacity = 4096).
3. Spawns one asyncio background task that ticks all owned organisms
   every `tick_interval_s` (default 300 = 5 min).
4. Exposes `/healthz` returning shard, organism count, total ticks,
   posts emitted, and last error.

Module: `kotodama.organism.fleet_cell_main`. Same `async serve(stop_event,
healthz_port, api_port)` contract as `UnispscAgentExecutorCell`.

## Replacement

`UnispscOrganismC10101500Cell` (introduced by ADR-2605232345 §Fleet
placement) is **subsumed by `UnispscOrganismFleetCell` shard-0** (joseph
owns segment 10, which includes c10101500). The single-organism cell is
removed from `fleet.toml` in the same change as this ADR's mass-deploy
cells.

## Sharding contract (mirror of `UnispscAgentExecutorCell`)

```toml
[cells.UnispscOrganismFleetCell]
healthz_port_base = 13040  # per-shard, +10 per shard
trigger = "lan-api"
api_port_base = 13140
adr = ["2605240000", "2605232345", "2605171300"]
sharding = "by-segment-prefix"
shard_assignments = { shard-0 = "10-29", shard-1 = "30-44", shard-2 = "45-60" }
module = "kotodama.organism.fleet_cell_main"
registry_path = "00-contracts/actor-registry/unispsc.json"
organism_lru_max = 4096
tick_interval_s = 300
```

Node assignments:

| Shard | Node | Healthz port | API port |
|---|---|---|---|
| shard-0 | joseph | 13040 | 13140 |
| shard-1 | issachar | 13050 | 13150 |
| shard-2 | dan | 13060 | 13160 |

Optional `UNISPSC_ORGANISM_SHARD_ALL=1` env var spawns a synthetic
shard -1 (segments 0-99) for jacob single-node operation, mirroring
the executor cell's all-segments mode.

# Consequences

## 正の効果

- All 18,342 UNSPSC actors gain heartbeat behavior. `/profile/did:web:…`
  answers shift from "lookup-only" to "tick-aware mood + Shinka cadence"
  uniformly.
- Sharding mirrors the executor cell, so a `c{code}` invoke and its
  organism live on the same node. No cross-node hop for classify path.
- Memory footprint is bounded: organism LRU 4096 × ~2 KB ≈ 8 MB per
  shard. Underlying classify graph LRU is shared with executor.
- The fleet cell is a pure additive change — no modifications to
  generated `c{code}.py` files, the executor cell, or the registry.

## 負の効果 / コスト

- Cold start: first tick on each shard lazy-imports up to LRU-capacity
  classify graphs. With 4096 graphs at p50 50 ms compile per ADR-2605171300,
  worst-case cold sweep is ~200 s per shard. The cell streams imports
  on demand (LRU-on-access), so steady-state ticks are fast; cold
  startup is the only window where this matters.
- Joucho provider default is still the deterministic personality from
  ADR-2605240015 (no real mood signal yet). Real MST-backed joucho is
  Phase 5b future work.
- Follow graph integration is stubbed (returns []). Real Follow reads
  land in ADR-2605240030 (Phase 6).

## Out of scope

- Cross-organism Invoke (organism A asks organism B for opinion). The
  call surface exists (each organism has a stable DID), but routing
  belongs in a separate ADR.
- Mood signal sources: web traffic to `/profile/...`, classify-path
  invocation count, follower engagement deltas. All future work.
- ISIC mirror (~428 organisms). Symmetric design; deferred to ADR
  after ISIC fleet generation (ADR-2605180900 Phase 3) lands.

# Alternatives Considered

## A. One cell per code (18,342 cells)

却下理由: cell-runner spawn cost + healthz port allocation + supervisor
state for 18k cells; ridiculous. The fleet cell is the obvious shape.

## B. One organism shared across all codes (parameterized by code per
   tick)

却下理由: organism state (CadenceState, InboxBuffer, joucho history) is
per-actor. Sharing would collapse 18,342 personalities into one and
defeat the "ecosystem" framing.

## C. Stagger ticks (each organism gets its own offset)

却下理由: micro-optimization. The 5-min batch tick is already <1% CPU
even on the heaviest shard. Staggering would help only if the tick
became expensive (e.g., real MST writes per tick); revisit then.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism (Wave 1)
- ADR-2605171300 — Open-UNSPSC generative agent fleet (18,342 codes)
- ADR-2605192415 — Religious-corp daemon architecture (Murakumo fleet)
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/fleet_cell_main.py`
- `40-engine/kotoba/crates/kotoba-kotodama/cells/unispsc_agent_executor/cell.py` — shard mirror
- `00-contracts/actor-registry/unispsc.json` — registry SoT
