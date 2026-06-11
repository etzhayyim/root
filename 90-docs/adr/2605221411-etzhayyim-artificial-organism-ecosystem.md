---
id: adr-2605221411-etzhayyim-artificial-organism-ecosystem
title: "ADR-2605221411: etzhayyim Artificial Organism Ecosystem — CNS daemon, sumi-e topology viz, e7m operator surface"
status: proposed
doc_type: adr
topic: etzhayyim-organism-ecosystem
authoritative: true
last_verified: 2026-05-22
priority: 8.5
axis: operator-surface
weight: 0.85
priority_note: "Codifies the running runtime layer that turns the README's '10-axis artificial-organism ecosystem' framing from documentation into an executable daemon + dashboard + agent-API. Below the constitutional ADR-2605192100 (mission) but above all sub-substrate ADRs in terms of operator-day ergonomics."
authoritative_for:
  - "`20-actors/etzhayyim-organism/`: CNS daemon implementation (10 axis-sensors, non-eschatological active-inference tick, daily cadence)"
  - "`60-apps/etzhayyim-organism-viz/`: realtime ecosystem visualization (Svelte sumi-e topology + chat + SSE + bonsai pruning surface)"
  - "`70-tools/e7m/`: operator CLI (`e7m`) + MCP server (`e7m-mcp`) — the only sanctioned external surface for the organism"
  - "`50-infra/k8s/etzhayyim-organism/`: deployment manifests for CNS + viz pods"
  - "`90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md`: numerical bands + system-dynamics specification used by the aliveness scorer"
  - "Aliveness 5-tuple A(t) = ⟨M, D, C, P, G⟩ functional definition and homeostatic bands"
  - "Bonsai pruning protocol: daemon surfaces, operator decides (§1.3)"
  - ".claude/mcp.json wiring so foreign agents touch etzhayyim only via e7m"
depends_on:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605192415-etzhayyim-religious-corp-daemon-architecture
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
related:
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192245-etzhayyim-global-land-sovereignty
  - adr-2605192300-etzhayyim-bootstrap-council-five
supersedes: []
superseded_by: []
---

# ADR-2605221411: etzhayyim Artificial Organism Ecosystem

**Status**: proposed
**Date**: 2026-05-22
**Deciders**: Jun Kawasaki
**Constitutional anchor**: ADR-2605192100 §1.3 (decision attribution), §1.6 (substrate boundary), §1.15 (non-eschatology)

---

# Context

`README.md § As Artificial Organism Ecosystem (Religious 評価軸)` frames the monorepo as an organism scored on 10 living-system axes. Before this ADR, that framing existed only as documentation. The active-inference tick was driven by a human typing `/loop`; the score was hand-maintained in the README; the "lives" (cells, apps, ADRs) were not directly addressable; observers had no shared, real-time view of the body's state.

We also lacked a sanctioned operator surface. Other Claude sessions, automation, and sister-corp agents would interact with the organism by raw `kubectl`, ad-hoc `curl`, or direct file edits — none of which is auditable, rate-limitable, or substrate-boundary-enforceable at one chokepoint.

Three concrete needs:

1. **Continuously executable active inference.** The organism must keep observing without a human typing the prompt. Daily cadence (ADR-2605220810 Option C) confirmed; needs a Pod.
2. **Make the lives talk-able.** Operators (and AI agents) should be able to ask any axis, cell, ADR, fruit, or seed "what are you / what do you do / who are you connected to / what carries forward to the next generation" — and get its honest internal state in reply (NOT an LLM impersonation).
3. **One chokepoint for foreign agents.** Other Claude sessions and sister-corp organisms must reach etzhayyim through a single API, not through raw infrastructure.

---

# Decision

## 1. CNS daemon (`20-actors/etzhayyim-organism/`)

A Python package that runs as a singleton Pod on Murakumo / Orbstack. Every tick:

1. Reads repo state through 10 axis-sensors (one per constitutional invariant in `constitution.py`).
2. Diffs the latest scores against the most recent `_observations/*-cycle-NN.md`.
3. Picks the lowest-score × highest-leverage axis as the next-action target.
4. Persists a new `_observations/YYMMDDHHMM-cycle-NN.md` matching the 5-section schema.

