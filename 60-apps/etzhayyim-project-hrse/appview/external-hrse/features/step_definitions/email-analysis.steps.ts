// @etzhayyim/cyber-freelance#EmailAnalysisSteps
// Email Analysis関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

// 循環依存を回避するため、直接動的インポートを使用
let emailAnalyzerModule: typeof import("@/lib/services/email-analyzer.js") | null = null;

async function analyzeEmail(email: import("@/lib/services/email-analyzer.js").EmailContent) {
	if (!emailAnalyzerModule) {
		emailAnalyzerModule = await import("@/lib/services/email-analyzer.js");
	}
	return emailAnalyzerModule.analyzeEmail(email);
}

Given("an email is received", async function (this: ICustomWorld) {
	this.context.email = {
		from: "test@example.com",
		to: "hr@company.com",
		subject: "Job Application",
		html: null,
		text: "I am interested in the position.",
		date: new Date().toISOString(),
	};
});

When("the email is analyzed using LLM", async function (this: ICustomWorld) {
	const email = this.context.email;
	if (!email) {
		throw new Error("Email not set in context");
	}

	// 環境変数を確認して設定（LLMServiceのコンストラクタエラーを回避）
	if (!process.env.OPENAI_API_KEY && !process.env.OPENROUTER_API_KEY_251025) {
		process.env.OPENAI_API_KEY = "test-api-key-for-coverage";
	}

	try {
		// 直接動的インポートを使用して循環依存を回避しつつ、実際のサービス関数を呼び出す
		const result = await analyzeEmail(email);
		
		this.context.analysisResult = result;
		this.context.analysisError = result.success ? null : new Error(result.error || "Analysis failed");
	} catch (error) {
		// 予期しないエラーをキャッチしてコンテキストに保存
		this.context.analysisError = error;
		this.context.analysisResult = {
			success: false,
			'entityType': null,
			confidence: null,
			'extractedData': null,
			'emailMetadata': {
				from: email.from,
				to: email.to,
				subject: email.subject,
				date: email.date || new Date().toISOString(),
			},
			error: error instanceof Error ? error.message : "Unknown error",
		};
	}
});

Then(
	"structured information about job seekers, jobs, or agencies should be extracted",
	async function (this: ICustomWorld) {
		const result = this.context.analysisResult;
		if (!result) {
			throw new Error("Analysis result not found");
		}

		// エラーが発生した場合は、エラーとして扱う（モック結果で上書きしない）
		if (!result.success) {
			throw new Error(`Email analysis failed: ${result.error || "Unknown error"}`);
		}

		expect(result.success).toBe(true);
		expect(result.entityType).not.toBeNull();
		expect(result.extractedData).not.toBeNull();
	}
);

Then("the extracted data should be valid", async function (this: ICustomWorld) {
	const result = this.context.analysisResult;
	if (!result) {
		throw new Error("Analysis result not found");
	}

	// エラーが発生した場合は、エラーとして扱う（モック結果で上書きしない）
	if (!result.success) {
		throw new Error(`Email analysis failed: ${result.error || "Unknown error"}`);
	}

	expect(result.success).toBe(true);
	expect(result.confidence).toBeGreaterThan(0);
	expect(result.entityType).not.toBe("Unknown");
	expect(result.entityType).not.toBeNull();
});
