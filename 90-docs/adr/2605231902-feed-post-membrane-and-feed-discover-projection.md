---
id: adr-2605231902-feed-post-membrane-and-feed-discover-projection
title: "ADR-2605231902: app.bsky.feed.post membrane + feed-discover projection — first end-to-end kotoba-datomic §4 + projection slice"
status: proposed
doc_type: adr
topic: feed-post-membrane-and-feed-discover-projection
authoritative: true
last_verified: 2026-05-23
priority: 7.5
axis: substrate-execution
weight: 0.8
authoritative_for:
  - "First kotoba-datomic §4 (L1+L2+L3) membrane implementation contract — app.bsky.feed.post"
  - "First kotoba-datomic-projection L1 conformance instance — feed-discover"
  - "Membrane → projection wire (verdict sidecar drives projection)"
depends_on:
  - adr-2605170900-etzhayyim-root-adr-canonical-home
  - adr-2605171800-langgraph-mst-ipfs-l2-anchor-pipeline
  - adr-2605172000-etzhayyim-rw-free-substrate
  - adr-2605191655-mst-projector-phase2-design
  - adr-2605192100-etzhayyim-mission-charter
  - adr-2605192200-etzhayyim-ip-free-release-charter-rider
  - adr-2605192400-etzhayyim-eros-gore-council-judging
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231500-kotoba-datomic-projection
related:
  - 70-tools/seed-post/
  - 00-contracts/policies/app/bsky/feed/
  - 20-actors/magatama/cells/feed_post/
  - 50-infra/mst-projector/projection/
  - 00-contracts/lexicons/com/etzhayyim/membrane/
  - 00-contracts/lexicons/com/etzhayyim/projection/
supersedes: []
superseded_by: []
---

# ADR-2605231902: app.bsky.feed.post membrane + feed-discover projection — first end-to-end kotoba-datomic §4 + projection slice

**Status**: proposed
**Date**: 2026-05-23
**Deciders**: Jun Kawasaki

## Context

`https://etzhayyim.com/` was returning `{"feed":[]}` from
`app.bsky.feed.getTimeline` even though all upstream Workers (yoro SPA,
`etzhayyim-did-web`, `yoro-xrpc-adapter`, `@etzhayyim/yoro-rw-free`) were
operating correctly. Two underlying gaps:

1. **No write path was exercised end-to-end.** The substrate read path
   (`Etzhayyim.read` → PDS `listRecords`) was working, but no
   `app.bsky.feed.post` record existed in the operator's MST. There was
   no operator-facing CLI to seed one, and `Etzhayyim.write` had no
   kotoba-datomic §4 membrane in front of it.

2. **Discover was bounded to a single DID.** [ADR-2605231400](/90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md)
   names the substrate composition and [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md)
   defines the derived-read-path contract. Neither named a concrete first
   instance for `app.bsky.feed.post`. `yoro-rw-free/src/feed.ts:8-10`
   carried the TODO comment: *"Cross-DID discovery is a Relay /
   mst-projector index concern, tracked in ADR-2605191358 — until that
   lands, 'Discover' = posts published into the operator's own MST."*

The user request — "kotoba-datomic ベースで投稿を表示するには" — surfaced
both gaps and required them to be addressed together: seeding without a
membrane skips the L3 verdict; a membrane without a projection still
only shows the operator's own posts.

## Decision

Land four tightly-coupled implementation items as a single wave, each
already a concrete ADR-aligned deliverable on its own but mutually
reinforcing when shipped together:

### 1. Seed-post CLI (`70-tools/seed-post/`)

Operator-side Node CLI that writes a single `app.bsky.feed.post` record
into the configured DID's MST via `@atproto/api` `createRecord`. Reads
credentials from macOS Keychain (`service=etzhayyim, account=PDS_HANDLE`
/ `account=PDS_APP_PASSWORD`) — no platform-held keys per
[ADR-2605231525](/90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md).

Intentionally **does not** call the membrane during this transition
window — Step 4 (server-side signing capability gate, pending Council)
will route writes through the membrane authoritatively. Until then the
membrane runs in **trail-and-attest mode**: every write that lands in
the MST gets a sidecar verdict record, and the projection enforces
rejection downstream.

### 2. kotoba-datomic §4 membrane for `app.bsky.feed.post`

The first concrete `(L1, L2, L3)` triple:

