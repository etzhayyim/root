---
id: adr-2604261936-ipfs-self-hosted-vultr-b2
title: "ADR: ipfs.etzhayyim.com — self-hosted Kubo on Vultr VKE with Backblaze B2 block backend"
status: proposed
doc_type: adr
topic: ipfs-self-hosted
authoritative: true
last_verified: 2026-04-26
authoritative_for:
  - ipfs.etzhayyim.com gateway topology
  - Kubo + B2 datastore split
  - IPFS pin policy alignment with PDS uploadBlob
related:
  - adr-0048-kotoba-vultr-b2-primary
  - adr-2604251400-pds-uploadblob-r2-to-b2-migration
  - adr-2604251935-blockchain-vke-head-ingest
  - adr-0029-did-etzhayyim-method-specification
  - adr-2604261717-staked-claim-truth-incentive
supersedes: []
superseded_by: []
---

# Context

etzhayyim は CID 中心 (DAG-CBOR + multihash) の design で、ADR-0029 (`did:etzhayyim`),
ADR-2604251400 (PDS `uploadBlob` SHA-256 content-addressed → B2),
ADR-2604261717 (`atRecordCid` field on `stakedAttestation`) のいずれも
"content-addressed object" を前提とする。これらの blob は現在 **B2 直書き
+ R2 origin proxy + 内部 SDK** で扱っており、外部からの IPFS-protocol
(`/ipfs/{cid}`) 互換 fetch ができない。

要件:

1. **`ipfs.etzhayyim.com` を public IPFS gateway として公開**。`https://ipfs.etzhayyim.com/ipfs/<cid>`
   で誰でも CID を取得できる (Cloudflare's /Pinata's gateway と同等の semantic)。
2. **データ実体は Backblaze B2** (ADR-0048 / ADR-2604251400 の方針継続)。
   block は B2、IPFS metadata + DAG index のみ pod-local PVC。
3. **Vultr VKE 上の pod** (Kotoba/Datomic / geth-private と同じ cluster)。
   独立 namespace `ipfs`、専用 node pool 不要 (既存 `kotoba-pool-32gb` に同居可)。
4. **PDS / claim-stake / did:etzhayyim genesis-op** の blob を **自動 pin**。
   federation 時に CAR export 経由で外部 PDS にも届くため必須。
5. **書き込み API は HMAC で gate** (`/api/v0/add`, `/api/v0/pin/add` 等)。
   read paths (`/ipfs/`, `/ipns/`, `/api/v0/cat|get|dag/get|block/get`) は public。

外部 hosted (Pinata / web3.storage / Filecoin Saturn) 不採用根拠:

- **Sovereignty**: ADR-0014 の self-hosted PLC、ADR-0048 の自前 Kotoba/Datomic、
  ADR-2604251935 の自前 BTC/ETH ノードと方針整合。
- **Cost predictability**: Pinata 50 GB tier=$20/mo + 0.15 USD/GB egress、
  自前 B2 + Vultr LB は ~$30/mo 固定 (B2 storage $0.005/GB/mo + Bandwidth Ally で
  CF への egress $0)。
- **Latency control**: gateway 自前 → CF 経由で global edge cache に乗る。
  external host だと cache ヒット率が我々の制御外。

# Decision

**Kubo (go-ipfs) v0.31.x を Vultr VKE 上で StatefulSet として運用、
`go-ds-s3` datastore plugin で blocks を B2 に格納する 2-tier 構成。**

```
external:
  client ─────► ipfs.etzhayyim.com (CF DNS, proxied)
              ─► etzhayyim-ipfs-proxy (CF Worker)
                  • /ipfs/*, /ipns/*           = public, no auth
                  • /api/v0/{cat,get,dag/get,
                            block/get,resolve} = public, no auth
                  • /api/v0/{add,pin,key,
                            config,repo/gc}    = HMAC required
                  • metrics/admin              = blocked
              ─► Vultr LoadBalancer :443
                  → caddy TLS proxy :8443 (self-signed for CF Origin)
                    → kubo Service :8080 (gateway) / :5001 (api)
                      → kubo pod
                          ├─ blocks    → s3ds plugin → B2
                          │                          etzhayyim-nats/ipfs/blocks/
                          ├─ metadata  → levelds → 5 Gi PVC
                          └─ swarm     → :4001 (NodePort, libp2p TCP+UDP)

internal services (PDS, claim-consumer, …):
  service binding `IPFS_API` → etzhayyim-ipfs-proxy
  → /api/v0/add for new blob ingest, /api/v0/pin/add for retention guarantees
```

