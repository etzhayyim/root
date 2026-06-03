---
id: adr-2604241121-repo-commit-stays-on-pds
title: "ADR: Repo commit stays on PDS — write-path singleton invariant (why chat/signal/actor Workers only own reads)"
status: proposed
doc_type: adr
topic: service-topology
authoritative: true
last_verified: 2026-04-24
authoritative_for:
  - Why AT Protocol `com.atproto.repo.*` commits must stay on the PDS Worker
  - Why chat.etzhayyim.com / signal.etzhayyim.com / actor Workers only serve reads + non-commit state
  - Split-service boundary rule — what can move out of PDS and what can't
  - Conditions under which this invariant could ever be revisited
related:
  - adr-2604241038-yoro-pds-ideal-topology
  - adr-2604231828-appview-domain-separation-bsky-etzhayyim-ai
  - adr-2604231811-atproto-extension-service-layers
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-0041-pds-commit-content-addressed-pk
supersedes: []
superseded_by: []
---

# Context

ADR-2604241038 Phase δ splits `chat.bsky.convo.*` and `com.etzhayyim.signal.*`
off the PDS into dedicated Workers (`chat.etzhayyim.com`, `signal.etzhayyim.com`).
Phase δ2 / δ3 migrated the **read** handlers (`listConvos`, `getConvo*`,
`getMessages`, `listDevices`, `getPrekeyBundle*`, `getIdentityFingerprint`)
but **writes** (`sendMessage`, `acceptConvo`, `leaveConvo`,
`muteConvo`, `unmuteConvo`, `addReaction`, `removeReaction`,
`updateRead`, `updateAllRead`, `deleteMessageForSelf`,
`registerPrekeys`, `replenishOtpks`, `ensureDevice`, `revokeDevice`,
`renameDevice`, `setEncryption`, `verifyIdentity`, `rotateGroupKey`)
stayed on the PDS. The chat / signal Workers return `501` for every
write and the PDS's routing-table `fallback: "local"` policy falls the
request through to `ctx.comAtprotoRepoCreateRecord` — the PDS's
repo-MST + blob + firehose commit pipeline.

This is not an accident of migration phasing. It's a deliberate
invariant. The ADR makes that invariant explicit and names the
conditions under which it could ever be revisited.

# The invariant

> **A single Worker (the PDS) owns the write path for every AT
> Protocol repo.** All repo commits (`com.atproto.repo.createRecord`,
> `applyWrites`, `deleteRecord`, `putRecord`, `uploadBlob`) route
> through that Worker. Downstream Workers (AppView, chat, signal,
> actor) serve reads, non-commit state writes, and domain data that
> lives outside the AT Protocol repo (Hyperdrive-direct per ADR-0036).

## What belongs on the PDS

- `com.atproto.*` — native AT Protocol surface (repo CRUD, sync, identity)
- NSID-addressed record writes that land in `vertex_repo_commit` +
  `vertex_repo_record` with an MST + signed commit:
  - `chat.bsky.convo.sendMessage` / `acceptConvo` / `leaveConvo` /
    `muteConvo` / `unmuteConvo` / `updateRead` / etc. (via
    `ctx.comAtprotoRepoCreateRecord`)
  - `com.etzhayyim.signal.registerPrekeys` / `replenishOtpks` /
    `ensureDevice` / `setEncryption` / etc.
  - Anything the client SDK encodes as "create a record in the user's
    repo, firehose it, persist the MST block"

## What belongs downstream

- `app.bsky.*` reads — AppView computed views over `vertex_repo_record`
  (ADR-2604231828)
