---
id: blockchain-node-vultr-b2-zeebe-ingest-design-260425
title: "Blockchain node on Vultr Kubernetes: Bitcoin/Ethereum + B2 cold storage + Zeebe ingest"
status: proposed
doc_type: design
topic: blockchain-node-ingest
authoritative: false
last_verified: 2026-04-25
related:
  - 90-docs/260425-ingest-orchestration-zeebe-python-k8s-mcp-design.md
  - 90-docs/adr/0048-kotoba-vultr-b2-primary.md
  - 90-docs/adr/0056-bpmn-as-actor.md
  - 50-infra/vultr/geth-private/
---

# Goal

Vultr Kubernetes Engine 上に Bitcoin / Ethereum の public chain node を置き、
block / transaction / log / balance delta を Zeebe + Python worker で
durable ingest する。NVMe block storage は高いので、Backblaze B2 を使える
範囲で使い、FUSE を含む選択肢を評価する。

# Executive Summary

B2 は **live node datadir ではなく cold object store** として使う。Bitcoin
Core, Geth, Erigon は LevelDB / MDBX / freezer / chainstate などのローカル
DB に強く依存し、rename, append, random read/write, fsync, compaction が発生
する。B2 を rclone/s3fs/mountpoint FUSE で datadir に直接載せると、性能だけ
でなく atomicity / consistency / retry 時の破損リスクが設計上残る。

採用案は:

```text
public chain P2P
  -> bitcoin-core / ethereum execution+consensus StatefulSet
       hot PVC: Vultr HDD Block Storage or small NVMe cache
       cold B2: snapshots, raw block export, ingest artifacts, backfill datasets
  -> RPC / ZMQ / Engine API / logs
  -> blockchain-ingest Python worker
  -> Zeebe process state + Kotoba/Datomic graph rows + B2 raw artifacts
```

node 自体は Kubernetes `StatefulSet` + `ReadWriteOnce` PVC に固定する。B2 は
sidecar / CronJob / Zeebe task から `rclone copy/sync` または S3 API で
参照し、node process の critical write path には置かない。

# Storage Decision

| Data | Bitcoin | Ethereum | Storage |
|---|---|---|---|
| hot chainstate / block index / txindex | `chainstate/`, `indexes/` | execution DB, consensus DB | Vultr Block Storage PVC |
| recent raw blocks needed by node | pruned `blocks/` | recent bodies/state | same PVC |
| immutable old raw block files | optional `blk*.dat` export | optional ancient/snapshot export | B2 object prefix |
| archive state | not required for first phase | do not run Geth archive on B2 | external provider or separate archive node |
| ingest raw evidence | RPC responses, block json, receipts | logs, receipts, traces if enabled | B2 |
| canonical facts | block/tx/log rows | block/tx/log rows | Kotoba/Datomic |

## Why not B2 FUSE for live datadir

Object storage FUSE is useful for sequential files and read-heavy datasets, not
for database directories. AWS Mountpoint explicitly does not implement full
POSIX semantics and targets sequential/random reads plus sequential writes, not
general filesystem mutation. rclone can mount B2 and supports VFS cache modes,
but writes that need seek/update semantics depend on local cache and delayed
upload. Backblaze's own rclone guidance says write workloads need
`--vfs-cache-mode writes` because applications expect to write into the middle
of a file.

Blockchain nodes are exactly the kind of workload that exposes this mismatch:

- LevelDB/MDBX compaction rewrites files and expects durable local fsync.
- chainstate / account state needs random read/write latency.
- database corruption recovery is expensive because resync may take days.
- FUSE cache large enough to mask this becomes a local disk again, losing the
  main cost benefit.

Therefore, B2 FUSE is allowed only for **read-only or write-once artifacts**:
backfill block dumps, snapshots, exported receipts, and operator restore media.

# Node Profiles

## P0: cost-first ingest node

Use this for initial production ingest where slight lag is acceptable.

| Chain | Client | Storage | Notes |
|---|---|---|---|
| Bitcoin | Bitcoin Core pruned | 200-500 Gi Vultr HDD Block Storage | `prune=150000` to `400000`, `txindex=0`; ingest walks new blocks only |
| Ethereum | Erigon full/minimal or Geth snap full | 1-2 TiB Vultr HDD Block Storage, NVMe only if catch-up is too slow | no archive state; ingest logs from head and bounded historical windows |

