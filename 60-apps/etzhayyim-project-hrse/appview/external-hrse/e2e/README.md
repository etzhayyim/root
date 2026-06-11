# E2Eテスト設定ガイド

このディレクトリには、Playwrightを使用したEnd-to-Endテストが含まれています。

## セットアップ

### 1. Clerk認証の設定

E2EテストでClerk認証を使用するには、以下の手順を実行してください：

1. **テストユーザーの作成**
   - Clerk Dashboardでテストユーザーを作成します
   - ユーザー名とパスワード認証を有効にします

2. **環境変数の設定**
   - `.envrc`ファイルを作成し、以下のいずれかの認証方法を設定します：

   **方法1: パスワード認証**
   ```bash
   export E2E_CLERK_USER_USERNAME="your_test_username"
   export E2E_CLERK_USER_PASSWORD="your_test_password"
   ```

   **方法2: メールコード認証（推奨 - テスト用メールアドレス）**
   ```bash
   # +clerk_testサブアドレスを使用（実際のメールは送信されません）
   export E2E_CLERK_TEST_EMAIL="test+clerk_test@example.com"
   # 検証コードは自動的に424242が使用されます
   ```

   **方法3: 電話番号認証（テスト用電話番号）**
   ```bash
   # +1 (XXX) 555-0100 から +1 (XXX) 555-0199 の範囲
   export E2E_CLERK_TEST_PHONE="+12015550100"
   # 検証コードは自動的に424242が使用されます
   ```

   - `direnv`がインストールされている場合は、`direnv allow`を実行して環境変数を有効化します
   - `direnv`がインストールされていない場合は、`.envrc.example`を参考に`.envrc`を作成し、手動で`source .envrc`を実行するか、シェルの起動時に自動的に読み込まれるように設定してください

   **テスト用メールと電話番号について:**
   - Clerkのテストモードでは、`+clerk_test`サブアドレスを含むメールアドレスや、`+1 (XXX) 555-0100`から`+1 (XXX) 555-0199`の範囲の電話番号を使用すると、実際のメールやSMSが送信されません
   - 検証コードは常に`424242`です
   - 詳細: [Clerk Test Emails and Phones](https://clerk.com/docs/guides/development/testing/test-emails-and-phones)

3. **認証状態の生成**
   - 初回実行時に、`e2e/global.setup.ts`が自動的に認証状態を`playwright/.clerk/user.json`に保存します
   - このファイルは`.gitignore`に含まれているため、リポジトリにはコミットされません

### 2. テストの実行

```bash
# すべてのE2Eテストを実行
pnpm test:e2e

# 特定のプロジェクト（ブラウザ）で実行
pnpm test:e2e --project=chromium

# 特定のテストファイルを実行
pnpm test:e2e e2e/job-seeker/profile.spec.ts

# UIモードで実行（デバッグに便利）
pnpm test:e2e:ui

# デバッグモードで実行
pnpm test:e2e:debug
```

### 3. テストレポート

テスト実行後、以下の場所にレポートが生成されます：

- HTMLレポート: `playwright-report/index.html`
- JSONレポート: `playwright-report/results.json`

## テストファイルの構造

- `e2e/global.setup.ts` - グローバルセットアップ（Clerk認証状態の保存）
- `e2e/job-seeker/` - 求職者向けページのテスト
- `e2e/job-seeker/` - 求職者向けページのテスト
- `e2e/recruiter/` - リクルーター向けページのテスト
- `e2e/admin/` - 管理画面のテスト
- `e2e/semantic-matching.spec.ts` - セマンティックマッチング機能のテスト
- `e2e/matching.spec.ts` - マッチング機能のテスト

## direnvのセットアップ

このプロジェクトでは`direnv`を使用して環境変数を管理します。

### direnvのインストール

```bash
# macOS
brew install direnv

# シェル設定に追加（zshの場合）
echo 'eval "$(direnv hook zsh)"' >> ~/.zshrc
source ~/.zshrc
```

### 環境変数の設定

1. `.envrc.example`をコピーして`.envrc`を作成：
   ```bash
   cp .envrc.example .envrc
   ```

2. `.envrc`を編集して実際の値を設定：
   ```bash
   export E2E_CLERK_USER_USERNAME="your_test_username"
   export E2E_CLERK_USER_PASSWORD="your_test_password"
   export NEXT_PUBLIC_APP_URL="http://localhost:3000"
   ```

3. `direnv allow`を実行して環境変数を有効化：
   ```bash
   direnv allow
   ```

これで、プロジェクトディレクトリに入ると自動的に環境変数が読み込まれます。

## 参考資料

- [Clerk Playwright Testing Guide](https://clerk.com/docs/guides/development/testing/playwright/overview)
- [Playwright Documentation](https://playwright.dev/docs/intro)
- [direnv Documentation](https://direnv.net/)
