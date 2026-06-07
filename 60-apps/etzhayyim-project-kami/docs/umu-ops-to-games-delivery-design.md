# UMU -> OPS(WIT import) -> GAMES 配信設計

## 目的

`etzhayyim-project-umu` で `ops.etzhayyim.com` 系 WIT（現行は `etzhayyim:platform/etzhayyim-mcp@0.1.0`）を基準に、
以下の一連フローを標準化する。

1. UMU でプロジェクト作成
2. ゲーム開発（Godot Web Export）
3. `etzhayyim-project-games` へ配信

## スコープ

- `umu.etzhayyim.com`: 企画/作成/開発のハブ
- `ops.etzhayyim.com`: MCP/WIT 契約でのオーケストレーション境界
- `games.etzhayyim.com` (`etzhayyim-project-games`): 公開配信面

## 依存ルール

- WADM `Application` namespace は `kotodama-runtime`（`default` 禁止）
- App system 資源は `kotodama-system`
- HTTPRoute は `etzhayyim-performers-org-org_34dKrNTTK3cNixZzHIzzFwLw1s4`
- 画像 push は `ghcr.io/etzhayyim/*`
- deploy は `mage Deploy` を利用

## WIT 契約設計

UMU 側 world は現行どおり `etzhayyim:platform/etzhayyim-mcp@0.1.0` を include し、
OPS 連携は次の logical contract として扱う（段階導入）。

- `project-lifecycle`:
  - `create-project(input) -> project-id`
  - `set-project-status(project-id, status)`
- `game-build`:
  - `register-export(project-id, artifact-manifest)`
  - `validate-export(project-id) -> report`
- `game-delivery`:
  - `publish-to-games(project-id, target-channel) -> release-id`
  - `get-release-status(release-id) -> status`

実体は当面 `etzhayyim:platform/etzhayyim-mcp@0.1.0` 経由で MCP ツール呼び出しにマップし、
将来 `etzhayyim:ops/*` パッケージへ切り出す。

## E2E フロー設計

### 1) Project 作成（UMU）

- 入口: `umu.etzhayyim.com` の project 作成 UI/API
- UMU が生成する最小情報:
  - `project_id` (`umu-<nanoid>`)
  - `game_slug`
  - `title`
  - `owner`
  - `visibility`
- 永続化:
  - `games/<slug>/etzhayyim-discovery.yaml`（運用メタ）
  - `wasi:keyvalue/store`（編集中の状態、進行状態）
- 状態遷移:
  - `draft` -> `in-development`

### 2) ゲーム開発（UMU）

- Godot で `Web (HTML5)` export
- 出力配置（UMU 内）:
  - `wasm/umu-godot-hub/static/play/<slug>/`
  - `games/<slug>/project.godot`
- 検証:
  - `<slug>.html/.js/.wasm/.pck` の存在
  - エントリ URL `/play/<slug>/` が解決可能
- 状態遷移:
  - `in-development` -> `ready-for-release`

### 3) 配信準備（OPS 経由）

- UMU -> OPS（WIT import 経由）で publish 要求
- OPS が実行する責務:
  - 配信対象ディレクトリ生成
  - カタログメタ更新（タイトル、カテゴリ、タグ、年齢属性）
  - リリースID採番
- 生成アーティファクト（設計上の標準）:
  - `release-manifest.json`
  - `asset-checksums.txt`
  - `delivery-report.json`

### 4) `etzhayyim-project-games` への配信

- 配信先（標準）:
  - ゲーム資産: `60-apps/etzhayyim-project-games/games/etzhayyim-games/games/<slug>/`
  - 静的配信資産: `60-apps/etzhayyim-project-games/wasm/games-7m8oocsn/static/games/<slug>/`
  - カタログ登録: `PROJECT.jsonld`（または同等メタ管理）
- 配信後:
  - `WADM_MANIFEST=60-apps/etzhayyim-project-games/wasm/games-7m8oocsn/wadm/games-static.wadm.yaml mage Deploy`
  - `kubectl get mga -n kotodama-runtime` と `/_app/version.json` の疎通確認
- 状態遷移:
  - `ready-for-release` -> `published`

## 失敗時ハンドリング

- publish 失敗時は `release-failed` へ遷移し、再実行可能にする
- 失敗理由は `delivery-report.json` と keyvalue に保存
- 部分成功（資産コピー済み/カタログ未更新）は `rollback-required` を返す

## 最小実装ステップ

1. UMU: project state モデル（`draft` から `published`）を keyvalue で確立
2. UMU: `etzhayyim-discovery.yaml` 生成を project 作成時に自動化
3. OPS 連携: `publish-to-games` 相当の MCP 呼び出しを追加
4. GAMES: `<slug>` 配下の資産配置とカタログ更新を自動化
5. Deploy: `mage Deploy` + ヘルスチェックを CI に固定

## 境界の要点

- UMU は「制作」と「配信要求」までを担当
- OPS は「配信オーケストレーション」を担当
- GAMES は「公開面」と「公開用カタログ」を担当

この分割で `ops.etzhayyim.com` 側 WIT を拡張しても UMU/GAMES の責務を崩さずに運用できる。
