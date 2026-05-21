// @etzhayyim/cyber-freelance#E2ECucumberHooks
// E2E BDD用のCucumber hooks

import {
	Before,
	After,
	BeforeAll,
	AfterAll,
	setDefaultTimeout,
	Status,
} from "@cucumber/cucumber";
import type { IE2EWorld } from "./e2e-world.js";
import * as fs from "node:fs";
import * as path from "node:path";

// E2Eテスト用のタイムアウトを60秒に設定
setDefaultTimeout(60 * 1000);

// スクリーンショットディレクトリを作成
BeforeAll(function () {
	const screenshotDir = path.resolve(process.cwd(), "reports/screenshots");
	if (!fs.existsSync(screenshotDir)) {
		fs.mkdirSync(screenshotDir, { recursive: true });
	}

	const reportsDir = path.resolve(process.cwd(), "reports");
	if (!fs.existsSync(reportsDir)) {
		fs.mkdirSync(reportsDir, { recursive: true });
	}
});

// 各シナリオの前にブラウザを初期化
Before({ tags: "@e2e" }, async function (this: IE2EWorld) {
	const browserName =
		(process.env.BROWSER as "chromium" | "firefox" | "webkit") || "chromium";
	await this.initBrowser(browserName);
});

// 失敗時にスクリーンショットを撮影
After({ tags: "@e2e" }, async function (this: IE2EWorld, scenario) {
	if (scenario.result?.status === Status.FAILED && this.page) {
		const scenarioName = scenario.pickle.name.replace(/[^a-zA-Z0-9]/g, "_");
		const screenshotPath = await this.takeScreenshot(`failed-${scenarioName}`);
		this.attach(`Screenshot saved: ${screenshotPath}`, "text/plain");
	}

	await this.closeBrowser();
});

// 全テスト終了時のクリーンアップ
AfterAll(function () {
	// 追加のクリーンアップが必要な場合はここに追加
});