Bitcoin Core pruned mode still fully validates blocks but discards older raw
block/undo data after validation. This is enough for head ingest and reorg
handling when the prune window is sized generously. It is not enough for
arbitrary old block serving or old wallet rescan.

Ethereum should start with a non-archive execution client. Geth snap/full nodes
keep recent state and checkpoints; archive mode is a different cost class. If
historical block bodies are needed more than historical state, prefer Erigon
with pruning mode that keeps block history while pruning state, then export
immutable datasets to B2.

## P1: balanced node

Use HDD block storage for bulk data and a small NVMe PVC for cache if needed:

```text
/data/node        -> vultr-block-storage-hdd, 2-4 TiB
/data/cache       -> vultr-block-storage, 100-300 GiB
/data/b2-mirror   -> rclone/s3fs mount, read-only in node pod or sidecar only
```

The node process should write only to `/data/node` and `/data/cache`. B2 mirror
mounts are exposed to sidecars or ingest jobs, not to the node datadir.

## P2: archive / explorer grade

Do not attempt this on B2 FUSE. Use a dedicated archive service, dedicated large
block volumes, or split archive responsibility:

- one or more RPC provider fallbacks for historical `trace_*` / old state
- local head node for trust-minimized new-block ingest
- B2 object lake for raw block/receipt/log artifacts after extraction

# Kubernetes Topology

All resources must be namespaced; never create resources in `default`.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: blockchain
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: bitcoin-mainnet
  namespace: blockchain
spec:
  serviceName: bitcoin-mainnet
  replicas: 1
  selector:
    matchLabels:
      app: bitcoin-mainnet
  template:
    metadata:
      labels:
        app: bitcoin-mainnet
    spec:
      containers:
        - name: bitcoind
          image: ruimarinho/bitcoin-core:latest
          args:
            - -printtoconsole
            - -server=1
            - -prune=300000
            - -rpcbind=0.0.0.0
            - -rpcallowip=10.0.0.0/8
            - -zmqpubhashblock=tcp://0.0.0.0:28332
            - -zmqpubrawtx=tcp://0.0.0.0:28333
          volumeMounts:
            - name: data
              mountPath: /home/bitcoin/.bitcoin
  volumeClaimTemplates:
    - metadata:
        name: data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: vultr-block-storage-hdd
        resources:
          requests:
            storage: 500Gi
```

Ethereum should be split into execution and consensus StatefulSets or a single
pod with two containers only for P0. Production should separate lifecycle but
co-locate with node affinity when Engine API latency matters.

```text
Namespace/blockchain
  StatefulSet/eth-execution-mainnet
    PVC/data: vultr-block-storage-hdd
    Service/eth-exec-rpc ClusterIP only
  StatefulSet/eth-consensus-mainnet
    PVC/data: vultr-block-storage-hdd
    Service/eth-beacon ClusterIP only
  Deployment/blockchain-ingest-worker
    connects to Zeebe + RPC services + B2 + Kotoba/Datomic
  CronJob/blockchain-ingest-start-bitcoin-head
    thin starter: creates Zeebe instance and exits
  CronJob/blockchain-b2-snapshot
    maintenance only, no cursor ownership
```

# Zeebe + Python Ingest

Kubernetes CronJobs only create Zeebe instances. Cursors, retries, reorg
handling, rate limits, and writes live in Zeebe variables plus Kotoba/Datomic
`vertex_ingest_*` rows from the generic ingest design.

## BPMN process suite

| Process | Trigger | Purpose |
|---|---|---|
| `blockchain.bitcoin.head.delta` | `*/1 * * * *` Cron starter or ZMQ event bridge | ingest new Bitcoin blocks |
| `blockchain.ethereum.head.delta` | `*/1 * * * *` Cron starter or websocket subscription | ingest new Ethereum blocks/logs |
| `blockchain.reorg.reconcile` | incident / detected parent mismatch | roll back derived rows to common ancestor |
| `blockchain.backfill.range` | manual MCP / operator | bounded block range backfill |
| `blockchain.snapshot.to_b2` | daily maintenance Cron starter | copy deterministic snapshots/artifacts to B2 |

Logical task chain:

```text
start
  -> health gate (node RPC sync status + Kotoba/Datomic visibility)
  -> read cursor
  -> get chain tip
  -> plan block range with max batch size
  -> fetch block headers
  -> detect reorg
  -> fetch full blocks / receipts / logs
  -> persist raw artifact to B2
  -> normalize canonical rows
  -> write graph rows
  -> verify row counts and parent links
  -> update cursor
  -> emit audit
