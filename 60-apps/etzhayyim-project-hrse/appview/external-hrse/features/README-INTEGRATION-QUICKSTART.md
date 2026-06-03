# BDD統合テスト クイックスタート

## 実行手順

### 1. バックエンドサービスの起動

```bash
# セットアップスクリプトを実行（推奨）
pnpm test:bdd:integration:setup

# または手動で起動
docker-compose up -d postgres connect-go

# サービスが起動するまで待機（約30秒）
sleep 30
```

### 2. 統合テストの実行

```bash
# 統合テストを実行（セットアップ + テスト）
pnpm test:bdd:integration

# または、カバレッジ付きで実行
pnpm test:bdd:coverage
```

### 3. カバレッジレポートの確認

```bash
# カバレッジレポートを生成
pnpm test:bdd:coverage:report

# Capability to BDDカバレッジを評価
pnpm check:bdd-coverage

# HTMLレポートを開く
open coverage/index.html
```

## 環境変数の自動設定

`features/support/integration-setup.ts`が自動的に以下の環境変数を設定します：

- `DATABASE_URL`: `postgresql://placeholder:placeholder@localhost:5432/placeholder` (placeholder)
- `CONNECT_API_URL`: `http://localhost:8083`
- `GRAPHQL_API_URL`: `http://localhost:8082/graphql`
- `OPENAI_API_KEY`: `test-api-key-for-coverage` (テスト用)
- `NEXT_PUBLIC_APP_URL`: `http://localhost:3000`

## トラブルシューティング

### サービスが起動しない場合

```bash
# ログを確認
docker-compose logs postgres
docker-compose logs connect-go

# サービスを再起動
docker-compose restart postgres connect-go
```

### ポートが使用されている場合

```bash
# 既存のサービスを停止
docker-compose down

# 再度起動
docker-compose up -d postgres connect-go
```