- `chat.bsky.convo.*` reads + non-commit state (read receipts, typing
  indicators if they don't get materialized as repo records)
- `com.etzhayyim.signal.*` key lookups + device metadata reads
- `com.etzhayyim.vault.*` — isolated ciphertext store, no AT repo
  involvement (ADR-2604231811 Layer 12)
- Domain data writes that ADR-0036 routes directly to Hyperdrive
  bypassing PDS: `com.etzhayyim.apps.<actor>.<kind>` collection writes that
  live in `vertex_<actor>_<kind>` typed tables, not AT records

# Why

Four reasons the PDS must remain the only writer per repo. None of
them are about code locality; all of them are about the AT Protocol
data model.

## 1. MST single-writer invariant

An AT Protocol repo is a signed Merkle Search Tree. Every commit:

1. reads the current root CID,
2. mutates the MST (insert/delete leaves),
3. signs the new root with the user's signing key,
4. appends a commit record with the new root + parent CID,
5. emits to the firehose in monotonically increasing `seq` order.

If two Workers independently commit to the same repo in parallel, they
either (a) both read the same root and produce forked commits with the
same parent, creating a fork the firehose can't linearize, or (b) race
on `seq` allocation and produce duplicate seqs. ADR-0041 documents the
1/10-persistence-drop incident we hit when CF isolates independently
read `MAX(seq)` and collided. That was within a **single** Worker's
parallel isolates; moving writes across Workers multiplies the problem.

A multi-writer repo is a research-grade consensus problem (Paxos /
Raft / CRDT-with-conflict-resolution). AT Protocol explicitly designs
it out by pinning the writer to one host. Following the spec is not
optional here.

## 2. Firehose linearization

`com.atproto.sync.subscribeRepos` streams commits to all AppView /
Relay / 3rd-party subscribers in `seq` order per repo. Subscribers
rely on this ordering to maintain indexes (AppView's `mv_feed_with_author`,
relay's event log, etc.). A single writer trivially produces a totally
ordered event log; two independent writers produce interleaved events
that subscribers would need explicit sequencing from some coordinator
to recombine — which is just "the PDS" under a different name.

## 3. Signing key custody

The user's signing key (`vertex_etzhayyim_key_signing`, envelope-encrypted
with `SS_REPO_SIGNING_KEK` per ADR-0010) is stored in the PDS's D1
`SIGNING_KEYS_D1` binding. Moving write authority to chat or signal
Workers means either:

- (a) shipping the envelope-encrypted key to each Worker (each must
  decrypt with `SS_REPO_SIGNING_KEK`; the key leaves one place and
  lives in three), or
- (b) having each Worker call back to the PDS for per-commit signing
  (which is just a PDS-serving-as-signing-service architecture —
  i.e. the commit still flows through the PDS, just via an extra
  network hop).

Option (a) widens the blast radius of a Worker compromise by 3x.
Option (b) is the current architecture with extra latency.

## 4. Commit content-addressed PK + graph-worker consumer invariants

ADR-0041 makes `vertex_repo_commit.vertex_id` content-addressed:
`${repo}:${collection}:${rkey}:${action}`. The graph-worker consumer
(`ORDER BY seq ASC`) tolerates duplicate rows (same content → same
PK → dedup) and gap rows (stale seqs). This works because all writes
go through one Worker whose isolates only disagree on `seq`, never on
content. Multi-writer would break the content-addressing (two Workers
producing different actions for the same rkey) or force a
cross-Worker deduplication layer that doesn't exist.

# Decision

The write path for AT Protocol repos is a **singleton on the PDS
Worker**. Downstream Workers (AppView, chat, signal, actor hostname)
serve reads and non-repo state only. Migration ADRs (ADR-2604231828,
ADR-2604241038) preserve this rule implicitly by only moving read
methods; this ADR makes the rule explicit so future split proposals
don't quietly violate it.

## Operational consequences

- Chat / signal Workers return `501 MethodNotImplemented` for all
  commit-producing NSIDs. PDS's routing-table `fallback: "local"`
  routes the request through `dispatchViaRoutingTable` and lands on
  the local handler chain (`handlers/pds/server.ts` XRPC_CHAT_METHODS
  / `handlers/etzhayyim/index.ts` XRPC_SIGNAL_WRITE_METHODS). The `501 →
  fallback` contract is the mechanism that keeps the invariant alive
  even when a downstream Worker is deployed with the write surface
  stubbed out.

- Actor Workers (`com.etzhayyim.apps.<actor>.*` via `pipethroughActorWorker`)
  own their *domain* writes via ADR-0036 Hyperdrive-direct INSERT into
  `vertex_<actor>_<kind>` typed tables. These are **not** AT repo
  commits — they don't land in `vertex_repo_commit`, aren't
  firehose-emitted, aren't signed. That's why ADR-0036 could move them
  out of the PDS while this ADR keeps repo commits locked down. The
  distinction is: "AT record / can a 3rd-party AppView subscribe
  via firehose?" If yes → PDS. If no → actor Worker.

- PDS write throughput is a real scaling ceiling. Today it's fine;
  content-addressed commits (ADR-0041) brought 10/10 persistence under
  10-parallel bursts. When writes reach a level that a single CF
  Worker class can't handle, the answer is **not** to split writes
  across Workers — it's to shard repos across PDS instances (each one
  still the singleton for its repo set). That's the AT Protocol
  federation answer.