## Components

| Component | Where | Image / Tech | Resources | Notes |
|---|---|---|---|---|
| **kubo** StatefulSet | ns `ipfs`, replicas=1 | `ipfs/kubo:v0.31.0` | req 1 vCPU / 2 Gi, lim 2 vCPU / 4 Gi | repo on PVC; blocks on B2 |
| **PVC** `kubo-repo-0` | Vultr Block Storage HDD | `vultr-block-storage-hdd-retain` | 40 Gi (Vultr minimum; metadata fits in ~1 GiB) | levelds metadata + go-ds-s3 measure dir |
| **caddy TLS proxy** Deployment | ns `ipfs`, replicas=2 | `caddy:2.8.4-alpine` | req 25m / 32 Mi | mirror `geth-private/40-tls-proxy.yaml` |
| **Vultr LB** | LB :443 | `service.beta.kubernetes.io/vultr-loadbalancer-protocol=tcp` | — | terminates TLS via caddy self-signed cert |
| **CF Worker** `etzhayyim-ipfs-proxy` | CF account | TS, single file | — | route `ipfs.etzhayyim.com/*`; HMAC SS binding for write paths |
| **B2 prefix** `s3://etzhayyim-nats/ipfs/blocks/` | Bandwidth Alliance, region `us-west-004` | shares the bucket already used by Kotoba/Datomic Hummock state (ADR-0048); application key in `etzhayyim.b2` Keychain is scoped to this `bucketId` so no new key provisioning needed | — | block storage only; lifecycle = none (pinned) |

## Datastore configuration

Kubo `~/.ipfs/config.Datastore.Spec` (`go-ds-s3` v1.0.0+):

```jsonc
{
  "type": "mount",
  "mounts": [
    {
      "child": {
        "type": "s3ds",
        "region": "us-west-004",
        "bucket": "etzhayyim-nats",
        "rootDirectory": "ipfs/blocks",
        "regionEndpoint": "https://s3.us-west-004.backblazeb2.com",
        "accessKey": "$S3_ACCESS_KEY",
        "secretKey": "$S3_SECRET_KEY"
      },
      "mountpoint": "/blocks",
      "type": "measure",
      "prefix": "s3.datastore"
    },
    {
      "child": { "type": "levelds", "path": "datastore" },
      "mountpoint": "/",
      "type": "measure",
      "prefix": "leveldb.datastore"
    }
  ]
}
```

`/blocks` mount = block content (large, on B2). `/` mount = catch-all metadata
(small, on PVC: pinset, mfs root, peer-id keys, repo lock). Pod restart preserves
identity (peer-id) via PVC; block data is untouched on B2.

## CF Worker auth split

`etzhayyim-ipfs-proxy/src/index.ts` (~120 LoC):

| Path family | Method | Auth | Rationale |
|---|---|---|---|
| `/ipfs/{cid}/...` | GET, HEAD | none | Public content addressing; CDN cache aggressively |
| `/ipns/{name}/...` | GET, HEAD | none | DNSLink / publish-key resolved by Kubo |
| `/api/v0/{cat,get,resolve,refs/local}` | POST | none | Pure read |
| `/api/v0/{dag/get,block/get,object/get}` | POST | none | Pure read of any present block |
| `/api/v0/{add,block/put,dag/put}` | POST | HMAC `X-etzhayyim-Ipfs-Auth` | Adds blocks to local store + B2 |
| `/api/v0/pin/add`, `/api/v0/pin/rm` | POST | HMAC | Retention bytes — never expose to anon |
| `/api/v0/{key,config,repo/gc,bootstrap}/...` | POST | HMAC | Admin |
| `/api/v0/swarm/peers` | POST | HMAC | Operational |
| `/_metrics`, `/debug/*` | any | blocked | Prevent leakage |

HMAC = `hex(hmac_sha256(SS_IPFS_HMAC, body))` over the canonical request body.
Mirror of `etzhayyim-geth-rpc-proxy` (ADR-0074 Phase 2-A).

## Pin policy

| Source | Pin? | TTL |
|---|---|---|
| `com.atproto.repo.uploadBlob` (PDS) | **yes** | until repo deletion |
| `com.etzhayyim.claim.stakedAttestation.atRecordCid` | **yes** | forever |
| `did:etzhayyim` genesis-op DAG-CBOR | **yes** | forever (sovereignty) |
| User-pin via `/api/v0/pin/add` (HMAC-gated) | yes | until unpin |
| Anonymous `/ipfs/{cid}` fetch (cache miss → DHT pull) | **no** | until next GC |
| Auto-discovered via swarm | **no** | until next GC |

