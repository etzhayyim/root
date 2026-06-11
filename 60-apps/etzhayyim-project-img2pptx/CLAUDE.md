# etzhayyim-project-img2pptx

**img2pptx.etzhayyim.com** — Image to PowerPoint shape conversion actor

## Domain

画像 (PNG/JPEG/SVG) を OOXML PresentationML の DrawingML 図形データ (.pptx) に変換する。画像のコンテンツをスライド上の図形 (rectangle, freeform path, image shape) として配置し、W Protocol record として永続化。MCP tools 経由で AI Agent がプレゼン生成を自動化可能。

## Architecture

- **TS Native + Lexicon Contract** (DEFAULT)
- **Single Worker**: `wasm/etzhayyim-wasm-img2pptx-im92pp7x/src/app.ts`
- **Blob Storage**: B2 path = `blobs/{library_did_hash}/{blake3}.pptx`
- **Generation Pipeline**: Image blob → shape definition → OOXML XML assembly → ZIP pack → .pptx blob

## DID

| DID | role |
|---|---|
| `did:web:img2pptx.etzhayyim.com` | service actor (sole) |

## Record Types (NSID)

| NSID | description |
|---|---|
| `com.etzhayyim.apps.img2pptx.conversion` | 変換ジョブメタデータ (sourceBlake3, outputBlobRef, slideCount, shapeCount, status) |
| `com.etzhayyim.apps.img2pptx.slide` | 生成スライド (slideIndex, shapes, imageBlobRef) |

## MCP Tools (AsAgentTool)

| command NSID | MCP tool name | description |
|---|---|---|
| `com.etzhayyim.apps.img2pptx.convertImage` | `convertImage` | 画像 → .pptx 変換 (image shape + optional vector trace) |
| `com.etzhayyim.apps.img2pptx.convertSvg` | `convertSvg` | SVG → PPTX DrawingML shape 変換 |
| `com.etzhayyim.apps.img2pptx.createPresentation` | `createPresentation` | 複数画像 → multi-slide .pptx 生成 |
| `com.etzhayyim.apps.img2pptx.listConversions` | `listConversions` | 変換履歴一覧 |
| `com.etzhayyim.apps.img2pptx.getConversion` | `getConversion` | 変換結果の詳細取得 |

## PPTX Generation Strategy

.pptx = ZIP archive (OOXML PresentationML):

```
[Content_Types].xml
_rels/.rels
ppt/presentation.xml          → slide order
ppt/slides/slide{N}.xml       → DrawingML shape tree (sp, pic, cxnSp)
ppt/_rels/presentation.xml.rels
ppt/slides/_rels/slide{N}.xml.rels → image rels
ppt/media/image{N}.{ext}      → embedded images
docProps/core.xml              → metadata
```

Shape types:
- **Image shape (`p:pic`)**: 画像をそのままスライドに配置
- **Freeform path (`a:custGeom`)**: SVG path → DrawingML path 変換
- **Rectangle (`p:sp` + `a:prstGeom`)**: テキスト付き矩形

## Design E 3-Tier Write

| Tier | action |
|---|---|
| Tier 1 Social | `app.bsky.feed.post` — "Generated: {title} ({slideCount} slides, {shapeCount} shapes)" |
| Tier 2 Domain | `com.etzhayyim.apps.img2pptx.conversion` / `.slide` records |
| Tier 3 State | conversion progress, per-user history (Preferences) |

## Reactive Pipeline

`handleComAtprotoSyncSubscribeReposCommit`:
- `com.etzhayyim.apps.img2pptx.conversion` create → track conversion status

## Prohibited

- Base64 encoding for blob upload (use FormData multipart)
- Direct HTTP fetch (all via W Protocol)
- Multiple source files (single `src/app.ts`)
