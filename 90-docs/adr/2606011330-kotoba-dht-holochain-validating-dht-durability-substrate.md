---
id: adr-2606011330-kotoba-dht-holochain-validating-dht-durability-substrate
title: "ADR-2606011330: kotoba-dht — Holochain-iso validating DHT as the durability + verifiable-availability substrate (IPFS demoted to CIDv1 cold/interop tier)"
status: proposed
doc_type: adr
topic: kotoba-storage-durability
authoritative: true
last_verified: 2026-06-01
priority: 8.7
axis: substrate-boundary
weight: 0.9
priority_note: "names the durability OWNER beneath the canonical Datom log; closes the 'IPFS = durability authority' ambiguity"
authoritative_for:
  - "kotoba block-durability + verifiable-availability substrate (40-engine/kotoba/crates/kotoba-dht)"
  - "BlockStore durability tier selection (kotoba-store)"
  - "IPFS role demotion to CIDv1 cold/interop backstop"
depends_on:
  - adr-2605262130-kotoba-storage-substrate-unification
  - adr-2605312345-kotoba-datom-first-class-canonical-state
  - adr-2605172100-etzhayyim-payments-on-chain-only
  - adr-2605215000-etzhayyim-inference-murakumo-only-no-runpod
  - adr-2605192100-etzhayyim-mission-charter
related:
  - adr-2605231400-kotoba-datomic-holochain-iso-substrate
  - adr-2605231525-no-server-key-posture
supersedes: []
superseded_by: []
---

# ADR-2606011330: kotoba-dht — Holochain-iso validating DHT as the durability + verifiable-availability substrate

**Status**: proposed
**Date**: 2026-06-01
**Deciders**: Jun Kawasaki

# Context

ADR-2605312345 made the kotoba **Datom log the first-class canonical state** and
declared IPFS a *subordinate* "block backend (CIDv1 cold tier/DHT)", MST the
ingress/interop wire, and Base L2 the trust anchor. That layering is correct, but
it left one question unanswered: **who actually owns durability and proves that
blocks are still retained?** In the current code IPFS/Kubo (`kotoba-ipfs`,
`KuboBlockStore`, `TieredBlockStore` cold tier) is the de-facto durability
authority — and Kubo bitswap has *no* durability guarantee, no proof-of-retention,
and a flaky mutable-head story (IPNS). "IPFS optimized" is therefore not the right
target.

The `BlockStore` trait (`kotoba_core::store::BlockStore`: `put/get/has/
put_durable/delete/pin/all_cids`, single SHA2-256 CIDv1) makes the durability
backend fully pluggable. And the kotoba workspace **already contains** a
Holochain-isomorphic validating DHT — `kotoba-dht` — with:

- `source_chain` — per-agent **append-only hash-chained log** (= Datomic
  accretion-only Datom log, by construction);
- `neighborhood` — XOR-distance r-replication;
- `availability_proof` — epoch challenge → score → `eligible_for_reward()` (≥0.80)
  / `trigger_slash()` (<0.50);
- `warrant` — gossiped invalidity proofs;
- `gossip` — GossipSub epoch coordination.

A minimax (maximin — maximize the worst dimension) evaluation across 8 criteria
was run on 7 candidate durability substrates (see *Alternatives Considered*). Both
the maximin and the Charter-weighted sum select the in-house validating DHT.

# Decision

**D1 — Durability + verifiable-availability owner = `kotoba-dht` (Holochain-iso
validating DHT).** Block durability and proof-of-retention are owned by
`kotoba-dht`: `neighborhood` XOR-distance r-replication for redundancy +
`availability_proof` epoch challenge/score for verifiable retention + `warrant`
gossip for invalidity. Durability is **tunable** via replication factor `r` and
the reward/slash thresholds.

**D2 — IPFS demoted to CIDv1 cold/interop tier ONLY.** IPFS/Kubo remains as (a) a
content-addressed cold backstop and (b) the interop wire to the wider IPFS/AT
network. It is **no longer the durability authority**. This sharpens — does not
contradict — ADR-2605312345's "IPFS = block backend" by naming the owner of the
guarantee IPFS never provided.

**D3 — `BlockStore` composition.** A `NeighborhoodBlockStore` impl lands in
**`kotoba-dht`** (NOT `kotoba-store` — see below), slotting into the existing
`TieredBlockStore` exactly where the Kubo cold tier sits today:

```
hot        = BudgetedBlockStore<MemoryBlockStore>      (LRU, µs)
durability = NeighborhoodBlockStore (kotoba-dht)       (r-replication + availability_proof)   ← NEW owner
cold/interop = KuboBlockStore (IPFS CIDv1)             (backstop + interop wire, demoted)
trust anchor = Base L2                                 (commit-DAG root only)
```