GC は手動のみ (`ipfs repo gc` を `wrangler tail` 経由で操作)。pinned content は
GC 対象外。pinset の整合性は Kubo 内蔵 mfs に委ねる (B2 上の orphan block は
6-month cron で `ipfs refs --recursive` 走査 + 差分 delete を別途設計、Phase 2)。

## Network topology — swarm

| Inbound | Port | Protocol | Decision |
|---|---|---|---|
| Gateway HTTP | 8080 (cluster), 443 (public via caddy) | TCP/HTTPS | always exposed |
| API HTTP | 5001 (cluster only) | TCP | **never** publicly exposed |
| Swarm libp2p | 4001 | TCP + UDP/QUIC | NodePort 30401 + Vultr LB rule |

Swarm を public に出す理由:
- bitswap で他 IPFS ノードから content 取得 → public CID の cache ヒット率
- 我々の content を他 gateway (cf-ipfs.com 等) が pull できる
- AT Protocol federation の foundation (今は CAR over HTTP だが、将来 IPFS swarm 直送 path を残す)

公開しない選択 (private gateway 化) も妥当。Phase 1 は public、Phase 1.5 で metric 見て再判断。

## Lexicon alignment

XRPC 経路は新規追加せず、Kubo HTTP API を直接プロキシする。理由:

- AT Protocol の `/xrpc/com.atproto.repo.uploadBlob` は既に PDS で実装済 (ADR-2604251400 で B2 に格納)
- IPFS gateway が `/ipfs/{cid}` で取れるのは IPFS 標準 contract で、独自 NSID で wrap すると η を下げる (ADR-0005 Shannon redundancy)
- 内部 caller (PDS, claim-consumer) は CF Worker service binding 経由で `/api/v0/add` `/api/v0/pin/add` を叩く

将来 `com.etzhayyim.ipfs.pin` lexicon を追加するのは、permission gate / org 単位の quota が必要になった時のみ。

# Consequences

## Positive

- 完全 self-hosted、Pinata / web3.storage 依存ゼロ。
- 月額 ~$30 (Vultr LB $10 + node share $0 + B2 storage 100 GB ≈ $0.50 + egress $0 via Bandwidth Ally + CF Worker $5 if free tier exhausted)。
- AT Protocol blob (`uploadBlob` SHA-256 content) と DAG-CBOR (CID) を同じ store に統合。
- B2 を canonical block store にすることで、PDS と IPFS が **同じ content-hash** を共有 (block dedup を将来導入可能)。
- CF edge cache が gateway responses を冗長化、global low-latency。

## Negative

- Kubo libp2p は memory hungry。2 Gi だと数千 peer 接続で OOM 余地あり。Phase 1.5 で `Swarm.ConnMgr.HighWater` を絞って制御。
- s3ds は per-block 1 S3 GET。低 latency 用途では PVC + filestore に戻す検討余地。Bench → Phase 2 で再判断。
- B2 multipart abort 系 outage (ADR-0048 / ADR-2604251011) は IPFS にも波及。Hummock とは別 bucket なので blast radius 限定だが、同 B2 account quota は共有。
- Public swarm を出すと、他人の content も serve する責務がある (CSAM 等)。Cloudflare gateway 経由なら CF 側 abuse policy も走るが、自前 origin としての moderation は別 ADR (`ipfs-content-moderation` 必要)。

## Security

- API port :5001 を **絶対に** Vultr LB / Service `type: LoadBalancer` で出さない。Cluster-internal のみ。caddy → :8080 (gateway) のみ公開。
- write paths は HMAC + CF Worker レイヤで完全 gate。署名漏洩 = block 追加可能 (B2 課金リスク) なので Keychain 専用 secret store。
- B2 key は `$S3_ACCESS_KEY` env に直接展開 (Kubo 制約)。Helm secret + Vultr CSI 経由でディスクに残さない。
- Peer ID 秘密鍵は `~/.ipfs/config.Identity.PrivKey` (PVC)。PVC restore drill 必須 (Phase 2)。

# Phase plan

**Phase 1 — single-node MVP [PROPOSED]**

