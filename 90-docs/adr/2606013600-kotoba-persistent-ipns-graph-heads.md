---
id: adr-2606013600-kotoba-persistent-ipns-graph-heads
title: "ADR-2606013600: kotoba durable IPNS graph heads — disk-persistent registry replaces in-memory default"
status: active
doc_type: adr
topic: kotoba-ipns-head-durability
authoritative: true
last_verified: 2026-06-01
priority: 4.5
axis: architecture
weight: 0.45
priority_note: "Datomic graph heads (and therefore the yoro feed) survive a kotoba restart instead of being lost with the in-memory IPNS registry."
authoritative_for:
  - kotoba-ipns-registry-durability
depends_on:
  - adr-2606013200-yoro-kotoba-feed-readpath-migration
  - adr-2605312345-kotoba-datom-first-class-canonical-state
related:
  - "40-engine/kotoba/crates/kotoba-ipfs/src/ipns.rs"
supersedes: []
superseded_by: []
---

# ADR-2606013600: kotoba durable IPNS graph heads (disk-persistent registry)

**Status**: active
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

A kotoba datomic graph is addressed by an IPNS name that resolves to the latest
**commit CID** (the graph *head*). Commit blocks are durable in the cold tier
(Kubo), but the head pointer lived in `InMemoryIpnsRegistry` — an
`Arc<RwLock<HashMap>>` with **no persistence**. So on a kotoba restart the head
was lost: `datomic.datoms` returned `404 "no distributed Datomic/IPNS head for
graph"` even though every block was still stored. Concretely, the yoro feed
(ADR-2606013200) went empty after each restart and had to be re-ingested.

`KuboIpnsRegistry` (KOTOBA_IPNS=kubo) can publish heads to Kubo IPNS, but it is
DHT-bound (slow), needs per-name `ipfs key gen`, and its own doc warns that a
missing alias mapping makes reads 404 "even though the data is durably stored."
For a single node the simplest reliable durability is local disk.

# Decision

**Add a disk-persistent IPNS registry and make it the default.**

- `PersistentIpnsRegistry` (`crates/kotoba-ipfs/src/ipns.rs`): keeps records in
  memory (fast resolve + the same monotonic-sequence stale-guard as the
  in-memory registry) **and mirrors every successful publish to a JSON file**
  (atomic temp-file + rename); the file is reloaded at construction. Persisted
  records keep their Ed25519 signature, so a wrapping `SignedIpnsRegistry`
  re-verifies them on reload. File format: a JSON array of `IpnsRecord`.
- Server selection (`KOTOBA_IPNS`):
  - `kubo` → `KuboIpnsRegistry` (distributed IPNS, unchanged),
  - `memory` → `InMemoryIpnsRegistry` (explicit ephemeral opt-out; tests),
  - **unset (default)** → `PersistentIpnsRegistry` at
    `${KOTOBA_STORE_PATH}/ipns-heads.json`; falls back to in-memory only when
    `KOTOBA_STORE_PATH` is unset (with a warning).

The in-memory-by-default behaviour is **pruned**: a node with a store path is
durable without any extra env.

# Consequences

- **Datomic graph heads survive restart.** The yoro feed no longer needs
  re-ingestion after a kotoba restart (head from `ipns-heads.json` + blocks from
  Kubo cold tier ⇒ full recovery). Verified: transact → restart → `datomic.datoms`
  still resolves the head.
- Durability is **node-local** (single JSON file on `KOTOBA_STORE_PATH`). It is
  not distributed consensus; `KOTOBA_IPNS=kubo` remains the path for
  cross-node/public IPNS. The two can layer later (persist locally + publish to
  Kubo).
- Atomic writes (temp + rename) prevent head-file corruption on crash. The whole
  map is rewritten per publish — fine at graph-count scale; if head churn ever
  dominates, switch to per-name files or an append log.
- Block durability still depends on the cold tier (Kubo) being reachable on
  publish; if Kubo is down, blocks are hot-only and a restart still loses data
  regardless of the head. (Operational: keep the Kubo daemon up — see
  KOTOBA-FEED-DEPLOY.md.)

# Alternatives Considered

- **KOTOBA_IPNS=kubo as the default.** Rejected as the default: DHT latency,
  per-name key-gen, and the documented alias-mapping 404 failure mode make it
  heavier and less reliable than a local file for a single node. Kept as an
  opt-in for distributed publishing.
- **Persist into sled / the KSE block store.** The head is a tiny mutable
  pointer, not content-addressed block data; a plain JSON file on the existing
  store path is simpler and avoids entangling mutable-name state with the
  immutable block store.
- **Rely on WAL replay to rebuild heads.** WAL replay restores `QuadStore`
  state, but the datomic IPNS head was never persisted, so replay could not
  reconstruct it — this ADR persists the head itself.

# References

- ADR-2606013200 (yoro feed kotoba read-path; the feed that was emptied on restart)
- ADR-2605312345 (kotoba Datom log = first-class canonical state)
- `40-engine/kotoba/crates/kotoba-ipfs/src/ipns.rs` (`PersistentIpnsRegistry`)
- `40-engine/kotoba/crates/kotoba-server/src/server.rs` (registry selection)