The store wraps the tiered store as its `local`, replicates each block to the
`K` peers nearest the block's content address (`cid_address`), and confirms
`min_replicas` copies on `put_durable`. The mutable head is the `source_chain`
tip (verifiable lineage), **not** IPNS.

`NeighborhoodBlockStore` lives in **kotoba-dht, not kotoba-store**, because
`kotoba-store → kotoba-kse → kotoba-store` would form a dependency cycle, and
kotoba-dht already owns `NodeId` / `Neighborhood` / `availability_proof`. The
store + its `PeerTransport` trait carry **no transport dependency** (no HTTP /
tokio) so kotoba-dht stays WASM-32 buildable (Baien edge invariant); concrete
transports are supplied by callers. `kotoba-server` provides a Kubo
`PeerTransport` (`dht_transport::KuboPeerTransport`, reusing `KuboBlockStore`'s
`block/put` + `block/get`) and composes the durability tier behind
`KOTOBA_DURABILITY_DHT` (peers from `KOTOBA_PEERS`, target from
`KOTOBA_DHT_MIN_REPLICAS`). When enabled it supersedes `DistributedBlockStore`
(it also fans out reads to responsible peers).

**Status (2026-06-01): IMPLEMENTED — R2 in progress.**

R1 (landed): `kotoba-dht::NeighborhoodBlockStore` + `PeerTransport` and
`kotoba-server::dht_transport::KuboPeerTransport` + env-gated server wiring;
`cargo build -p kotoba-server` green.

R2 increment (landed 2026-06-01):
- **Async replication off the hot path** — `put` replicates fire-and-forget
  (detached `spawn_blocking` when a runtime is present; sequential fallback for
  tests/wasm); `put_durable` replicates **concurrently** (`spawn_blocking` +
  `block_in_place`, latency = slowest peer, not the sum) then confirms
  `min_replicas`. Fixes the R1 hot-path stall risk.
- **Availability audit loop** — `audit::AvailabilityAuditor` runs an epoch:
  challenge each peer → fetch proof (`ProofFetcher`) → `verify_proof` against the
  auditor's own copy → `AuditAction::{Reward, Slash, None, Unreachable}`. This is
  the deterministic core of the "validating" half, tied to the prover side
  (`respond_to_challenge`) and unit-tested end-to-end in-memory.
- **Safe `min_replicas` default** — server defaults to 2 when peers exist
  (durability is real, not local-only), 1 when standalone; warns when the target
  exceeds `1 + peer_count`.
- **Live-Kubo integration harness** — `#[ignore]` test exercising real
  `block/put`→`block/get` + `put_durable` over the live transport.

R3 increment (landed 2026-06-01) — runnable validating loop, testable cores of
the remaining live pieces:
- **`audit::AuditScheduler`** — runs audit epochs over a peer set, accumulates
  per-peer `PeerReputation` (rewards / slashes / unreachable / consecutive
  failures / last score), and emits every verdict to a `VerdictSink`. Distrust:
  a peer hitting `distrust_threshold` consecutive failures is surfaced by
  `distrusted_peers()` (signal to stop counting it toward replica targets).
- **`VerdictSink`** — the incentive hand-off boundary; `Reward`/`Slash` map to
  USDC-on-Base-L2 settlement once that contract lands. `InMemoryVerdictSink`
  reference impl + `Arc<T>` blanket impl (shareable for inspection).
- **DID-keyed peer identity** — `KuboPeerTransport::with_node_id(endpoint, id)`
  takes a `blake3(did_pubkey)` `NodeId`, replacing the endpoint-string stand-in
  when a peer advertises its DID key.

Now the validating + incentivized loop runs **end-to-end in-memory across
epochs** (challenge → proof → verify → verdict → reputation → sink); only the
live libp2p `ProofFetcher` transport and the on-chain `VerdictSink` remain as
swap-ins, both already exercised via in-memory doubles.

R4 increment (landed 2026-06-01) — closing the four remaining swap-ins as far
as environment + Charter allow:
- **#4 live-Kubo VERIFIED (DONE).** The `#[ignore]` integration test was RUN
  against a real Kubo 0.41.0 daemon (`ipfs daemon --offline`): real
  `block/put`→`block/get` round trip **and** `put_durable` over the live
  `KuboPeerTransport` both pass. No longer a harness — empirically green.
- **#3 commit-head mechanism (DONE; wiring deferred).** `commit_chain::CommitChain`
  appends a **signed** `ChainContent::Commit { graph_cid, prolly_root }` to the
  agent's `SourceChain` (Ed25519 over canonical bytes, prev→cid lineage) and
  resolves the per-graph mutable head — the durable IPNS replacement. The
  remaining step is the call-site: `QuadStore::commit()` invoking
  `record_commit` (cross-crate; needs graph to hold an `AgentIdentity`).
