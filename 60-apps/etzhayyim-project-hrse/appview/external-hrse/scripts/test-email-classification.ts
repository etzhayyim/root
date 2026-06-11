#!/usr/bin/env tsx
/**
 * メール分類動作検証スクリプト
 * Resend APIから受信メールを取得し、OpenRouter APIで分類・分析を行う
 */

// 環境変数を読み込み（オプション）
try {
	// eslint-disable-next-line @typescript-eslint/no-require-imports
	const dotenv = require("dotenv");
	dotenv.config({ path: ".env.local" });
} catch {
	// dotenvが利用できない場合は環境変数が既に設定されていることを前提とする
}

const RESEND_API_KEY = process.env.RESEND_API_KEY;
const OPENROUTER_API_KEY = process.env.OPENROUTER_API_KEY_251025 || process.env.OPENAI_API_KEY;
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

if (!RESEND_API_KEY) {
	console.error("ERROR: RESEND_API_KEY is not set");
	process.exit(1);
}

if (!OPENROUTER_API_KEY) {
	console.error("ERROR: OPENROUTER_API_KEY_251025 or OPENAI_API_KEY is not set");
	process.exit(1);
}

interface ResendReceivedEmail {
	id: string;
	from: string;
	to: string[];
	subject: string;
	html?: string | null;
	text?: string | null;
	'createdAt': string;
}

interface ClassificationResult {
	emailId: string;
	success: boolean;
	error?: string;
	analysis?: {
		'entityType': string | null;
		confidence: number | null;
		'extractedData': Record<string, unknown> | null;
	};
	routing?: {
		success: boolean;
		action: string | null;
		'entityType': string | null;
		'entityId': string | null;
		message: string | null;
		error: string | null;
	};
}

async function unsupportedFetch(endpoint: string): Promise<never> {
	throw new Error(`Unsupported: fetch is disabled in hrse (${endpoint})`);
}

async function fetchResendEmails(limit: number = 10): Promise<ResendReceivedEmail[]> {
	console.log(`\n📧 Fetching emails from Resend API (limit: ${limit})...`);

	const url = `https://api.resend.com/emails/receiving?limit=${limit}`;
	const response = await unsupportedFetch(url);

	if (!response.ok) {
		const errorText = await response.text();
		throw new Error(`Resend API error: ${response.status} - ${errorText}`);
	}

	const resendResponse = await response.json();
	const emails = resendResponse.data || [];

	console.log(`✅ Fetched ${emails.length} emails`);
	return emails;
}

async function classifyEmails(emails: ResendReceivedEmail[]): Promise<ClassificationResult[]> {
	console.log(`\n🤖 Classifying ${emails.length} emails...`);

	// ローカルサーバーが起動している場合、APIエンドポイントを使用
	// そうでない場合は直接LLMサービスを使用
	const useApiEndpoint = process.env.USE_API_ENDPOINT === "true";

	if (useApiEndpoint) {
		// APIエンドポイントを使用（認証が必要な場合はスキップ）
		try {
			const response = await unsupportedFetch(`${APP_URL}/api/admin/classify-emails`);

			if (response.ok) {
				const result = await response.json();
				return result.results || [];
			}
		} catch (error) {
			console.warn("⚠️  API endpoint not available, using direct classification");
		}
	}

	// 直接LLMサービスを使用（開発用）
	const { analyzeEmail } = await import("../src/lib/services/email-analyzer");
	const { routeRecord } = await import("../src/lib/services/record-router");
	const { EmailContent } = await import("../src/lib/services/email-analyzer");

	const results: ClassificationResult[] = [];

	for (const email of emails) {
		try {
			const emailContent: EmailContent = {
				from: email.from || "",
				to: Array.isArray(email.to) ? email.to[0] || "" : email.to || "",
				subject: email.subject || "",
				html: email.html || null,
				text: email.text || null,
				date: email.createdAt || new Date().toISOString(),
			};

			const analysisResult = await analyzeEmail(emailContent);

			if (!analysisResult.success) {
				results.push({
					emailId: email.id,
					success: false,
					error: analysisResult.error || "Analysis failed",
				});
				continue;
			}

			const routingResult = await routeRecord(analysisResult);

			results.push({
				emailId: email.id,
				success: true,
				analysis: {
					'entityType': analysisResult.entityType,
					confidence: analysisResult.confidence,
					'extractedData': analysisResult.extractedData,
				},
				routing: {
					success: routingResult.success,
					action: routingResult.action,
					'entityType': routingResult.entityType,
					'entityId': routingResult.entityId,
					message: routingResult.message,
					error: routingResult.error,
				},
			});
		} catch (error) {
			results.push({
				emailId: email.id,
				success: false,
				error: error instanceof Error ? error.message : "Unknown error",
			});
		}
	}

	return results;
}

function printResults(results: ClassificationResult[], emails: ResendReceivedEmail[]) {
	console.log("\n" + "=".repeat(80));
	console.log("📊 Classification Results");
	console.log("=".repeat(80));

	const successCount = results.filter((r) => r.success).length;
	const failureCount = results.filter((r) => !r.success).length;

	console.log(`\n✅ Success: ${successCount}`);
	console.log(`❌ Failed: ${failureCount}`);
	console.log(`📧 Total: ${results.length}`);

	console.log("\n" + "-".repeat(80));

	for (let i = 0; i < results.length; i++) {
		const result = results[i];
		const email = emails.find((e) => e.id === result.emailId);

		console.log(`\n📧 Email ${i + 1}:`);
		console.log(`   ID: ${result.emailId}`);
		console.log(`   From: ${email?.from || "N/A"}`);
		console.log(`   Subject: ${email?.subject || "N/A"}`);

		if (result.success) {
			console.log(`   ✅ Status: Success`);
			if (result.analysis) {
				console.log(`   📋 Entity Type: ${result.analysis.entityType || "N/A"}`);
				console.log(`   📊 Confidence: ${((result.analysis.confidence || 0) * 100).toFixed(1)}%`);
			}
			if (result.routing) {
				console.log(`   🔀 Routing Action: ${result.routing.action || "N/A"}`);
				if (result.routing.entityId) {
					console.log(`   🆔 Entity ID: ${result.routing.entityId}`);
				}
				if (result.routing.error) {
					console.log(`   ⚠️  Routing Error: ${result.routing.error}`);
				}
			}
		} else {
			console.log(`   ❌ Status: Failed`);
			console.log(`   ⚠️  Error: ${result.error || "Unknown error"}`);
		}
		console.log("-".repeat(80));
	}
}

async function main() {
	try {
		console.log("🚀 Starting email classification test...");
		console.log(`📌 Using OpenRouter API: ${!!process.env.OPENROUTER_API_KEY_251025}`);

		// Resendからメールを取得
		const emails = await fetchResendEmails(10);

		if (emails.length === 0) {
			console.log("⚠️  No emails found in Resend");
			return;
		}

		// メールを分類
		const results = await classifyEmails(emails);

		// 結果を表示
		printResults(results, emails);

		console.log("\n✅ Classification test completed!");
	} catch (error) {
		console.error("\n❌ Error:", error);
		process.exit(1);
	}
}

main();
