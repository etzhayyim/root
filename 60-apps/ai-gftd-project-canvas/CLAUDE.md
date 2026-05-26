# ai-gftd-project-canvas — canvas.etzhayyim.com

**Protocol Canvas rendering & collaboration** — W Protocol record visualization, interactive card layout, real-time collaborative canvas.

## Architecture

| 項目 | 値 |
|---|---|
| Domain | `canvas.etzhayyim.com` |
| Runtime | **Single Worker** (TS Native) |
| nanoid | `cnv5dr4w` |
| performerType | `service` (default sensitivity: `public`) |
| uiType | `appview` (Protocol Canvas card) |

## Multi-DID Architecture `[DESIGN]`

| DID | 用途 |
|---|---|
| `did:web:canvas.etzhayyim.com` | Controller (app 本体) |
| `did:web:canvas.etzhayyim.com:board:{nanoid}` | Canvas board |
| `did:web:canvas.etzhayyim.com:template:{nanoid}` | Reusable canvas template |

## Design E 3-Tier Write

| Tier | 用途 | 関数 | Collection NSID |
|---|---|---|---|
| **1 Social** | Canvas 公開共有 | `AppBskyFeedPost(did, text, {embed})` | `app.bsky.feed.post` |
| **2 Domain** | board/element/layer/template | `ComAtprotoRepoCreateRecord(kind, payload)` | `app.etzhayyim.apps.canvas.*` |
| **3 State** | 表示設定 | `Preferences()` | server-side |

## Domain Record Types (Tier 2, camelCase) `[DESIGN]`

| Kind | NSID | 内容 |
|---|---|---|
| `board` | `app.etzhayyim.apps.canvas.board` | Canvas board 定義 (title, dimensions, visibility) |
| `element` | `app.etzhayyim.apps.canvas.element` | Canvas 要素 (shape, text, image, connector) |
| `layer` | `app.etzhayyim.apps.canvas.layer` | Layer 管理 (z-order, visibility, lock) |
| `template` | `app.etzhayyim.apps.canvas.template` | Reusable canvas template |

## Reactive Pipeline (ComAtprotoSyncSubscribeRepos) `[DESIGN]`

- `app.etzhayyim.apps.canvas.board` create -> social notification via AppBskyFeedPost
- `app.etzhayyim.apps.canvas.element` create -> AI auto-layout suggestion

## File Structure

```
60-apps/ai-gftd-project-canvas/
├── CLAUDE.md
├── wit/canvas/package.wit           # Domain WIT capability
└── wasm/ai-gftd-wasm-canvas-cnv5dr4w/
    ├── src/app.ts                   # TS Native — Design E reactive pipeline
    ├── magatama.jsonld
    └── wit/world.wit                # Component WIT (contract + capability export)
```
