---
id: adr-2605092800-kami-gsplat-preview-bake-pipeline
title: KAMI Gsplat Preview Renderer + Splat→Mesh Bake Pipeline for maps.etzhayyim.com
status: active
doc_type: adr
topic: kami-gsplat-preview-bake
authoritative: true
last_verified: 2026-05-10
authoritative_for:
  - kami-engine 3D Gaussian Splatting policy
  - maps.etzhayyim.com splat asset preview path
  - splat-to-mesh bake pipeline contract
  - mapillary-to-3dgs trainer + idempotency rules
  - per-tile spend cap + per-job cost telemetry
related:
  - maps-kami-street-asset-pipeline
  - 90-docs/260409-kami-engineering-sdk-design.md
  - adr-0036-worker-direct-hyperdrive-persistence
  - adr-2604251830-shannon-optimal-layered-architecture
  - adr-2605080700-graph-schema-live-kotoba-baseline
supersedes: []
superseded_by: []
---

# Goal

`maps.etzhayyim.com` の street-level / landmark 再構成パイプラインに、
PlayCanvas が browser で実用化している 3D Gaussian Splatting (3DGS) を
**preview / QC ツール** として導入する。Runtime 配信形式は引き続き
static mesh を採用する (260416-maps-kami-street-asset-pipeline-design 維持)。

# Scope

- 3DGS アセット (PLY / .splat compact 形式) の Kotoba/Datomic 永続化
- 3DGS アセットの browser 直接プレビュー (kami-engine WASM, wgpu)
- 3DGS → mesh GLB の bake 起動 XRPC
- kami-engine-sdk への splat 取得・WASM 投入 helper の追加

# Non-Goals

- city-scale 3DGS の runtime 配信
- 3DGS を gameplay の collision / nav surface として使う
- 3DGS を gltf / glb 同等の 1st-class delivery format にする

これらは `260416-maps-kami-street-asset-pipeline-design.md` の決定を
そのまま継承する。

# Decision

## D1. Runtime 配信 = static mesh のまま

`260416-maps-kami-street-asset-pipeline-design.md` の Decision を維持。
`vertex_spatial.Building` + `mesh_tile` GLB が runtime 配信形式の SSoT。
3DGS は **再構成中間表現 + preview/QC** に限定する。

## D2. Renderer の場所

3DGS renderer は `kami-pipelines::GsplatAdapter` (CPU sort + wgpu draw,
`RenderPipeline` trait 実装) として実装する。`kami-render::splat` /
`splat_loader` の既存データ構造とローダを再利用する。
`kami-render::splat_pipeline` の experimental scaffolding は追加 PR 範囲外
(将来 GPU radix sort 化したいときに整理する)。

`kami-app-maps3d` は `gsplat.rs` 経由で `GsplatAdapter` を組み込む。
preview tile は `set_gsplat_asset(tileH3, bytes, format)` で WASM に注入する。

ARCHITECTURE 上の所有関係:

| Crate | 役割 |
|---|---|
| `kami-render::splat` / `splat_loader` | data shapes + PLY/.splat parser (SSoT) |
| `kami-pipelines::GsplatAdapter` | shared `RenderPipeline` adapter (SSoT) |
| `kami-app-maps3d::gsplat` | per-game wasm-bindgen surface |
| (任意の他 game crate) | 同 adapter を再利用可能 (例: scene 検証用) |

`kami-render::splat_pipeline` の自己完結化 / GPU sort 移行は別 ADR で扱う。

## D3. Persistence (Kotoba/Datomic / ADR-0036)

新規テーブル:

- `vertex_maps_gsplat_asset` — splat 1 ファイル = 1 行
  - PK: `vertex_id` (`at://{authority}/com.etzhayyim.apps.maps.gsplatAsset/{rkey}`)
  - 主要列: `source_did`, `tile_h3`, `b2_key`, `byte_size`, `splat_count`,
    `sh_degree`, `format`, `generated_at`, `bake_job_id`, `props` JSON
  - RLS: `actor_did` / `org_did` / `at_did` / `created_at` (ADR-0095)
- `edge_maps_gsplat_baked_to` — splat → mesh の lineage
  - PK: `(gsplat_vertex, mesh_vertex)`
  - 主要列: `baked_at`, `bake_job_id`, `mesh_vertex_label`

書き込み = `createKyselyDb(env.HYPERDRIVE).insertInto(...)` 直接 (T2 Tier)。
PDS bypass。`ON CONFLICT` 不使用 (RW append-only / ADR-0048 / record-log)。

## D4. XRPC Lexicons

`com.etzhayyim.apps.maps.*` 名前空間に 3 メソッドを追加する。

| NSID | 種別 | 役割 |
|---|---|---|
| `com.etzhayyim.apps.maps.getGsplatAsset` | query | 単一 asset 取得 (preview 配信) |
| `com.etzhayyim.apps.maps.listGsplatAssets` | query | tile_h3 / bbox / source_did で一覧 |
| `com.etzhayyim.apps.maps.bakeGsplatAsset` | procedure | bake job を BPMN へ enqueue |