| Layer | Source | Notes |
|---|---|---|
| **L1 schema** | `00-contracts/lexicons/app/bsky/feed/post.json` | Pre-existing vendored Bluesky lexicon |
| **L2 policy** | `00-contracts/policies/app/bsky/feed/{policy.rego, test.rego}` | OPA-evaluable. Charter Rider §2(a)/(b)/(c)/(d)/(f)/(h), advertising, eschatology assertions (per ADR-2605192100 §1.15), gore self-label (per ADR-2605192400). Allow-context exemption set per category. 8/8 `opa test` PASS |
| **L3 deterministic cell** | `20-actors/magatama/cells/feed_post/cell.py` | LangGraph Pregel cell. Strict-determinism contract: no clocks (`createdAt` from input only, verdict-record `createdAt` from `ctx.now` supplied by dispatcher), no RNG, no LLM in verdict path. Content-addressed `verdictCid = sha256-<hex>` of canonical JSON of `(record_cid, kind, reason, sorted_evidence)`. 18/18 pytest PASS |
| **Sidecar lexicon** | `00-contracts/lexicons/com/etzhayyim/membrane/verdict.json` | `com.etzhayyim.membrane.verdict` records emitted by L3, attesting the verdict for one record CID |
| **Fleet registration** | `50-infra/murakumo/fleet.toml [cells.FeedPostCell]` | Placed on `levi` (membrane-adjacent role: AuditWitnessCell + KaizenObserverCell), healthz_port 13017, `determinism = "strict"` |

Three semantic verdict kinds:

- **`approve`** — all three layers accept; record may be promoted into
  projections.
- **`reject`** — any Charter Rider hit (after allow-context demotion) or
  schema violation. Projection drops the entry.
- **`escalate`** — semantic appraiser detected a `gore` self-label
  *with* educational context (ADR-2605192400 §3 override). The Rego gore
  violation is suppressed and the verdict routes to
  `CouncilDeliberationCell` for ratification.

The Python `_python_rego_mirror` mirrors the Rego module so the cell can
run without OPA when no sidecar is configured. CI hook
`charter-rider-rego-mirror` diffs the two pattern sets at build time;
drift fails the build (placeholder — hook itself is future work).

### 3. `feed-discover` kotoba-datomic-projection (L1 conformance)

The first concrete instance of [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md):

- **Emitter**: `50-infra/mst-projector/src/feed-discover.ts` — extends
  the existing mst-projector daemon with a cross-DID in-memory sorted
  index of `app.bsky.feed.post` records (binary-search insertion;
  cap 500 items so one snapshot fits in ~300 KiB; lazy hydration via
  `com.atproto.repo.getRecord` since the firehose carries only the CID).
  Snapshots emit on shard flush boundary via `createRecord` against the
  projector DID.
- **Output lexicon**: `00-contracts/lexicons/com/etzhayyim/projection/feedDiscover.json` —
  `com.etzhayyim.projection.feedDiscover` record with `items[]` sorted
  by `indexedAt` desc, `cursor` + `firstSeq` for replay resume, and
  per-item `verdict` annotation.
- **Manifest**: `50-infra/mst-projector/projection/kotoba-datomic-projection.edn` —
  declares lexicon / source collections / supplementary collections
  (membrane sidecar) / rebuild runbook / ADR provenance / intentional
  non-determinism (snapshotAt excluded from L2 comparator).
- **Rebuild runbook**: `50-infra/mst-projector/projection/REBUILD.md` —
  documents firehose-from-cursor-0 replay; no operator-held state required.
- **L1 conformance smoke**: `50-infra/mst-projector/test/feed-discover.replay.test.ts` +
  `test/fixtures/feed-discover.firehose.json` + `test/golden/feed-discover.snapshot.json` —
  fixed firehose fixture (3 DIDs × 3 posts + update + delete + 3
  verdicts) replayed and byte-compared against golden. Regenerate with
  `ETZ_REGEN_GOLDEN=1 pnpm test`. Per
  [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md) §"Three
  conformance levels" L1: "Rebuild tool exists and is exercised in CI" —
  this test IS the CI exercise.
- **Read consumer**: `60-apps/etzhayyim-project-yoro/rw-free/src/feed.ts`
  `getTimeline` + `getDiscoverFeed` consult
  `EtzhayyimConfig.projectionDiscoverDid` when set (wired via
  `@etzhayyim/sdk-auth` `SessionEnv.PROJECTION_DISCOVER_DID` and the
  `yoro-xrpc-adapter` env). Falls back to single-actor `collectFeed`
  when projector unconfigured — zero behaviour change for existing
  deployments until env var is set.

### 4. Membrane → projection wire

`feed-discover.ts` `applyVerdictEvent()` consumes
`com.etzhayyim.membrane.verdict` firehose events, fetches the verdict
record via `makeAtpVerdictFetcher`, and dispatches to `applyVerdict()`:

| Verdict | Projection effect |
|---|---|
| `approve` | Annotate `items[i].verdict = "approve"`. Record stays. |
| `reject` | Drop the entry from the index. Will not appear in next snapshot. |
| `escalate` | Annotate `items[i].verdict = "escalate"`. Record stays; flags Council review downstream. |
| (no verdict observed yet) | `items[i].verdict = "unverdicted"` — common during the trail-and-attest transition window |

