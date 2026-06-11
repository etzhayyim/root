# サイバーセキュリティ特化型フリーランスマッチングプラットフォーム

DESIGN.mdのOWL/SHACLベースのドメインモデルを基に実装された、サイバーセキュリティ特化型のフリーランスマッチングプラットフォームです。

## 技術スタック

- **フロントエンド**: Next.js 14.x (App Router) + React 18.x + Tailwind 3.x
- **API層**: Connect-RPC (Go + connectrpc.com/connect) + Protocol Buffers
- **データベース**: PostgreSQL + pgx (Go)
- **認証・サブスクリプション**: Clerk v6.x
- **バリデーション**: Zod v4.1.12
- **型システム**: TypeScript (strict mode)
- **Linter/Formatter**: Biome
- **テスト**: Vitest + React Testing Library
- **Webhook署名検証**: svix

## プロジェクト構造

```
src/
  app/                    # Next.js App Router
    freelancer/          # フリーランス向けUI
      profile/           # プロファイル作成/編集
      jobs/              # 案件検索・詳細
      proposals/         # 応募管理
    hire-manager/        # 企業担当向けUI
      jobs/              # 案件管理・応募評価
    admin/               # 管理画面
      master-data/       # マスターデータ管理
    api/
      webhooks/          # Clerk Webhook
  internal/              # Bounded Context
    zod/                 # Zod Schema定義（SHACL→Zod変換）
  components/            # React components
    JobWizard/          # 案件作成ウィザードコンポーネント
  lib/                   # ユーティリティ
    connect/             # Connect-Web クライアント
      client.ts          # Connect Transport設定
      hooks.ts           # React Hooks for Connect services
      server-client.ts   # サーバーサイド Connect クライアント
    clerk-subscription.ts  # Clerk Subscription管理
    db.ts                # PostgreSQL クライアント

performers/services/connect-go/  # Connect-Go API (Go)
  cmd/server/           # サーバーエントリーポイント
  internal/service/     # Connect サービス実装
    job_seeker.go       # JobSeekerService
    agency.go           # AgencyService
    job.go              # JobService
    ...
proto/                  # Protocol Buffers定義
  hrse/v1/             # サービス定義
    job_seeker.proto
    agency.proto
    job.proto
    ...
```

## セットアップ

### Docker Composeを使用したセットアップ（推奨）

```bash
# 環境変数を設定（.envファイルを作成）
cp .env.example .env
# .envファイルを編集して必要な値を設定

# すべてのサービスを起動
docker-compose up

# バックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 停止
docker-compose down
```

### ローカル開発環境

#### 1. データベースのセットアップ

```bash
# PostgreSQLを起動（Docker Composeを使用）
docker-compose up postgres -d

# または、ローカルのPostgreSQLを使用
export DATABASE_URL="postgresql://placeholder:placeholder@localhost:5432/placeholder" # placeholder
```

#### 2. Connect-Go サービスのセットアップ

```bash
# Protocol Buffers からコードを生成
pnpm codegen:proto

# Connect-Go サーバーを起動
cd performers/services/connect-go
go run cmd/server/main.go

# または、Docker Compose を使用
docker-compose up connect-go
```

#### 3. Next.jsフロントエンドのセットアップ

```bash
# 依存関係のインストール
pnpm install

# Protocol Buffers から型を生成
pnpm codegen:proto

# 開発サーバー起動
pnpm dev
```

## Docker Compose サービス

- **postgres**: PostgreSQL 16 データベース（ポート: 5432）
- **connect-go**: Connect-Go API サービス（ポート: 8083）
- **nextjs**: Next.js フロントエンド（ポート: 3000）
- **temporal**: Temporal Server（ポート: 7233）
- **temporal-ui**: Temporal Web UI（ポート: 8088）

## Connect-RPC API

Connect-RPC APIは `http://localhost:8083` で利用可能です。

### 主要なサービス

