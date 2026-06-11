# vertex_other Legacy Removal Plan (Kysely Schema First)

## Goal
- `vertex_other` / `mv_vertex_other_count` 依存を段階的に 0 にし、各 app を typed table + Kysely schema へ移行する。
- `@etzhayyim/kotodama-host-sdk` の `legacy-vertex-other` surface を最終的に削除する。

## Current Snapshot (2026-04-23)
- `pnpm -s lint:no-vertex-other`: pass (literal table name 直接参照は 0)
- ただし legacy helper / constant 経由の参照は残存。
- `rg -l "legacy-vertex-other|LEGACY_VERTEX_OTHER|legacyVertex" ...`: **37 files**

## Scope
- SDK: `40-engine/kotoba/crates/kotoba-kotodama/sdk/kotodama-host-sdk/src/legacy-vertex-other.ts` と re-export。
- App/API: `60-apps/*/src/app.ts` の fallback query (`LEGACY_VERTEX_OTHER_TABLE`)。
- Infra/Engine: `40-engine/*`, `50-infra/*` の legacy table fallback。

## Phased Plan

### Phase 0: Freeze (immediate)
- 新規コードで `legacy-vertex-other` import 禁止。
- 既存コードは「増やさない」状態を維持。
- Exit criteria:
  - CI で `legacy-vertex-other` import 数が増えない。

### Phase 1: Typed Schema Bootstrap (high-traffic apps first)
- 対象 app ごとに migration 追加: `vertex_<domain>` / 必要な `mv_*_count`。
- `30-graph/graph-schema/src/database-strict.ts` へ型を追加。
- app read path を typed table へ切替。
- 初期優先:
  1. `maps-ui-uqpel6i6`
  2. `shigotoba-jobs-component`
  3. `stripe-st4rp301`
  4. `intel-i7n73l0x`
- Exit criteria:
  - 上記 app で `LEGACY_VERTEX_OTHER_*` 参照 0。

### Phase 2: Infra/Engine Cutover
- `40-engine`, `50-infra` の fallback を typed route に統一。
- `resolveVertexTable("Other")` 経由の fallback を順次削除。
- Exit criteria:
  - infra/engine 側で `LEGACY_VERTEX_OTHER_TABLE` 参照 0。

### Phase 3: SDK Removal
- `legacy-vertex-other.ts` を削除。
- `index.ts` の re-export 削除。
- 依存 app の compile/lint 通過を確認。
- Exit criteria:
  - repo 全体で `legacy-vertex-other|LEGACY_VERTEX_OTHER|legacyVertex` 0 hit。
  - `pnpm -s lint:no-vertex-other` pass。

## Implementation Rules
- 各 app は「1 collection = 1 typed table」を原則にする。
- ad-hoc JSON scan (`props::jsonb ->>`) を新規導入しない。
- migration と app 切替を同一 PR に入れ、read/write 経路を分離しない。

## Next Action Queue
1. `maps-ui-uqpel6i6`: typed table migration + app read path cutover
2. `shigotoba-jobs-component`: `legacyVertexPropsByLabelQuery` 置換
3. `stripe-st4rp301`: card/cardholder/transaction typed tables へ切替
