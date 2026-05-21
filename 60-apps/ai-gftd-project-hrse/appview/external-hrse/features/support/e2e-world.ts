// @etzhayyim/cyber-freelance#E2ECucumberWorld
// E2E BDD用のCucumber World設定（Playwright統合）

import { setWorldConstructor, World } from "@cucumber/cucumber";
import {
	chromium,
	firefox,
	webkit,
	type Browser,
	type BrowserContext,
	type Page,
	type BrowserType,
} from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";

export interface IE2EWorld {
	page: Page;
	browser: Browser;
	browserContext: BrowserContext;
	context: Record<string, unknown>;
	graphqlUrl: string;
	baseUrl: string;
	storageStatePath: string;

	// Browser management
	initBrowser(browserName?: "chromium" | "firefox" | "webkit"): Promise<void>;
	closeBrowser(): Promise<void>;

	// Navigation
	goto(path: string): Promise<void>;
	waitForNavigation(): Promise<void>;

	// Element interactions
	click(selector: string): Promise<void>;
	fill(selector: string, value: string): Promise<void>;
	selectOption(selector: string, value: string | string[]): Promise<void>;
	getText(selector: string): Promise<string>;
	isVisible(selector: string): Promise<boolean>;
	waitForSelector(selector: string, options?: { timeout?: number }): Promise<void>;

	// Assertions
	assertUrl(expected: string | RegExp): Promise<void>;
	assertTextVisible(text: string): Promise<void>;
	assertElementVisible(selector: string): Promise<void>;
	assertElementHidden(selector: string): Promise<void>;

	// GraphQL
	graphqlRequest(query: string, variables?: Record<string, unknown>): Promise<unknown>;

	// Screenshots
	takeScreenshot(name: string): Promise<string>;
}

class E2EWorld extends World implements IE2EWorld {
	public page!: Page;
	public browser!: Browser;
	public browserContext!: BrowserContext;
	public context: Record<string, unknown> = {};
	public graphqlUrl: string;
	public baseUrl: string;
	public storageStatePath: string;

	constructor(options: Parameters<typeof World>[0]) {
		super(options);
		this.graphqlUrl = process.env.GRAPHQL_API_URL || "http://localhost:8082/graphql";
		this.baseUrl = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";
		this.storageStatePath = path.resolve(
			process.cwd(),
			"playwright/.clerk/user.json"
		);
	}

	async initBrowser(browserName: "chromium" | "firefox" | "webkit" = "chromium"): Promise<void> {
		const browserTypes: Record<string, BrowserType> = {
			chromium,
			firefox,
			webkit,
		};

		const browserType = browserTypes[browserName];
		if (!browserType) {
			throw new Error(`Unknown browser: ${browserName}`);
		}

		this.browser = await browserType.launch({
			headless: process.env.CI === "1" || process.env.HEADLESS === "true",
		});

		// 認証状態をロード（存在する場合）
		const contextOptions: Parameters<Browser["newContext"]>[0] = {
			baseURL: this.baseUrl,
		};

		if (fs.existsSync(this.storageStatePath)) {
			contextOptions.storageState = this.storageStatePath;
		}

		this.browserContext = await this.browser.newContext(contextOptions);
		this.page = await this.browserContext.newPage();

		// タイムアウト設定
		this.page.setDefaultTimeout(30000);
		this.page.setDefaultNavigationTimeout(30000);
	}

	async closeBrowser(): Promise<void> {
		if (this.page) {
			await this.page.close();
		}
		if (this.browserContext) {
			await this.browserContext.close();
		}
		if (this.browser) {
			await this.browser.close();
		}
	}

	async goto(urlPath: string): Promise<void> {
		await this.page.goto(urlPath);
	}

	async waitForNavigation(): Promise<void> {
		await this.page.waitForLoadState("networkidle");
	}

	async click(selector: string): Promise<void> {
		await this.page.click(selector);
	}

	async fill(selector: string, value: string): Promise<void> {
		await this.page.fill(selector, value);
	}

	async selectOption(selector: string, value: string | string[]): Promise<void> {
		await this.page.selectOption(selector, value);
	}

	async getText(selector: string): Promise<string> {
		const element = await this.page.locator(selector);
		return element.textContent() ?? "";
	}

	async isVisible(selector: string): Promise<boolean> {
		const element = this.page.locator(selector);
		return element.isVisible();
	}

	async waitForSelector(
		selector: string,
		options?: { timeout?: number }
	): Promise<void> {
		await this.page.locator(selector).waitFor({
			timeout: options?.timeout ?? 30000,
		});
	}

	async assertUrl(expected: string | RegExp): Promise<void> {
		const url = this.page.url();
		if (typeof expected === "string") {
			if (!url.includes(expected)) {
				throw new Error(`Expected URL to contain "${expected}", but got "${url}"`);
			}
		} else {
			if (!expected.test(url)) {
				throw new Error(
					`Expected URL to match pattern "${expected}", but got "${url}"`
				);
			}
		}
	}

	async assertTextVisible(text: string): Promise<void> {
		const locator = this.page.getByText(text);
		const isVisible = await locator.isVisible();
		if (!isVisible) {
			throw new Error(`Expected text "${text}" to be visible`);
		}
	}

	async assertElementVisible(selector: string): Promise<void> {
		const locator = this.page.locator(selector);
		const isVisible = await locator.isVisible();
		if (!isVisible) {
			throw new Error(`Expected element "${selector}" to be visible`);
		}
	}

	async assertElementHidden(selector: string): Promise<void> {
		const locator = this.page.locator(selector);
		const isVisible = await locator.isVisible();
		if (isVisible) {
			throw new Error(`Expected element "${selector}" to be hidden`);
		}
	}

	private async unsupportedFetch(endpoint: string): Promise<never> {
		throw new Error(`Unsupported: fetch is disabled in hrse (${endpoint})`);
	}

	async graphqlRequest(
		query: string,
		variables?: Record<string, unknown>
	): Promise<unknown> {
		try {
			const headers: Record<string, string> = {
				"Content-Type": "application/json",
			};

			// 認証トークンが設定されている場合はAuthorizationヘッダーに追加
			if (this.context.authenticated && this.context.authToken) {
				headers["Authorization"] = `Bearer ${String(this.context.authToken)}`;
			}

			const response = await this.unsupportedFetch(this.graphqlUrl);

			if (!response.ok) {
				throw new Error(
					`GraphQL API returned ${response.status}: ${response.statusText}`
				);
			}

			return await response.json();
		} catch (error) {
			if (error instanceof Error) {
				throw error;
			}
			throw new Error(`GraphQL request failed: ${String(error)}`);
		}
	}

	async takeScreenshot(name: string): Promise<string> {
		const screenshotDir = path.resolve(process.cwd(), "reports/screenshots");
		if (!fs.existsSync(screenshotDir)) {
			fs.mkdirSync(screenshotDir, { recursive: true });
		}

		const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
		const filename = `${name}-${timestamp}.png`;
		const filepath = path.join(screenshotDir, filename);

		await this.page.screenshot({ path: filepath, fullPage: true });
		return filepath;
	}
}

setWorldConstructor(E2EWorld);

export { E2EWorld };
export type { IE2EWorld };
