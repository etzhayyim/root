# etzhayyim-project-photos — photos.etzhayyim.com

**AI-powered photo storage & organization** — Google Photos ライクなユーザー別写真管理サービス。

## Architecture

| 項目 | 値 |
|---|---|
| Domain | `photos.etzhayyim.com` |
| Runtime | **Single Worker** (TS Native) |
| nanoid | `krtjlccu` |
| performerType | `service` (default sensitivity: `public`) |
| uiType | `appview` (Protocol Canvas card) |

## Multi-DID Architecture `[DESIGN]`

| DID | 用途 |
|---|---|
| `did:web:photos.etzhayyim.com` | Controller (app 本体) |
| `did:web:photos.etzhayyim.com:library:{nanoid}` | ユーザー写真ライブラリ |
| `did:web:photos.etzhayyim.com:album:{nanoid}` | 共有アルバム |

## Design E 3-Tier Write

| Tier | 用途 | 関数 | Collection NSID |
|---|---|---|---|
| **1 Social** | 写真公開投稿 | `AppBskyFeedPost(libraryDID, text, {embed})` | `app.bsky.feed.post` |
| **2 Domain** | photo/album/tag/share_grant | `ComAtprotoRepoCreateRecord(kind, payload)` | `com.etzhayyim.apps.photos.*` |
| **3 State** | 表示設定 | `Preferences()` | server-side |

## Domain Record Types (Tier 2, camelCase) `[DESIGN]`

| Kind | NSID | 内容 |
|---|---|---|
| `photo` | `com.etzhayyim.apps.photos.photo` | 写真メタデータ (blob_ref, EXIF, geo, dimensions) |
| `album` | `com.etzhayyim.apps.photos.album` | アルバム定義 (title, visibility, album_did) |
| `album_item` | `com.etzhayyim.apps.photos.album_item` | アルバム↔写真リレーション |
| `tag` | `com.etzhayyim.apps.photos.tag` | タグ (manual/ai/ai_geo) |
| `share_grant` | `com.etzhayyim.apps.photos.share_grant` | 共有権限 |

## Reactive Pipeline (ComAtprotoSyncSubscribeRepos) `[DESIGN]`

- `com.etzhayyim.apps.photos.photo` create → murakumo vision auto-tagging + geo-reverse
- `com.etzhayyim.apps.photos.share_grant` create → social notification via AppBskyFeedPost

## Sensitivity & Governance `[DESIGN]`

| 対象 | Sensitivity | 理由 |
|---|---|---|
| Photo blob | `confidential` | 個人写真デフォルト非公開 |
| Album (private) | `confidential` | owner のみ |
| Album (shared) | `internal` | share_grant target DID のみ |
| Album (public) | `public` | Tier 1 Social |
| FaceCluster | `restricted` | 生体情報 (GDPR Art.9) |

## Blob Storage `[DESIGN]`

- FormData + multipart 必須 (base64 禁止)
- Client Blake3 事前計算 → checkBlobExists → linkBlob (dedup) or upload
- >64 MiB: 自動 multipart chunked parallel
- B2 path: `blobs/{library_did_hash}/{blake3}.{ext}`

## File Structure

```
60-apps/etzhayyim-project-photos/
├── CLAUDE.md
├── wit/photos/package.wit           # Domain WIT capability
└── wasm/etzhayyim-wasm-photos-krtjlccu/
    ├── src/app.ts                    # TS Native — Design E reactive pipeline
    ├── kotodama.jsonld
    └── wit/world.wit                # Component WIT (contract + capability export)
```