| Surface | Path | Notes |
|---|---|---|
| K8s manifests | `50-infra/vultr/ipfs/manifests/{00-namespace,10-statefulset,20-service,40-tls-proxy,apply.sh}.yaml` | mirror geth-private layout |
| Datastore JSON | `50-infra/vultr/ipfs/config/datastore_spec.json` | go-ds-s3 + levelds, env-substituted at boot |
| init-config script | `50-infra/vultr/ipfs/scripts/init-config.sh` | first-boot: `ipfs init`, swap datastore, set Gateway/HTTPHeaders |
| CF Worker | `50-infra/cloudflare/workers/ipfs-proxy/{src/index.ts,wrangler.jsonc,package.json,tsconfig.json}` | path-based auth split |
| CLAUDE.md | `50-infra/vultr/ipfs/CLAUDE.md` | runbook, B2 keychain refs, restore drill |
| DNS | `ipfs.etzhayyim.com` CNAME → CF, route Worker | via `etzhayyim dns-sync` |

**Phase 1.5 — pin integration [PROPOSED]**

- PDS `uploadBlob` 後に `IPFS_API.fetch("/api/v0/pin/add?arg=<cid>")` を fire-and-forget
- claim-consumer が `ClaimPosted` event の `atRecordCid` を pin
- `did:etzhayyim` genesis op の CID も pin (resolver Worker に統合)

**Phase 2 — operational hardening [PROPOSED]**

- Multi-replica (StatefulSet replicas=2 で IPFS Cluster コーディネーション)
- B2 lifecycle 別 cron で orphan block GC
- Public swarm を `Swarm.ConnMgr` で絞る、metrics → Vultr Prometheus
- IPFS gateway TLS を Origin Cert 経由 (geth-private と同パターン)

**Phase 3 — federation [DEFERRED]**

- `did:web:ipfs.etzhayyim.com` で IPFS service identity 確立
- AT Protocol PDS の CAR import を IPFS swarm 経由 fallback (現 HTTP 一本依存を解消)
- Cluster sharding (multi-region に拡張、B2 single-source 維持)

# Alternatives Considered

## Alt 1: Helia (TS IPFS) on CF Worker

- **Pro**: Worker-native, k8s 不要、cold-start 1ms
- **Con**: Helia は "thin client" 寄り、s3 datastore 未成熟、libp2p 接続が CF の TCP/UDP 制限に合わない (公式に DNS-over-HTTPS / HTTP gateway only 推奨)
- **Reject**: 完全な IPFS node にならない、bitswap 効率悪化

## Alt 2: Pinata / web3.storage / Storj

- **Pro**: Zero ops、即時 production
- **Con**: monthly cost が etzhayyim content 量で 5-10x、sovereignty 喪失、API key revocation 依存
- **Reject**: ADR-0048 / ADR-0014 の自前主義に反する

## Alt 3: Filecoin Saturn (decentralized CDN)

- **Pro**: 完全 decentralized、節点として収入も可能
- **Con**: 我々の content を pin する保証なし (probabilistic)、SLA ゼロ、Filecoin token 経済に依存
- **Defer**: 将来の "重い情報" anchoring 経路として ADR-2604261717 と組み合わせて検討

## Alt 4: Helia + Cloudflare R2

- **Pro**: B2 と R2 の選択
- **Con**: ADR-2604251400 で R2→B2 移行済み (egress cost で B2 が最適)
- **Reject**: コスト + ADR 連続性

## Alt 5: Single-node IPFS without B2 (PVC-only)

- **Pro**: 最もシンプル、s3ds の追加 latency なし
- **Con**: PVC 容量が canonical store になり、ADR-0048 の B2-as-cold-storage 方針から外れる、PVC 拡張が痛い
- **Reject**: 物理 disk 上限が architectural ceiling になる

# References

- Kubo: https://github.com/ipfs/kubo
- go-ds-s3 plugin: https://github.com/ipfs/go-ds-s3
- IPFS HTTP API: https://docs.ipfs.tech/reference/kubo/rpc/
- IPFS gateway spec: https://specs.ipfs.tech/http-gateways/
- Backblaze B2 S3-compat: https://www.backblaze.com/docs/cloud-storage-s3-compatible-api
- ADR-0048 — Kotoba/Datomic Vultr B2 primary
- ADR-2604251400 — PDS uploadBlob R2→B2 migration
- ADR-2604251935 — blockchain VKE head ingest (same Vultr cluster pattern)
- ADR-2604261717 — staked claim truth-incentive (`atRecordCid` → IPFS pin target)
- ADR-0029 — did:etzhayyim CIDv1 path schema
