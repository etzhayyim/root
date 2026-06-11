# etzhayyim-project-shomeisyashin

証明写真生成サービス shomeisyashin.etzhayyim.com — 自撮り写真を証明写真規格に変換。murakumo VL (qwen3-vl-8b) で顔検出・背景解析。

## Architecture

```
Browser → shomeisyashin.etzhayyim.com (SSR)
       → API → /etzhayyim.shomeisyashin.v1.ShomeisyashinCommandService/... + QueryService/...
                  ↓
           App: etzhayyim-wasm-shomeisyashin-f901c7i4
             ├─ UploadPhoto (FormData multipart → CDN R2)
             ├─ GenerateIDPhoto (murakumo VL 顔解析 + Canvas crop/resize)
             ├─ ListPhotos / GetPhoto (SQL graph)
             └─ SQL graph → photos metadata
```

## Component

| Component | Folder | Role |
|---|---|---|
| shomeisyashin-api | `wasm/etzhayyim-wasm-shomeisyashin-f901c7i4/` | XRPC API + SSR |

## Graph Nodes

| Node | Purpose |
|---|---|
| `:Photo` | Original upload metadata (photo_id, blob_key, mime_type, width, height) |
| `:IDPhoto` | Generated ID photo (id_photo_id, photo_id, blob_key, format, width_mm, height_mm, bg_color, face_json) |

## ID Photo Formats

| Format | Size (mm) | Usage |
|---|---|---|
| `passport_jp` | 35x45 | Japanese passport |
| `mynumber` | 24x30 | My Number card |
| `drivers_jp` | 24x30 | Japanese driver's license |
| `resume_jp` | 30x40 | Japanese resume (履歴書) |
| `visa_us` | 51x51 | US visa |
| `passport_intl` | 35x45 | ICAO standard |

## Flow

1. User captures/uploads selfie (FormData multipart → CDN B2)
2. murakumo VL analyzes: face bounding box, head tilt, eye position, background suitability
3. Server-side canvas: crop to face center, resize to format, apply white/blue background
4. Generated ID photo stored in CDN B2 + metadata in SQL graph
5. User downloads or re-generates with different format/background

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-shomeisyashin/wasm/etzhayyim-wasm-shomeisyashin-f901c7i4/svelte
pnpm install && pnpm build
cd ..
etzhayyim build
etzhayyim deploy --smoke-url https://f901c7i4.etzhayyim.com/health
```
