# Docker Compose 開発環境

## 概要

このdocker-compose.ymlは開発環境用の設定です。以下のサービスが含まれます：

- **PostgreSQL**: データベース
- **GraphQL**: Rust GraphQLサービス
- **GraphQL Code Generator**: 型自動生成（watchモード）
- **Web**: Next.jsアプリケーション

## セットアップ

### 1. 環境変数の設定

`.env`ファイルを作成：

```bash
DATABASE_URL=postgresql://postgres:placeholder@postgres:5432/scap  # placeholder EXAMPLE
NVD_API_KEY=your-nvd-api-key
OVAL_API_URL=https://oval.mitre.org
```

### 2. サービス起動

```bash
docker-compose up
```

これにより以下が自動的に実行されます：

1. PostgreSQLが起動
2. Rust GraphQLサービスが起動（ポート8080）
3. GraphQL Code GeneratorがGraphQLサービスの準備を待機
4. GraphQLスキーマから型を自動生成
5. 型生成完了後、watchモードで継続監視
6. Next.jsアプリケーションが起動（ポート3000）

### 3. 型生成の確認

型は`ports/services/graphql/generated/types.ts`に生成されます。

GraphQLスキーマが変更されると、自動的に型が再生成されます。

## 個別サービス起動

### GraphQLサービスのみ

```bash
docker-compose up graphql
```

### 型生成のみ（再実行）

```bash
docker-compose exec graphql-codegen pnpm graphql:codegen:docker
```

### Next.jsアプリケーションのみ

```bash
docker-compose up web
```

## ローカル開発（Docker外）

Docker外で開発する場合：

1. PostgreSQLとGraphQLサービスを起動：
   ```bash
   docker-compose up postgres graphql
   ```

2. 型を生成：
   ```bash
   pnpm graphql:codegen
   ```

3. Next.jsアプリケーションを起動：
   ```bash
   pnpm dev
   ```

## トラブルシューティング

### GraphQLサービスが起動しない

```bash
# ログを確認
docker-compose logs graphql

# サービスを再ビルド
docker-compose build graphql
docker-compose up graphql
```

### 型生成が失敗する

```bash
# GraphQLサービスが起動しているか確認
curl http://localhost:8080/health

# 型生成を手動実行
docker-compose exec graphql-codegen pnpm graphql:codegen:docker
```

### ポートが既に使用されている

`docker-compose.yml`のポート番号を変更：

```yaml
ports:
  - "3001:3000"  # Next.js
  - "8081:8080"  # GraphQL
  - "5433:5432"  # PostgreSQL
```

## データベースマイグレーション

```bash
# マイグレーション実行（Rust GraphQLサービス経由）
docker-compose exec graphql diesel migration run
```