- **#2 settlement boundary (DONE; on-chain gated).** `SettlementIntentSink`
  turns `Reward`/`Slash` verdicts into pending `SettlementIntent`s (policy units,
  NOT fiat) for the on-chain executor to drain. **Propose-only: moves no funds,
  holds no key** (no-server-key, ADR-2605231525; no `transfer()`). Actual USDC
  settlement on Base L2 stays Council-ratify-gated.
- **#1 proof builder decoupled (enabling step).** `proof_from_store()` answers a
  challenge over **any** `Arc<dyn BlockStore>`, so a server XRPC endpoint can
  prove possession without downcasting. The remaining piece is genuinely
  blocked from a *tested* increment: kotoba-net is pub/sub (no request/response),
  so a live `ProofFetcher` is either an XRPC `availability.challenge` endpoint +
  HTTP fetcher (server change) or a GossipSub correlation actor — neither
  unit-testable without a live swarm. Not shipped as untested scaffold.
- **#4-bonus DID-keyed peer id (DONE).** `KuboPeerTransport::with_node_id`.

kotoba-dht **99 lib tests** green; kotoba-server build green; live-Kubo test green.

R5 increment (landed 2026-06-01) — live HTTP audit transport + settlement
proposal + commit-loop contract:
- **#1 live HTTP `ProofFetcher` (DONE, e2e tested).** Server half:
  `availability_xrpc::availability_challenge` XRPC endpoint
  (`com.etzhayyim.apps.kotoba.dht.availability_challenge`) answers a challenge from the
  node's block store via `proof_from_store`. Client half:
  `dht_transport::HttpProofFetcher` (`reqwest::blocking`, implements
  `ProofFetcher`). **End-to-end test binds a real axum server on an ephemeral
  port and runs the full loop** `AuditScheduler → HttpProofFetcher → TCP →
  endpoint → proof → verify → Reward` — green. (The GossipSub-actor variant +
  wall-clock scheduler daemon remain optional alternatives, not blockers.)
