# etzhayyim-project-pptx — pptx.etzhayyim.com

**PowerPoint editor + image conversion + content extraction** — PPTX upload, Canvas 2D + KAMI Engine wgpu (WebGPU/WebGL2) editing, kagami graph persistence, OOXML export. Figma-like UX. Consolidates img2pptx + mime-pptx.

## Architecture

| Item | Value |
|---|---|
| Domain | `pptx.etzhayyim.com` |
| Endpoint | `https://t53br1o0.etzhayyim.com/editor` |
| Runtime | **Single Worker** (TS Native) |
| nanoid | `t53br1o0` |
| performerType | `service` (default sensitivity: `internal`) |
| uiType | `appview` |
| Client rendering | wgpu WebGPU/WebGL2 via KAMI Engine (primary) + Canvas 2D (fallback) |
| Client framework | Svelte 5 (runes, `$state` object pattern) |
| OOXML library | fflate (ZIP) + custom DrawingML parser/exporter |
| Bundle | ~139KB inline HTML (JS 130KB + CSS 8KB, gzip 46KB) |
| WASM | kami-web 1.7MB (wgpu instanced SDF rect shader) |
| Consolidated apps | img2pptx (`im92pp7x` → Logical Actor), mime-pptx (`lcryu45x` → Logical Actor) |

## Consolidated Apps

**pptx.etzhayyim.com は 3 アプリの統合版。** img2pptx と mime-pptx の機能を XRPC command として一本化。旧 Worker は Logical Actor 化。

| 旧 App | 旧 nanoid | 統合先 NSID | 機能 |
|---|---|---|---|
| img2pptx.etzhayyim.com | `im92pp7x` | `com.etzhayyim.apps.pptx.convertImage` | 画像 → slide shape |
| img2pptx.etzhayyim.com | `im92pp7x` | `com.etzhayyim.apps.pptx.convertSvg` | SVG → DrawingML shapes |
| img2pptx.etzhayyim.com | `im92pp7x` | `com.etzhayyim.apps.pptx.createFromImages` | 複数画像 → multi-slide |
| mime-pptx.etzhayyim.com | `lcryu45x` | `com.etzhayyim.apps.pptx.extractAllText` | 全テキスト抽出 |
| mime-pptx.etzhayyim.com | `lcryu45x` | `com.etzhayyim.apps.pptx.searchText` | 全文検索 |
| mime-pptx.etzhayyim.com | `lcryu45x` | `com.etzhayyim.apps.pptx.getMetadata` | メタデータ |
| mime-pptx.etzhayyim.com | `lcryu45x` | `com.etzhayyim.apps.pptx.getSlide` | slide + text + image refs |

## Data Pipeline

```
Upload (.pptx ZIP)
  → fflate: zip decompress + OOXML DrawingML XML parse (ooxml-parser.ts)
  → In-memory: PptxPresentation → PptxSlide → PptxShape/PptxImage typed graph
  → wgpu: GPU instanced SDF rect rendering (kami-web WASM) / Canvas 2D fallback
  → Edit: multi-select, resize, rotate, text edit, snap guides, layers
  → Export: graph → OOXML XML rebuild → fflate zip → .pptx download
  → Persist (backend): kagami SQL graph → RisingWave Hyperdrive read

Image conversion:
  Image blob → convertImage → slide + image shape (auto-sized)
  SVG → convertSvg → DrawingML freeform shape
  Multiple images → createFromImages → multi-slide presentation

Content extraction:
  Presentation → extractAllText → concatenated text (LLM summarization)
  Query → searchText → full-text search across slides
  Presentation → getMetadata → title, author, slideCount
  Slide index → getSlide → text + image refs
```

## Deploy

**Workers Assets は account-level Worker mode でも直接 serve されない。** Svelte build output は `inline-build.mjs` が base64 エンコードし、`src/app.ts` の `EDITOR_HTML_B64` 定数に patch。Hono `/editor` route が decode して HTML serve。

```bash
cd svelte && pnpm build    # vite build → _svelte/ → inline-build.mjs patches src/app.ts
cd .. && etzhayyim deploy --no-check --smoke-url https://t53br1o0.etzhayyim.com/health
```

## Rendering Architecture

```
Browser
├─ KAMI WASM loaded (/pkg/kami_web.js, 1.7MB)
│   └─ render_document_frame() → wgpu (WebGPU → WebGL2 fallback, ~97% coverage)
│       ├─ UiRect instanced quads (GPU, 1 draw call per shape type)
│       ├─ SDF rounded rect WGSL shader (anti-aliased, per-pixel border)
│       └─ 1000+ shapes @ 60fps
└─ KAMI WASM not available
    └─ Canvas 2D fallback (slide-renderer.ts)
        └─ ctx.fillRect / ctx.ellipse per shape (CPU, ~50 shapes smooth)

Toggle: toolbar badge "wgpu" / "Canvas2D" (click to switch when KAMI loaded)
```