- `ctx.comAtprotoRepoCreateRecord` stays the only entry point. Any
  write-producing handler (including ones defined in `handlers/etzhayyim/*`
  that don't live in the `com.atproto.*` namespace) calls it, so the
  MST + firehose invariants are maintained structurally rather than
  by convention.

# When this invariant could be revisited

Only when at least one of the four reasons above no longer applies:

1. AT Protocol spec adopts a multi-writer repo model (CRDT-like
   conflict resolution, multi-head Merkle). This is upstream work,
   not ours.
2. Firehose subscribers stop requiring linearization per repo
   (i.e. AppView index can tolerate out-of-order commits and
   reconcile). Possible but expensive and would re-open issues we've
   already solved.
3. Signing key custody moves to a Vault-like shared service with
   per-commit delegation, removing the "ship the key everywhere"
   objection. ADR-2604231811 Layer 12 (Secret Vault) already exists,
   so this is *technically* feasible today, but the other three
   reasons still stand.
4. Cloudflare Workers adopt multi-isolate atomic writes to a shared
   seq counter that doesn't require PDS-side MAX(seq) scanning.
   Unlikely to ship as a platform primitive.

If a future proposal claims any of these hold, the proposal must
explicitly answer the other three — not just the one it solves.

# Alternatives considered (and rejected)

## A1. Move chat writes into chat.etzhayyim.com

- **Pros:** isolation, chat latency detached from PDS write queue.
- **Cons:** violates every one of the four reasons in #Why. Worst of
  the four: multi-writer MST, either forks or needs a consensus
  layer. **Rejected.**

## A2. Chat / signal Worker calls PDS over HTTPS (not service binding) for commits

- **Pros:** avoids the circular-dep class that ADR-2604231828 ruled
  out (service binding creates subrequest depth loop).
- **Cons:** the commit still flows through the PDS — the HTTPS hop
  is extra latency with no architectural gain. Same as "PDS owns
  writes" except slower. **Rejected.**

## A3. Write-outbox pattern: each Worker writes an event, async PDS consumer commits

- **Pros:** synchronous per-Worker path, PDS becomes an async
  consumer.
- **Cons:** loses synchronous commit semantics that AT Protocol
  clients depend on (`createRecord` returns `uri` + `cid` of the
  committed record; async outbox can't). Firehose ordering becomes a
  consumer problem. **Rejected** unless AT Protocol spec changes.

## A4. Per-namespace MST (each Worker owns its own MST for its own
    collection prefix)

- **Pros:** each Worker truly single-writer for its slice.
- **Cons:** breaks the "one repo per DID" AT Protocol primitive.
  Client SDKs (`@atproto/api`) expect a single MST per DID. Relays
  expect one firehose stream per DID. Not compatible with the
  federation surface we actually target. **Rejected.**

## A5. Status quo (this ADR's decision)

- **Pros:** zero AT Protocol spec deviation, preserves ADR-0041 +
  ADR-0036 invariants, reads still scale out via split Workers.
- **Cons:** PDS is a write ceiling; when we hit it, shard across PDS
  instances (the federation answer), not across Workers within one
  instance.
- **Chosen.**

# Non-goals

- Scaling PDS write throughput beyond the current content-addressed
  commit path (ADR-0041 covers that; if we hit a new ceiling, write a
  new ADR).
- Moving **reads** back onto the PDS — that's rolling back Phase δ,
  explicitly out of scope.
- Letting downstream Workers bypass PDS for writes under an "it's
  small" exception — there is no small exception; the four reasons
  apply to 1 write/year the same as 1M/day.

# References

- ADR-0036 — Worker-direct Hyperdrive persistence (domain data
  bypasses PDS; repo commits don't)
- ADR-0041 — Content-addressed PK for `vertex_repo_commit` (solves the
  single-writer MAX(seq) race within one Worker; doesn't solve
  multi-writer)
- ADR-2604231828 — AppView split (reads moved, writes stayed)
- ADR-2604241038 — Topology contracts; this ADR is the design
  rationale behind Contract 1 "1 Worker = 1 layer" applied to the
  write layer.
- AT Protocol spec §Sync + §Repo — the upstream source of the
  single-writer requirement.