`getGsplatAsset` は B2 signed URL + metadata を返す (binary は B2 直配信)。
`bakeGsplatAsset` は `sdk.zeebe.publishMessage({ name: "com.etzhayyim.apps.maps.bakeGsplatAsset", correlationKey: vertex_id, ... })` で k8s pod に委譲する (ADR-2604251830 L7)。

## D5. SDK

`@etzhayyim/kami-engine-sdk` に `./gsplat` サブモジュールを追加する。

- `loadGsplatAsset(endpoint, tileH3)` → `{ bytes: Uint8Array, format, meta }`
- `pushToWasm(wasm, tileH3, asset)` — `set_gsplat_asset` を呼ぶ薄い wrapper
- `removeFromWasm(wasm, tileH3)` — 同 `remove_gsplat_asset`
- 型: `GsplatAssetMeta`

ロードは XRPC `getGsplatAsset` → signed URL → fetch の 2 段。SDK の中で
binary を保持しない (即 wasm 投入)。

## D6a. Mapillary → 3DGS trainer (RunPod L40S, 2026-05-09)

`maps.etzhayyim.com` の `did:web:maps.etzhayyim.com:street_view` (Mapillary) を入力に、
preview 用の 3DGS PLY を生成する pipeline を加える。SuperSplat は editor /
viewer 専用 (生成不可) なので trainer は別系統で持つ。

採用 trainer = **`gsplat`** (`nerfstudio-project/gsplat`)。維持されており CUDA
backend が安定。COLMAP で SfM、`gsplat` で training、PLY 出力。SuperSplat / 本
adapter どちらでも開ける。

Pipeline:

1. `cmdTrainGsplatFromMapillary` XRPC が message-start BPMN を publish
2. `bulk-ingest-gsplat-train` k8s pod (`workers/gsplat_train_dumper.py`) が:
   a. Mapillary Graph API v4 で bbox 内 image list を取得
   b. RunPod `/run` (`runpod-endpoint-gsplat/handler.py`) に転送
   c. `/status` をポーリング、`COMPLETED` で `plyBase64` を取得
   d. B2 に `maps-bulk-ingest/gsplat/{tile_h3}-{train_job_id}.ply` で保存
   e. `vertex_maps_gsplat_asset` に 1 行 INSERT (RW append-only、`bake_job_id` は NULL)
3. browser 側の prefetch ループ (`maps-3d.htm?gsplat=1`) が次の tick で
   `getGsplatAsset` 経由で取得し `set_gsplat_asset` で WASM に流し込む

Phase 1 (shipped) — RunPod endpoint は **synthetic 1024-splat ring stub**。
GPU 不要。BPMN + dumper + B2 + RW + browser fetch + WGSL render の経路を
「実 GPU 課金なしで」end-to-end 確認できる。

Phase 2 (shipped 2026-05-09) — `_run_train_real` に Mapillary→COLMAP→gsplat→PLY
の実装を投入。3 つの単純化:

1. SH degree = 0 (DC band only) — preview 品質には十分、PLY 軽量、収束速い
2. No densification — COLMAP sparse cloud (10k-50k pts) を init として使い、
   そのまま train。strategy なし (operator が後で `DefaultStrategy` 追加可能)
3. Opacity-cull at half-step (logit > -3.0、σ ≈ 0.05) + final 50k 上限

Bring-up: `Dockerfile.phase2` (`runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04`
+ apt `colmap` + `requirements-phase2.txt`) で build、L40S 48 GiB endpoint に attach、
`RUNPOD_PHASE=2` template env を設定。1 scene ≈ 10-20 min / $0.40-$0.80。
詳細手順は `runpod-endpoint-gsplat/README.md` §Phase 2。

## D6b. Splat → Mesh Bake Pipeline (shipped 2026-05-10)

splat → mesh bake は同じ RunPod endpoint を `mode: "bake"` で再利用する。
endpoint の Phase 2 image (`Dockerfile.phase2`) には Open3D + trimesh +
torch + gsplat が同梱されているため、別 endpoint 不要。

Pipeline:

1. `cmdBakeGsplatAsset` XRPC が message-start BPMN
   (`bakeGsplatAsset.bpmn`) を publish (correlationKey=tileH3)
2. `bulk-ingest-gsplat-train` k8s pod の `_run_bake` が:
   a. `vertex_maps_gsplat_asset` から最新 splat 行を解決 (tile_h3 / vertex_id)
   b. B2 から PLY をダウンロード
   c. RunPod `/run` に `{mode:"bake", plyBase64, targetTriangles}` を POST
   d. `/status` をポーリング、`COMPLETED` で `glbBase64` を取得
   e. B2 に `maps-bulk-ingest/gsplat-mesh/{tile_h3}-{bake_job_id}.glb` で保存
   f. `vertex_maps_gsplat_mesh` + `edge_maps_gsplat_baked_to` を 1 行ずつ INSERT
3. browser 側の prefetch loop が `getGsplatAsset` の `bakedMeshUrl` を拾い、
   `set_mesh_tile(tileH3, glb)` で kami-app-maps3d の **既存 mesh tile pipeline**
   に流し込む — runtime delivery は静的 mesh のまま (260416 design 維持)

RunPod handler bake mode の中身 (gsplat preview asset → static mesh):

