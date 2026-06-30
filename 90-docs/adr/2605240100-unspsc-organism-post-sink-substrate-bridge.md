---
id: adr-2605240100-unispsc-organism-post-sink-substrate-bridge
title: "ADR-2605240100: UNSPSC organism post sink — NDJSON queue + TS-side drainer (substrate-boundary-honoring)"
status: proposed
doc_type: adr
topic: unispsc-organism-post-sink
authoritative: true
last_verified: 2026-05-24
priority: 6.5
axis: architecture
weight: 0.65
priority_note: "Replaces logger.info post sink with an NDJSON append-only queue file that a TS-side drainer (via @etzhayyim/sdk) consumes and writes to AT MST → IPFS → Base L2. Honors the substrate boundary (CLAUDE.md: 'only via @etzhayyim/sdk') by keeping all atproto/MST/viem code on the TS side. Mirrors the MstCheckpointSaver IPC pattern from ADR-2605171800."
authoritative_for:
  - UnispscOrganism post sink contract
  - NDJSON queue line schema (one post = one JSON object per line)
  - drainer interface (TS-side @etzhayyim/sdk consumer)
depends_on:
  - adr-2605232345-unispsc-actor-as-organism
  - adr-2605240000-unispsc-organism-fleet-mass-deploy
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172100-etzhayyim-payments-on-chain-only
related:
  - adr-2605240015-unispsc-organism-joucho-personality
  - adr-2605240030-unispsc-organism-followers
supersedes: []
superseded_by: []
---

# ADR-2605240100: UNSPSC organism post sink — NDJSON queue + TS-side drainer

**Status**: proposed
**Date**: 2026-05-24
**Deciders**: Jun Kawasaki

# Context

ADR-2605232345 introduced `UnispscOrganism.post_sink: Callable[[str], None]`
as the hook for Shinka post emission. The Wave 1/2 implementation wires it
to `logger.info`, which means posts exist only in container logs and never
reach `etzhayyim.com/profile/did:web:etzhayyim.com:actor:c{code}`.

To close the loop, posts must reach the AT Protocol PDS so they federate
to the profile viewer. But:

- CLAUDE.md substrate boundary rule: "Substrate client imports: only via
  `@etzhayyim/sdk`. Direct `@atproto/api`/`viem`/IPFS client imports
  forbidden from app code."
- The `@etzhayyim/sdk` Python binding is not shipped (ADR-2605240030 §B
  noted this for the follower path; same here).
- ADR-2605171800 already established the pattern for substrate-side
  writes from Python: an IPC sidecar holds the substrate code; Python
  talks to it over Unix socket / file queue. `MstCheckpointSaver` is the
  reference implementation for LangGraph state.

This ADR establishes the same pattern for Shinka post writes.

# Decision

## File queue (Python side)

`UnispscOrganism.post_sink` is set to `NdjsonQueuePostSink(path)`, where
`path` is an NDJSON file. Each tick that emits a Shinka post appends one
JSON object:

```json
{
  "v": 1,
  "ts": 1748131234567,
  "actorDid": "did:web:etzhayyim.com:actor:c10101500",
  "code": "10101500",
  "title": "Live Animal",
  "mood": "joyful",
  "contentSourceKind": "inbound",
  "text": "[10101500/Live Animal] inbound classify → permit='DENIED' mood=joyful",
  "lexicon": "app.bsky.feed.post",
  "createdAt": "2026-05-24T01:23:45Z"
}
```

Writes are atomic (single `write()` per line, `O_APPEND` open). File
rotation is the drainer's responsibility — the Python sink only ever
appends.

Default path: `/var/lib/etzhayyim/organism-posts/{shard}.ndjson` in
production (DaemonSet `emptyDir` + sidecar share), `~/.etzhayyim/log/
organism-posts/{shard}.ndjson` in dev.

Env vars:
- `UNISPSC_ORGANISM_POST_SINK=ndjson|logger|null` (default: `logger`).
- `UNISPSC_ORGANISM_POST_QUEUE_PATH=/...` (default: above).

## Drainer (TS side — Wave 3)

A standalone TS process running alongside each organism DaemonSet:

```
Container 'cell' (Python)              Container 'drainer' (TS sidecar)
─────────────────────────              ────────────────────────────────
fleet_cell_main.py    ───append───►   /var/lib/etzhayyim/organism-posts/{shard}.ndjson
  Shinka post                          │
                                       ▼
                                       drainer.ts (Wave 3, separate ADR)
                                         - tails NDJSON file
                                         - validates each line
                                         - dispatches to @etzhayyim/sdk:
                                             sdk.pds.dispatch({
                                               type: "app.bsky.feed.post",
                                               actorDid: line.actorDid,
                                               text: line.text,
                                               createdAt: line.createdAt,
                                             })
                                         - truncates drained lines
```