- **JobSeekerService**: 求職者プロファイル管理
  - `GetJobSeekerProfile`, `CreateJobSeekerProfile`, `UpdateJobSeekerProfile`, `SearchJobSeekers`
- **JobService**: 案件管理
  - `GetJob`, `ListJobs`, `CreateJob`, `UpdateJob`, `SearchJobs`
- **AgencyService**: 人材紹介会社管理
  - `GetAgency`, `CreateAgency`, `UpdateAgency`, `ListAgencies`
- **HiringService**: 採用プロセス管理
  - `CreateProposal`, `UpdateProposal`, `CreateContract`
- **MatchingService**: マッチング機能
  - `GetMatchScore`, `RecommendJobs`, `RecommendFreelancers`
- **MasterDataService**: マスターデータ取得
  - `ListCertifications`, `ListSpecializations`, `ListLanguages`, `ListNationalities`, `ListWorkPermits`

## 実装済み機能

### ✅ 認証・サブスクリプション
- Clerk v6.x による認証（サインイン・サインアップ）
- Clerk Subscription API実装（メタデータ機能を使用）
- Webhook によるサブスクリプション・支払いイベント処理
- 認証保護されたルート管理（middleware）

### ✅ フリーランス向け機能
- プロファイル管理（作成・編集）
- 案件検索・詳細表示
- 応募管理（作成・確認・撤回）

### ✅ 企業担当向け機能
- プロファイル管理
- 案件管理（作成・編集・一覧・詳細）
- 案件作成ウィザード（JobWizard）
- 応募評価・管理

### ✅ 管理機能
- マスターデータ管理ページ（`/admin/master-data`）
  - 資格（セキュリティ資格）のCRUD操作
  - 専門分野のCRUD操作
  - 言語のCRUD操作
  - 国籍のCRUD操作
  - 在留資格のCRUD操作
- 初期データ投入スクリプト（`pnpm seed:master-data`）
- 認証保護（認証済みユーザーのみアクセス可能）

### ✅ Connect-RPC API (Go)
- Protocol Buffers による型安全なAPI定義
- Connect-Go による XRPC/Connect プロトコル対応
- pgx による型安全なデータベースアクセス
- Clerk認証統合

## 開発コマンド

```bash
# データベース
# マイグレーションはSQLxを使用（Rust側で管理）
pnpm seed:master-data  # マスターデータ投入

# Protocol Buffers
pnpm codegen:proto       # Protocol Buffers から型を生成
pnpm codegen:proto:lint  # proto ファイルのリント

# 注意: proto ファイルを変更した場合は、必ず codegen:proto を実行してください

# Connect-Go サービス
cd performers/services/connect-go
go build ./cmd/server   # ビルド
go run ./cmd/server    # 実行
```

## 環境変数

`.env`ファイルを作成して以下の変数を設定してください：

```bash
# Database
DATABASE_URL=postgresql://placeholder:placeholder@localhost:5432/placeholder # placeholder

# Next.js
NEXT_PUBLIC_APP_URL=http://localhost:3000

# Connect-RPC API
NEXT_PUBLIC_CONNECT_API_URL=/api/connect
CONNECT_API_URL=http://localhost:8083

# Clerk Authentication
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
CLERK_SECRET_KEY=sk_test_...
```

## Protocol Buffers アプローチ

このプロジェクトは**Protocol Buffers**を使用した型安全なAPI通信を採用しています：

1. **API定義**: `proto/hrse/v1/*.proto` でサービスとメッセージを定義
2. **型生成**: `buf generate` でサーバー側（Go）とクライアント側（TypeScript）の型を自動生成
3. **実装**: Connect-Go でサーバー側を実装、Connect-Web でクライアント側から呼び出し

### ワークフロー

```bash
# 1. proto ファイルを編集
#    proto/hrse/v1/*.proto を編集

# 2. 型を再生成
pnpm codegen:proto

# 3. サーバー側の実装を追加・更新
#    performers/services/connect-go/internal/service/*.go を編集

# 4. クライアント側で使用
#    src/lib/connect/hooks.ts または src/lib/connect/server-client.ts を使用

# 4. 再度型を生成（クエリ/ミューテーションの型も更新される）
pnpm codegen
```