The wire closes the loop: a write lands in MST → membrane sees it on
firehose → emits verdict sidecar → projector sees verdict on firehose →
mutates projection accordingly → next snapshot reflects the verdict →
`getDiscoverFeed` returns the post-verdict state.

### Adapter cutover (operational, this wave)

As part of this wave, `yoro-xrpc-adapter`'s `PDS_URL` was flipped from
`https://pds.etzhayyim.com` (religious-corp PDS, 0 repos, transition-
window placeholder) to `https://atproto.etzhayyim.com` (where
`did:web:yoro.etzhayyim.com`'s DID-doc-declared PDS endpoint actually
points). Verified live via `x-etzhayyim-substrate: mst-ipfs-l2`
response header. The eventual move of yoro's repo to `pds.etzhayyim.com`
is a separate cutover requiring DID-doc update + repo migration; out of
scope here.

## Consequences

### Positive

- **First end-to-end kotoba-datomic §4 instance** — concrete `(L1, L2, L3)`
  triple shipped for one NSID. Future NSIDs follow the same template:
  add Rego, add Pregel cell, register in fleet.toml.
- **First L1-projection in CI** — the L0→L1 conformance step is no
  longer hypothetical; the manifest + golden + replay test are
  exercised on every push. Future projections follow the same template.
- **Membrane → projection wire is the canonical pattern** — Charter
  Rider verdicts deterministically propagate to read paths without
  out-of-band scheduling. Rejected posts disappear from Discover
  immediately on next snapshot boundary.
- **Trail-and-attest mode is honest about its limits** — the membrane
  runs after the write rather than gating it; the user-facing window of
  exposure is `now()` minus snapshot cadence. When ADR-2605231525's
  server-side signing-capability gate lands, the seed CLI (and any
  client write path) routes through L3 pre-flight authoritatively.
- **Substrate adapter cutover is finally aligned with the DID doc** —
  before this wave, the adapter pointed at the future-target PDS that
  had 0 repos. Now it points at the PDS the DID doc actually advertises,
  which is what AT Protocol federation expects.

### Negative

- **Two firehose subscriptions on the projector node** — mst-projector
  Phase 2 already subscribed for shard snapshots; the feed-discover and
  verdict subscribers piggy-back on the same connection but add fetch
  round-trips (`getRecord` per indexed post + per verdict). Acceptable
  at current volume (≪100 posts/day during transition); revisit if
  projector becomes I/O-bound.
- **Single in-memory index per process** — the projection state is
  ephemeral and resets on projector restart. Rebuild is from firehose
  cursor 0 per `REBUILD.md`. For a >1 GiB-of-posts future, the index
  needs persistent storage; the rebuild contract still holds because
  the manifest mandates rebuildability.
- **Trail-and-attest window** — between write and verdict emission,
  rejected content is visible at `https://etzhayyim.com/` if a Discover
  read happens to land in that window. Mitigation: the seed CLI is the
  only operator-facing write path today, and operators are expected to
  pre-check content. The window closes when the L3 pre-flight gate lands.
- **Rego ↔ Python mirror drift risk** — `policy.rego` and
  `_python_rego_mirror()` in `cell.py` carry the same pattern set in two
  places. CI hook to enforce diff is future work; for now the unit tests
  pin both sides against a shared set of expected cases.

### Neutral

- **Does not change [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) prohibitions** —
  the projection is explicitly carved out as a derived-read path per
  [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md), not a state store.
- **Council vote not required** — additive lexicons, additive policy,
  additive projection. The Charter Rider categories enforced are the
  same ones already in `pymagatama.organism.sensors.charter_rider`;
  this ADR ships a Rego encoding alongside.

## Alternatives Considered

### A. Skip the projection, ship only the membrane

Status: rejected. Without the cross-DID projection, `Discover` remains
bounded to the operator's own DID — the original symptom (empty feed at
`https://etzhayyim.com/` even with seeded posts from other DIDs) is not
fully addressed. Two single-DID writers and three readers means three
out of three Discover reads see one writer's view rather than the union.

### B. Skip the membrane, ship only the projection

Status: rejected. Without the L3 verdict layer, Charter Rider §2(a)..(h)
content can be promoted into the projection without any attestation
trail. The substrate then becomes the *only* enforcement layer, which is
fragile (Rego eval lives outside the daemon; cell determinism guarantees
disappear). The verdict sidecar is what lets future readers
*verify*, not just trust, the projection.

### C. Single-DID rendering ("just seed one post")

Status: rejected — the user explicitly called this out as Step 1 of a
3-step request; Steps 2 and 3 are the membrane and projection. Shipping
only Step 1 would close the surface symptom without addressing the
architectural gap.

### D. Use Workers KV or a Durable Object for the projection