## XRPC Commands (23 total)

### Presentation Management (5)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.upload` | Upload and parse PPTX file |
| `com.etzhayyim.apps.pptx.create` | Create new blank presentation |
| `com.etzhayyim.apps.pptx.delete` | Delete presentation |
| `com.etzhayyim.apps.pptx.export` | Export presentation to PPTX |

### Slide Editing (8)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.addSlide` | Add slide |
| `com.etzhayyim.apps.pptx.removeSlide` | Remove slide |
| `com.etzhayyim.apps.pptx.reorderSlides` | Reorder slides |
| `com.etzhayyim.apps.pptx.addShape` | Add shape to slide |
| `com.etzhayyim.apps.pptx.updateShape` | Update shape properties |
| `com.etzhayyim.apps.pptx.removeShape` | Remove shape |
| `com.etzhayyim.apps.pptx.editText` | Edit text in shape |
| `com.etzhayyim.apps.pptx.addImage` | Add image to slide |

### Search & Query (3)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.search` | Search presentations |
| `com.etzhayyim.apps.pptx.listSlides` | List slides |
| `com.etzhayyim.apps.pptx.getSlideElements` | Get slide elements |

### Image Conversion (3, from img2pptx)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.convertImage` | Image blob → slide shape |
| `com.etzhayyim.apps.pptx.convertSvg` | SVG → DrawingML shapes |
| `com.etzhayyim.apps.pptx.createFromImages` | Multiple images → multi-slide presentation |

### Content Extraction (4, from mime-pptx)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.extractAllText` | All text from all slides (LLM summarization) |
| `com.etzhayyim.apps.pptx.searchText` | Full-text search across slides |
| `com.etzhayyim.apps.pptx.getMetadata` | Presentation metadata |
| `com.etzhayyim.apps.pptx.getSlide` | Single slide with text + image refs |

### Utility (3)

| NSID | Description |
|---|---|
| `com.etzhayyim.apps.pptx.health` | Health check |
| `com.etzhayyim.apps.pptx.describe` | Describe capabilities |
| `com.etzhayyim.apps.pptx.wave` | Wave greeting |

## Editor Features (Figma-Like UX)

### Phase 1 — Core Interaction

| Feature | Module |
|---|---|
| Multi-select (shift+click, rubber band) | `editor-state.svelte.ts` |
| Transform handles (8 resize + rotation) | `transform-handles.ts` |
| Smart guides (5px snap threshold, magenta lines) | `snap-engine.ts` |
| Scroll zoom (cursor center, 0.1x–5.0x) | `App.svelte` |
| Space+drag pan | `App.svelte` |
| Cursor feedback (resize/move/grab/crosshair) | `App.svelte` |
| Arrow nudge (1px / 10px with shift) | `App.svelte` |
| Z-layer scroll (selection → bringForward/sendBackward) | `App.svelte` |

### Phase 2 — Productivity

| Feature | Description |
|---|---|
| Layers panel | z-order, visibility/lock toggle, name edit |
| Text editing | double-click → contenteditable overlay + B/I/U toolbar |
| Align/distribute | 6 align + 2 distribute for multi-select |
| Group/ungroup | Cmd+G / Cmd+Shift+G |
| Rulers | top 20px + left 20px, inch markings, zoom/pan tracking |

### Phase 3 — Polish

| Feature | Description |
|---|---|
| Grid overlay | dot grid, configurable size, snap toggle |
| Slide drag reorder | HTML5 drag in slide panel |
| Corner radius handle | orange handle for roundRect |
| Minimap | 150px, viewport rect, click-to-pan |
| Path2D cache | shape path caching for drag performance |
| Slide sorter | full-width grid view of all slides |
| Rich text toolbar | font family/size/color/alignment |

### Keyboard Shortcuts

| Key | Action |
|---|---|
| V / R / O / T / L | Select / Rect / Ellipse / Text / Line tool |
| Arrow / Shift+Arrow | Nudge 1px / 10px |
| Cmd+A | Select all |
| Cmd+C / V / X / D | Copy / Paste / Cut / Duplicate |
| Cmd+G / Cmd+Shift+G | Group / Ungroup |
| Cmd+[ / ] | Send backward / Bring forward |
| Cmd+Z / Cmd+Shift+Z | Undo / Redo |
| Cmd+S | Export .pptx |
| Delete | Delete selected |
| Escape | Deselect / exit text edit |
| Space+drag | Pan |
| Scroll (no selection) | Zoom |
| Scroll (with selection) | Z-layer reorder |

## WIT Interfaces (5)

| Interface | Functions |
|---|---|
| `presentation-management` | upload, create, delete, export, duplicate |
| `slide-editing` | addSlide, removeSlide, reorderSlides, addShape, updateShape, removeShape, editText, addImage |
| `presentation-search` | search, listSlides, getSlideElements |
| `image-conversion` | convertImage, convertSvg, createFromImages |
| `content-extraction` | extractAllText, searchText, getMetadata, getSlide |