- 24 viewpoints をシーン中心の fibonacci sphere 上に生成、各 view を
  `gsplat.rasterization(render_mode="RGB+D")` で RGB + depth 取得
- depth は `alpha > 0.5` でマスク (低 coverage pixel を fusion に持ち込まない)
- Open3D `ScalableTSDFVolume(voxel_length=radius/256, sdf_trunc=4·voxel)` に
  `integrate(rgbd, intrinsic, extrinsic)` を回す
- `extract_triangle_mesh()` → `simplify_quadric_decimation(target=5000)`
- trimesh `export(file_type="glb")` で binary GLB 化、base64 で返す

Phase 1 (CPU) bake stub は splat PLY の bbox からハンドロール 8-vertex / 12-tri
GLB を吐く (依存ゼロ、~860 B)。BPMN + dumper + B2 + RW + browser path を実
mesh extraction なしで end-to-end 確認できる。

## D16. Train idempotency via image-set hash (shipped 2026-05-10)

### 設計

D10 の content-addressing は **output** の dedupe (PLY/GLB のバイト列が
同一なら B2 にも同じキーで上書きされる)。今回 D16 は **input** の
dedupe を加える: Mapillary imageIds set がハッシュ的に変わって
いなければ COLMAP + gsplat 自体を回さない。combined で full
idempotent.

`mv_maps_gsplat_job_latest` に `imageids_hash` 列を追加 (Alembic
`r_20260510150000_*`)。dumper は Mapillary list 結果から
`sha256(",".join(sorted(image_ids)))` を計算し、

```sql
SELECT job_id FROM mv_maps_gsplat_job_latest
WHERE tile_h3 = ? AND job_kind = 'train'
  AND status = 'completed' AND imageids_hash = ?
ORDER BY ts DESC LIMIT 1
```

の hit があれば即 return:

```python
_emit_job_state(
    status='completed',
    phase='skipped-duplicate',
    message=f'reused job_id={dup_job_id}',
    runtime_ms=elapsed_ms,
    cost_usd=0.0,
    imageids_hash=ids_hash,
)
```

auto-chain は早期 return path でも走らせるので、既存 splat 行に
対して bake が新規発火する (mesh が無いケースでは新規 bake、
mesh が既にあるケースでは bake 側の B2 dedupe + content addressing
で実質 0 コスト)。

### 不変条件

- ハッシュは sort 済 imageIds 上での SHA-256 → image set の重複
  順番不変、加減で値が変わる
- Mapillary が新画像を撮影 → imageId が増減 → ハッシュ変化 →
  通常の RunPod 経路を走る
- Operator が `force: true` を送れば cap gate と同じく override
  可能 ─ ただし dedupe は cap と違って "skip するだけで害はない"
  ので force パラメータは worker 側にのみ影響、dumper 側はハッシュ
  比較 only

### 帯域 + 課金影響

| 操作 | 旧挙動 | D16 |
|---|---|---|
| 同 tile 5 分後の再 train | 全パス: $0.50 / call | dedupe hit: $0 |
| Mapillary refresh で 1 画像追加 | 全パス | 全パス (期待動作) |
| 操作ミスで連打 (10 click) | $5 | $0.50 (1 回目だけ実行、残り skip) |

### Bring-up

```bash
# Schema
cd 30-graph/graph-schema
source scripts/load-database-url.sh && pnpm db:migrate
source scripts/load-database-url.sh && pnpm db:gen
source scripts/load-database-url.sh && pnpm db:drift

# Dumper roll
cd 60-apps/etzhayyim-project-maps/bulk-ingest
./deploy.sh build && ./deploy.sh apply
kubectl -n maps-bulk-ingest rollout restart deploy/bulk-ingest-gsplat-train

# Verify
# Click 「📷 Train splat here」twice on the same tile (no Mapillary refresh between).
# First click: train normally (cost ~$0.50, train job emits status=completed phase=completed).
# Second click within minutes: dedupe hit — train job emits status=completed phase=skipped-duplicate
# cost_usd=0.0 message="reused job_id=gsplattrain-..."
```

## D15. Per-tile spend cap + failure webhook (shipped 2026-05-10)

### Per-tile lifetime spend cap

D14 で `vertex_maps_gsplat_job.cost_usd` を永続化したので、per-tile
の累積支払額を SUM で引けるようになった。1 tile が train/bake を
延々と再走するような事故 (例: BPMN の retry loop / cache invalidation
バグ / 操作ミスでの連打) で 1 tile が $50+ を消費する経路を遮断する。

`cmdTrainGsplatFromMapillary` + `cmdBakeGsplatAsset` は publish 前に
`SELECT SUM(cost_usd) FROM vertex_maps_gsplat_job WHERE tile_h3 = ?
AND status = 'completed' AND cost_usd IS NOT NULL` を引き、
`MAPS_GSPLAT_LIFETIME_CAP_USD` (default $10) 以上ならば refuse する:

```json
{
  "error": "train refused: tile lifetime spend cap exceeded (pass force:true to override)",
  "tileH3": "8c2a1072b59ffff",
  "lifetimeSpendUsd": 10.42,
  "capUsd": 10.0
}
```

