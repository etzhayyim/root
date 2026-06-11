#!/usr/bin/env tsx
/**
 * ローカル動作検証スクリプト: Resend Email Sync Cron Job
 *
 * 使用方法:
 *   export RESEND_API_KEY="yourKey"
 *   export OPENROUTER_API_KEY_251025="yourKey"
 *   export CRON_SECRET="testSecret"
 *   export NEXT_PUBLIC_APP_URL="http://localhost:3000"
 *   pnpm tsx scripts/test-cron-resend-email-sync.ts
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
const CRON_SECRET = process.env.CRON_SECRET || "testSecret";
const APP_URL = process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000";

if (!RESEND_API_KEY) {
	console.error("ERROR: RESEND_API_KEY is not set");
	process.exit(1);
}

if (!OPENROUTER_API_KEY) {
	console.error("ERROR: OPENROUTER_API_KEY_251025 or OPENAI_API_KEY is not set");
	process.exit(1);
}

async function unsupportedFetch(endpoint: string): Promise<never> {
	throw new Error(`Unsupported: fetch is disabled in hrse (${endpoint})`);
}

async function testCronJob() {
	console.log("🚀 Starting Resend Email Sync Cron Job Test");
	console.log(`📌 App URL: ${APP_URL}`);
	console.log(`📌 Using OpenRouter API: ${!!process.env.OPENROUTER_API_KEY_251025}`);
	console.log("");

	try {
		// APIエンドポイントを呼び出し
		const url = `${APP_URL}/api/cron/resend-email-sync`;
		console.log(`📡 Calling: ${url}`);

		const response = await unsupportedFetch(url);

		const status = response.status;
		const data = await response.json();

		console.log(`\n📊 Response Status: ${status}`);
		console.log("📋 Response Body:");
		console.log(JSON.stringify(data, null, 2));

		if (status === 200 && data.success) {
			console.log("\n✅ Cron job executed successfully!");
			console.log(`   - Processed: ${data.processed}`);
			console.log(`   - Skipped: ${data.skipped}`);
			console.log(`   - Errors: ${data.errors}`);

			if (data.results && data.results.length > 0) {
				console.log("\n📧 Email Processing Results:");
				data.results.slice(0, 5).forEach((result: { emailId: string; status: string; error?: string }, index: number) => {
					console.log(`   ${index + 1}. Email ${result.emailId}: ${result.status}`);
					if (result.error) {
						console.log(`      Error: ${result.error}`);
					}
				});
				if (data.results.length > 5) {
					console.log(`   ... and ${data.results.length - 5} more`);
				}
			}
		} else if (status === 401) {
			console.error("\n❌ Authentication failed. Check CRON_SECRET environment variable.");
			console.error("   Expected: Authorization header with Bearer token");
		} else {
			console.error("\n❌ Cron job failed");
			console.error(`   Status: ${status}`);
			console.error(`   Error: ${data.error || data.message || "Unknown error"}`);
		}

		process.exit(status === 200 && data.success ? 0 : 1);
	} catch (error) {
		console.error("\n❌ Error executing cron job:", error);
		if (error instanceof Error) {
			console.error(`   Message: ${error.message}`);
			console.error(`   Stack: ${error.stack}`);
		}
		process.exit(1);
	}
}

testCronJob();
