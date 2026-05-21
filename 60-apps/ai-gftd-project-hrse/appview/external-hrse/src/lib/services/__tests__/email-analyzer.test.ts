// @etzhayyim/cyber-freelance#EmailAnalyzerTest
// Email AnalyzerサービスのVitestテスト（カバレッジ測定用）

import { describe, it, expect, vi, beforeEach } from "vitest";
import { analyzeEmail, type EmailContent } from "../email-analyzer.js";

// LLMServiceをモック
const mockAnalyzeEmailWithRetry = vi.fn().mockResolvedValue({
	'entityType': "JobSeeker",
	confidence: 0.9,
	'extractedData': {
		name: "Test User",
		email: "test@example.com",
	},
});

vi.mock("@/lib/llm/openai.js", () => {
	class MockLLMService {
		analyzeEmailWithRetry = mockAnalyzeEmailWithRetry;
	}
	return {
		LLMService: MockLLMService,
	};
});

describe("Email Analyzer Service", () => {
	beforeEach(() => {
		// 環境変数を設定（LLMServiceのコンストラクタで必要）
		process.env.OPENAI_API_KEY = "test-api-key-for-coverage";
		process.env.OPENROUTER_API_KEY_251025 = "";
		// モックをリセット
		mockAnalyzeEmailWithRetry.mockResolvedValue({
			'entityType': "JobSeeker",
			confidence: 0.9,
			'extractedData': {
				name: "Test User",
				email: "test@example.com",
			},
		});
	});

	it("should analyze email and extract structured information", async () => {
		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Job Application",
			html: null,
			text: "I am interested in the position.",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(true);
		expect(result.entityType).toBe("JobSeeker");
		expect(result.confidence).toBeGreaterThan(0);
		expect(result.extractedData).not.toBeNull();
		expect(result.emailMetadata).not.toBeNull();
		expect(result.error).toBeNull();
	});

	it("should handle low confidence results", async () => {
		// Low confidenceのモックを設定
		mockAnalyzeEmailWithRetry.mockResolvedValueOnce({
			'entityType': "JobSeeker",
			confidence: 0.3, // Low confidence
			'extractedData': {
				name: "Test User",
				email: "test@example.com",
			},
		});

		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Job Application",
			html: null,
			text: "I am interested in the position.",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(true);
		expect(result.confidence).toBeLessThan(0.5);
	});

	it("should handle Unknown entity type", async () => {
		// Unknown entity typeのモックを設定
		mockAnalyzeEmailWithRetry.mockResolvedValueOnce({
			'entityType': "Unknown",
			confidence: 0.5,
			'extractedData': {},
		});

		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Unknown Email",
			html: null,
			text: "Some random text.",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(false);
		expect(result.entityType).toBeNull();
		expect(result.error).not.toBeNull();
	});

	it("should handle errors gracefully", async () => {
		// エラーをスローするモックを設定
		mockAnalyzeEmailWithRetry.mockRejectedValueOnce(new Error("API Error"));

		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Error Test",
			html: null,
			text: "Test",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(false);
		expect(result.error).not.toBeNull();
		expect(result.entityType).toBeNull();
		expect(result.confidence).toBeNull();
	});

	it("should handle email without date", async () => {
		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Job Application",
			html: null,
			text: "I am interested in the position.",
			date: null, // dateがnullの場合のブランチをカバー
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(true);
		expect(result.emailMetadata).not.toBeNull();
		expect(result.emailMetadata?.date).toBeDefined(); // 自動生成された日付が設定される
	});

	it("should handle non-Error exceptions", async () => {
		// Errorインスタンスではない例外をスローするモックを設定
		mockAnalyzeEmailWithRetry.mockRejectedValueOnce("String error");

		const email: EmailContent = {
			from: "test@example.com",
			to: "hr@company.com",
			subject: "Error Test",
			html: null,
			text: "Test",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(false);
		expect(result.error).toBe("Unknown error"); // Errorインスタンスでない場合は"Unknown error"
		expect(result.entityType).toBeNull();
		expect(result.confidence).toBeNull();
	});

	it("should handle other entity types (Job, Agency)", async () => {
		// Job entity typeのモックを設定
		mockAnalyzeEmailWithRetry.mockResolvedValueOnce({
			'entityType': "Job",
			confidence: 0.95,
			'extractedData': {
				title: "Software Engineer",
				company: "Tech Corp",
			},
		});

		const email: EmailContent = {
			from: "hr@techcorp.com",
			to: "candidates@techcorp.com",
			subject: "Job Posting: Software Engineer",
			html: null,
			text: "We are hiring a Software Engineer.",
			date: new Date().toISOString(),
		};

		const result = await analyzeEmail(email);

		expect(result.success).toBe(true);
		expect(result.entityType).toBe("Job");
		expect(result.confidence).toBe(0.95);

		// Agency entity typeのモックを設定
		mockAnalyzeEmailWithRetry.mockResolvedValueOnce({
			'entityType': "Agency",
			confidence: 0.88,
			'extractedData': {
				name: "Recruitment Agency",
				services: ["IT Recruitment"],
			},
		});

		const agencyEmail: EmailContent = {
			from: "contact@recruitment-agency.com",
			to: "clients@recruitment-agency.com",
			subject: "Our Services",
			html: null,
			text: "We provide IT recruitment services.",
			date: new Date().toISOString(),
		};

		const agencyResult = await analyzeEmail(agencyEmail);

		expect(agencyResult.success).toBe(true);
		expect(agencyResult.entityType).toBe("Agency");
		expect(agencyResult.confidence).toBe(0.88);
	});
});