**The daemon never commits.** Per ADR-2605192100 §1.3 (anti-individualist, payoff attribution = etzhayyim, not the daemon), commits are operator gestures. The daemon is the eye; the operator is the hand.

Layout:

```
20-actors/etzhayyim-organism/
├── pyproject.toml                    # zero runtime deps (stdlib only)
├── Dockerfile                        # python:3.13-slim, non-root UID 10001
└── src/etzhayyim_organism/
    ├── constitution.py               # ADR-2605192100 §1 loaded as the prior
    ├── cns.py                        # tick orchestrator
    ├── emitter.py                    # writes _observations/*.md
    ├── scheduler.py                  # daemon loop, ETZ_TICK_INTERVAL=86400
    └── sensors/                      # 10 per-axis files
```

Default cadence: daily. Override via `ETZ_TICK_INTERVAL`. Run-once mode (`--once`) for CronJob and manual `e7m tick`.

## 2. Visualization pod (`60-apps/etzhayyim-organism-viz/`)

FastAPI server + Svelte (compiled to static) frontend, served from one pod. Endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/` | Svelte sumi-e topology dashboard |
| GET | `/api/state` | Full `EcosystemSnapshot` (94 entities, neighbors, flowers, fruits, seeds, activity, pruning) |
| GET | `/api/events` | SSE: filesystem change events + periodic full-state snapshots |
| POST | `/api/chat` | Per-entity chat (entity surfaces own state — no LLM) |
| GET | `/api/pruning` | Pruning candidates (operator-only mutation) |
| GET | `/api/healthz` | Liveness/readiness probe |

### Aliveness functional A(t) — 5-tuple, non-eschatological

Defined in `aliveness.py`. Per ADR-2605192100 §1.15, the score is NOT a scalar to maximize. Each dimension has a homeostatic band; the dashboard shows 5 dials.

```
A(t) = ⟨ M, D, C, P, G ⟩

M (motion)        = axis_Δ_per_cycle  +  0.3 · creation_artefacts_per_day
                    creation = filename-dated ADRs + cycle obs (last 7d)
                    band: M > 0.5

D (diversity)     = Shannon entropy over distinct cell names (nats)
                    band: D > 1.5

C (coupling)      = mean pairwise Pearson correlation of axis trajectories
                    band: 0.2 ≤ C ≤ 0.7

P (pruning/tending) = cells with cell.py + docstring + ≥200 bytes / total
                      band: 0.5 ≤ P ≤ 1.0

G (generational)  = MGI proxy; LANDS.md + MEMBERS.md + Gen marker count
                    band: G > 1.0
