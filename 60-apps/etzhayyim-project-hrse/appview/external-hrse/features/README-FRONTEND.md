# フロントエンドBDDテスト

## 概要

フロントエンドでBDDテストを実行するための設定と使用方法を説明します。

## アーキテクチャ

フロントエンドBDDテストは、以下のコンポーネントで構成されています：

1. **Playwright**: ブラウザ自動化ツール
2. **Cucumber.js**: BDDテストフレームワーク
3. **Worldクラス**: Playwrightの`Page`と`Browser`を統合
4. **ステップ定義**: フロントエンド操作のステップ定義

## 使用方法

### フロントエンドBDDテストの実行

```bash
# フロントエンドBDDテストを実行（@frontendタグ付き）
pnpm test:bdd:frontend

# カバレッジ付きでフロントエンドBDDテストを実行
pnpm test:bdd:frontend:coverage
```

### タグの使用

フロントエンド操作を使用するBDDシナリオには、`@frontend`タグを付与します：

```gherkin
@agency-profile @frontend
Feature: Agency Profile Management (Frontend)
  Scenario: Successfully create a new agency profile through the UI
    Given I am on the "/agency/profile" page
    When I create an agency profile with:
      | field | value |
      | name  | Test Agency |
    Then I should see a success message
```

## ステップ定義

### ページ遷移

```gherkin
Given I am on the "/agency/profile" page
When I navigate to "/agency/profile"
```

### フォーム入力

```gherkin
When I fill in the "エージェンシー名" field with "Test Agency"
When I fill in the form fields:
  | field        | value              |
  | name         | Test Agency        |
  | contactEmail | contact@example.com|
```

### ボタンクリック

```gherkin
When I click the "保存" button
When I click the "作成" link
```

### 要素の確認

```gherkin
Then I should see "プロファイルを保存しました"
Then I should see a success message
Then I should see a validation error
Then the "name" field should contain "Test Agency"
```

## カバレッジ

フロントエンドBDDテストを実行すると、`src/`ディレクトリ内のコードのカバレッジが計測されます。

カバレッジレポートは`coverage/`ディレクトリに生成されます：

- `coverage/index.html`: HTMLレポート
- `coverage/coverage-final.json`: JSONレポート
- `coverage/lcov.info`: LCOVレポート

## 注意事項

1. **認証**: フロントエンドBDDテストを実行するには、Clerk認証が必要です。`playwright/.clerk/user.json`に認証状態が保存されている必要があります。

2. **サーバー起動**: フロントエンドBDDテストを実行するには、Next.js開発サーバーとGraphQLサーバーが起動している必要があります。

3. **テスト環境**: フロントエンドBDDテストは、実際のブラウザで実行されるため、テスト環境の設定が必要です。

## 既存のBDDテストとの違い

| 項目 | GraphQL API直接呼び出し | フロントエンド操作 |
|------|------------------------|-------------------|
| 実行方法 | GraphQL APIを直接呼び出し | ブラウザでUI操作 |
| カバレッジ | 0% (APIのみ) | フロントエンドコードをカバー |
| 実行速度 | 高速 | やや遅い |
| テスト範囲 | API層のみ | UI層を含む |

## トラブルシューティング

### 認証エラー

```
Error: User not authenticated
```

**解決方法**: `playwright/.clerk/user.json`に認証状態が保存されていることを確認してください。

### ページが見つからない

```
Error: Page not found
```

**解決方法**: Next.js開発サーバーが起動していることを確認してください。

### カバレッジが0%

**原因**: フロントエンド操作を使用していない場合、カバレッジは0%になります。

**解決方法**: `@frontend`タグを付与したBDDシナリオを実行してください。
