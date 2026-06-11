#!/usr/bin/env tsx
/**
 * @etzhayyim/cyber-freelance#CheckEnv
 * ビルド前に必要な環境変数が設定されているかチェック
 */

import { config } from "dotenv";
import { resolve } from "path";

// .env.localファイルを読み込む
config({ path: resolve(process.cwd(), ".env.local") });
// .envファイルも読み込む（フォールバック）
config({ path: resolve(process.cwd(), ".env") });

const requiredEnvVars = [
	{
		name: "NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY",
		description: "Clerk Publishable Key (required for authentication)",
		required: true,
	},
	{
		name: "CLERK_SECRET_KEY",
		description: "Clerk Secret Key (required for authentication)",
		required: true,
	},
] as const;

const optionalEnvVars = [
	{
		name: "DATABASE_URL",
		description: "Database connection URL",
		required: false,
	},
] as const;

function checkEnvVars() {
	const missing: string[] = [];
	const warnings: string[] = [];

	console.log("🔍 Checking required environment variables...\n");

	// Check required environment variables
	for (const envVar of requiredEnvVars) {
		const value = process.env[envVar.name];
		if (!value || value.trim() === "") {
			missing.push(envVar.name);
			console.error(`❌ ${envVar.name}: ${envVar.description}`);
		} else {
			// Mask sensitive values
			const maskedValue =
				envVar.name.includes("SECRET") || envVar.name.includes("KEY")
					? `${value.substring(0, 10)}...`
					: value;
			console.log(`✅ ${envVar.name}: ${maskedValue}`);
		}
	}

	console.log("\n📋 Checking optional environment variables...\n");

	// Check optional environment variables
	for (const envVar of optionalEnvVars) {
		const value = process.env[envVar.name];
		if (!value || value.trim() === "") {
			warnings.push(envVar.name);
			console.warn(`⚠️  ${envVar.name}: ${envVar.description} (optional)`);
		} else {
			const maskedValue =
				envVar.name.includes("SECRET") ||
				envVar.name.includes("KEY") ||
				envVar.name.includes("DATABASE_URL") ||
				envVar.name.includes("PASSWORD")
					? "設定済み（値は非表示）"
					: value;
			console.log(`✅ ${envVar.name}: ${maskedValue}`);
		}
	}

	if (missing.length > 0) {
		console.error("\n❌ Build failed: Missing required environment variables:");
		missing.forEach((name) => {
			console.error(`   - ${name}`);
		});
		console.error(
			"\n💡 Please set the required environment variables before building.",
		);
		console.error(
			"   For Vercel: Use 'vercel env add <VAR_NAME> production'",
		);
		console.error(
			"   For local: Create .env.local file with required variables",
		);
		process.exit(1);
	}

	if (warnings.length > 0) {
		console.warn(
			`\n⚠️  Warning: ${warnings.length} optional environment variable(s) not set.`,
		);
		console.warn("   The application may not function correctly without these.");
	}

	console.log("\n✅ All required environment variables are set!");
}

checkEnvVars();