## Graph Model (kagami SQL)

| PPTX Structure | SQL Node | Edge |
|---|---|---|
| Presentation | `(:Presentation {did, title})` | |
| Slide | `(:Slide {order, layoutRef})` | `(:Presentation)-[:HAS_SLIDE]->(:Slide)` |
| Shape | `(:Shape {type, x, y, w, h, rotation, cornerRadius, visible, locked, groupId})` | `(:Slide)-[:CONTAINS]->(:Shape)` |
| TextBody | `(:TextBody {align, verticalAlign})` | `(:Shape)-[:HAS_TEXT]->(:TextBody)` |
| Paragraph | `(:Paragraph {level, spacing})` | `(:TextBody)-[:HAS_PARA]->(:Paragraph)` |
| Run | `(:Run {text, bold, italic, underline, size, color, font})` | `(:Paragraph)-[:HAS_RUN]->(:Run)` |
| Image | `(:Image {blobCid, w, h, mime})` | `(:Slide)-[:CONTAINS]->(:Image)` |
| Theme | `(:Theme {name, colors})` | `(:Presentation)-[:USES_THEME]->(:Theme)` |

## Multi-DID Architecture `[DESIGN]`

| DID | Purpose |
|---|---|
| `did:web:pptx.etzhayyim.com` | Controller (app) |
| `did:web:pptx.etzhayyim.com:presentation:{nanoid}` | Individual presentation |
| `did:web:pptx.etzhayyim.com:template:{nanoid}` | Reusable slide template |

## Design E 3-Tier Write

| Tier | Purpose | Function | Collection NSID |
|---|---|---|---|
| **1 Social** | Share presentation | `AppBskyFeedPost(did, text, {embed})` | `app.bsky.feed.post` |
| **2 Domain** | presentation/slide/shape/textRun/image | `ComAtprotoRepoCreateRecord(kind, payload)` | `com.etzhayyim.apps.pptx.*` |
| **3 State** | Editor preferences | `Preferences()` | server-side |

## PPTX Export — OOXML Compliance

Keynote/PowerPoint 互換:
- `<p:clrMap>` 12 色ロール mapping (slideMaster 必須)
- `<p:bgRef idx="1001">` (scheme-based background)
- Shape `id >= 2` (1 = group reserved)
- `<a:bodyPr rtlCol="0">`, `<a:rPr dirty="0" lang="en-US">`
- `saveSubsetFonts="1"`, `<p:sldSz type="custom"/>`
- `docProps/app.xml` + `docProps/core.xml` (Keynote 要求)

## File Structure

```
60-apps/etzhayyim-project-pptx/
├── CLAUDE.md
├── wit/pptx/package.wit                         # 5 WIT interfaces (25 functions)
└── wasm/etzhayyim-wasm-pptx-t53br1o0/
    ├── kotodama.jsonld                          # Agent profile, triggers, routes
    ├── wrangler.jsonc                           # Workers Assets + PDS binding
    ├── src/
    │   └── app.ts                               # Backend: 23 XRPC commands + /editor /embed routes
    ├── wit/world.wit                            # contract + 5 capability exports
    └── svelte/                                  # Client-side Svelte 5 editor
        ├── package.json                         # fflate, svelte 5, vite
        ├── vite.config.ts
        ├── 70-tools/70-tools/70-tools/scripts/inline-build.mjs             # Post-build: base64 → patch app.ts
        └── src/
            ├── main.ts
            ├── App.svelte                       # Editor UI (toolbar, dual canvas, panels)
            └── lib/
                ├── ooxml-parser.ts              # PPTX ZIP → typed slide graph
                ├── pptx-exporter.ts             # Slide graph → OOXML → ZIP → .pptx
                ├── slide-renderer.ts            # Canvas 2D rendering + hit testing
                ├── editor-state.svelte.ts       # Svelte 5 $state + undo/redo + mutations
                ├── transform-handles.ts         # Resize/rotation/cornerRadius handles
                ├── snap-engine.ts               # Smart guides + snap-to-shape
                └── kami-bridge.ts               # KAMI wgpu GPU renderer + Canvas 2D fallback
```

## kami-engine-sdk Integration

`@etzhayyim/kami-engine-sdk/document` module に汎用ドキュメントモデル + KAMI scene bridge を追加済み。

KAMI wgpu WASM (`kami-web/src/document.rs`):
- `render_document_frame(canvas_id, slide_json)` — wgpu instanced SDF rect rendering
- `check_document_gpu()` — WebGPU/WebGL2 検出
- `document_gpu_info()` — GPU adapter info
- WGSL shader: `sdf_rounded_rect()` + anti-aliased border ring + alpha blending
