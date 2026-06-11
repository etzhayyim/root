---
id: adr-2605232345-unispsc-actor-as-organism
title: "ADR-2605232345: UNSPSC actor as ecosystem organism — Python heartbeat-cadence port + reference wrapper"
status: proposed
doc_type: adr
topic: unispsc-organism
authoritative: true
last_verified: 2026-05-23
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Turns the 18,344 UNSPSC LangGraph actors from passive request-reply handlers (ADR-2605180900) into autonomous organisms with joucho 情緒 mood + InboxBuffer + Shinka post cadence, matching the TS heartbeat-cadence pattern in @etzhayyim/kotodama-host-sdk. Scope: 1 reference organism (c10101500); mass-deploy gated on a separate hardware-capacity ADR."
authoritative_for:
  - Python port of joucho heartbeat-cadence (kotodama.organism)
  - UNSPSC actor → organism wrapping contract
  - one-organism-per-cell fleet placement convention
depends_on:
  - 2605171300
  - adr-2605180900-unispsc-isic-langserver-actor-lexicon-xrpc-mcp
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
related:
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
supersedes: []
superseded_by: []
---

# ADR-2605232345: UNSPSC actor as ecosystem organism — Python heartbeat-cadence port + reference wrapper

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

# Context

ADR-2605171300 generated 18,344 per-commodity LangGraph StateGraphs at
`kotodama/langgraph_graphs/unispsc_agents/c{code}.py`. ADR-2605180900
wired them behind a langserver pod with four call surfaces (HTTP / Actor /
XRPC / MCP). The result is a sharp asymmetry:

- The TS-native app fleet (~198 apps on `@etzhayyim/kotodama-host-sdk`) runs
  the **organism pattern**: joucho 情緒 5-axis mood × `InboxBuffer` ×
  `FollowerReward` × Shinka post cadence × Kyumei-Koji self-investigation,
  all driven by `resolveHeartbeatCadence()`
  (`40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/heartbeat-cadence.ts`).
- The Python LangGraph fleet is **stateless**. Each `c{code}.py` exposes
  a compiled `graph` that runs when invoked. There is no tick, no inbox,
  no Follow graph, no Shinka. The actors are listed on
  `etzhayyim.com/profile/did:web:etzhayyim.com:actor:c{code}` but they
  do not "live" in any meaningful sense.

The user-facing question — _"is each actor at `…/profile/did:web:…` operating
as an artificial ecosystem organism?"_ — currently has answer **no** for
the UNSPSC subset. This ADR closes that gap on the call-pattern side
without forcing a full 18,344-mass-deploy. The organism wrapper is built
to plug onto **any** UNSPSC code, but only one reference instance
(`c10101500` Live Animal) is wired into `fleet.toml`. Mass deploy is a
separate hardware-capacity ADR (Murakumo fleet has 10 nodes; running
18,344 heartbeat ticks needs sizing).

# Decision

Adopt a four-piece organism stack for Python LangGraph actors, matching
the TS heartbeat-cadence shape as closely as the substrate allows.

## Module layout

```
40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/
├── __init__.py         # public surface: JouchoScores, Mood, InboxBuffer,
│                       # CadenceState, FollowerReward, HeartbeatCadence,
│                       # ContentSource, determine_mood, resolve_heartbeat_cadence,
│                       # UnispscOrganism
├── joucho.py           # JouchoScores + Mood + determine_mood + mood_to_cadence +
│                       # apply_stress_scaling
├── inbox.py            # InboxBuffer + FollowerSnapshot + FollowerReward +
│                       # InboundCommit + InboundReaction + content-diversity helpers
├── cadence.py          # CadenceState + resolve_heartbeat_cadence + ContentSource +
│                       # HeartbeatCadence dataclass
└── unispsc_organism.py # UnispscOrganism: wraps a UNSPSC LangGraph code into
                        # tick-able organism with classify path + Shinka emission
```

## Reference wrapper contract

```python
from kotodama.organism import UnispscOrganism

# Wrap any UNSPSC code into an organism.
organism = UnispscOrganism.for_code(
    code="10101500",
    classify_input_factory=lambda evt: {
        "input": {"description": evt.text, "species": evt.species},
    },
    post_sink=lambda post: ...,   # caller decides MST write vs. stdout
    follower_score_provider=...,  # optional; default returns []
)

# Per heartbeat tick:
result = await organism.tick(now_ms=time.time() * 1000)
#   result.cadence: HeartbeatCadence
#   result.classifications: list of `graph.invoke(...)` terminal states
#                           for inbox commits the mood decided to act on
#   result.posts:           list of Shinka strings emitted this tick
#   result.rewards:         FollowerReward[] consumed this tick

# Push inbound events between ticks:
organism.inbox.add_commit(InboundCommit(collection=..., repo=..., rkey=..., time=...))
organism.inbox.add_reaction(InboundReaction(type="like", uri=..., from_=..., time=...))
```

The wrapper is **substrate-agnostic** on purpose. `post_sink` and the
follower-score provider are caller-supplied so the same class runs in
unit tests (in-memory), in the cell-runner LAN cell (MST writes via
AnchorBridge), and in K8s Pods (PDS XRPC).

## Heartbeat-cadence port mapping (TS → Python)