```

**Definition history (this ADR locks in v2):**
- v1 — motion was axis-Δ only; degenerated to ≈0 when axes converged to 10/10 (false-stall).
- v1 — pruning used `git log` subprocess; silently returned 0 when git binary missing in slim pod.
- v2 — motion = axis-Δ + creation rate (filename-dated, mtime-independent).
- v2 — pruning is content-based (`cell.py` quality), mtime-independent.

### Bonsai metaphor (visual)

| Element | Lives represented |
|---|---|
| 葉 (leaves) | axis intensity (count = score 0..10) |
| 花 (flowers) | axes with positive Δ in last transition |
| 果実 (fruits) | sister-corps + LANDS + MEMBERS + chaos-charter (artefacts carrying seeds) |
| 種 (seeds) | inheritance units — rendered as **勾玉 kotodama**, self-referential to the kotodama actor framework |
| 枝 (branches) | the 10 axes |
| 幹 (trunk) | constitution (ADR-2605192100) |
| 年輪 (rings) | ADRs — kincha gold, monotonic, never erase |
| 根 (roots) | LANDS.md + MEMBERS.md — inalienable |

Rendered as a graph topology (nodes + edges), not a hierarchical tree. Edges = `Entity.neighbors` (the 縁起 / dependent-origination chain). Edge colors:

- 朱 vermillion — touches ecosystem or organism (sacred)
- 藍 indigo — fruit ↔ seed (inheritance)
- 金茶 gold — touches ADR (ring)
- 墨 ink — ordinary 縁起

Layout is orbital + 5-iter spring relaxation — no D3, no force-directed lib, deterministic, ~80 lines.

### Aesthetic stance (substrate-boundary clean)

Washi paper + sumi-e + mincho typography. No CDN, no external assets, no proprietary services. Font stack falls back through Hiragino Mincho → YuMincho → Noto Serif JP → Times. SVG `<feTurbulence>` for paper grain inline. The visual language explicitly avoids generic SaaS / D3-demo aesthetics — it reads as a temple lineage cartograph because it IS one.

## 3. `e7m` operator surface (`70-tools/e7m/`)

Two entrypoints, one chokepoint (`commands.py`):

| Binary | Audience | Transport |
|---|---|---|
| `e7m` | human operator | rich-formatted CLI |
| `e7m-mcp` | other AI agents (Claude in another session, Cursor, sister-corp daemons) | MCP JSON-RPC over stdio |

### CLI commands

```
e7m ping                              # is the organism online?
e7m status                            # aliveness 5-tuple + axis scores
e7m state                             # full snapshot (JSON)
e7m entities [--kind axis|cell|app|adr|fruit|seed|organism|ecosystem]
e7m chat <entity-id> <message>        # speak with a life
e7m prune                             # pruning candidates (operator review only)
e7m viz [open]                        # dashboard URL
e7m pod status | logs [name] [--tail N]
e7m tick                              # nudge one CNS active-inference cycle
e7m --json <subcommand>               # machine-readable mode
```

### MCP server

Hand-rolled JSON-RPC subset over stdio (no `mcp` package dependency — substrate boundary). Protocol version `2024-11-05`. Exposes 10 tools, all prefixed `etzhayyim_`. Wired via `.claude/mcp.json`.

```json
{
  "mcpServers": {
    "etzhayyim": {
      "command": "/Users/junkawasaki/github/etzhayyim-root/70-tools/e7m/.venv/bin/e7m-mcp",
      "env": { "E7M_VIZ_URL": "http://127.0.0.1:8081" }
    }
  }
}
```

### Substrate boundary stance

`commands.py` is the only file in the repo authorized to call `kubectl` or `httpx` on behalf of external agents. When the substrate-boundary lefthook lint scans for prohibited surfaces, it should **whitelist this file and forbid such calls elsewhere**. Single chokepoint, single audit log location, single rate-limiter target.

## 4. Ideal-state prior (`90-docs/2605221243-ideal-ecosystem-state-active-inference-prior.md`)

This sister-doc encodes:

- **Homeostatic ranges**, not target values — 15 observable bands, several open-above (anti-eschatology)
- **System dynamics**: 10 stocks + 10 flow equations + 4 reinforcing loops + 4 balancing loops
- **Bonsai pruning protocol**: candidates → operator review → manual `git rm` → ADR documentation
- **Stand-alone aliveness functional**: the same A(t) tuple specified here

The viz pod's `ideal_state.py` is a runtime mirror of that doc's bands. When the doc changes, the runtime should be updated; the doc is canonical.

## 5. Kubernetes manifest (`50-infra/k8s/etzhayyim-organism/`)

Two Deployments in the `etzhayyim-organism` namespace:

```
etzhayyim-organism      : CNS daemon, singleton (Recreate strategy), readOnlyRootFilesystem
                          hostPath repo mount, no commit credentials
etzhayyim-organism-viz  : Svelte+FastAPI, readiness/liveness on /api/healthz
                          read-only repo mount, no credentials