operator override = `force: true` (両 lexicon に追記済)。env 値は worker
の `_mapsEnv` binding 経由で読み取り、cluster-wide で一括変更可能。

### Failure webhook

dumper の `_run_train` / `_run_bake` 例外 handler は、
`_emit_job_state(status='failed')` の直後に
`_post_failure_webhook(kind, tile_h3, job_id, message)` を呼ぶ。
`GSPLAT_FAILURE_WEBHOOK_URL` env が空なら no-op。設定されていれば
Slack + Discord 互換の `{text: "..."}` 最小 payload を POST する:

```
:rotating_light: gsplat *train* failed — `gsplattrain-1747...` tile=`8c2a1072b59ffff`
```COLMAP found no valid reconstruction```
```

webhook 失敗そのもの (timeout / 4xx) は ≤ 4s tail で握り潰す ─ 元の
job failure は既に RW + log に記録済みなので、webhook の再試行で
本流を遅らせる必要はない。

### Bring-up (差分のみ)

```bash
# Worker re-deploy (per-tile cap + cap response fields)
cd 60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6
etzhayyim deploy

# Dumper re-roll (failure webhook + same parse)
cd ../../bulk-ingest && ./deploy.sh build && ./deploy.sh apply

# Operator: set webhook URL secret (Slack incoming or Discord)
kubectl -n maps-bulk-ingest patch secret maps-bulk-ingest-credentials --type merge \
  -p '{"stringData":{"GSPLAT_FAILURE_WEBHOOK_URL":"https://hooks.slack.com/services/..."}}'

# Optional: tune the per-tile cap (default $10 in worker code)
wrangler secret put MAPS_GSPLAT_LIFETIME_CAP_USD --env=production
# (or in maps-ui wrangler.jsonc env binding)
kubectl -n maps-bulk-ingest rollout restart deploy/bulk-ingest-gsplat-train

# Verify cap
curl -X POST https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.trainGsplatFromMapillary \
  -H 'content-type: application/json' \
  -d '{"lat":35.6812,"lng":139.7671}'
# After spending $10+ on the same tile:
# → {"error":"train refused: tile lifetime spend cap exceeded ...","capUsd":10.0,"lifetimeSpendUsd":10.42,...}
# Override:
# -d '{"lat":35.6812,"lng":139.7671,"force":true}'
```

## D14. Per-job cost rollup (shipped 2026-05-10)

D8 で handler が `stats.estimatedCostUsd = runtime_ms × RUNPOD_COST_USD_PER_SEC`
を return するようになっていたが、これまで永続化していなかった。
Operator が「先月いくら gsplat に使った？」を答えられるよう、
`vertex_maps_gsplat_job` に `cost_usd double precision` 列を追加し、
dumper が RunPod response から抽出して INSERT 時に書き込む。
job-time に固定するので、後から `RUNPOD_COST_USD_PER_SEC` env が
変わっても historical rollup は不変。

### Schema (Alembic `r_20260510140000_alter_gsplat_job_cost_usd`)

```sql
ALTER TABLE vertex_maps_gsplat_job ADD COLUMN IF NOT EXISTS cost_usd double precision;

DROP MATERIALIZED VIEW IF EXISTS mv_maps_gsplat_job_latest;
CREATE MATERIALIZED VIEW mv_maps_gsplat_job_latest AS
  SELECT DISTINCT ON (job_id)
    job_id, job_kind, tile_h3, status, phase, message,
    splat_count, triangle_count, byte_size, runtime_ms, cost_usd, ts
  FROM vertex_maps_gsplat_job
  WHERE ts > to_char(now() - INTERVAL '7 days', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')
  ORDER BY job_id, ts DESC;
```

Kotoba/Datomic は MV body を ALTER できないので DROP+CREATE。idempotent。

### XRPC

`com.etzhayyim.apps.maps.getGsplatCostSummary` (query, no params) が 3 つの
時間バケット {today UTC / last 7 days / last 30 days} それぞれで
`job_kind` 別に SUM(cost_usd) を返す。Worker handler は 3 並列クエリ
(`Promise.all`) で answer する。

### UI

`?jobs=1` の HUD パネル先頭に `$0.42 today · $3.20 7d · $14.80 30d`
ライン (緑色 today を強調) を追加、30s 間隔で reflesh。`refreshJobsHud`
内から fire-and-forget で並列に呼ぶので polling 1 ラウンドあたり
+1 リクエスト increment。

### 帳簿モデル

完了時のみ書き込まれるので、`status='completed'` AND `cost_usd IS NOT NULL`
で SUM すれば実支払額の lower bound が出る (`failed`/`skipped-low-psnr`
は ¥0 ではないが GPU 課金は実発生しているので、operator が必要なら
`status IN ('completed','failed')` の二段ロールアップを別 view で作れば
よい — 本 PR ではシンプルに completed のみ)。

