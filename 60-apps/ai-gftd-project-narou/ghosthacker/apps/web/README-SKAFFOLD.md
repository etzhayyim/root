# Skaffold ローカル開発ガイド

Skaffoldを使用してKubernetes上でstoryboard-editorをローカル開発します。

## 前提条件

1. **Kubernetesクラスター** (OrbStack, minikube, kindなど)
2. **Skaffold** がインストールされていること
   ```bash
   # macOS
   brew install skaffold
   ```

## クイックスタート

### 開発モードで起動（ホットリロード有効）

```bash
cd 260123-jump/apps/260123-storyboard
skaffold dev --profile dev
```

これにより以下が自動的に実行されます:
- ✅ Dockerイメージのビルド
- ✅ Kubernetesへのデプロイ
- ✅ ポートフォワード（Backend: 8081, Frontend: 1421）
- ✅ ファイル変更の監視と自動リロード
- ✅ ログストリーミング

### アクセス

- **Frontend**: http://localhost:1421
- **Backend API**: http://localhost:8081

## コマンド

### 開発モード

```bash
# 開発モードで起動（ファイル変更を監視）
skaffold dev --profile dev

# 一度だけビルド＆デプロイ
skaffold run --profile dev
```

### ビルドのみ

```bash
# すべてのイメージをビルド
skaffold build --profile dev

# 特定のイメージのみビルド
skaffold build --profile dev --build-artifacts storyboard-editor/backend
```

### デプロイのみ

```bash
# 既存のイメージを使用してデプロイ
skaffold deploy --profile dev
```

### クリーンアップ

```bash
# すべてのリソースを削除
skaffold delete --profile dev
```

## ファイル同期

開発モードでは、以下のファイルが自動的にコンテナに同期されます:

**Backend:**
- `**/*.go` → `/app`
- `**/*.mod`, `**/*.sum` → `/app`

**Frontend:**
- `src/**/*.{ts,svelte,js,css}` → `/app/src`
- `package.json`, `vite.config.ts`, `svelte.config.js` → `/app`

## トラブルシューティング

### イメージが見つからない

```bash
# ローカルイメージを確認
docker images | grep storyboard-editor

# イメージを再ビルド
skaffold build --profile dev
```

### ポートが既に使用中

```bash
# ポート使用状況を確認
lsof -i :8081
lsof -i :1421

# 既存のプロセスを停止するか、skaffold.yamlのlocalPortを変更
```

### Kubernetesクラスターに接続できない

```bash
# クラスター情報を確認
kubectl cluster-info

# 名前空間を確認
kubectl get namespaces

# Podの状態を確認
kubectl get pods -n storyboard-editor

# ログを確認
kubectl logs -n storyboard-editor -l app=storyboard-backend
kubectl logs -n storyboard-editor -l app=storyboard-frontend
```

### ホットリロードが動作しない

開発モードでは、Backendは`air`を使用してホットリロードします。
Frontendは`vite`の開発サーバーを使用します。

```bash
# Backendのログを確認
kubectl logs -n storyboard-editor -l app=storyboard-backend -f

# Frontendのログを確認
kubectl logs -n storyboard-editor -l app=storyboard-frontend -f
```

## 環境変数

必要に応じて、`k8s/backend-deployment.yaml`に環境変数を追加できます:

```yaml
env:
  - name: WORKSPACE_ROOT
    value: "/workspace"
  - name: PORT
    value: "8081"
  - name: TEMPORAL_ADDRESS
    value: "temporal-frontend.temporal-system:7233"
```

## リソース制限

`k8s/backend-deployment.yaml`と`k8s/frontend-deployment.yaml`でリソース制限を調整できます:

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "100m"
  limits:
    memory: "256Mi"
    cpu: "500m"
```
