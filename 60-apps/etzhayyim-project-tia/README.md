# Business Context: Internet Account Protection System
*GraphQL API (Rust) + Next.js Applications - Clean Architecture*


## 1. OVERVIEW

インターネットアカウント保護システムは、Facebook, LinkedIn, X(Twitter), LINE, Instagram などのソーシャルメディアプラットフォームにおけるアカウント乗っ取りやなりすましを検知・防止する分散型監視システムである。

## 2. BUSINESS DOMAIN

### Core Business Value
- **アカウント保護**: InternetAccountOwner が所有するインターネットアカウントのなりすまし検知
- **分散監視**: Seeker による協働的なアカウント監視ネットワーク
- **AI支援評価**: Gemini 2.5 Flash を用いた画像・プロフィール類似性評価
- **自動対応**: 検知結果に基づくプラットフォームへの自動連絡

### Key Business Rules
1. アカウント所有者は自らのアカウントのみ保護対象として登録可能
2. 検知はプラットフォーム毎の特徴（画像・プロフィール）を考慮
3. 類似性評価は 0-1 のスコアで定量的に表現
4. 報告は即時性と正確性を両立

## 3. ACTORS & RESPONSIBILITIES

### Primary Actors

#### InternetAccountOwner (アカウント所有者)
**責任**: システムのエンドユーザー。アカウントの保護を希望する個人/法人。
- authenticator を通じて認証・登録
- 自らが所有する internetaccounts を保護対象として登録
- reporter からの検知報告を受け取り対応

#### Seeker (検索者/監視参加者)
**責任**: アカウント監視ネットワークの参加者。分散型監視を実現。
- 保護対象アカウント一覧にアクセス
- アカウント名からプラットフォーム検索ページをクリック
- クリック操作により recorder を起動

#### Administrator (管理者)
**責任**: システム全体の運営・管理。
- authenticator を通じて認証制御
- システム設定・監視

### Secondary Actors

#### Authenticator (認証制御システム)
**責任**: 全アクターの認証を一元管理。
- InternetAccountOwner, Seeker, Administrator の認証
- セッション管理とアクセス制御

#### Recorder (記録システム)
**責任**: アカウントページの自動保存。
- Chrome拡張により開かれたページを自動記録
- MHTML形式でのページ保存
- プラットフォーム毎の特徴抽出

#### Detector (検知システム)
**責任**: 保存ページからの類似性評価。
- プラットフォーム毎の情報抽出（画像・プロフィール）
- Gemini 2.5 Flash による類似性評価
- 評価スコアの計算と閾値判定

#### Reporter (報告システム)
**責任**: 検知結果の所有者への通知。
- detector の評価結果を InternetAccountOwner に報告
- 通知チャネル管理（メール・アプリ内通知）

#### Platformer (プラットフォーム連絡窓口)
**責任**: 各プラットフォームへの公式連絡。
- Facebook, LinkedIn, X, LINE, Instagram への報告
- プラットフォーム毎の連絡API/手順の管理

## 4. BUSINESS PROCESSES

### Primary Process: Account Protection Flow

1. **Registration** (登録フェーズ)
   - InternetAccountOwner → GraphQL API で認証・登録
   - アカウント情報を保護対象としてデータベースに保存

2. **Monitoring** (監視フェーズ)
   - Seeker → GraphQL API で保護対象一覧取得
   - アカウント名検索 → プラットフォームページクリック
   - Recorder → ページ自動保存 (MHTML)

3. **Detection** (検知フェーズ)
   - GraphQL detectors API → 保存ページ解析
   - プラットフォーム特徴抽出 (画像・プロフィール)
   - Gemini 2.5 Flash → 類似性評価 (0-1スコア)

4. **Reporting** (報告フェーズ)
   - GraphQL reports API → InternetAccountOwner に通知
   - 評価スコアと証拠データの提示

5. **Response** (対応フェーズ)
   - InternetAccountOwner → GraphQL API で状況確認・対応判断
   - GraphQL platforms API → 必要に応じてプラットフォーム連絡

### Supporting Processes

- **Authentication Flow**: 全アクターの認証管理
- **Data Management**: アカウント・検知履歴の管理
- **Quality Assurance**: 検知精度の継続的改善

## 5. TECHNICAL INTEGRATION (GraphQL + Next.js Architecture)

### Architecture Overview

#### API Layer
- **GraphQL API (Rust)**: Rust + async-graphql + Actix Web による型安全なGraphQL API
- **Apollo Client**: Next.jsアプリケーションからのGraphQLクライアント

#### Application Layer
- **Seeker App**: 完全に独立したNext.jsアプリケーション
  - 内部パッケージ依存なし（`@etzhayyim-tia/components`、`@etzhayyim-tia/graphql-client`を統合）
  - Clerk認証を直接使用
  - Apollo Clientを統合
- **Admin App**: Next.jsアプリケーション（GraphQL + Apollo Client）
  - 内部パッケージ依存なし（`@etzhayyim-tia`パッケージを削除）
  - GraphQLクライアントとプロバイダーを実装
  - Apollo Clientを使用してRust GraphQL APIと通信
- **InternetAccountOwner App**: Next.jsアプリケーション（GraphQL + Apollo Client）
  - 内部パッケージ依存なし（`@etzhayyim-tia`パッケージを削除）
  - GraphQLクライアントとプロバイダーを実装
  - Apollo Clientを使用してRust GraphQL APIと通信

#### Domain Layer (N0: DOMAIN)
- **InternetAccount**: アカウントの型定義とビジネスルール
- **DetectionResult**: 検知結果の型と評価ロジック
- **SimilarityScore**: 類似性スコアの計算ルール