```bash
# Bring-up
cd 30-graph/graph-schema
source scripts/load-database-url.sh && pnpm db:migrate    # alembic forward to r_20260510140000
source scripts/load-database-url.sh && pnpm db:gen        # regenerate database.ts
source scripts/load-database-url.sh && pnpm db:drift      # confirm zero drift

# Worker
cd 60-apps/etzhayyim-project-maps/appview/maps-ui-uqpel6i6
etzhayyim deploy   # picks up cmdGetGsplatCostSummary

# Dumper
cd ../../bulk-ingest
./deploy.sh build && ./deploy.sh apply
kubectl -n maps-bulk-ingest rollout restart deploy/bulk-ingest-gsplat-train

# Verify
curl https://maps.etzhayyim.com/xrpc/com.etzhayyim.apps.maps.getGsplatCostSummary | jq
# → {"today":{"totalUsd":0.42,"count":1,"byKind":[{"kind":"train","totalUsd":0.42,"count":1}]},...}
```

## D13. GPU-side LOD + parallel prefetch + cache rewrite (shipped 2026-05-10)

### GPU-side LOD (sh_degree=0 forced past 50 m)

D11/D12 の streaming-LOD は bandwidth と CPU sort 負荷を距離で削るが、
fragment shader 側の SH band-1..3 evaluation はそのまま走っていた。
degree=3 cloud で 1 splat あたり ~16 px 占有 × 30 ops/fragment ≈ 500
ops/splat 相当の specular 計算が遠 tile でも続く。

`kami_pipelines::GsplatAdapter::prepare` で sort 直後に
`sort_scratch.last()` から最近接 splat の距離² を取り、
`> FAR_SH_THRESHOLD_M² = 2500` なら uniform 内 sh_degree を 0 に上書き
する。WGSL `evaluate_sh` の `if u.sh_degree < 1u { return ... }` で
即 return するので追加コードなし。view-dependent specular は 50 m を
過ぎると視差が ~0.1° に縮んで人間に区別不能なので品質劣化は事実上ない。

### Cache-Control rewrite tool

D12 以前にアップロード済みの blob は `Cache-Control` ヘッダなし。
`bulk-ingest/tools/rewrite_gsplat_cache_control.py` を 1 回走らせれば
`copy_object(MetadataDirective="REPLACE", CacheControl=immutable)`
で既存 blob 全件を上書きできる。idempotent (`already up-to-date`
で skip) なので何度回しても安全。

```bash
cd 60-apps/etzhayyim-project-maps/bulk-ingest
source ~/.etzhayyim/maps.env  # B2_*
python3 tools/rewrite_gsplat_cache_control.py
# → list_objects_v2 paginate
# → copy_object self-loop with header rewrite
# → updates ~thousands of blobs at B2 default rate
```

### Parallel 1-ring prefetch (HTTP/2 multiplex)

D11/D12 までの prefetch は `for (const tile of cells) { await ... }`
で 7 tile を直列 fetch していた → 7×RTT。`Promise.all(cells.map(
async (tile) => { try { ... } catch {} }))` に置換、HTTP/2
multiplex で 1×RTT に短縮。HTTP/1.1 origin あたり 6 並列制限が
あっても 7 tile は許容範囲 (1 件キューでわずかに伸びる程度)。

per-tile try/catch で 1 件失敗が batch 全体を reject するのを防ぐ
(共有 Set/Map mutation は JS single-thread なので race なし)。

### 帯域 + 体感影響まとめ (degree=3 100k splat scene)

| 操作 | D11 (fraction-LOD のみ) | D12+D13 |
|---|---|---|
| 1-ring 初回 fetch latency | 7×RTT 直列 | 1×RTT 並列 |
| 1-ring bandwidth (centre 12m) | 168 MB | 28 MB (cap-bound) |
| 同 tile 再 entry | 168 MB | **0 B** (immutable cache) |
| Far tile fragment cost | 30 ops/fragment × N | 0 (sh_degree=0) |

## D12. LOD byte budget + immutable cache (shipped 2026-05-10)

### Per-tier byte budget cap

D11 の fraction-only LOD は degree=0 (~56 B/splat、3 MB / 100k tile)
には十分だが、degree=3 (236 B/splat、~24 MB / 100k tile) では far
tier でも数 MB を fetch してしまう。`MAX_BYTES_PER_LOD` を fraction
の上に重ねて hard cap する:

| LOD | bytes cap |
|---|---|
| 1.0 | 4 MB |
| 0.5 | 2 MB |
| 0.25 | 1 MB |
| 0.10 | 512 KB |

`lodEffectiveBytes(lod, total) = max(8 KiB, min(total × lod, cap))`。
8 KiB の下限は header + 数十 splat を保証するため (degree=3 でも
header 360 B + 30 splats × 236 B ≈ 7.4 KiB なので余裕)。

検証 (browser smoke):

| Total | LOD | Eff bytes | Cap-bound |
|---|---|---|---|
| 3.1 MB (degree=0) | 1.0 | 3072 KB | no (fraction wins) |
| 3.1 MB | 0.5 | 1536 KB | no |
| 3.1 MB | 0.25 | 768 KB | no |
| 3.1 MB | 0.10 | 307 KB | no |
| 25.2 MB (degree=3) | 1.0 | 4096 KB | **yes** (16 % of total) |
| 25.2 MB | 0.5 | 2048 KB | yes |
| 25.2 MB | 0.25 | 1024 KB | yes |
| 25.2 MB | 0.10 | 512 KB | yes (~2 % of total) |

### B2 immutable cache headers

