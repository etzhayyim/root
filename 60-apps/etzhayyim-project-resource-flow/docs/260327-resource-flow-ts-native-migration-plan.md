# 260327 Resource Flow TS Native Pilot

対象: `60-apps/etzhayyim-project-resource-flow/wasm/etzhayyim-wasm-resource-flow-r3s0fl0w`

## Scope

- `src/app.ts` と `src/worker.ts` を追加して TS Native スキャフォールドを置く。
- コマンド: `resource-flow.list`, `resource-flow.detail`
- `/_heartbeat` を実装し、`fetch` の既存ルートは `sdk.handleRequest`。
- `build.mjs` を追加して esbuild バンドルを有効化。

## 実装内容（Pilot）

- `resource-flow.list`: `country` と `limit` を受けて `cypherQueryJson` をプレースホルダ実行し、`ResourceFlow` 一覧を返却。
- `resource-flow.detail`: `id` 指定で明細を取得。
- `runHeartbeat`: 最小の heartbeat action を返却。

## 次アクション

1. Digest/sankey/lineage/anomaly の既存 WIT オペレーションへ順次接続。
2. `ResourceFlow` クエリと schema を運用実データに合わせて置換。