#### Schema Layer (N1: SCHEMA)
- **GraphQL Schema**: Rustで定義されたGraphQLスキーマ
- **AccountRegistrationInput**: アカウント登録の入力仕様
- **DetectionReport**: 検知報告の型定義
- **SimilarityEvaluation**: 類似性評価の型定義

#### Ports Layer (N2: PORTS)
- **AccountRepository**: アカウントCRUDの抽象（Rust実装）
- **DetectionService**: 検知処理の抽象
- **NotificationService**: 通知送信の抽象

#### Application Layer (N3: APP) - GraphQL Resolvers
- **RegisterAccount**: アカウント登録ユースケース (GraphQL mutation)
- **ProcessDetection**: 検知処理ユースケース (GraphQL mutation)
- **SendNotification**: 通知送信ユースケース (GraphQL mutation)

#### Infrastructure Layer (N6: INFRA-RES)
- **ChromeExtension**: Recorder の資源管理
- **GeminiClient**: AI評価サービスの資源管理
- **PlatformAPIs**: 各プラットフォームAPIの資源管理
- **PostgreSQL**: データベース（sqlx経由）

## 6. QUALITY ATTRIBUTES

### Functional Requirements
- **Accuracy**: 検知精度 > 95% (False Positive < 5%)
- **Timeliness**: 検知から報告まで < 30分
- **Scalability**: 同時監視アカウント数 10,000+

### Non-Functional Requirements
- **Reliability**: システム可用性 > 99.9%
- **Security**: アカウントデータ暗号化・アクセス制御
- **Performance**: 類似性評価 < 5秒/アカウント
- **Maintainability**: プラットフォーム追加対応 < 1週間

## 7. RISKS & MITIGATIONS

### Technical Risks
- **AI Accuracy**: Gemini APIの変動 → 継続的再学習と閾値チューニング
- **Platform Changes**: API変更 → Platformer の抽象化レイヤ
- **Scalability**: 高負荷 → 分散処理アーキテクチャ

### Business Risks
- **Adoption**: 参加者不足 → インセンティブ設計
- **False Positives**: 誤検知 → 所有者確認フロー
- **Platform Policies**: 連絡制限 → 公式チャネル確保

## 8. SUCCESS METRICS

- **Detection Rate**: 月間検知数 / 登録アカウント数
- **Response Time**: 検知から対応完了までの時間
- **User Satisfaction**: アカウント所有者の満足度調査
- **System Reliability**: MTTR (Mean Time To Recovery)

## 9. DEVELOPMENT SETUP

### Docker Compose

プロジェクトはDocker Composeを使用して開発環境を構築します。

#### サービス構成

- **postgres**: PostgreSQL データベース (ポート: 5432)
- **graphql**: Rust GraphQL API サーバー (ポート: 4000)
- **seeker**: Seeker Next.js アプリケーション (ポート: 25929)
  - 独立したアプリケーション（内部パッケージ依存なし）
- **admin**: Admin Next.js アプリケーション (ポート: 25930)
- **internetaccountowner**: Internet Account Owner Next.js アプリケーション (ポート: 25931)

#### GraphQLスキーマ生成

GraphQLスキーマ（SDL）とintrospection JSONはRust側で生成され、TypeScript側のcodegenで使用されます：

```bash
# ワークスペースルートから
make schema

# または直接実行
cd performers/services/graphql
cargo run --bin generate-schema

# 以下のファイルが生成されます:
# - performers/ports/graphql/schema.graphql (SDL)
# - performers/ports/graphql/introspection.json (TypeScript codegen用)
```

TypeScript側の型を生成（introspection JSONを使用）：

```bash
# スキーマ生成 + 型生成
make generate

# または個別に
cd performers/actors/internetaccountowner
pnpm generate:schema  # Rust側でスキーマ・introspection生成
pnpm generate:types  # TypeScript型生成（introspection.jsonを使用）

# ビルド時は自動的にスキーマと型が生成されます
cd performers/actors/internetaccountowner
pnpm build  # prebuildで自動的にスキーマ・型生成 → ビルド
```

#### 起動方法

```bash
# すべてのサービスをバックグラウンドで起動
docker-compose up -d

# ログを確認
docker-compose logs -f

# 特定のサービスのログを確認
docker-compose logs -f seeker

# サービスを停止
docker-compose down

# ボリュームも含めて完全に削除
docker-compose down -v
```

#### アーキテクチャの特徴

- **Seeker App**: 完全に独立したNext.jsアプリケーション
  - 内部パッケージ依存なし（`@etzhayyim-tia/*`パッケージを使用しない）
  - Clerk認証を直接使用
  - Apollo Clientを統合してGraphQL APIと通信

- **Admin App**: 独立したNext.jsアプリケーション
  - 内部パッケージ依存なし（`@etzhayyim-tia/*`パッケージを削除）
  - GraphQLクライアントとプロバイダーを実装
  - Apollo Clientを使用してRust GraphQL APIと通信

- **InternetAccountOwner App**: 独立したNext.jsアプリケーション
  - 内部パッケージ依存なし（`@etzhayyim-tia/*`パッケージを削除）
  - GraphQLクライアントとプロバイダーを実装
  - Apollo Clientを使用してRust GraphQL APIと通信

- **GraphQL API**: Rust実装
  - `performers/services/graphql`に実装
  - async-graphql + Actix Web
  - すべてのアプリケーションがこのAPIを使用

---

*This context document serves as the foundation for implementing the Internet Account Protection System using LLMS DAG RULES v3.17.14+ architecture.*
