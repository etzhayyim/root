---
id: adr-2604251935-blockchain-vke-head-ingest
title: "ADR: Public blockchain head ingest on Vultr VKE"
status: accepted
doc_type: adr
topic: blockchain-ingest
authoritative: true
last_verified: 2026-04-25
authoritative_for:
  - blockchain-head-ingest
  - vultr-vke-blockchain-nodes
  - blockchain-b2-cold-storage-boundary
related:
  - blockchain-node-vultr-b2-zeebe-ingest-design-260425
  - 90-docs/adr/0048-kotoba-vultr-b2-primary.md
  - 90-docs/adr/0094-kotoba-stable-three-node-topology.md
supersedes: []
superseded_by: []
---

# Context

We need local public-chain RPC sources for Bitcoin and Ethereum so downstream
actors such as malak, intel, and yabai can ingest on-chain head deltas through
the standard durable ingest path: Kubernetes Cron starts Zeebe, and Python
workers perform acquisition and Kotoba/Datomic writes.

NVMe block storage is too expensive for the initial deployment. Backblaze B2 is
cheap and durable, but object storage/FUSE is not acceptable for live Bitcoin
or Ethereum databases. LevelDB/Pebble/MDBX-style node datadirs need local block
semantics, low-latency random IO, locks, and crash recovery behavior that B2
mounts do not provide.

# Decision

Run P0 public blockchain ingest in the `blockchain` namespace on Vultr VKE:

- `StatefulSet/bitcoin-mainnet`: Bitcoin Core mainnet, pruned, 500Gi
  `vultr-block-storage-hdd-retain` PVC.
- `StatefulSet/ethereum-mainnet`: Geth v1.15.11 + Lighthouse v8.x, 1500Gi
  execution PVC and 200Gi consensus PVC, both
  `vultr-block-storage-hdd-retain`.
- `Deployment/blockchain-ingest-worker`: Python Zeebe worker image
  `ghcr.io/etzhayyim/pymagatama:20260425-blockchain-ingest-rw-fallback-v2`.
- `CronJob/blockchain-bitcoin-head-ingest` and
  `CronJob/blockchain-ethereum-head-ingest`: run every 10 minutes with
  `concurrencyPolicy: Forbid`.
- Zeebe processes:
  `blockchain_bitcoin_head_delta` and `blockchain_ethereum_head_delta`.

Ethereum execution peering is explicitly configured:

- `--port=30303`
- `--discovery.port=30303`
- `--maxpeers=100`
- `--nat=extip:45.76.77.26`
- TCP `hostPort: 30303`

B2 remains cold storage only:

- raw block/tx artifacts
- snapshots
- restore drills
- backfill datasets

B2 must not be mounted as live node datadir.

# Current State

As of 2026-04-25 19:35 JST:

- Bitcoin pod is running and validating 2015-era blocks around height 365k.
- Bitcoin ingest has completed Zeebe runs and landed 11k+ fallback rows in
  `vertex_blockchain_actor`.
- Ethereum Lighthouse is synced to head but optimistic because Geth execution
  sync is still at block 0.
- Geth now advertises `45.76.77.26:30303` and has begun seeing peers, but has
  not yet advanced `eth.blockNumber`.
- Kotoba/Datomic DDL for `vertex_blockchain_block` and `vertex_blockchain_tx`
  failed during RW scheduler instability. Until RW DDL is stable, worker writes
  deterministic rows into `vertex_blockchain_actor.props` with `kind=block|tx`.

# Consequences

- This is cost-first and operationally conservative, not fastest sync.
- Bitcoin and Ethereum sync completion is a wait-and-observe operation unless
  Geth peers remain near zero for an extended period.
- Dedicated `vertex_blockchain_block` and `vertex_blockchain_tx` tables remain
  the target schema, but fallback landing preserves ingest continuity.
- B2 integration is a later writer/snapshot step; it is not on the critical
  path for chain sync.

# Wait-Time Guidance

Bitcoin on HDD block storage is progressing, but it is still at about 2015-era
history. At verification progress ~5.4% and height ~365k / ~946k headers,
expect roughly 1-3 days for Bitcoin to become practically useful for head
ingest. The estimate is intentionally conservative because later blocks contain
more transactions and validate more slowly than the 2015-era blocks currently
being processed.

Ethereum Geth snap sync on HDD can complete in several hours if peers stabilize
and state download starts, but can take 1-3 days on slow disks or poor peering.
If `admin.peers.length` remains below 3 or `eth.blockNumber` remains 0 for
more than 2-3 hours after the `--nat=extip` fix, revisit peering/firewall or
switch to a faster bootstrap path.

# Alternatives Considered

- **B2 FUSE as node datadir**: rejected. Cheap, but unsafe for live chain DBs.
- **NVMe from day one**: rejected for P0 cost. Use only if sync time blocks
  business value.
- **Remote public RPC only**: rejected as primary source. It is useful as a
  bootstrap or fallback, but local nodes are the trust-minimized ingest source.
- **Erigon instead of Geth**: viable later for historical queries, but Geth +
  Lighthouse is the lower-risk P0 deployment.

# References

- `50-infra/vultr/blockchain-node/manifests/`
- `20-actors/magatama/py/src/pymagatama/ingest/blockchain.py`
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/ingest/blockchainBitcoinHeadDelta.bpmn`
- `etzhayyim-root/00-contracts/bpmn/com/etzhayyim/ingest/blockchainEthereumHeadDelta.bpmn`
