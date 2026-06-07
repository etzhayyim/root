# etzhayyim-project-gyotaku

`etzhayyim-project-gyotaku` は、`etzhayyim-project-www-crawler` と連携して Web ページを時系列で保存・表示するアーカイブプロジェクトです。

## 目的

- crawler の結果を継続的に収集し、URL ごとに時系列スナップショットを保存
- Wayback Machine 風に、過去時点のページ内容を参照・比較できる基盤を提供
- Common Crawl の CDX/Range 取得を使って過去アーカイブを取り込む
- crawler 取得時は kotodama WIT 側の `text_content` を優先して保存し、本文の参照はテキスト魚拓として提供

## 実装方針

- App component として `wasm/gyotaku-mcp-component` を運用
- スナップショットは `kotodama WIT` の `gyotaku_snapshots` Arrow table へ保存
- MCP tools + REST endpoint で保存・検索・表示を提供
- `/archive/view/{id}` はテキスト本文のみ返却（本文未取得時は 404）

## 表示の方針

- `gyotaku` では HTML 再生成は行わず、`TextContent`（および同一 URL/Result を紐づけられる場合の kotodama WIT `text_content`）を優先して表示
- `capture_from_crawler` の既定は本文再取得を行わず、クローラ保存データの kotodama WIT 本文を使う

## CDN で公開する手順

1. CDN 側の WADM で `CDN_PULUMI_SITES` に `gyotaku` を含める（`cdn.wadm.yaml` と `cdn-test.wadm.yaml` 反映済み）
2. `gyotaku` 側の Gateway 公開ルート（`PROJECT.jsonld`）に `gyotaku.etzhayyim.com` の `/xrpc` を追加済み
3. 既存デプロイ済み環境では `cdn.import_sites` を叩いて KV レジストリを更新
   - `tools/call` の `subdomains` を省略すると設定 `CDN_PULUMI_SITES` から `gyotaku` を読込
4. 以降、`https://gyotaku.etzhayyim.com/xrpc` から XRPC 経由で `get_snapshot / archive` 系 API を利用