end
```

## Python worker task names

```text
blockchain.rpc.health
blockchain.cursor.read
blockchain.range.plan
blockchain.bitcoin.fetchBlock
blockchain.ethereum.fetchBlock
blockchain.ethereum.fetchReceipts
blockchain.ethereum.fetchLogs
blockchain.raw.persistB2
blockchain.normalize
blockchain.graph.write
blockchain.graph.verify
blockchain.cursor.advance
blockchain.reorg.reconcile
```

Worker modules:

```text
20-actors/magatama/py/src/pymagatama/ingest/blockchain/
  core.py       # Zeebe envelope, cursor, reorg utilities
  bitcoin.py    # Bitcoin Core RPC/ZMQ client
  ethereum.py   # execution/beacon RPC client
  b2.py         # artifact writer, manifest, snapshot helpers
  schema.py     # normalized row dataclasses / validation
```

# Kotoba/Datomic Model

First phase tables should be append-friendly and deterministic:

```sql
vertex_blockchain_block(
  vertex_id,
  chain,
  height,
  block_hash,
  parent_hash,
  block_time,
  raw_artifact_uri,
  canonical_status,
  ingested_at
)

vertex_blockchain_tx(
  vertex_id,
  chain,
  block_hash,
  tx_hash,
  tx_index,
  from_addr,
  to_addr,
  value,
  fee,
  status,
  raw_artifact_uri,
  ingested_at
)

vertex_blockchain_log(
  vertex_id,
  chain,
  block_hash,
  tx_hash,
  log_index,
  address,
  topic0,
  topics_json,
  data_hex,
  removed,
  raw_artifact_uri,
  ingested_at
)
```

`vertex_id` is deterministic:

```text
block: blockchain:{chain}:block:{height}:{hash}
tx:    blockchain:{chain}:tx:{tx_hash}
log:   blockchain:{chain}:log:{tx_hash}:{log_index}
```

Reorg policy:

- cursor advances only after parent link verification.
- if stored `tip_hash != rpc.parent_hash`, run `blockchain.reorg.reconcile`.
- mark old rows `canonical_status='orphaned'` rather than deleting.
- reinsert replacement canonical rows with deterministic ids including hash.

# B2 Layout

```text
b2://etzhayyim-nats/blockchain/
  bitcoin/mainnet/raw-block/yyyy/mm/dd/{height}-{hash}.json.zst
  bitcoin/mainnet/snapshots/bitcoin-core/{date}/manifest.json
  ethereum/mainnet/raw-block/yyyy/mm/dd/{height}-{hash}.json.zst
  ethereum/mainnet/receipts/yyyy/mm/dd/{height}-{hash}.json.zst
  ethereum/mainnet/logs/yyyy/mm/dd/{height}-{hash}.json.zst
  ethereum/mainnet/snapshots/{client}/{date}/manifest.json
```

Snapshots are restore accelerators, not the primary database. Every snapshot
must have a manifest with:

- client name/version
- chain id/network
- block height/hash at snapshot point
- source PVC id
- file list and sha256
- restore test status

# FUSE Options

Allowed:

```text
rclone mount b2:etzhayyim-nats/blockchain /mnt/b2-blockchain \
  --read-only \
  --vfs-cache-mode full \
  --vfs-cache-max-size 100G \
  --dir-cache-time 1h
```

Conditionally allowed for export jobs only:

```text
rclone mount b2:etzhayyim-nats/blockchain /mnt/b2-blockchain \
  --vfs-cache-mode writes \
  --vfs-write-back 30s \
  --vfs-cache-max-size 200G
