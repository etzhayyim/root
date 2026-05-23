// @etzhayyim/cyber-freelance#GlobalSetup
// Playwrightグローバルセットアップ - Clerk認証状態の保存

import { clerk, clerkSetup } from "@clerk/testing/playwright";
import { chromium, FullConfig } from "@playwright/test";
import path from "path";

async function globalSetup(config: FullConfig) {
	// Clerkのセットアップ
	await clerkSetup();

	// 認証状態ファイルのパス
	const authFile = path.join(__dirname, "../playwright/.clerk/user.json");

	// 認証方法の選択（優先順位: パスワード > メールコード > 電話番号）
	const username = process.env.E2E_CLERK_USER_USERNAME;
	const password = process.env.E2E_CLERK_USER_PASSWORD;
	const testEmail = process.env.E2E_CLERK_TEST_EMAIL;
	const testPhoneNumber = process.env.E2E_CLERK_TEST_PHONE;

	if (!username && !testEmail && !testPhoneNumber) {
		console.warn(
			"⚠️  E2E認証情報が設定されていません。以下のいずれかを設定してください:",
		);
		console.warn(
			"   - E2E_CLERK_USER_USERNAME + E2E_CLERK_USER_PASSWORD (パスワード認証)",
		);
		console.warn(
			"   - E2E_CLERK_TEST_EMAIL (メールコード認証、例: test+clerkTest@example.com)",
		);
		console.warn(
			"   - E2E_CLERK_TEST_PHONE (電話番号認証、例: +12015550100)",
		);
		console.warn("   Tests will run without authentication. Some tests may fail.");
		return;
	}

	// ブラウザを起動
	const browser = await chromium.launch();
	const context = await browser.newContext();
	const page = await context.newPage();

	try {
		// アプリケーションのログインページに移動
		const baseUrl = config.projects[0]?.use?.baseURL || "http://localhost:3000";
		await page.goto(baseUrl);

		// 認証方法に応じてサインイン
		if (username && password) {
			// パスワード認証
			console.log("🔐 Using password authentication...");
			await clerk.signIn({
				page,
				signInParams: {
					strategy: "password",
					identifier: username,
					password: password,
				},
			});
		} else if (testEmail) {
			// メールコード認証（テスト用メールアドレスを使用）
			console.log(`📧 Using email code authentication with ${testEmail}...`);
			await clerk.signIn({
				page,
				signInParams: {
					strategy: "emailCode",
					identifier: testEmail,
					code: "424242", // Clerkテストモードの固定検証コード
				},
			});
		} else if (testPhoneNumber) {
			// 電話番号認証（テスト用電話番号を使用）
			console.log(`📱 Using phone number authentication with ${testPhoneNumber}...`);
			await clerk.signIn({
				page,
				signInParams: {
					strategy: "phoneCode",
					identifier: testPhoneNumber,
					code: "424242", // Clerkテストモードの固定検証コード
				},
			});
		}

		// 認証が成功したことを確認するために保護されたページに移動
		await page.goto(`${baseUrl}/job-seeker/profile`);

		// ページが読み込まれるまで待つ
		await page.waitForLoadState("networkidle");

		// 認証状態を保存
		await context.storageState({ path: authFile });

		console.log(`✅ Authentication state saved to ${authFile}`);
	} catch (error) {
		console.error("❌ Failed to authenticate:", error);
		throw error;
	} finally {
		await browser.close();
	}
}

export default globalSetup;