### 開発時の推奨事項

- **Protocol Buffers変更時**: `pnpm codegen:proto` を実行して型を最新化
- **ビルド前**: 必ず `pnpm codegen:proto` を実行して型を最新化
- **スキーマ変更時**: proto ファイルを変更したら、`pnpm codegen:proto` を実行してサーバー側とクライアント側の型を同期

## Connect-Web クライアントの使用方法

### クライアントサイド（Client Component）

```tsx
"use client";

import { useJobServiceClient } from "@/lib/connect/hooks";
import { create } from "@bufbuild/protobuf";
import { ListJobsRequestSchema } from "@/gen/proto/hrse/v1/job_pb";

export default function JobsPage() {
  const jobClient = useJobServiceClient();
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchJobs() {
      try {
        const request = create(ListJobsRequestSchema, {
          status: "open",
          limit: 10,
          offset: 0,
        });
        const response = await jobClient.listJobs(request);
        setJobs(response.jobs || []);
      } catch (error) {
        console.error("Failed to fetch jobs:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchJobs();
  }, [jobClient]);

  // ...
}
```

### サーバーサイド（Server Component / API Route）

```tsx
// Server Component または API Route
import { getJobServiceClient } from "@/lib/connect/server-client";
import { create } from "@bufbuild/protobuf";
import { ListJobsRequestSchema } from "@/gen/proto/hrse/v1/job_pb";

export default async function JobsPage() {
  const jobClient = await getJobServiceClient();

  const request = create(ListJobsRequestSchema, {
    status: "open",
    limit: 10,
    offset: 0,
  });

  const response = await jobClient.listJobs(request);

  return (
    <div>
      {response.jobs?.map((job) => (
        <div key={job.id}>{job.title}</div>
      ))}
    </div>
  );
}
```

**注意事項**:
- クライアントサイドでは `useJobServiceClient()` などの hooks を使用します
- サーバーサイドでは `getJobServiceClient()` などの関数を使用します
- サーバーサイドではClerkの`auth()`関数を使用してトークンを自動取得します
- Protocol Buffers の型安全性により、コンパイル時に型チェックが行われます

## 注意事項

- Connect-Go APIはGoで実装されており、Protocol Buffersを使用して型安全な通信を実現します
- proto ファイルを変更したら、`pnpm codegen:proto` を実行して型を再生成してください
- Docker Composeを使用する場合、Connect-Go サーバーが自動的に起動します
- マスターデータ投入スクリプト（`pnpm seed:master-data`）を実行するには、`DATABASE_URL`環境変数が設定されている必要があります
- 管理ページ（`/admin/master-data`）にアクセスするには、Clerkで認証済みである必要があります
- データベースマイグレーションは `pnpm db:migrate` で実行してください
- Clerk v6対応: クライアントサイドでは`useAuth`フックから`getToken`を取得し、サーバーサイドでは`auth()`関数を使用します

## プロジェクト構造の詳細

### マスターデータ
- **資格**: CISSP, CISA, CISM, CEH, GSEC, GCIH, GPEN, OSCP, SSCP, CCSP
- **専門分野**: PenTest, SOC, DevSecOps, IncidentResponse, ThreatIntelligence, VulnerabilityManagement, SecurityArchitecture, Compliance, IAM, CloudSecurity, NetworkSecurity, ApplicationSecurity
- **言語**: 日本語、英語、中国語、韓国語、スペイン語、フランス語、ドイツ語、ポルトガル語、ロシア語、アラビア語
- **国籍**: 30カ国（ISO 3166-1 alpha-2コード）
- **在留資格**: 日本の在留資格10種類

### データベーススキーマ
- 19テーブル（ユーザーアカウント、フリーランス、企業、案件、応募、契約、支払い、マスターデータ等）
- マイグレーション管理（SQLx）
