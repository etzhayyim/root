# Paketo Buildpacks + Scaffold (Temporal Operator) 設定ガイド

Storyboard EditorをPaketo BuildpacksとScaffold（Temporal Operator）を使用して構築・デプロイします。

## アーキテクチャ

- **Paketo Buildpacks**: Dockerfile不要のクラウドネイティブビルド
- **Scaffold (Temporal Operator)**: Kubernetes上でTemporalクラスターを管理
- **PostgreSQL**: Temporalの永続化ストレージ

## 前提条件

1. **Paketo CLI (pack)**
   ```bash
   # macOS
   brew install buildpacks/tap/pack
   
   # Linux/Windows
   # https://buildpacks.io/docs/tools/pack/
   ```

2. **Kubernetesクラスター** (OrbStack, minikube, kindなど)

3. **kubectl** がインストールされていること

## セットアップ

### 1. Scaffold (Temporal Operator) のインストール

```bash
cd 260123-jump/apps/260123-storyboard
chmod +x k8s/setup.sh
./k8s/setup.sh
```

このスクリプトは以下を実行します:
- ✅ cert-managerのインストール
- ✅ Scaffold Operatorのインストール
- ✅ PostgreSQLのデプロイ
- ✅ Temporalデータベースの初期化
- ✅ Temporal Clusterのデプロイ

### 2. Paketo Buildpacksでビルド

**重要**: Paketo Buildpacksは1つのターゲットしかサポートしていないため、serverとworkerを**別々のイメージ**としてビルドします。

```bash
cd backend

# 事前にprotoファイルを生成（bufが必要）
buf generate

# Serverイメージをビルド
pack build storyboard-editor/server \
  --builder paketobuildpacks/builder-jammy-base \
  --env BP_GO_TARGETS="./cmd/server"

# Workerイメージをビルド
pack build storyboard-editor/worker \
  --builder paketobuildpacks/builder-jammy-base \
  --env BP_GO_TARGETS="./cmd/worker"
```

**注意**: 
- Paketo Buildpacksのビルド環境には`buf`がインストールされていないため、事前に`buf generate`を実行してprotoファイルを生成する必要があります。
- または、生成されたprotoファイルをコミットしておくことを推奨します。
- Skaffoldを使用する場合、`project-server.toml`と`project-worker.toml`が自動的に`project.toml`としてコピーされます。

### 3. Skaffoldでデプロイ

```bash
# 開発モード（Paketo Buildpacks使用）
skaffold dev --profile dev
```

## Paketo Buildpacks設定

### `backend/project-server.toml` / `backend/project-worker.toml`

Paketo Buildpacksの設定ファイル。serverとworkerで別々の設定ファイルを使用します:

**project-server.toml**:
```toml
[build]
  [[build.env]]
    name = "BP_GO_TARGETS"
    value = "./cmd/server"
```

**project-worker.toml**:
```toml
[build]
  [[build.env]]
    name = "BP_GO_TARGETS"
    value = "./cmd/worker"
```

**重要**: 
- `BP_GO_TARGETS`はパッケージパス（ディレクトリ）を指定する必要があります。`./cmd/server/main.go`ではなく`./cmd/server`を使用してください。
- Paketo Buildpacksは1つのターゲットしかサポートしていないため、複数のバイナリをビルドするには別々のイメージとしてビルドする必要があります。

### ビルドオプション

- **Builder**: `paketobuildpacks/builder-jammy-base` (Go対応)
- **Buildpacks**: 
  - `paketo-buildpacks/go-dist` - Goランタイム
  - `paketo-buildpacks/go-build` - Goビルド

## Scaffold (Temporal Operator) 設定

### `k8s/temporal-cluster.yaml`

TemporalClusterカスタムリソースでTemporalクラスターを定義:

- **Version**: 1.24.0
- **Services**: frontend, matching, history, worker
- **UI**: Temporal Web UI
- **Persistence**: PostgreSQL

### Temporalクラスターへの接続

アプリケーションからTemporalに接続するには:

```go
temporalClient, err := client.Dial(client.Options{
    HostPort: os.Getenv("TEMPORAL_ADDRESS"), // "storyboard-temporal-frontend.temporal-system.svc.cluster.local:7233"
})
```

## ポートフォワード

Skaffoldが自動的に以下をフォワードします:

- **Server**: `localhost:8081`
- **Frontend**: `localhost:1421`
- **Temporal UI**: `localhost:8080`
- **Temporal Frontend**: `localhost:7233`

**注意**: Workerはバックグラウンドで実行されるため、ポートフォワードは不要です。

## 手動でのアクセス

```bash
# Temporal UI
kubectl port-forward -n temporal-system svc/storyboard-temporal-ui 8080:8080

# Temporal Frontend (XRPC)
kubectl port-forward -n temporal-system svc/storyboard-temporal-frontend 7233:7233
```

## トラブルシューティング

### Paketo Buildpacksのビルドが失敗する

```bash
# ビルドログを確認
pack build storyboard-editor/backend --builder paketobuildpacks/builder-jammy-base --verbose

# ローカルでテスト
pack build storyboard-editor/backend --builder paketobuildpacks/builder-jammy-base --run-image paketobuildpacks/run-jammy-base
```

### Temporalクラスターが起動しない

```bash
# TemporalClusterリソースの状態を確認
kubectl get temporalcluster -n temporal-system

# Podの状態を確認
kubectl get pods -n temporal-system

# ログを確認
kubectl logs -n temporal-system -l app=temporal-frontend
```

### PostgreSQL接続エラー

```bash
# PostgreSQLの状態を確認
kubectl get pods -n storyboard-editor -l app=postgresql

# データベース接続をテスト
kubectl exec -n storyboard-editor -it $(kubectl get pod -n storyboard-editor -l app=postgresql -o jsonpath='{.items[0].metadata.name}') -- \
  psql -U postgres -c "SELECT 1;"
```

## メリット

### Paketo Buildpacks

1. **Dockerfile不要**: 自動的に最適なビルド方法を選択
2. **セキュリティ**: 定期的に更新されるベースイメージ
3. **マルチステージビルド**: 自動的に最適化されたレイヤー構造
4. **ビルドキャッシュ**: 効率的なインクリメンタルビルド

### Scaffold (Temporal Operator)

1. **宣言的設定**: YAMLでTemporalクラスターを定義
2. **自動管理**: Operatorがクラスターのライフサイクルを管理
3. **スケーリング**: レプリカ数の動的調整
4. **高可用性**: 複数のサービスインスタンスによる冗長化

## 参考リンク

- [Paketo Buildpacks](https://paketo.io/)
- [Scaffold (Temporal Operator)](https://github.com/temporalio/scaffold)
- [Temporal Documentation](https://docs.temporal.io/)
