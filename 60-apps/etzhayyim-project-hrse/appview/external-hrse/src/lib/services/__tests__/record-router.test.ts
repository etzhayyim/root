// @etzhayyim/cyber-freelance#RecordRouterTest
// Record RouterサービスのVitestテスト（カバレッジ測定用）

import { describe, it, expect, vi, beforeEach } from "vitest";
import { routeRecord, type RoutingResult } from "../record-router.js";
import type { EmailAnalysisResult } from "../email-analyzer.js";
import { getRecordRouterServiceClient } from "@/lib/connect/server-client.js";

// RecordRouterServiceClientをモック
vi.mock("@/lib/connect/server-client.js", () => {
	return {
		getRecordRouterServiceClient: vi.fn().mockResolvedValue({
			routeRecord: vi.fn().mockResolvedValue({
				success: true,
				action: "created",
				entityType: "JobSeeker",
				entityId: "test-entity-id",
				message: "Record created successfully",
				error: null,
			}),
		}),
	};
});

describe("Record Router Service", () => {
	beforeEach(() => {
		vi.clearAllMocks();
	});

	it("should route record successfully", async () => {
		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBe("created");
		expect(result.entityType).toBe("JobSeeker");
		expect(result.entityId).toBe("test-entity-id");
		expect(result.error).toBeNull();
	});

	it("should handle update action", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockResolvedValueOnce({
			success: true,
			action: "updated",
			entityType: "JobSeeker",
			entityId: "existing-entity-id",
			message: "Record updated successfully",
			error: null,
		});

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBe("updated");
		expect(result.entityId).toBe("existing-entity-id");
	});

	it("should handle skip action", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockResolvedValueOnce({
			success: true,
			action: "skipped",
			entityType: "JobSeeker",
			entityId: null,
			message: "Record skipped",
			error: null,
		});

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBe("skipped");
	});

	it("should handle errors gracefully", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockRejectedValueOnce(new Error("Connection error"));

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(false);
		expect(result.error).not.toBeNull();
		expect(result.action).toBeNull();
		expect(result.entityType).toBe("JobSeeker"); // エラー時もentityTypeは保持される
	});

	it("should handle missing email metadata", async () => {
		const analysis: EmailAnalysisResult = {
			success: true,
			'entityType': "JobSeeker",
			confidence: 0.9,
			'extractedData': {
				name: "Test User",
				email: "test@example.com",
			},
			'emailMetadata': null,
			error: null,
		};

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBe("created");
	});

	it("should handle null entityType in analysis", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockResolvedValueOnce({
			success: true,
			action: "created",
			entityType: null, // responseのentityTypeがnullの場合のブランチをカバー
			entityId: "test-entity-id",
			message: "Record created",
			error: null,
		});

		const analysis: EmailAnalysisResult = {
			success: true,
			'entityType': null, // entityTypeがnullの場合のブランチをカバー
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.entityType).toBeNull(); // responseのentityTypeがnullなので、結果もnullになる
	});

	it("should handle null confidence", async () => {
		const analysis: EmailAnalysisResult = {
			success: true,
			'entityType': "JobSeeker",
			confidence: null, // confidenceがnullの場合のブランチをカバー
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
	});

	it("should handle null action in response", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockResolvedValueOnce({
			success: true,
			action: null, // actionがnullの場合のブランチをカバー
			entityType: "JobSeeker",
			entityId: "test-entity-id",
			message: null, // messageがnullの場合のブランチをカバー
			error: null,
		});

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBeNull();
		expect(result.message).toBeNull();
	});

	it("should handle null entityType in response", async () => {
		const mockClient = await getRecordRouterServiceClient();
		vi.mocked(mockClient.routeRecord).mockResolvedValueOnce({
			success: true,
			action: "created",
			entityType: null, // entityTypeがnullの場合のブランチをカバー
			entityId: "test-entity-id",
			message: "Record created",
			error: null,
		});

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.entityType).toBeNull();
	});

	it("should handle non-Error exceptions", async () => {
		const mockClient = await getRecordRouterServiceClient();
		// Errorインスタンスではない例外をスローするモックを設定
		vi.mocked(mockClient.routeRecord).mockRejectedValueOnce("String error");

		const analysis: EmailAnalysisResult = {
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

		const result = await routeRecord(analysis);

		expect(result.success).toBe(false);
		expect(result.error).toBe("Unknown error"); // Errorインスタンスでない場合は"Unknown error"
		expect(result.action).toBeNull();
		expect(result.entityType).toBe("JobSeeker"); // エラー時もentityTypeは保持される
	});

	it("should handle analysis with error field", async () => {
		const analysis: EmailAnalysisResult = {
			success: false,
			'entityType': "JobSeeker",
			confidence: 0.5,
			'extractedData': null,
			'emailMetadata': {
				from: "test@example.com",
				to: "hr@company.com",
				subject: "Job Application",
				date: new Date().toISOString(),
			},
			error: "Analysis failed", // errorフィールドが設定されている場合のブランチをカバー
		};

		const result = await routeRecord(analysis);

		expect(result.success).toBe(true);
		expect(result.action).toBe("created");
	});
});
