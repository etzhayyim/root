// @etzhayyim/cyber-freelance#PlaywrightConfig
// Playwright E2Eテスト設定

import { defineConfig, devices } from "@playwright/test";

/**
 * E2Eテスト設定
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
	testDir: "./e2e",
	globalSetup: require.resolve("./e2e/global.setup.ts"),
	/* テストの最大実行時間 */
	timeout: 30 * 1000,
	expect: {
		/* expectアサーションのタイムアウト */
		timeout: 5000,
	},
	/* テストを並列実行 */
	fullyParallel: true,
	/* CI環境では失敗時にリトライしない */
	forbidOnly: !!process.env.CI,
	/* CI環境では失敗時にリトライ */
	retries: process.env.CI ? 2 : 0,
	/* 並列実行するワーカー数 */
	workers: process.env.CI ? 1 : 4,
	/* レポート設定 */
	reporter: process.env.CI
		? [["html"], ["json", { outputFile: "playwright-report/results.json" }]]
		: [["html"], ["list"]],
	/* 共有設定 */
	use: {
		/* ベースURL */
		baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
		/* アクションのタイムアウト */
		actionTimeout: 10 * 1000,
		/* ナビゲーションのタイムアウト */
		navigationTimeout: 30 * 1000,
		/* トレースを記録（失敗時のみ） */
		trace: "on-first-retry",
		/* スクリーンショットを記録（失敗時のみ） */
		screenshot: "only-on-failure",
		/* 動画を記録（失敗時のみ） */
		video: "retain-on-failure",
	},

	/* プロジェクト設定 */
	projects: [
		{
			name: "chromium",
			use: {
				...devices["Desktop Chrome"],
				storageState: "playwright/.clerk/user.json",
			},
		},
		{
			name: "firefox",
			use: {
				...devices["Desktop Firefox"],
				storageState: "playwright/.clerk/user.json",
			},
		},
		{
			name: "webkit",
			use: {
				...devices["Desktop Safari"],
				storageState: "playwright/.clerk/user.json",
			},
		},
		/* モバイルデバイステスト */
		{
			name: "Mobile Chrome",
			use: {
				...devices["Pixel 5"],
				storageState: "playwright/.clerk/user.json",
			},
		},
		{
			name: "Mobile Safari",
			use: {
				...devices["iPhone 12"],
				storageState: "playwright/.clerk/user.json",
			},
		},
		/* iPadテスト（Apple Human Interface Guidelinesに基づく） */
		{
			name: "iPad",
			use: {
				...devices["iPad Pro"],
				storageState: "playwright/.clerk/user.json",
			},
		},
	],

	/* 開発サーバーの設定 */
	webServer: [
		{
			command: "pnpm dev",
			url: "http://localhost:3000",
			timeout: 120 * 1000,
			reuseExistingServer: true,
		},
		// GraphQLサーバーは既存のサーバーを使用するか、手動で起動してください
		// {
		// 	command: "cd performers/services/graphql && cargo run --bin graphql",
		// 	url: "http://localhost:8080/graphql",
		// 	timeout: 120 * 1000,
		// 	reuseExistingServer: true,
		// },
	],
});






