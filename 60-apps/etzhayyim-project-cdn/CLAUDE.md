# etzhayyim-project-cdn

CDN ブロブストレージゲートウェイ (`cdn.etzhayyim.com`)。
キーでデータを公開し、実データは Backblaze B2 に保存、Cloudflare CDN で配信する。

## App Components

| Component | nanoid | 役割 |
|---|---|---|
| `etzhayyim-wasm-cdn-cdn7gft2` | `cdn7gft2` | CDN blob gateway + upload API |

## Architecture

```
Client
  ↓ GET /cdn/{key}
cdn.etzhayyim.com (Cloudflare proxied)
  ↓ Cache-Control: public, max-age=86400
App (cdn7gft2)
  ↓ S3 SigV4
Cloudflare R2 (bucket: etzhayyim-graph, key: cdn/{key})
```

## API Endpoints

- App direct: `https://cdn7gft2.etzhayyim.com`
- CDN: `https://cdn.etzhayyim.com/cdn/{key}`
- XRPC: `https://cdn7gft2.etzhayyim.com/xrpc`

## Arrow Tables

| Table | 用途 |
|---|---|
| `cdn_blobs_current` | ブロブメタデータ (key, b2_key, content_type, size, cid, visibility) |

RLS: `org_id`, `user_id`, `actor_id` 必須。

## B2 Configuration (kotodama variables)

| Variable | 説明 |
|---|---|
| `cdn_s3_endpoint` | S3 endpoint (B2) |
| `cdn_s3_bucket` | Bucket 名 (default: `etzhayyim-graph`) |
| `cdn_s3_region` | Region (default: `auto`) |
| `cdn_s3_access_key_id` | B2 Access Key ID |
| `cdn_s3_secret_access_key` | B2 Secret Access Key |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-cdn/wasm/etzhayyim-wasm-cdn-cdn7gft2
etzhayyim build && etzhayyim deploy
```