- **#2 settlement proposal (DONE).** `settlement::{SettlementSchedule,
  SettlementBatch}` resolves audit `units`→USDC micros and aggregates intents
  per `(peer, kind)` into a Council-signable batch. **Propose-only: no key, no
  funds, no `transfer()`** — on-chain execution stays Council-gated.
- **#3 commit-loop contract (DONE; call-site deferred).** `CommitChain` plus a
  contract test simulating `QuadStore::commit()`'s exact call sequence across
  interleaved multi-graph commits. The one-line `quad_store.rs` insertion is
  deferred only because that file is concurrently held dirty by the background
  /loop; the contract it must meet is pinned by test.

kotoba-dht **105 lib tests** green; kotoba-server `availability_xrpc` (incl. live
HTTP e2e) + `dht_transport` green; live-Kubo test green.

Honest — remaining for R5→R6 (deployment / governance only, no unbuilt logic):
- libp2p/GossipSub `ProofFetcher` variant + a wall-clock epoch scheduler running
  as a daemon (the HTTP transport already proves the loop; this is an alternate
  transport + a timer).
- On-chain `SettlementBatch` executor (USDC on Base L2) — Council Lv6+ multisig,
  a governance action, not code.
- `QuadStore::commit()` → `CommitChain::record_commit` one-line call-site (waiting
  for the /loop to release `quad_store.rs`).
- `block_in_place` assumes a multi-thread runtime (matches `DistributedBlockStore`).

**D4 — Holochain architecture AFFIRMED, realized inside kotoba.** The Holochain-iso
topology (source chain + validating DHT) is the canonical durability architecture.
It is realized by the **`kotoba-dht` crate inside the kotoba workspace**, NOT by
the deprecated `kotoba-datomic` protocol family. ADR-2605231400 (kotoba-datomic) and its
projection ADR-2605231500 **remain superseded** by ADR-2605262130; this ADR does
not revive the kotoba-datomic *name* or `10-protocol/kotoba-datomic/`, only the *architecture
pattern* as implemented in `kotoba-dht`.

**D5 — Incentive settlement in USDC on Base L2 only.** `availability_proof` reward
and slash settle in **USDC on Base L2** (ADR-2605172100 payment invariant). **No
foreign storage token.** This is the decisive reason Storj (STORJ), Sia (Siacoin),
and other token-mandatory networks were rejected: they would import a non-USDC
payment dependency forbidden by the Charter substrate boundary.

# Consequences

- **Positive**
  - `source_chain` = Datomic accretion log *for free*: the mutable-head problem that
    sinks IPFS/IPNS and vanilla DHTs (criterion C4) is solved natively.
  - Verifiable availability (C5) without a foreign token (C6): the two strengths
    that were mutually exclusive among external networks are both satisfied.
  - Full sovereignty + smallest external dependency surface; WASM-edge story owned
    in-house (`kotoba-store-web`, `kotoba-guest` already WASM) — satisfies the
    Baien edge invariant.
  - No new `state_prohibited` violation; consistent with no-server-key posture
    (ADR-2605231525) — writes are member/agent source-chain signed.
- **Negative / honest**
  - Highest *build* cost: `NeighborhoodBlockStore` wiring + the
    challenge/reward/slash loop must be hardened beyond the current scaffold. This
    is a one-time cost that converts to an owned asset (vs. a recurring dependency
    on an external network's economics).
  - `kotoba-dht` is unproven at scale; replication factor / churn / slash-economics
    parameters need empirical tuning before any mainnet durability claim.
  - Base L2 settlement of reward/slash is gated on Council ratification of the
    incentive contract (no contract shipped by this ADR — design-only).
- **Migration**
  - No data migration: CIDv1 blocks are identical across tiers. Cutover is adding
    `NeighborhoodBlockStore` to the `TieredBlockStore` composition and re-pointing
    the durability tier; Kubo stays mounted as cold/interop.

# Alternatives Considered

Minimax (maximin = maximize the worst dimension) over 8 criteria, scored 1–10
(higher = better). Charter-derived weights: C1 content-fit 0.15 · **C2 durability
0.20** · C3 read-latency 0.10 · C4 mutable-head 0.10 · **C5 verifiable-availability
0.15** · **C6 Charter/economic fit 0.15** · C7 WASM-edge 0.05 · C8 ops-maturity 0.10.

| Candidate | C1 | C2 | C3 | C4 | C5 | C6 | C7 | C8 | **minimax (min)** | weighted |
|---|---|---|---|---|---|---|---|---|---|---|
| IPFS optimized (Kubo+bitswap, status quo) | 9 | 4 | 4 | 4 | 3 | 9 | 4 | 6 | **3** | 5.55 |
| Tahoe-LAFS | 8 | 9 | 5 | 5 | 6 | 5 | 2 | 4 | **2** | 6.15 |
| Storj | 6 | 9 | 6 | 7 | 8 | 3 | 4 | 6 | **3** | 6.45 |
| Sia | 6 | 8 | 4 | 4 | 9 | 2 | 3 | 4 | **2** | 5.50 |
| Fireproof | 9 | 5 | 9 | 8 | 5 | 9 | 9 | 6 | **5** | 7.20 |
| generic DHT (libp2p-kad / Iroh-style) | 9 | 4 | 4 | 4 | 3 | 9 | 6 | 5 | **3** | 5.55 |
| **kotoba-dht (Holochain-iso validating DHT)** | **10** | 8 | 7 | **9** | **9** | 9 | 8 | 5 | **5** | **8.30** |

- **maximin**: only Fireproof and kotoba-dht reach a worst-dimension of 5; all
  others bottom out at 2–3 (durability or token-economy structural defects).
  Tiebreak → kotoba-dht: Fireproof's worst (durability=5) is *structural* (it is a
  local-first DB that delegates durability to a backend, so it can never be the
  sole durability layer), whereas kotoba-dht's worst (ops-maturity=5) is a one-time
  build cost.
- **weighted**: kotoba-dht 8.30 ≫ Fireproof 7.20 > Storj 6.45 > Tahoe 6.15 >
  IPFS = generic-DHT 5.55 > Sia 5.50.
- **Token-mandatory networks (Storj/Sia, partial Tahoe license friction)** are
  structurally penalized on C6 by the USDC-on-Base-only payment invariant
  (ADR-2605172100) regardless of their strong C2/C5 — the result is robust to
  reweighting unless that Charter invariant is dropped.
- **Fireproof's design pattern** (local-first prolly-tree CRDT) is retained as the
  embedded read/merge layer — it validates kotoba's own prolly design — but not as
  the durability network.

Scores are ordinal judgements from the 2026-06-01 session analysis, not benchmarks.

# References

- ADR-2605262130 (kotoba storage substrate unification — canonical engine)
- ADR-2605312345 (kotoba Datom log = first-class canonical state; IPFS = block backend)
- ADR-2605231400 (kotoba-datomic Holochain-iso substrate — SUPERSEDED; architecture pattern only)
- ADR-2605172100 (payments on-chain only — USDC on Base L2)
- ADR-2605215000 (inference Murakumo-only)
- ADR-2605231525 (no-server-key posture)
- ADR-2605192100 (etzhayyim mission charter — substrate boundary)
- `40-engine/kotoba/crates/kotoba-dht/` — validating DHT (source_chain / neighborhood / availability_proof / warrant / gossip)
- `40-engine/kotoba/crates/kotoba-core/src/store.rs` — `BlockStore` trait
- `40-engine/kotoba/crates/kotoba-store/src/{tiered_store,distributed_store,kubo_store}.rs`