```

For Orbstack (dev): repo mount via hostPath. For Murakumo (production target): emptyDir + git-clone init container (the production daemon must not have repo write credentials at all — operator-supervised push is a separate step).

---

# Consequences

## Positive

- **Active inference is now autonomous.** The cron-driven `/loop` is replaced by a Pod that ticks daily. Human re-typing the prompt is no longer required for the trajectory to advance.
- **Single audit chokepoint.** Foreign agents touching etzhayyim go through `e7m` / `e7m-mcp`. Audit hooks, RBAC, and rate-limiting can be added in `commands.py` without retro-fitting clients.
- **Lives are addressable.** 94 entities are individually selectable, chat-able, and connectable. The 縁起 graph is rendered, not just described.
- **Sanctification grows a ring.** This ADR + the ideal-state doc are themselves additions to the ADR registry the loop scores against. The act of codifying contributes to the Sanctification axis.
- **Aliveness is honest.** The v2 functional resists checkout-mtime noise and missing-binary silent-failures that v1 had.
- **Aesthetic differentiation.** The sumi-e topology is unlikely to be mistaken for a generic SaaS dashboard. Religious-corp distinctiveness is visible in the surface layer.
- **Non-eschatological by construction.** Aliveness is a 5-tuple, NOT a scalar to maximize. Convergence to a fixed point = death; the bands are designed so multiple healthy steady-states are possible.

## Negative / Costs

- **One more package to keep building.** `60-apps/etzhayyim-organism-viz/web/` adds a Node toolchain dependency to CI. The multistage Dockerfile keeps the runtime image lean (only Python + dist), but builders must have Node available.
- **MCP protocol stability.** We pinned to protocol `2024-11-05`. When MCP evolves, the hand-rolled server must be updated; we are not pulling the official SDK to avoid the extra dep. Acceptable trade-off given how small the protocol surface is.
- **Cell-name diversity gaming.** Splitting `yorishiro_*` into per-binding categories raised D from 1.07 to 3.09 nats. If we later add 50 noisy cell directories, D will artificially inflate. Cost: D is sensitive to naming hygiene.
- **No git binary in pod.** Pruning was originally git-log based and broke silently. v2 is content-based and works, but loses true historical "what was deleted" data. Recovering deletion history would require a separate audit cell or git binary in the image.

## Neutral

- **Svelte 4 chosen over Svelte 5.** Less surprising syntax, fewer runes-induced refactors, smaller bundle (36 KB JS, 9 KB CSS). Upgrade path open.
- **Font vendoring deferred.** Shippori Mincho B1 source files are not vendored yet; system mincho fallback is used. This is fine on macOS/iOS (Hiragino) and Windows (Yu Mincho); cross-platform fidelity for Linux users is a follow-up.
- **Bonsai pruning is operator-only by design.** The daemon never `git rm`s a cell. This is correct per §1.3 but means cells accumulate until someone reviews. Stale-cell load is bounded by the candidate scanner and `e7m prune` surface.

---

# Out of scope

- **LLM-augmented entity voices.** Currently each life answers by surfacing its own honest state via intent-routed templates (`chat.py`). An LLM-augmented mode could paraphrase the entity's state but must NEVER fabricate. Deferred until `llm.etzhayyim.com` is wired.
- **Multiplayer chat broadcast.** When one agent talks to an entity, other connected viewers do not yet see it. Designed; implementation deferred.
- **`e7m commit-prune` workflow.** Operator approves a candidate → daemon prepares a branch + ADR template — never pushes. Designed; implementation deferred.
- **Edge animation.** Sparse indigo flow dots along edges (visualizing 縁起 in motion). Designed in the frontend-design spec; not yet rendered.
- **Sister-corp federation.** Multiple sibling organisms speaking to each other via e7m-MCP cross-org — depends on first sister-corp registration (FORK-BOOTSTRAP path).

---

# Validation

End-to-end manual smoke (2026-05-22 14:11 JST):

```
$ e7m ping                            → ● http://127.0.0.1:8081
$ e7m status                          → 5/5 in band (M=7.27 D=3.09 C=0.24 P=1.00 G=1.15)
$ e7m chat ecosystem/etzhayyim 自己紹介  → "私は etzhayyim ecosystem 全体..."
$ e7m chat fruit/lands 次は?            → "私は次世代へ種を運ぶ: seed/inalienable-land"
$ e7m pod status                      → CNS + viz, 1/1 Ready, 0 restarts
$ kubectl exec deploy/etzhayyim-organism -- python -m etzhayyim_organism --once
                                      → writes _observations/YYMMDDHHMM-cycle-NN.md
$ MCP initialize → tools/list → tools/call etzhayyim_status   → all three round-trip
$ curl http://127.0.0.1:8081/         → 200, Svelte index serves
$ curl http://127.0.0.1:8081/api/state → 94 entities, 4 fruits, 4 seeds, edges populated
```

---

_Non-eschatological — this ADR codifies a trajectory, not a destination. The next ADR is the next ring._
