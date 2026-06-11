# etzhayyim-project-immutizer

`etzhayyim-project-immutizer` は、etzhayyim OS 向けの **クラウド連携型アンチウイルス設計** です。ローカル検査は `etzhayyim-project-os` 内の `etzhayyim-system` が担当し、`immutizer.etzhayyim.com` が脅威インテリジェンスで結果を補強します。

## 設計方針

- **ローカル優先**: まず端末内でスキャン（Quick/Full/Path）を実施。
- **クラウド補強**: ローカル結果を `immutizer.etzhayyim.com` に送信し、追加判定・既知脅威照合を行う。
- **フェイルセーフ**: クラウド障害時でもローカル結果は必ず返却。
- **Tauri 統合**: デスクトップ UI から `run_immutizer_scan` コマンドで一括実行。

## etzhayyim OS (Tauri) との統合点

統合済みコマンド:

- `run_immutizer_scan(scan)`
  - `scanType`: `quick` / `full` / `path`
  - `path`: `scanType=path` のとき必須

内部フロー:

1. Tauri Rust が MCP XRPC 経由で `etzhayyim-project-os` の scanner/blocking capability を呼び出し。
2. 必要に応じて Immutizer のクラウド判定 capability を XRPC で合成。
3. XRPC 連携が未構成の場合は `cloudError` に理由を返却。

## 環境変数

- `IMMUTIZER_BASE_URL`
  - デフォルト: `https://immutizer.etzhayyim.com`
  - ステージング切替時に上書き可能

## 返却モデル（概要）

- `project`: `etzhayyim-project-immutizer`
- `provider`: 実際に使用した Immutizer の URL
- `scanType`: 実行スキャン種別
- `protocol`: `mcp-grpc`
- `local`: ローカル結果（gRPC 実装時に返却）
- `cloud`: クラウド補強結果（gRPC 実装時に返却）
- `cloudError`: XRPC 未構成/障害メッセージ


## Capabilities カタログ

- **常駐型 anti virus (resident protection)**
  - バックグラウンド監視で不審ファイル・不審挙動を検知。
- **スキャン型 anti virus (on-demand scan)**
  - `quick` / `full` / `path` の明示実行。
- **クラウド補強 (cloud intelligence)**
  - `immutizer.etzhayyim.com` 側の既知脅威情報で判定を強化。
- **迷惑メールブロック (spam/phishing blocking)**
  - スパム・フィッシングの分類/遮断判定に利用可能な capability。

> Tauri では `get_immutizer_capabilities` で上記一覧を取得し、`run_immutizer_scan` で実行系処理を呼び出します。


## API ポリシー

- Immutizer 統合 API は **MCP XRPC のみ**を許可します。
- **REST/HTTP API 形式は禁止**です。
