---
id: adr-2605301030-kotoba-kg-storage-session-52-entity-actor-graph
title: "ADR-2605301030: kotoba KG storage session — 53-entity actor/doctrine graph on a live datomic node, IPFS-pinned provenance, and the snapshot-of-hot commit discipline"
status: active
doc_type: adr
topic: kotoba-kg-storage-session
authoritative: true
last_verified: 2026-05-30
priority: 5.5
axis: operations
weight: 0.5
priority_note: "Session-closure ADR for a 12-iteration /loop that stood up 40-engine/kotoba as a live datomic (EAVT) storage node, loaded the repo's industry/actor/doctrine model into it as a queryable knowledge graph (53 distinct entities), pinned all provenance via DataLad + git-annex + sidecar IPFS (ADR-2605241500), and discovered + documented the kotoba commit snapshot-of-hot discipline plus a canonical seed + rehydrate recovery path. Records operational invariants future operators need before ingesting into kotoba."
authoritative_for:
  - kotoba operator runbook (serve via launchd, JWT-shaped auth tier, kg.ingest_batch + commit)
  - snapshot-of-hot commit discipline (commit seals hot Arrangement only; never partial-ingest+commit after restart)
  - kg-seed-v1.ndjson canonical SoT + rehydrate.sh disaster-recovery contract
  - kotoba CLI shadow-install + ad-hoc codesign requirement on Apple Silicon
depends_on:
  - ADR-2605262130 (kotoba storage substrate unification — engine, EAVT/AEVT/AVET/VAET, commit→ProllyTree)
  - ADR-2605241500 (dataset CID substrate — DataLad + git-annex + sidecar IPFS pinner)
  - ADR-2605215000 (Murakumo-only inference — kotoba-llm stays disabled)
  - ADR-2605292100 (kotoba v0.1.0 tag + Homebrew tap)
related:
  - adr-2605261000-labor-liberation-transition-mechanism
  - adr-2605301020-basic-high-income-imputed-and-commons-asset-doctrine
  - adr-2605192130-etzhayyim-tithe-redistribution
supersedes: []
superseded_by: []
---

# ADR-2605301030: kotoba KG storage session

**Status**: active
**Date**: 2026-05-30
**Deciders**: Jun Kawasaki

# Context

A 12-iteration `/loop` (session 2605291222) was tasked with: *stand up
`40-engine/kotoba`, use it as storage, persist data via its Datomic-style EAVT,
and for repo-worthy data persist via DataLad + IPFS remote pin.* The loop both
**built operational state** (a live node + a populated graph + pinned
provenance) and **discovered operational invariants** that were not documented
in the kotoba CLAUDE.md. This ADR records the durable outcome so the work is
reproducible and the pitfalls are not re-hit.

# Decision

## 1. kotoba runs as a launchd-supervised datomic storage node

- Binary: brew `kotoba 0.1.0` shadowed by a locally-built CLI at
  `~/.local/bin/kotoba` (PATH-precedes `/opt/homebrew/bin`). The p2p build
  (`cargo build -p kotoba-cli --features kotoba-server/p2p`) enables the
  libp2p mesh (QUIC + GossipSub + Kademlia).
- Service: `~/Library/LaunchAgents/com.etzhayyim.kotoba.plist` runs plain
  `kotoba serve` on :8077, store at `~/.local/kotoba-etzhayyim/sled`, IPFS
  cold tier at Kubo :5001, `KeepAlive` gated on the IPFS volume PathState.
- **Apple Silicon codesign**: copying a freshly-built binary with `cp`
  invalidates the ad-hoc signature → `Killed: 9` (SIGKILL) on exec, which
  surfaces as launchd `LastExitStatus = 9` crash-loop. Fix: re-sign after every
  install with `codesign --force --sign - ~/.local/bin/kotoba`.

## 2. The graph: 53 entities across 7 types

Loaded via `kg.ingest_batch` (NSID `com.etzhayyim.apps.kotobase.kg.ingest`) then
sealed with `kotoba commit`:

| type | n | source |
|---|---|---|
| supply-chain-analysis-actor | 4 | jukyu / supplychain / handotai / shosha |
| planetary-infra-producer | 1 | kuni-umi |
| tier-b-actor | 28 | repo CLAUDE.md Tier-B roster |
| constitutional-substrate | 6 | 50-infra religious-corp wave (TitheRouter … Constitution.sol) |
| core-actor | 5 | kotodama / kuni-umi / etzhayyim-sdk / kotodama-go / etzhayyim-bpmn-sdk |
| labor-liberation-stage | 7 | ladder L0..L6 (precededBy chain) |
| doctrine | 1 | Basic High Income (ADR-2605301020), linked to ladder/public-fund/tithe-router/land-registry |

