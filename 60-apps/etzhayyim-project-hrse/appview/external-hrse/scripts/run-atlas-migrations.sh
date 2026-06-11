#!/bin/bash
set -e

# SKIP_MIGRATIONS環境変数が設定されている場合はスキップ
if [ "$SKIP_MIGRATIONS" = "true" ]; then
  echo "Skipping migrations (SKIP_MIGRATIONS=true)"
  exit 0
fi

# Atlas CLIのインストール（Vercel環境）
if ! command -v atlas &> /dev/null; then
  echo "Installing Atlas CLI..."
  curl -sSf https://atlasgo.sh | sh
  export PATH="$HOME/.atlas:$PATH"
fi

# DATABASE_URLが設定されているか確認
if [ -z "$DATABASE_URL" ]; then
  echo "Warning: DATABASE_URL is not set. Skipping migrations."
  exit 0
fi

# マイグレーションディレクトリの確認
if [ ! -d "migrations" ]; then
  echo "Warning: migrations directory not found. Skipping migrations."
  exit 0
fi

# マイグレーションファイルの存在確認
if [ ! -f "migrations/atlas.sum" ]; then
  echo "Warning: migrations/atlas.sum not found. Skipping migrations."
  exit 0
fi

# マイグレーションの実行（atlas migrate applyは既に適用済みをスキップする）
echo "Running Atlas migrations (will skip already applied migrations)..."
atlas migrate apply --env vercel || {
  echo "Warning: Migration failed, but continuing build..."
  exit 0
}

echo "Migrations check completed."