Content-addressed upload (D10) は SHA-256 key で identity 不変なので
`Cache-Control: public, max-age=86400, immutable` を `put_object` に
付与する (`_b2_upload(cache_control=...)`)。browser HTTP cache が
full body / Range slice 双方をキャッシュ、tile 再入時の splat / mesh
fetch は **0 B over the wire** で済む (`200 OK from disk cache` /
`(disk cache)` の DevTools 表示)。

dedupe (D10) と組み合わせると:

| 操作 | B2 PUT | B2 GET | wire bandwidth |
|---|---|---|---|
| 初回 train | 1 | 0 | upload only |
| 同 tile 再 train (same input) | 0 (head 304) | 0 (no fetch) | 0 |
| Player 再 enter (cache valid) | 0 | 0 | 0 |
| Player 再 enter (cache evicted) | 0 | 1 | re-download |

`max-age=86400` は 1 日、`immutable` は再 validation skip を browser に
許可する。invalidation が必要なら content rewrite (key 変更) で十分
─ SHA-256 key が変わるので。

## D11. Streaming-LOD splats via Range fetch (shipped 2026-05-10)

### 設計

splat の per-tile bandwidth + GPU 負荷を距離に応じて段階的に減らす。
追加スキーマ・追加 blob・追加 trainer pass なし。3 つの観察を組み合わせる:

1. **Dumper sort**: `_run_train_real` は最終 cap 後、splat tensor を
   `argsort(opacities, descending=True)` で並び替えてから `_write_ply`
   する。on-disk PLY は body の頭から「最高 opacity 順」になる。
2. **PLY loader truncation**: `kami_render::splat_loader::load_ply`
   は `for v in 0..vertex_count { if base + stride > body.len() break }`
   で部分 body を許容する (regression test
   `load_ply_binary_tolerates_truncated_body` で固定)。header が
   N=1000 と宣言していても、body に 295 splat 分しか無ければ
   295 splat の cloud が返る。
2 つを組み合わせると、HTTP `Range: bytes=0-<targetBytes>` で先頭の
M バイトだけ取得すれば、最高 opacity 順の上位 ⌊M/stride⌋ splat を
取得したのと同等になる ─ **品質 LOD が free で得られる**。

### 4-tier ladder (browser)

| 距離 | LOD | bytes | 期待 splat |
|---|---|---|---|
| < 15 m | 1.0 | full | 100% |
| 15-30 m | 0.5 | first 50% | top-50% by opacity |
| 30-60 m | 0.25 | first 25% | top-25% |
| > 60 m | 0.10 | first 10% | top-10% |

各 prefetch tick で `cellToLatLng(tileH3)` → `lngLatToWorld` → 距離
計算 → `lodForDistance` で目標 LOD 決定 → 現在の LOD と比較して
upgrade が必要なら range-fetch して `set_gsplat_asset(tile, buf)`
で置換 (replace-by-name)。downgrade は不要 (近づいたら fetch する
だけ、遠ざかったら現状を維持しても OK)。

### 検証

local browser smoke で 1000-splat PLY を 3 段階 truncation:

| Truncation | Bytes | Loaded splat |
|---|---|---|
| 100% | 56 360 B | 1 000 |
| 30% | 16 908 B | **295** (header 360 B + 295×56 B = 16 880 B) |
| 10% | 5 636 B | **94** |

count は header 取り回し含めて期待値と一致。

### 帯域影響 (推定)

7-tile 1-ring (centre + 6 ring) で player が tile centre から
平均 6 m 離れた状態:

| シーン | 全 LOD=1.0 | mixed (centre=1.0, ring=0.5) |
|---|---|---|
| 50k splat / tile (~2.8 MB / tile) | 19.6 MB | 11.2 MB (-43%) |
| 100k splat / tile (~5.6 MB) | 39.2 MB | 22.4 MB (-43%) |

player が edge に立つと ring の半分は >30 m → LOD=0.25 に落ち、
さらに半減する。LOD のお蔭で同じ GPU memory 予算で **broader 1-ring
or finer H3** に踏み込める余地が生まれる。

## D10. Ops hardening (mesh evict + content addressing + bake gate, shipped 2026-05-10)

### Mesh tile auto-evict (closes GPU memory leak)

D9 の auto-evict は splat path のみ `remove_gsplat_asset` を呼んでおり、
mesh path は negative-cache 削除のみで GPU 上の wgpu vertex/index buffer
を残していた。今回 `remove_mesh_tile(tileH3)` を `kami-app-maps3d` の
既存 wasm-bindgen export 経由で呼ぶように変更、長時間プレイ時のメモリ
単調増加を完全に閉じた。`__maps3d_clearGsplatCache()` も両方を呼ぶ。

### Content-addressed B2 keys (cost dedupe)

dumper の splat / mesh upload を `{prefix}/{ab}/{sha256_hex}.{ext}`
形式に変更。`_b2_head` で既存 blob を確認し、ヒットなら upload を
skip する。同一 input (Mapillary 画像セットが変わらない再 train、同一
splat の再 bake) は B2 storage cost を 0 で済ませる。root CLAUDE.md
"Content-Addressed Blob Storage" 規定 (PDS uploadBlob path と整合) に
従う。`vertex_maps_gsplat_asset.b2_key` / `vertex_maps_gsplat_mesh.b2_key`
は forward-only に変更 (新規行のみ content-addressed、旧行は tile-keyed
のまま)、`cmdGetGsplatAsset` は b2_key を URL 化するだけなので無変更。

