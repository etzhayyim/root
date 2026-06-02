# etzhayyim-project-ipfs

IPFS コンテンツ公開ゲートウェイ + **Federation publish** (`ipfs.etzhayyim.com`)。
Public W Protocol records を CIDv1 content-addressed で IPFS gateway に自動公開。

## App Components

| Component | nanoid | 役割 |
|---|---|---|
| `etzhayyim-wasm-ipfs-ip5s7b2x` | `ip5s7b2x` | IPFS gateway + federation publish |

## Architecture

```
Federation Publish (heartbeat, ~60s scan):
  on-heartbeat
    ↓
  G("Record").Match(sensitivity_ord=0).WhereIsNull("ipfsCid").Query()
    ↓ public records without CID
  SHA-256(content) → CIDv1 base32 (raw codec)
    ↓
  R2 PUT (etzhayyim-ipfs bucket, key: ipfs/{cid})
    ↓
  WRecord("ipfsCid", {cid, collection, rkey, repo, ...})
    ↓
  G("Record").Match({rkey}).Set({ipfs_cid: cid})

Direct Publish (command):
  POST /xrpc/.../Publish {content_base64, content_type}
    ↓
  SHA-256(content) → CIDv1 → R2 PUT → WRecord("ipfsObject", ...)

Gateway (read):
  GET /ipfs/{cid}
    ↓
  G("IpfsObject"|"IpfsCid").Match({cid}) → b2_key
    ↓
  R2 GET → Cache-Control: immutable → CDN edge cache
```

## Security

- **Public data only**: sensitivity=public (T3) records のみ IPFS 公開対象
- AT Protocol firehose で既に公開されているデータと同一 (追加 attack surface なし)
- CID = SHA-256(content) — content-addressed, tamper-proof
- B2 bucket は gateway GET のみ (write は internal)
- Federation 相手が CID で record integrity を検証可能

## IPFS Gateway

- `GET /ipfs/{cid}` — CID でコンテンツ取得。Cloudflare エッジキャッシュ
- `GET /ipfs/{cid}?format=json` — JSON decode して返す (application/json content)
- `GET /.well-known/ipfs-gateway` — Gateway capability advertisement
- Response headers: `Cache-Control: public, max-age=29030400, immutable`, `X-IPFS-Path`, `Etag`, `Access-Control-Allow-Origin: *`
- CID は CIDv1 (base32, raw codec, sha2-256)

## Commands

| Command | 説明 |
|---|---|
| `publish` | Base64 content → CIDv1 → B2 upload → WRecord (idempotent) |
| `get_object` | CID で IpfsObject or IpfsCid メタデータ取得 |
| `list_objects` | Public オブジェクト一覧 (pagination) |
| `publish_public_records` | 手動 scan: public records → IPFS publish |
| `verify_cid` | CID integrity 検証 (recompute and compare) |

## Graph Labels

| Label | 用途 |
|---|---|
| `IpfsObject` | Direct publish オブジェクト (cid, b2_key, content_type, size, visibility) |
| `IpfsCid` | Federation publish CID (cid, b2_key, collection, rkey, repo, size) |

## WIT

- Domain: `etzhayyim:ipfs@1.0.0` (`60-apps/etzhayyim-project-ipfs/wit/ipfs/package.wit`)
- Interfaces: `ipfs-gateway` (resolve, list-by-did, list-by-collection), `ipfs-publish` (publish-record, verify)

## B2 Configuration

| Variable | 説明 |
|---|---|
| `ipfs_b2_endpoint` | S3 endpoint (default: B2) |
| `ipfs_b2_bucket` | Bucket 名 (default: `etzhayyim-ipfs`) |
| `ipfs_b2_region` | Region (default: `auto`) |
| `ipfs_b2_access_key_id` | B2 Access Key ID |
| `ipfs_b2_secret_access_key` | B2 Secret Access Key |

## Smoke Test

```bash
curl https://ip5s7b2x.etzhayyim.com/health

# Gateway
curl https://ipfs.etzhayyim.com/ipfs/{cid}
curl https://ipfs.etzhayyim.com/.well-known/ipfs-gateway

# Publish content
curl -X POST https://ip5s7b2x.etzhayyim.com/xrpc/etzhayyim.ipfs.v1.IpfsCommandService/Publish \
  -H "Content-Type: application/json" \
  -d '{"content_base64":"SGVsbG8gSVBGUw==","content_type":"text/plain"}'

# Trigger federation scan
curl -X POST https://ip5s7b2x.etzhayyim.com/xrpc/etzhayyim.ipfs.v1.IpfsCommandService/PublishPublicRecords \
  -H "Content-Type: application/json" \
  -d '{"limit":100}'

# Verify CID
curl -X POST https://ip5s7b2x.etzhayyim.com/xrpc/etzhayyim.ipfs.v1.IpfsCommandService/VerifyCid \
  -H "Content-Type: application/json" \
  -d '{"cid":"bafk..."}'
```

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-ipfs/wasm/etzhayyim-wasm-ipfs-ip5s7b2x
etzhayyim build && etzhayyim deploy
```

## Future Phases

- **Phase 2**: MDAG commit tree → Merkle root CID (per-DID commit chain on IPFS)
- **Phase 3**: IPNI announce (HTTP advertisement chain, no libp2p)
