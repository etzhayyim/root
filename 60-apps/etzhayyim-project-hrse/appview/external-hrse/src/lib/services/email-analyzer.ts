// @etzhayyim/cyber-freelance#EmailAnalyzer
// メール分析サービス

import { LLMService, type EmailContent, type EntityType } from "@/lib/llm/openai";

export interface EmailMetadata {
	from: string;
	to: string;
	subject: string;
	date: string;
}

export interface EmailAnalysisResult {
	success: boolean;
	'entityType': EntityType | null;
	confidence: number | null;
	'extractedData': Record<string, unknown> | null;
	'emailMetadata': EmailMetadata | null;
	error: string | null;
}

export type { EmailContent };

export async function analyzeEmail(
	email: EmailContent,
): Promise<EmailAnalysisResult> {
	try {
		// LLMServiceのインスタンスを作成（テストではモックされる）
		const llmService = new LLMService();
		const result = await llmService.analyzeEmailWithRetry(email, 3);

		if (result.confidence < 0.5) {
			console.warn("Low confidence analysis result", {
				confidence: result.confidence,
			});
		}

		if (result.entityType === "Unknown") {
			return {
				success: false,
				'entityType': null,
				confidence: null,
				'extractedData': null,
				'emailMetadata': null,
				error: "Could not determine entity type from email content",
			};
		}

		return {
			success: true,
			'entityType': result.entityType,
			confidence: result.confidence,
			'extractedData': result.extractedData,
			'emailMetadata': {
				from: email.from,
				to: email.to,
				subject: email.subject,
				date: email.date || new Date().toISOString(),
			},
			error: null,
		};
	} catch (error) {
		console.error("Email analysis failed", {
			from: email.from,
			to: email.to,
			subject: email.subject,
			error,
		});

		return {
			success: false,
			'entityType': null,
			confidence: null,
			'extractedData': null,
			'emailMetadata': null,
			error: error instanceof Error ? error.message : "Unknown error",
		};
	}
}