Verified with SPARQL over the IPFS-backed cold path (SELECT DISTINCT,
GROUP BY, relation traversal). **Always query kg counts with `DISTINCT`** —
append-only datoms mean a re-asserted entity yields duplicate plain rows.

## 3. Auth tier is JWT-shaped, not crypto-verified

The Authenticated graph tier parses a Bearer token as a JWT and checks `sub` +
unexpired `exp`; it does **not** verify the signature. A structurally-valid
JWT (`base64url(header).base64url({"sub":...,"exp":...}).<anysig>`) is accepted.
A bare opaque string ("demo-token") is rejected 401. `kotoba commit` / `demo`
auto-mint an operator JWT from the Keychain identity.

## 4. commit is snapshot-of-hot — the central discipline (INVARIANT)

`QuadStore::commit()` (kotoba-graph/src/quad_store.rs:3150) seals **only the
current hot Arrangement** into the 4 ProllyTrees; it does **not** union with the
cold ProllyTree. Consequences:

- A normal restart is safe: `kotoba serve` restores the full graph from the
  sled checkpoint + WAL replay (`committed_seq`-gated). No action needed.
- **Pitfall (iter-8 incident)**: after a restart the hot Arrangement is empty.
  Ingesting a *partial* set and committing produces a NEW root containing only
  that partial set; the CommitDag head advances to it and cold-path queries see
  only the partial graph. Prior commit blocks remain intact in IPFS (recoverable),
  but the live head is wrong.
- **Operator rule**: never partial-ingest + commit after a restart. Either
  ingest the FULL intended graph in one session before committing, or run
  `rehydrate.sh` first to repopulate hot from the seed, THEN add, THEN commit.

## 5. Canonical seed + rehydrate recovery path

- `kg-seed-v1.ndjson` (under the dataset annex-store, IPFS-pinned) is the
  canonical single source of truth for the graph: one JSON record per entity
  (id, type, labels, claims, relations), sorted by id for determinism.
- `rehydrate.sh` loads the entire seed via one `kg.ingest_batch` then does one
  `kotoba commit` → a unified root containing the whole graph. Idempotent and
  restart-safe (verified 3× consecutively + across a hard `kill -9` + launchd
  respawn). Resolves kotoba bin by absolute path (launchd PATH lacks
  `~/.local/bin`).
- **Rejected**: wiring rehydrate into the launchd boot path. It is unnecessary
  (checkpoint restore already restores the full graph on normal restart) and
  added a heavy, hard-to-observe boot process that could mask real checkpoint
  issues. rehydrate.sh stays a MANUAL disaster-recovery tool.

## 6. Provenance: 11 IPFS-pinned ops rows

Every iteration's provenance (KG ingest records, the seed + tool, the incident
writeup, the design-decision writeup) is persisted via `e7m-dataset
publish-ipfs` → DataLad superdataset manifest row in
`90-docs/baien/datasets.jsonl` + sidecar IPFS recursive pins (file CID + map
CID), per ADR-2605241500. 11 `ops-*` rows total. PDS `datasetPin` emit stays
Phase-1 dry-run.

# Consequences

- kotoba is now a usable, restart-durable datomic KG store for repo metadata,
  with a documented operator runbook and a one-command recovery path.
- The snapshot-of-hot discipline is the single most important operator fact;
  it is now an authoritative invariant rather than tribal knowledge.
- A `kotoba-vm` LegacyQuad/LegacyQuadObject alias fix (committed on submodule
  branch `fix/kotoba-vm-legacyquad-alias-2605300100`) is required for the p2p
  build to compile; upstream main (5c0b89f) is one commit ahead and may already
  carry it — reconcile on next subrepo sync.

# Alternatives Considered

- **launchd auto-rehydrate on boot** — rejected (§5): unnecessary + opaque.
- **Physical retract of duplicate datoms** — rejected: append-only duplicates
  are benign and normalized by `DISTINCT` + the CID-MV cache; low-level
  `quad.retract` with kg-graph-internal CIDs is cost > benefit.
- **kg.quad put CLI for writes** — rejected: it does not mint an operator JWT
  (401); `kg.ingest_batch` + `commit` is the supported write path.

# References

- ADR-2605262130 (kotoba storage substrate unification)
- ADR-2605241500 (dataset CID substrate — DataLad + git-annex + IPFS pinner)
- ADR-2605301020 (Basic High Income doctrine — ingested as the 53rd entity)
- ADR-2605261000 (Labor Liberation ladder — L0..L6 ingested)
- `90-docs/baien/datasets.jsonl` (11 ops-* provenance rows)
- kg-seed-v1.ndjson + rehydrate.sh (annex-store ops/kg-seed/, IPFS-pinned)