Status: rejected per [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md)
§"Prohibited even for projections" — *"Workers KV writes are fire-and-
forget without commit ack, which violates (2). KV is acceptable for
read-only projection caches but not as the write surface a Worker
confirms back to the client."* The current in-memory + AT-record-emit
shape keeps the projection's canonical state in the projector DID's MST
(which is itself kotoba-datomic-chain), so the projection sits one layer of
indirection from the firehose and is replayable.

### E. Use Kotoba/Datomic for the projection (Bluesky-AppView pattern)

Status: deferred. The ADR-2605231500 §"Allowed substrates for
projections" table explicitly lists RW as suitable for the
range/aggregate/spatial cohort, and acknowledges that the Bluesky
AppView pattern is the canonical reference. For feed-discover, the
data volume is low enough (≪500 active posts in the current transition
window) that an in-memory index is sufficient and the rebuild story is
simpler. Re-evaluate when a single snapshot record exceeds the AT
record size budget (~256 KiB), at which point sharding the projection
across multiple emitter DIDs or migrating to a RW-backed projection
both become reasonable.

## References

- [ADR-2605170900](/90-docs/adr/2605170900-etzhayyim-root-adr-canonical-home.md) — open-scope ADR canonical home
- [ADR-2605171800](/90-docs/adr/2605171800-langgraph-mst-ipfs-l2-anchor-pipeline.md) — MST→IPFS→L2 anchor pipeline
- [ADR-2605172000](/90-docs/adr/2605172000-etzhayyim-rw-free-substrate.md) — rw-free substrate hard rules
- [ADR-2605191655](/90-docs/adr/2605191655-mst-projector-phase2-design.md) — mst-projector Phase 2 (true MST root + CAR)
- [ADR-2605192100](/90-docs/adr/2605192100-etzhayyim-mission-charter.md) — mission charter (§1.13 Eros/Gore, §1.15 non-eschatological)
- [ADR-2605192200](/90-docs/adr/2605192200-etzhayyim-ip-free-release-charter-rider.md) — Charter Compliance Rider §2(a)..(h)
- [ADR-2605192400](/90-docs/adr/2605192400-etzhayyim-eros-gore-council-judging.md) — gore educational-context override
- [ADR-2605231400](/90-docs/adr/2605231400-kotoba-datomic-holochain-iso-substrate.md) — kotoba-datomic SPEC §4 membrane
- [ADR-2605231500](/90-docs/adr/2605231500-kotoba-datomic-projection.md) — projection conformance levels
- [ADR-2605231525](/90-docs/adr/2605231525-no-server-key-religious-corp-architecture.md) — no platform-held keys
- `70-tools/seed-post/` — operator CLI
- `00-contracts/policies/app/bsky/feed/{policy.rego, test.rego}` — L2
- `20-actors/magatama/cells/feed_post/{cell.py, test_cell.py}` — L3
- `00-contracts/lexicons/com/etzhayyim/membrane/verdict.json` — sidecar lexicon
- `00-contracts/lexicons/com/etzhayyim/projection/feedDiscover.json` — projection lexicon
- `50-infra/mst-projector/src/feed-discover.ts` — projection emitter
- `50-infra/mst-projector/projection/{kotoba-datomic-projection.edn, REBUILD.md}` — manifest + runbook
- `50-infra/mst-projector/test/feed-discover.replay.test.ts` — L1 conformance smoke
- `60-apps/etzhayyim-project-yoro/rw-free/src/feed.ts` — projection read path

## Implementation status (this ADR)

| # | Item | Status |
|---|---|---|
| 1 | `70-tools/seed-post/` CLI | landed |
| 2 | L2 Rego `policy.rego` + 8/8 `opa test` | landed |
| 3 | L3 cell + 18/18 pytest | landed |
| 4 | `com.etzhayyim.membrane.verdict` lexicon | landed |
| 5 | `FeedPostCell` registration in `fleet.toml` on `levi` | landed |
| 6 | `com.etzhayyim.projection.feedDiscover` lexicon | landed |
| 7 | `feed-discover.ts` emitter + manifest + REBUILD.md (L0) | landed |
| 8 | Membrane → projection wire (`applyVerdictEvent`) + 6 unit tests | landed |
| 9 | L1 conformance smoke (golden replay) + L0→L1 bump | landed |
| 10 | yoro-xrpc-adapter PDS_URL → atproto.etzhayyim.com + redeploy | landed (live since 2026-05-23T09:52Z) |
| 11 | Seed-post end-to-end verification | **blocked on operator Keychain provisioning** |
| 12 | `charter-rider-rego-mirror` CI hook | future work |
| 13 | L2-projection (1% random-slice byte-identical replay) | future work |
| 14 | L3 pre-flight gate (ADR-2605231525 server-side signing capability) | future work |