The drainer's `@etzhayyim/sdk` call is the single point where
substrate-side writes happen. Drainer impl is **out of scope for this
ADR** — only the contract (line schema + path) is fixed here so Python
side can ship without coupling.

## Line schema

| Field | Type | Required | Notes |
|---|---|---|---|
| `v` | int | yes | Schema version (1) |
| `ts` | int | yes | Unix epoch ms (Python-side) |
| `actorDid` | string | yes | Source DID (the organism) |
| `code` | string | yes | 8-digit UNSPSC code |
| `title` | string | yes | UNSPSC title |
| `mood` | string | yes | joucho mood enum value |
| `contentSourceKind` | string | yes | inbound / reaction / recordAnalysis / ... |
| `text` | string | yes | Post body |
| `lexicon` | string | yes | Target NSID (default `app.bsky.feed.post`) |
| `createdAt` | string | yes | ISO-8601, drainer uses this as the record `createdAt` |

Drainer reads `v` to decide compatibility. v=1 is the only schema this
ADR defines.

## Failure modes

- Disk full / file-write fails → log + drop post. Organism stays alive.
- Drainer behind / queue grows → posts buffer in NDJSON. No back-pressure
  on the Python side (organism heartbeat must not block on substrate
  writes). Operator monitors queue size via Prometheus on the drainer.
- Drainer crashes → posts accumulate in NDJSON until drainer restart.
  Cardinal: NDJSON file is the source of truth; drainer is a follower.

# Consequences

## 正の効果

- Substrate boundary preserved: no `@atproto/api` / `viem` / IPFS code on
  the Python side. The CLAUDE.md hard rule is honored cleanly.
- Organism heartbeat decoupled from substrate latency. A slow PDS write
  doesn't slow organism ticks.
- NDJSON queue is observable + tail-friendly. `tail -f` on a shard's
  queue file shows posts in real time.
- Crash isolation: drainer crash → posts queue; organism crash → posts
  already on disk. Neither loses data.
- TS drainer can reuse the existing `@etzhayyim/sdk` post path (same one
  `kotodama.AppBskyFeedPost` exposes on the TS app side).

## 負の効果 / コスト

- One extra hop: tick → NDJSON → drainer → PDS. Latency from organism
  tick to profile visibility is ~queue drain interval (target 5 s).
- NDJSON file disk usage. 18,342 organisms × ~12 posts/hr (conservative)
  × ~300 bytes/post = ~5 MB/hr per shard worst case. Bounded; drainer
  truncates after dispatch.
- Drainer is new code (Wave 3 deliverable). Until it lands, posts queue
  but don't reach PDS. The `logger` sink remains the default to avoid
  silent buildup.

## Out of scope

- The drainer TS impl itself (Wave 3, separate ADR).
- Prometheus metrics on the queue (drainer concern).
- Per-actor rate limiting at the drainer (drainer concern).
- Alternate transports (Unix socket, gRPC, Kafka) — NDJSON file is the
  Stage 2 minimum; revisit if scale demands.

# Alternatives Considered

## A. Direct HTTP from Python to `atproto.etzhayyim.com/xrpc/...`

却下理由: violates CLAUDE.md substrate boundary
("Direct `@atproto/api` ... from app code: prohibited"). Even though
HTTP isn't an import, the spirit of the rule is "Python organism does
not touch atproto directly" — bypass would corrupt the substrate
contract.

## B. Extend `MstCheckpointSaver` socket protocol with a `post` op

却下理由: conflates LangGraph checkpoint state (per-thread) with post
emission (per-actor). Different lifecycles (checkpoint is read-write,
post is append-only). Different drainer schedules. Different failure
modes. Separate file queue is cleaner.

## C. Wait for `@etzhayyim/sdk` Python binding

却下理由: indefinite blocker. The NDJSON queue is shippable today and
the drainer can be written in TS using the existing SDK.

# References

- ADR-2605232345 — UNSPSC actor as ecosystem organism (Wave 1)
- ADR-2605240000 — UNSPSC organism fleet mass-deploy (Wave 2)
- ADR-2605171800 — MstCheckpointSaver IPC sidecar pattern
- ADR-2605172100 — `@etzhayyim/sdk` substrate rules
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/checkpointer/mst_saver.py` — IPC reference
- `40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/organism/post_sink.py` — this ADR's deliverable
