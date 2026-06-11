# BDD統合テスト実行ガイド

## 概要

BDDテストを統合テストとして実行し、実際のAPI/データベース接続を使用してカバレッジを測定します。

## 前提条件

1. DockerとDocker Composeがインストールされていること
2. 必要なポートが利用可能であること（5432, 8083）

## セットアップ手順

### 1. バックエンドサービスの起動

```bash
# セットアップスクリプトを実行（推奨）
pnpm test:bdd:integration:setup

# または手動で起動
docker-compose up -d postgres connect-go
```

### 2. 環境変数の設定

`.env.local`ファイルを作成して、以下の環境変数を設定してください：

```bash
# Database
DATABASE_URL=postgresql://placeholder:placeholder@localhost:5432/placeholder # placeholder

# Connect API
CONNECT_API_URL=http://localhost:8083
NEXT_PUBLIC_CONNECT_API_URL=/api/connect

# GraphQL API
GRAPHQL_API_URL=http://localhost:8082/graphql
NEXT_PUBLIC_GRAPHQL_API_URL=http://localhost:8082/graphql

# App URL
NEXT_PUBLIC_APP_URL=http://localhost:3000

# OpenAI API (テスト用)
OPENAI_API_KEY=test-api-key-for-coverage
```

### 3. データベースのマイグレーションとシード

```bash
# マイグレーション
pnpm db:migrate

# マスターデータの投入
pnpm seed:master-data
```

## 統合テストの実行

### 基本的な実行方法

```bash
# 統合テストを実行（セットアップ + テスト）
pnpm test:bdd:integration

# または、個別に実行
pnpm test:bdd:integration:setup  # セットアップのみ
pnpm test:bdd:coverage           # テスト実行
```

### カバレッジ付きで実行

```bash
# すべてのBDDテストをカバレッジ付きで実行
pnpm test:bdd:coverage:all

# カバレッジレポートを確認
pnpm test:bdd:coverage:report

# Capability to BDDカバレッジを評価
pnpm check:bdd-coverage
```

## 自動セットアップ

`features/support/integration-setup.ts`が自動的に以下を実行します：

1. 環境変数のデフォルト設定
2. Docker Composeサービスの起動確認
3. サービスのヘルスチェック
4. サービスが起動するまでの待機

## トラブルシューティング

### サービスが起動しない場合

```bash
# Docker Composeサービスの状態を確認
docker-compose ps

# ログを確認
docker-compose logs postgres
docker-compose logs connect-go

# サービスを再起動
docker-compose restart postgres connect-go
```

### ポートが既に使用されている場合

```bash
# ポートの使用状況を確認
lsof -i :5432  # PostgreSQL
lsof -i :8083  # Connect-Go

# 既存のサービスを停止
docker-compose down
```

### データベース接続エラー

```bash
# データベースが起動しているか確認
docker-compose exec postgres pg_isready -U postgres

# データベースを再作成
docker-compose down -v
docker-compose up -d postgres
pnpm db:migrate
pnpm seed:master-data
```

## 注意事項

- 統合テストは実際のデータベースを使用するため、テストデータが作成される可能性があります
- テスト実行後は、必要に応じてデータベースをクリーンアップしてください
- `STOP_SERVICES_AFTER_TEST=true`を設定すると、テスト後にサービスが自動停止します
