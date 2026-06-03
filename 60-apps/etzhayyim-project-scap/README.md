# scap.etzhayyim.com

*Automatically synced with your [v0.dev](https://v0.dev) deployments*

[![Deployed on Vercel](https://img.shields.io/badge/Deployed%20on-Vercel-black?style=for-the-badge&logo=vercel)](https://vercel.com/etzhayyim/v0-scap-etzhayyim-ai)
[![Built with v0](https://img.shields.io/badge/Built%20with-v0.dev-black?style=for-the-badge)](https://v0.dev/chat/projects/fGPxHejv5ww)

## Overview

This repository will stay in sync with your deployed chats on [v0.dev](https://v0.dev).
Any changes you make to your deployed app will be automatically pushed to this repository from [v0.dev](https://v0.dev).

## Deployment

Your project is live at:

**[https://vercel.com/etzhayyim/v0-scap-etzhayyim-ai](https://vercel.com/etzhayyim/v0-scap-etzhayyim-ai)**

## Build your app

Continue building your app on:

**[https://v0.dev/chat/projects/fGPxHejv5ww](https://v0.dev/chat/projects/fGPxHejv5ww)**

## How It Works

1. Create and modify your project using [v0.dev](https://v0.dev)
2. Deploy your chats from the v0 interface
3. Changes are automatically pushed to this repository
4. Vercel deploys the latest version from this repository

## SCAP (Security Content Automation Protocol) コンプライアンススキャンプラットフォーム

## 概要

このプロジェクトは、Workflow DevKit、Crawlee、Diesel ORM (Rust GraphQL)を使用してSCAPデータを収集・処理し、セキュリティコンプライアンスを自動化するプラットフォームです。

## 主要機能

- **SCAP データ取得**: NIST、MITRE等の外部ソースからSCAPデータを自動収集
- **Workflow DevKit**: 耐久性のあるワークフローによるSCAPデータ処理
- **Crawlee**: Web scrapingによるSCAPコンテンツ収集
- **Diesel ORM (Rust GraphQL) + Supabase**: PostgreSQLデータベースへの保存（Rust GraphQLサービス経由）
- **Supabase Realtime**: リアルタイムメッセージングとイベント配信
- **GraphQL**: 型安全なAPIサービスによる統合
- **コンプライアンススキャン**: AWS、GitHub等の統合されたセキュリティスキャン

## アーキテクチャ

\`\`\`
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SCAP Sources  │    │ Workflow DevKit │    │ Rust GraphQL    │
│  (NIST, MITRE)  │───▶│    Workflows    │───▶│ Diesel + Supabase│
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │ Crawlee Scrapers│    │ SCAP Scan Service│
                    └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                    ┌─────────────────┐    ┌─────────────────┐
                    │Supabase Realtime│    │  GraphQL Service │
                    │  (Messaging)    │    │   (API Layer)    │
                    └─────────────────┘    └─────────────────┘
\`\`\`

## セットアップ

### 前提条件

- Node.js 18+
- pnpm
- Supabase アカウント（またはローカルPostgreSQL）

### 環境変数設定

\`\`\`bash
# Supabase Database設定
DATABASE_URL=postgresql://postgres:[password]@[host]:[port]/[database]  # placeholder EXAMPLE

# Supabase API設定
SUPABASE_URL=https://[project-id].supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key  # サーバーサイド用（オプション）

# NVD API設定（オプション - より高いレート制限のため）
NVD_API_KEY=your-nvd-api-key

\`\`\`

### インストール

\`\`\`bash
# 依存関係のインストール
pnpm install

# データベースマイグレーション（Rust GraphQLサービス経由）
cd performers/services/graphql
diesel migration run

# 開発サーバー起動
pnpm dev
\`\`\`

### データベース設定

このプロジェクトは **Diesel ORM (Rust GraphQL)** と **Supabase PostgreSQL** を使用しています。

#### Supabase設定手順

1. [Supabase](https://supabase.com)でアカウントを作成
2. 新しいプロジェクトを作成
3. 接続文字列とAPIキーを取得（`.env.local`に設定）
   - Database Settings → Connection String（PostgreSQL）
   - API Settings → Project API keys（anon key と service_role key）
4. マイグレーションを実行：

\`\`\`bash
# Rust GraphQLサービスでマイグレーションを実行
cd performers/services/graphql
diesel migration run

# Rust GraphQLサービスを起動
cargo run
\`\`\`

#### データベーススキーマ

以下のテーブルが作成されます：

- `scap_contents` - SCAPコンテンツ
- `cve_data` - CVE（脆弱性）データ
- `oval_definitions` - OVAL定義
- `scap_scan_results` - スキャン結果
- `integrations` - インテグレーション設定
- `scap_data_sources` - データソース設定

## Workflow DevKitの使用方法

### 1. Workflowの起動

\`\`\`bash
# GraphQL経由でWorkflowを起動
# 例: SCAPデータ収集ワークフロー
curl -X POST http://localhost:8080/api/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "mutation { triggerProcess(processKey: \"scap-data-collection\") { success message } }"}'
\`\`\`

### 2. Workflowの機能

**NVDデータ収集ワークフロー (`nvdCollectionWorkflow`)**
- NIST NVDからCVEデータを取得
- データベースに直接保存
- 自動retryとobservability

**OVALデータ収集ワークフロー (`ovalCollectionWorkflow`)**
- MITRE OVAL定義を取得
- データベースに直接保存

**統合データ収集ワークフロー (`integratedCollectionWorkflow`)**
- 複数のデータソースから一括収集
- エラーハンドリングと統計情報

**スケジュール実行ワークフロー (`scheduledCollectionWorkflow`)**
- `sleep()`ディレクティブによる定期実行
- リソース消費なしの待機

## 開発

### プロジェクト構造

\`\`\`
scap.etzhayyim.com/
├── app/                    # Next.js ルーティング（ports/ui/ から再エクスポート）
├── capabilities/          # 能力定義（RDF/OWL/SKOS/SHACL）
├── activities/            # 活動定義
├── performers/            # 実行主体
│   ├── systems/          # システム（UI Portを提供）
│   ├── services/         # サービス（UI Portを提供しない）
│   │   ├── graphql/     # GraphQL service (Rust)
│   │   ├── workflow-engine/  # Workflow Engine実装
│   │   ├── scap-data-service/  # SCAP データサービス実装
│   │   └── scap-scan-service/  # SCAP スキャンサービス実装
│   ├── actors/          # アクター（必要に応じて）
│   └── organizations/   # 組織（必要に応じて）
├── resources/            # リソース
│   ├── schemas/         # スキーマ（既存）
│   └── adapters/        # アダプター
│       ├── supabase/    # Supabase アダプター
│       └── data.ts      # データアダプター
├── ports/               # ポート
│   ├── ui/              # Human Port（UI Port）
│   │   ├── dashboard/  # ダッシュボードUI
│   │   ├── search/      # 検索UI
│   │   ├── admin/       # 管理UI
│   │   └── components/  # UI コンポーネント
│   └── services/        # Service Port
│       ├── graphql-client.ts  # GraphQL クライアント契約
│       └── graphql/     # GraphQL設定と生成型
└── ports/types/         # ポート型定義
    ├── types.ts         # 型定義
    ├── projection.ts    # データ投影
    └── utils.ts         # ユーティリティ
\`\`\`

### 主要サービス

**SCAPDataService**
- 外部SCAPソースからのデータ取得
- 定期更新のスケジューリング
- データベースへの直接保存

**SCAPScanService**
- セキュリティスキャンの実行
- コンプライアンス評価
- 脆弱性検出と報告

**Workflow DevKit Workflows**
- 耐久性のあるワークフロー実行
- 自動retryと状態永続化
- Observability（トレース、ログ、メトリクス）

**Crawlee Scrapers**
- OpenSCAPコンテンツのWeb scraping
- DISA STIGコンテンツのWeb scraping
- ブロッキング回避とプロキシローテーション

## 監視とメトリクス

\`\`\`bash
# Workflowステータス確認
curl http://localhost:3000/rpc/scap.getWorkerStatus

# データベースの確認
pnpm db:studio
\`\`\`

## トラブルシューティング

### よくある問題

1. **データベース接続エラー**
   \`\`\`bash
   # DATABASE_URLを確認
   echo $DATABASE_URL
   \`\`\`

2. **Workflow実行エラー**
   \`\`\`bash
   # Workflow DevKitのログを確認
   # トレースとメトリクスは自動的にキャプチャされます
   \`\`\`

3. **メモリ不足エラー**
   \`\`\`bash
   # Node.jsメモリ制限を増加
   export NODE_OPTIONS="--max-old-space-size=4096"
   \`\`\`

## ライセンス

MIT License

## 貢献

1. フォークしてブランチを作成
2. 変更をコミット
3. プルリクエストを作成

---

**注意**: 本番環境で使用する前に、適切なセキュリティ設定とパフォーマンステストを実施してください。
