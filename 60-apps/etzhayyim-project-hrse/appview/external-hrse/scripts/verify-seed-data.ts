#!/usr/bin/env tsx
/**
 * @etzhayyim/etzhayyim-hrse#VerifySeedData
 * Seedデータの投入状況を確認するスクリプト
 */

import { config } from "dotenv";
import { existsSync } from "node:fs";
// CHARTER-VIOLATION §substrate (ADR-2605172000) — operational script; migrate to MST PDS write path before Council ratifies ETZHAYYIM_SUBSTRATE_MODE=mst.
import postgres from "postgres";

// 本番環境では環境変数が直接設定されているため、.env.localは読み込まない
if (process.env.NODE_ENV !== "production" && existsSync(".env.local")) {
	config({ path: ".env.local" });
}

// .env.productionから読み込む
if (existsSync(".env.production")) {
	config({ path: ".env.production" });
}

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
	console.error("❌ DATABASE_URL environment variable is not set");
	process.exit(1);
}

const client = postgres(DATABASE_URL);

const tables = [
	"nationalities",
	"workPermits",
	"securityCertifications",
	"specializations",
	"workingLanguages",
	"skills",
	"trainings",
	"courses",
	"resources",
	"performers",
];

async function main() {
	console.log("🔍 Verifying seed data in production database...\n");

	try {
		for (const table of tables) {
			try {
				const result = await client`SELECT COUNT(*) as count FROM ${client(table)}`;
				const count = Number(result[0]?.count || 0);
				if (count > 0) {
					console.log(`  ✅ ${table}: ${count} records`);
				} else {
					console.log(`  ⚠️  ${table}: 0 records (needs seed)`);
				}
			} catch (error) {
				if (error instanceof Error && error.message.includes("does not exist")) {
					console.log(`  ❌ ${table}: table not found`);
				} else {
					console.log(`  ❌ ${table}: error - ${error instanceof Error ? error.message : String(error)}`);
				}
			}
		}

		console.log("\n✅ Seed verification completed!");
	} catch (error) {
		console.error("❌ Verification failed:", error);
		process.exit(1);
	} finally {
		await client.end();
	}
}

main();
