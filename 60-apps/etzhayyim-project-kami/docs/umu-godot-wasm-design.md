# `umu` Godot Web/Wasm 設計メモ

## 目的

Godot のゲームを `ops.etzhayyim.com` の基準（`etzhayyim:platform/etzhayyim-mcp@0.1.0`）で扱える
WIT 前提に寄せ、単一の wasm コンポーネントで配信できる構成を目指す。

## ルート方針

- まず Godot export（Web）を `static/play/<slug>/` に集約し、WASM 側で静的配信する。
- 受け入れたゲームデータは `project.godot` と運用メタを `games/` 配下で管理する（ゲーム名 / slug / エントリ / 起点 URL）。
- ここでの WIT 方針は `etzhayyim:platform/etzhayyim-mcp@0.1.0` を取り込み、将来 `ops.etzhayyim.com` 系のワークフロー API を
  追加実装しやすい状態を保つことです。
- 既存の `etzhayyim:platform/etzhayyim-mcp@0.1.0` を起点に、将来 `ops.etzhayyim.com` 固有インターフェースへ拡張する前提を残す。

## 必須ディレクトリ

- `wasm/umu-godot-hub/static/play/<game-slug>/`
- `games/<game-slug>/project.godot`
- `games/<game-slug>/etzhayyim-discovery.yaml`

## 取り込みフロー

1. Godot 側で `Web (HTML5)` エクスポート
2. `wasm/umu-godot-hub/static/play/<game-slug>/` へコピー
3. `wasm/umu-godot-hub/static/index.html` のメニュー更新（任意）
4. `mage Deploy` 実行（`WADM_MANIFEST=.../umu-godot-hub.wadm.yaml`）

## 参考

- `60-apps/etzhayyim-project-games` の既存ルート（`k8s/http-routes.yaml` / `kotodama.toml` / `wadm`) を合わせる
- wasm deploy standards の名前空間/ルールに準拠