```

Forbidden:

- mounting B2 as `/data/geth`, `/data/erigon`, `/home/bitcoin/.bitcoin`
- running LevelDB/MDBX/consensus DB directly on s3fs/rclone/mountpoint
- sharing one writable FUSE mount across multiple node pods

# Block Storage Examples / Findings

- Vultr VKE supports CSI-backed Block Storage PVCs. HDD block storage is the
  cheaper large-capacity class (`vultr-block-storage-hdd`, RWO, up to 40 TiB);
  NVMe block storage is the high-performance class (`vultr-block-storage`, up
  to 10 TiB). This matches blockchain node StatefulSet usage: one pod owns one
  volume.
- Kubernetes StatefulSet is the standard controller when a pod needs stable
  identity and stable storage. Each `volumeClaimTemplates` entry creates a PVC
  tied to a pod identity, and PVs are not deleted just because a StatefulSet pod
  is replaced.
- OVHcloud's Ethereum node guide provisions block storage for blockchain data
  before running the node. This is the same pattern as VKE + Vultr Block Storage:
  attach durable block storage to the node host/pod, then keep the client DB
  local to that block device.
- Ethereum client docs recommend local SSD/NVMe for Erigon, and Geth archive
  mode is multi-TB to tens-of-TB depending on mode. These are not object-store
  filesystem workloads.

# Rollout

1. Create namespace `blockchain` and secrets for node RPC, B2, Kotoba/Datomic, and
   Zeebe. Do not use `default`.
2. Deploy Bitcoin Core pruned StatefulSet with `vultr-block-storage-hdd`.
3. Deploy Ethereum non-archive node. Start with Erigon full/minimal if the goal
   is cheaper historical block ingest; use Geth snap full if operational
   familiarity matters more.
4. Add `blockchain-ingest-worker` Deployment and register Zeebe task handlers.
5. Add thin CronJobs that start `bitcoin.head.delta` and `ethereum.head.delta`.
6. Persist raw fetched blocks/receipts/logs to B2 before graph writes.
7. Add daily `snapshot.to_b2` process and monthly restore drill.
8. Revisit NVMe only if catch-up lag or RPC latency violates SLO.

# Open Questions

- Do we need Ethereum historical state queries (`eth_getBalance` at old blocks,
  traces) or only blocks/transactions/logs? Historical state moves the design
  into archive/provider territory.
- Is Bitcoin `txindex=1` required? If yes, budget more block storage and initial
  sync time; if no, pruned mode is enough for head ingest.
- Which chain set is in scope beyond Bitcoin/Ethereum: Polygon, Base, Arbitrum,
  Solana? Each should be a separate node profile.

# References

- Vultr VKE PVC / storage classes:
  https://docs.vultr.com/how-to-provision-persistent-volume-claims-on-vultr-kubernetes-engine
- Kubernetes StatefulSet storage:
  https://kubernetes.io/docs/concepts/workloads/controllers/statefulset/
- Backblaze B2 + rclone mount:
  https://www.backblaze.com/docs/en/cloud-storage-integrate-rclone-with-backblaze-b2
- Backblaze B2 + s3fs:
  https://www.backblaze.com/docs/cloud-storage-integrate-s3fs-with-backblaze-b2
- AWS Mountpoint for S3 filesystem semantics:
  https://docs.aws.amazon.com/AmazonS3/latest/userguide/mountpoint-usage.html
- Bitcoin full node pruning:
  https://bitcoin.org/en/full-node.html
- Bitcoin Core 0.11 pruning release note:
  https://bitcoincore.org/en/releases/0.11.0/
- Geth sync modes:
  https://geth.ethereum.org/docs/fundamentals/sync-modes
- Geth archive mode:
  https://geth.ethereum.org/docs/fundamentals/archive
- Erigon sync/prune modes:
  https://docs.erigon.tech/fundamentals/sync-modes
- Erigon hardware requirements:
  https://docs.erigon.tech/getting-started/hw-requirements
- OVHcloud Ethereum node with block storage:
  https://blog.ovhcloud.com/running-an-ethereum-node-on-ovhcloud-public-instances/