| TS symbol | Python symbol | Notes |
|---|---|---|
| `JouchoScores` | `joucho.JouchoScores` | dataclass, 0-100 fields |
| `determineMood` | `joucho.determine_mood` | identical thresholds (stress ≥70 trumps, axes ≥60 win, else neutral) |
| `moodToCadence` | `joucho.mood_to_cadence` | identical cooldown table |
| `applyStressScaling` | `joucho.apply_stress_scaling` | identical scaling |
| `InboxBuffer` | `inbox.InboxBuffer` | mutable dataclass + bounded `add_*` |
| `FollowerReward` | `inbox.FollowerReward` | identical fields + `reward_type` enum |
| `CadenceState` | `cadence.CadenceState` | identical cooldown timestamps |
| `ContentSource` | `cadence.ContentSource` | union via `kind` discriminator |
| `resolveHeartbeatCadence` | `cadence.resolve_heartbeat_cadence` | sync; joucho score query injected (default constant 50/50/30/50/50) |
| Shannon content-diversity window | identical (2h, max 2 consecutive same-type) | |

The Python version is **sync** because organisms tick from
`asyncio.create_task` already and the heartbeat resolver doesn't need
its own awaits in the in-process default. Hooks for async joucho
score lookup are pluggable (`joucho_provider` callable).

## What an organism "does" per tick

1. Read `JouchoScores` (default 50/50/30/50/50 if no provider).
2. Determine mood + cadence cooldowns (post/engage/drill/analyze/validate).
3. Resolve `contentSource` from `InboxBuffer` (inbound commits, reactions,
   follower wellness deltas, mood shift, or record analysis).
4. For each inbound commit the mood says to act on, call the underlying
   `graph.invoke(...)` (the UNSPSC code's classify graph). The classify
   output is appended to a per-tick result.
5. Emit a Shinka post if `shouldPost && contentSource != "none"`, formatted
   based on `contentSource.kind`. Post is handed to `post_sink`.
6. Emit `FollowerReward` like/love decisions (handed to `reward_sink`
   if provided; default no-op).
7. Update cadence timestamps + follower snapshots + recent-post-types.

The point: **the same `c10101500.py` LangGraph is the classify engine
underneath**. The organism layer adds heartbeat behavior on top, without
modifying the generated agent files.

## Fleet placement

Add one cell to `fleet.toml` on a node that already runs adjacent cells:

```toml
[cells.UnispscOrganismC10101500Cell]
healthz_port = 13030
trigger = "cron"           # heartbeat tick every 5 min
cron = "*/5 * * * *"
adr = ["2605232345", "2605171300", "2605180900"]
unispsc_code = "10101500"
module = "kotodama.organism.cell_main"
```

Node assignment: `dan` (already runs `UnispscAgentExecutorCell` shard-2
for segment 10 codes, so the per-code LangGraph is co-located and warm).

## Phase ordering

```
Phase 1  Python port + dataclasses + unit tests        (this ADR — done)
Phase 2  c10101500 reference organism + cell entry     (this ADR — done)
Phase 3  Hardware-capacity ADR for 18,344 mass deploy  (separate ADR)
Phase 4  Murakumo node sizing + per-shard organism     (separate ADR)
Phase 5  Joucho score provider wired to MST            (separate ADR)
Phase 6  Follow graph wired to AT Protocol             (separate ADR)
```

# Consequences

## 正の効果

- The user-visible `/profile/did:web:etzhayyim.com:actor:c{code}` answer
  shifts from "lookup-only" to "has a mood, has an inbox, posts when
  appropriate" for the reference code. The architecture for the rest is
  in place — only fleet capacity gates the remaining 18,343.
- The TS organism pattern (joucho + InboxBuffer + Shinka + diversity
  window) is now reusable on the Python side without rewriting business
  logic. Future religious-corp cells can adopt it.
- Underlying `c{code}.py` LangGraph files are **untouched**. The organism
  wrapper consumes them; no codemod across 18,344 files.

## 負の効果 / コスト

- Two parallel cadence implementations (TS + Python). The Python version
  must track TS changes manually until a shared spec is extracted.
- Joucho score provider default is a constant (50/50/30/50/50). Until a
  real MST-backed `JouchoScore` writer exists for these actors, their
  mood is "neutral" and cadence is the neutral table. The wiring is
  ready; the data source is not.
- Cron 5-min tick × 18,344 organisms = 220 ticks/sec. The reference cell
  ticks ~1/min, well under capacity. Mass-deploy needs separate ADR.

## Out of scope

- Mass-deploying organisms for all 18,344 codes (capacity ADR).
- Real joucho score backend (per-actor `JouchoScore` MST writer).
- Real Follow graph traversal (`vertex_actor` + `mv_followers` exists on
  the TS side but not yet on the Python organism path).
- Cross-organism conversation (Invoke between c{code} organisms).

# Alternatives Considered

## A. Modify each `c{code}.py` to embed organism behavior

却下理由: 18,344 file codemod; each file becomes ~250 LOC instead of
~80; reviews become unreviewable; the heartbeat shape rots fast under
that surface area.

## B. Run the TS heartbeat-cadence on Python actors via cross-language RPC

却下理由: every organism tick would require an RPC hop; the substrate is
local Murakumo Mac mini fleet; the latency win of in-process Python is
real and the TS impl is small enough to port directly.

## C. Skip the organism layer; let `etzhayyim.com/profile/...` just be a viewer

却下理由: the user explicitly asked for organism behavior. The profile
page is already wired into the AT Protocol identity layer; making it
return a heartbeating actor is the natural next step.

# References

- ADR-2605171300 — Open-UNSPSC Generative Agent Fleet (18,344 agents)
- ADR-2605180900 — UNSPSC + ISIC langserver, four call surfaces, Haiku-routed
- ADR-2605192415 — Religious-corp daemon architecture (Murakumo cell catalog)
- `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/heartbeat-cadence.ts` — TS reference
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/` — this ADR's deliverable
- `40-engine/kotoba/crates/kotoba-kotodama/cells/unispsc_agent_executor/cell.py` — classify path
- `50-infra/murakumo/fleet.toml` — placement
