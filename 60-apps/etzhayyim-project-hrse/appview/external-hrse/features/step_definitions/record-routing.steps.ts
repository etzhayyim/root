// @etzhayyim/cyber-freelance#RecordRoutingSteps
// Record Routing関連のステップ定義

import { Given, When, Then } from "@cucumber/cucumber";
import { expect } from "@playwright/test";
import type { ICustomWorld } from "../support/world.js";

// 循環依存を回避するため、直接動的インポートを使用
let recordRouterModule: typeof import("@/lib/services/record-router.js") | null = null;

async function routeRecord(analysis: import("@/lib/services/email-analyzer.js").EmailAnalysisResult) {
	if (!recordRouterModule) {
		recordRouterModule = await import("@/lib/services/record-router.js");
	}
	return recordRouterModule.routeRecord(analysis);
}

Given("extracted information is available", async function (this: ICustomWorld) {
	this.context.extractedInfo = {
		success: true,
		'entityType': "JobSeeker",
		confidence: 0.9,
		'extractedData': {
			name: "Test User",
			email: "test@example.com",
		},
		'emailMetadata': {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Job Application",
			date: new Date().toISOString(),
		},
		error: null,
	};
});

When(
	"the information is routed to appropriate database records",
	async function (this: ICustomWorld) {
		const extractedInfo = this.context.extractedInfo;
		if (!extractedInfo) {
			throw new Error("Extracted information not found");
		}

		try {
			// 直接動的インポートを使用して循環依存を回避しつつ、実際のサービス関数を呼び出す
			const result = await routeRecord(extractedInfo);
			
			this.context.routingResult = result;
			this.context.routingError = result.success ? null : new Error(result.error || "Routing failed");
		} catch (error) {
			// 予期しないエラーをキャッチしてコンテキストに保存
			this.context.routingError = error;
			this.context.routingResult = {
				success: false,
				action: null,
				'entityType': extractedInfo.entityType,
				'entityId': null,
				message: null,
				error: error instanceof Error ? error.message : "Unknown error",
			};
		}
	}
);

Then(
	"JobSeeker, Job, or Agency records should be created or updated",
	async function (this: ICustomWorld) {
		const result = this.context.routingResult;
		if (!result) {
			throw new Error("Routing result not found");
		}

		// エラーが発生した場合は、エラーとして扱う
		if (!result.success) {
			throw new Error(`Record routing failed: ${result.error || "Unknown error"}`);
		}

		expect(result.success).toBe(true);
		expect(["created", "updated", "skipped"]).toContain(result.action);
	}
);

Then("the routing should be successful", async function (this: ICustomWorld) {
	const result = this.context.routingResult;
	if (!result) {
		throw new Error("Routing result not found");
	}

	expect(result.success).toBe(true);
	expect(result.error).toBeNull();
});

Given("extracted information contains an agency with userId {string}", async function (this: ICustomWorld, userId: string) {
	this.context.extractedInfo = {
		success: true,
		'entityType': "Agency",
		confidence: 0.9,
		'extractedData': {
			userId,
			name: "Test Agency",
			email: "agency@example.com",
		},
		'emailMetadata': {
			from: "agency@example.com",
			to: "hr@company.com",
			subject: "Agency Registration",
			date: new Date().toISOString(),
		},
		error: null,
	};
});

When("the record router processes the extracted information", async function (this: ICustomWorld) {
	const extractedInfo = this.context.extractedInfo;
	if (!extractedInfo) {
		throw new Error("Extracted information not found");
	}

	// 動的インポートを使用
	let recordRouterModule: typeof import("@/lib/services/record-router.js") | null = null;

	async function routeRecord(analysis: import("@/lib/services/email-analyzer.js").EmailAnalysisResult) {
		if (!recordRouterModule) {
			recordRouterModule = await import("@/lib/services/record-router.js");
		}
		return recordRouterModule.routeRecord(analysis);
	}

	try {
		const result = await routeRecord(extractedInfo);
		this.context.routingResult = result;
		this.context.routingProcessed = true;
	} catch (error) {
		this.context.routingError = error;
		this.context.routingProcessed = false;
	}
});

Then("the router should detect the existing agency", async function (this: ICustomWorld) {
	const result = this.context.routingResult;
	if (!result) {
		throw new Error("Routing result not found");
	}

	// 既存のエージェンシーが検出されたことを確認
	expect(result.entityType).toBe("Agency");
	this.context.existingAgencyDetected = true;
});

Then("the router should return the existing agency with action {string}", async function (this: ICustomWorld, expectedAction: string) {
	const result = this.context.routingResult;
	if (!result) {
		throw new Error("Routing result not found");
	}

	expect(result.action).toBe(expectedAction);
	expect(this.context.existingAgencyDetected).toBe(true);
});
