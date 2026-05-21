# `umu` Godot Web/Wasm 設計メモ

## 目的

Godot のゲームを `ops.gftd.ai` の基準（`gftd:platform/gftd-mcp@0.1.0`）で扱える
WIT 前提に寄せ、単一の wasm コンポーネントで配信できる構成を目指す。

## ルート方針

- まず Godot export（Web）を `static/play/<slug>/` に集約し、WASM 側で静的配信する。
- 受け入れたゲームデータは `project.godot` と運用メタを `games/` 配下で管理する（ゲーム名 / slug / エントリ / 起点 URL）。
- ここでの WIT 方針は `gftd:platform/gftd-mcp@0.1.0` を取り込み、将来 `ops.gftd.ai` 系のワークフロー API を
  追加実装しやすい状態を保つことです。
- 既存の `gftd:platform/gftd-mcp@0.1.0` を起点に、将来 `ops.gftd.ai` 固有インターフェースへ拡張する前提を残す。

## 必須ディレクトリ

- `wasm/umu-godot-hub/static/play/<game-slug>/`
- `games/<game-slug>/project.godot`
- `games/<game-slug>/gftd-discovery.yaml`

## 取り込みフロー

1. Godot 側で `Web (HTML5)` エクスポート
2. `wasm/umu-godot-hub/static/play/<game-slug>/` へコピー
3. `wasm/umu-godot-hub/static/index.html` のメニュー更新（任意）
4. `mage Deploy` 実行（`WADM_MANIFEST=.../umu-godot-hub.wadm.yaml`）

## 参考

- `60-apps/ai-gftd-project-games` の既存ルート（`k8s/http-routes.yaml` / `magatama.toml` / `wadm`) を合わせる
- wasm deploy standards の名前空間/ルールに準拠