### Bake gate consistency

dumper の auto-chain は `evalPsnr < AUTO_BAKE_MIN_PSNR (18 dB)` で
skip + `phase=skipped-low-psnr` job state を残す。今回 manual bake
(`cmdBakeGsplatAsset`) もこの gate に従うようにした:
`mv_maps_gsplat_job_latest` で当該 tile の最新 train が
`skipped-low-psnr` ならば `BAKE_HARD_MIN_PSNR (12 dB)` 違反とみなして
refuse する。`force: true` でオペレータ override 可能 (lexicon に
追記済)。bake compute は実 GPU 課金なので、ノイズ出力に予算を使わない。

## D9. Cap bump + jobs HUD + auto-evict (shipped 2026-05-10)

### `MAX_SPLATS_PER_CLOUD` 50k → 100k

`sort_unstable_by` 上 100k pair (= 800 KB scratch) で M-series CPU
は ~10 ms。1 frame = 16.6 ms 内 record() に 6 ms を残す。`run_with_*`
adapter が複数の cloud を持つときは scratch がそれぞれ独立なので
ワーカー間の同期コストはない。GPU bitonic 化は 200k+ シーンが現れ
たら別 ADR で。pipeline / 訓練側の `_MAX_SPLATS_OUT` も同期。

### Jobs HUD overlay

`?jobs=1` で右上の小パネルが立ち上がり、30s 間隔で
`listGsplatJobs?limit=10` を polling。各行: tileH3 末尾 6 文字、kind
icon (📷/🔨)、status の色チップ (running=青/completed=緑/failed=赤)、
phase テキスト、相対時刻 (`12s` / `4m` / `2h`)。デフォルト off ─
production traffic に追加リクエストを乗せない。

### Auto-evict (1-ring 外の splat / mesh を撤去)

`gsplatLoaded` / `gsplatMeshLoaded` Set が今 GPU に乗っている tile
を追跡。各 prefetch tick で player の現在 H3 res-12 1-ring と差分を
取り、外れた tile に `remove_gsplat_asset(tileH3)` を呼んで GPU
メモリを開放、negative-cache も削除して再入時に再取得できるように
する。mesh は WASM 側に "remove" API が無いため negative-cache の
削除のみ ─ 再 bake で上書きされる経路に依存。長時間プレイで GPU
メモリが単調増加するのを防ぐ。

## D8. Higher-SH preview + cost telemetry + PSNR gate (shipped 2026-05-10)

### View-dependent specular preview (`f_rest_*`)

`runpod-endpoint-gsplat` は `exportRest=true` 指定時 SH band 1..3 係数を
PLY の `f_rest_*` プロパティとして書き出すが、これまで browser 側
renderer は DC band のみ評価していた。今回 `kami_render::splat` +
`splat_loader` + `kami_pipelines::GsplatAdapter` を拡張:

| 部品 | 変更 |
|---|---|
| `kami_render::splat::SplatCloud` | `sh_degree: u8` + `sh_rest: Vec<[f32; 3]>` (coefficient-major, per-splat (K-1) RGB triples for K=(degree+1)²) を追加 |
| `kami_render::splat_loader::load_ply` | `f_rest_*` プロパティを検出 (count → degree 推論)、PLY の channel-major レイアウトを coefficient-major に並べ替えて格納 |
| `kami_pipelines::GsplatAdapter` | bind group に `sh_rest_buf` (binding=3) を追加、`GsplatUniform` に `sh_degree` + `sh_rest_stride` を追加、WGSL に Inria coefficients + `evaluate_sh` 関数 (band 1..3) を追加。view direction = (camera - splat_centre).normalize()。DC-only path は bit-exact 不変 |

unit test 11/11 (含 `load_ply_binary_with_f_rest_degree_1` 新規) green。
local browser smoke で synthetic deg-1 PLY を inject、wall of splats
が view direction に応じて bright→dark gradient で表示されることを
WebGPU 上で確認。SH_C0 二重適用 bug を修正 (PLY の `f_dc_*` は
既に `(rgb-0.5)` 形式で格納されているので WGSL では再乗算しない、
band 1..3 のみ Inria coefficient × view-dir 寄与を加算)。

### Cost telemetry

`handler.py::_attach_cost` が `runtimeMs × RUNPOD_COST_USD_PER_SEC`
(L40S spot default `$0.00060/s`、env で override) を計算して
`stats.estimatedCostUsd` + `stats.costRateUsdPerSec` で返す。dumper は
job-state 行に書き込み、`listGsplatJobs` でそのまま query 可能。
SQLMesh 月次 rollup は SUM(stats.estimatedCostUsd) over
`vertex_maps_gsplat_job` で 1 view。

### PSNR auto-bake gate

