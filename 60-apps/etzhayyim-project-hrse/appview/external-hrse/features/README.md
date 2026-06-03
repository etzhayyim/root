# BDD Tests with Cucumber

このディレクトリには、capabilities.jsonldから自動生成されたCucumber BDDテストが含まれています。

## 構造

```
features/
├── *.feature          # Capabilityから生成されたfeatureファイル
├── support/
│   ├── world.ts       # Cucumber World設定
│   └── hooks.ts       # Before/After hooks
└── step_definitions/
    ├── common.steps.ts           # 共通のstep定義
    ├── email-analysis.steps.ts   # Email Analysis用step定義
    ├── record-routing.steps.ts   # Record Routing用step定義
    └── semantic-matching.steps.ts # Semantic Matching用step定義
```

## 使用方法

### Featureファイルの生成

capabilities.jsonldからfeatureファイルを生成：

```bash
pnpm generate:bdd
```

### BDDテストの実行

```bash
# BDDテストを実行
pnpm test:bdd

# カバレッジ付きでBDDテストを実行
pnpm test:bdd:coverage

# フロントエンドBDDテスト（カバレッジ付き）
pnpm test:bdd:frontend:coverage

# E2E BDDテスト（カバレッジ付き）
pnpm test:e2e:bdd:coverage
```

### カバレッジレポートの確認

```bash
# カバレッジレポートを生成
pnpm test:bdd:coverage:report

# HTMLレポートを開く
open coverage/index.html

# Capability to BDD カバレッジ評価
pnpm check:bdd-coverage
```

### カバレッジ評価のワークフロー

#### 統合テストとして実行（推奨）

1. **バックエンドサービスの起動**
   ```bash
   # セットアップスクリプトを実行（推奨）
   pnpm test:bdd:integration:setup

   # または手動で起動
   docker-compose up -d postgres connect-go
   ```

2. **統合テストを実行**
   ```bash
   # 統合テストを実行（セットアップ + テスト）
   pnpm test:bdd:integration

   # または、カバレッジ付きで実行
   pnpm test:bdd:coverage
   ```

3. **カバレッジレポートを生成**
   ```bash
   pnpm test:bdd:coverage:report
   ```

4. **Capability to BDD カバレッジを評価**
   ```bash
   pnpm check:bdd-coverage
   ```

#### 通常のBDDテスト（モック使用）

1. **BDDテストをカバレッジ付きで実行**
   ```bash
   # 通常のBDDテスト
   pnpm test:bdd:coverage

   # E2E BDDテスト
   pnpm test:e2e:bdd:coverage
   ```

2. **カバレッジレポートを生成**
   ```bash
   pnpm test:bdd:coverage:report
   ```

3. **Capability to BDD カバレッジを評価**
   ```bash
   pnpm check:bdd-coverage
   ```
   このコマンドは以下を表示します：
   - 全体のカバレッジサマリー（Lines, Functions, Branches, Statements）
   - 各CapabilityのBDDテストカバレッジ
   - カバレッジが80%未満のCapabilityの警告
   - HTMLレポートの場所

4. **すべてのBDDテストをカバレッジ付きで実行して評価**
   ```bash
   pnpm test:bdd:coverage:all
   ```
   このコマンドは以下を順に実行します：
   - `test:bdd:coverage` - 通常のBDDテスト（カバレッジ付き）
   - `test:e2e:bdd:coverage` - E2E BDDテスト（カバレッジ付き）
   - `test:bdd:coverage:report` - カバレッジレポート生成
   - `check:bdd-coverage` - Capability to BDD カバレッジ評価

## 統合テスト

詳細は `features/README-INTEGRATION.md` を参照してください。

## CapabilityからBDDへの変換

各Capabilityは以下のようにBDD featureファイルに変換されます：

1. **Feature**: Capabilityのラベル
2. **Description**: Capabilityの説明
3. **Scenarios**:
   - Capabilityが利用可能であること
   - エラーハンドリング
   - 入力検証
   - Capability固有のシナリオ

## Step定義の追加

新しいstep定義を追加する場合は、`features/step_definitions/`ディレクトリに追加してください。

## 参考

- [Cucumber.js Documentation](https://github.com/cucumber/cucumber-js)
- [nyc Documentation](https://github.com/istanbuljs/nyc)




