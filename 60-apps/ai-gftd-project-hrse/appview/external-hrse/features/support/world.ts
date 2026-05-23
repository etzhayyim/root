// @etzhayyim/cyber-freelance#CucumberWorld
// Cucumber World設定

import { setWorldConstructor, World } from "@cucumber/cucumber";
import type { Page, Browser } from "@playwright/test";
import { chromium } from "@playwright/test";

export interface ICustomWorld {
	page: Page;
	browser: Browser;
	context: Record<string, unknown>;
	graphqlUrl?: string;
	currentJob?: any;
	jobList?: any[];
	latestJob?: any;
	syncResult?: any;
	useFrontend?: boolean;
	initBrowser(): Promise<void>;
	closeBrowser(): Promise<void>;
	graphqlRequest?(query: string, variables?: any): Promise<any>;
}

class CustomWorld extends World implements ICustomWorld {
	public page!: Page;
	public browser!: Browser;
	public context: Record<string, unknown> = {};
	public graphqlUrl: string;
	public currentJob: any = null;
	public jobList: any[] = [];
	public latestJob: any = null;
	public syncResult: any = null;

	constructor(options: Parameters<typeof World>[0]) {
		super(options);
		this.graphqlUrl = process.env.GRAPHQL_API_URL || "http://localhost:8082/graphql";
	}

	async initBrowser() {
		this.browser = await chromium.launch({
			headless: process.env.CI === "1",
		});
		const context = await this.browser.newContext({
			baseURL: process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
		});
		this.page = await context.newPage();
	}

	async closeBrowser() {
		if (this.browser) {
			await this.browser.close();
		}
	}

	private async unsupportedFetch(endpoint: string): Promise<never> {
		throw new Error(`Unsupported: fetch is disabled in hrse (${endpoint})`);
	}

	async graphqlRequest(query: string, variables?: any): Promise<any> {
		try {
			const headers: Record<string, string> = { "Content-Type": "application/json" };
			
			// 認証トークンが設定されている場合はAuthorizationヘッダーに追加
			if (this.context.authenticated && this.context.authToken) {
				headers["Authorization"] = `Bearer ${this.context.authToken}`;
			}
			
			const response = await this.unsupportedFetch(this.graphqlUrl);
			
			if (!response.ok) {
				// HTTPエラーの場合はthrowする
				throw new Error(`GraphQL API returned ${response.status}: ${response.statusText}`);
			}
			
			const result = await response.json();
			
			// GraphQL APIはHTTP 200でエラーを返すことがあるため、errors配列を含むresultを返す
			// ステップ定義でエラーを適切に処理できるようにする
			return result;
		} catch (error) {
			// ネットワークエラーやその他のエラーを再スロー
			if (error instanceof Error) {
				throw error;
			}
			throw new Error(`GraphQL request failed: ${String(error)}`);
		}
	}
}

setWorldConstructor(CustomWorld);

export { CustomWorld };
export type { ICustomWorld };