dumper `_run_train` は train 完了後、`stats.evalPsnr <
AUTO_BAKE_MIN_PSNR` (default 18 dB) なら auto-chain を skip し
`phase=skipped-low-psnr` の job-state 行を emit する。COLMAP が
弱い + Mapillary シーケンスが疎なシーンで生成される低品質 splat が
そのまま bake → mesh まで進んで運用負荷を増やすのを防ぐ。operator
が後から手動で bake を triggerすることは可能。

## D7. Job-state observability + auto-chain (shipped 2026-05-10)

オペレータ向け可視化と train→bake 自動連鎖を追加。

### Job-state log

`vertex_maps_gsplat_job` (append-only) + `mv_maps_gsplat_job_latest`
(streaming MV、`DISTINCT ON (job_id)`、7 日 window) で train / bake 各
ジョブの phase 遷移を記録する。dumper pod が `_run_train` / `_run_bake`
の各 phase 移行で 1 行 INSERT する。MV は `(job_id)` で一意なので
`getGsplatJobStatus` は sub-ms。

### Auto-chain train → bake

dumper pod は train INSERT 完了後、即座に自身の `/trigger/bake` を
self-target POST する (デフォルト)。`autoBake: false` で無効化可能。
Zeebe を経由しないので、Zeebe BPMN engine が起動していない開発環境でも
single-pod だけで splat + mesh の両方が生成される。

production 経路 (UI 「🔨 Bake mesh here」 ボタン) は `cmdBakeGsplatAsset`
→ Zeebe `publishMessage` → BPMN `bakeGsplatAsset.bpmn` →
`/trigger/bake` で同じ dumper エンドポイントに到達する。両経路は冪等
(record-log re-INSERT で実質 upsert)。

### Quality metrics

train handler は registered images の 10% (max 8) を hold-out、訓練
完了時に rasterization で eval L1 + PSNR を計算し `stats.evalL1` /
`stats.evalPsnr` / `stats.registeredRatio` で返す。低 PSNR / 低
register-rate のシーンは bake してもメッシュ品質が悪いので、operator
は閾値で自動破棄する判断ができる (cron で `listGsplatJobs` を漁る)。

### XRPC surface

| NSID | Type | 用途 |
|---|---|---|
| `com.etzhayyim.apps.maps.getGsplatJobStatus` | query | `mv_maps_gsplat_job_latest` から jobId 一発 |
| `com.etzhayyim.apps.maps.listGsplatJobs` | query | tile / kind / status filter + pagination |

UI は train / bake ボタン押下後、返ってきた `jobId` を 5 秒間隔で
polling してトーストに `phase · 経過秒数` を表示、terminal status
で `splat_count` / `triangle_count` を表示して停止する。

## D6c. Bake Pipeline — legacy (mesh-only path, original 260416 design)

`bulk-ingest/workers/gsplat_bake_dumper.py` (新規, follow-up PR で実装) が
`bakeGsplatAsset` 起動 message を pull し、

1. B2 から PLY を取得
2. `nerfstudio` / `2dgs` / `gaussian-splatting-mesh` 系で mesh extract
3. Open3D quadric_decimation で簡略化
4. KTX2/BasisU テクスチャ書き戻し
5. `mesh_tile` (`vertex_spatial.Building` + B2 GLB) に upsert
6. `edge_maps_gsplat_baked_to` で lineage を残す

このパイプラインは本 ADR では契約のみ定義し、実装は別 PR で行う
(本 PR は preview path + persistence + lexicon + SDK + 起動 XRPC の
scaffold まで)。

# Rationale

| 設計 | 理由 |
|---|---|
| Runtime mesh 維持 | Switch / 低帯域 client での budget を 260416 で確認済 |
| renderer は preview のみ | 3DGS の sort cost と SH evaluation cost が city-scale で破綻するため。preview なら ≤50k splats / tile で CPU sort で十分 |
| kami-pipelines に SSoT | `40-engine/kami-engine/CLAUDE.md` の ownership 規定どおり (shared adapter は kami-pipelines、per-game は kami-app-{game}) |
| PLY/.splat 既存ローダ再利用 | `kami-render::splat_loader` 完成品の上に乗せる方が η 100%。新 crate 不要 |
| RW T2 直接書込 | ADR-0036 統一規則。社内 commit log や PDS firehose に splat blob meta を載せない (ADR-0036 §domain) |
| Bake は L8 pod | CF Worker 30s 制約で mesh extraction は不可能。BPMN start message → k8s pod (ADR-2604251830 L7→L8) |

# Exceptions

- `kami-render::splat_pipeline` (既存 experimental) は本 ADR の範囲外。
  GPU sort + tile-based culling + LOD streaming を後日扱う場合は新規 ADR で。
- 3DGS を VR / WebXR で本番運用したい future work は本 ADR を supersede する別 ADR で扱う。

# References

- `90-docs/platform/260416-maps-kami-street-asset-pipeline-design.md` (runtime mesh policy 維持)
- `40-engine/kami-engine/ARCHITECTURE.md` (ownership matrix)
- ADR-0036 (Worker-direct Hyperdrive Persistence)
- ADR-0095 (Simplified 3-Layer Identity + RW Vault)
- ADR-2604241342 (graph migration 4-failure pattern check)
- ADR-2604251830 (Shannon-Optimal 8-Layer Architecture, L7/L8 split)
