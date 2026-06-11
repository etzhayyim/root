# etzhayyim-project-color-by-number

協働カラーバイナンバー (`color-by-number.etzhayyim.com`)。
マス目に番号が割り振られたキャンバスを複数ユーザーが協力して塗り絵するゲーム。

## App Component

| Component | nanoid | 役割 |
|---|---|---|
| `etzhayyim-wasm-color-by-number-cbn8gf7x` | `cbn8gf7x` | Kotodama ランタイム WASM — AT + Signal + SQL 統合 |

## Architecture

```
Client (Widget API)
  ↓ XRPC / AT Protocol
etzhayyim.coloring.v1.ColoringCommandService / ColoringQueryService
  ↓ performer.Runtime (ATCommandEnvelope)
WASM component (kotodama runtime)
  ├── AT Protocol   — com.etzhayyim.command.coloring.paint / create → performer methods
  ├── Signal Protocol — group Sender Key session per canvas (E2E canvas events)
  └── SQL Protocol — yata graph (:Cell)-[:ADJACENT]->(:Cell) → color suggestion

Storage: kotodama WIT (LanceQuerySQL / LanceUpsertOne / KvGet / KvPut)
  ├── cbn_canvases_current   — canvas メタデータ
  ├── cbn_cells_current      — セル状態 (色番号 / 塗色 / 誰が塗ったか)
  └── cbn_signal_sessions_current — Signal group session per canvas
```

## AT Lexicon Routes

| Lexicon ID | performer method |
|---|---|
| `com.etzhayyim.command.coloring.paint` | `paint_cell` |
| `com.etzhayyim.command.coloring.create` | `create_canvas` |

## XRPC Services

- `etzhayyim.coloring.v1.ColoringCommandService` — PaintCell, CreateCanvas, InitSignalSession
- `etzhayyim.coloring.v1.ColoringQueryService` — GetCanvas, ListCanvases, GetCanvasGraph

## Arrow Tables

| Table | 用途 |
|---|---|
| `cbn_canvases_current` | キャンバスメタデータ (id, name, width, height, cell_count, visibility) |
| `cbn_cells_current` | セル状態 (canvas_id, cell_index, color_number, filled_color, filled_by) |
| `cbn_signal_sessions_current` | Signal group session (canvas_id, group_id, session_json, distribution_json) |

全テーブルに RLS: `org_id`, `user_id`, `actor_id`。

## Signal Protocol

各キャンバスに対して Sender Key グループセッションを保持する。
- `init_signal_session`: `SignalGroupInitSender` でセッション初期化 → `SenderKeyDistribution` を返却
- `paint_cell`: セル塗り変えイベントを `SignalGroupEncrypt` で暗号化してクライアントへ配信
- セッション状態は KV (`signal_sessions` バケット) に永続化

## SQL Protocol (yata graph)

キャンバスのグリッドトポロジーを yata graph (LanceDB append-only) に保持し、色サジェストに使用する。

- `(:Cell {canvas_id, index, row, col, filled_color})` ノード
- `(:Cell)-[:ADJACENT]->(:Cell)` エッジ (上下左右 4 方向)
- `get_canvas_graph`: 隣接セルの塗色頻度を集計し候補色を返す

## Kotodama Variables (kotodama.jsonld component.env)

| Variable (SPIN_VARIABLE_ prefix) | 説明 |
|---|---|
| `AUTH_JWKS_URL` | authn.etzhayyim.com JWKS URL |

## Build & Deploy

```bash
cd 60-apps/etzhayyim-project-color-by-number/wasm/etzhayyim-wasm-color-by-number-cbn8gf7x
etzhayyim build        # TS Native → esbuild bundle
etzhayyim deploy --smoke-url https://cbn8gf7x.etzhayyim.com/health
```
