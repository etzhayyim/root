// @etzhayyim/etzhayyim-hrse#RunMigrations
// Vercel ビルド時にSQLマイグレーションを実行するスクリプト
// sqlx互換のマイグレーション管理

import { readdir, readFile, access } from "node:fs/promises";
import { join } from "node:path";
import { constants } from "node:fs";
// CHARTER-VIOLATION §substrate (ADR-2605172000) — operational script; migrate to MST PDS write path before Council ratifies ETZHAYYIM_SUBSTRATE_MODE=mst.
import postgres from "postgres";

const MIGRATIONS_DIR = join(
	process.cwd(),
	"scripts/migrations",
);

async function createMigrationsTable(sql: ReturnType<typeof postgres>): Promise<void> {
	await sql`
    CREATE TABLE IF NOT EXISTS _sqlx_migrations (
      version BIGINT PRIMARY KEY,
      description TEXT NOT NULL,
      installedOn TIMESTAMPTZ NOT NULL DEFAULT NOW(),
      success BOOLEAN NOT NULL DEFAULT TRUE,
      checksum TEXT NOT NULL DEFAULT '',
      executionTime BIGINT NOT NULL DEFAULT 0
    )
  `;
	console.log("✅ Migration table ensured");
}

async function getAppliedMigrations(
	sql: ReturnType<typeof postgres>,
): Promise<Set<string>> {
	const rows = await sql<{ version: string }[]>`
    SELECT version::TEXT as version FROM _sqlx_migrations WHERE success = TRUE
  `;
	return new Set(rows.map((r) => r.version));
}

async function getMigrationFiles(): Promise<string[]> {
	try {
		await access(MIGRATIONS_DIR, constants.F_OK);
	} catch (error) {
		console.log(`⚠️ Migrations directory not found: ${MIGRATIONS_DIR}`);
		return [];
	}

	const files = await readdir(MIGRATIONS_DIR);
	return files
		.filter((f) => f.endsWith(".sql"))
		.filter((f) => {
			const version = extractVersion(f);
			if (!version) {
				console.warn(`⚠️ Skipping migration file without version prefix: ${f}`);
				return false;
			}
			return true;
		})
		.sort();
}

function extractVersion(filename: string): string {
	const match = filename.match(/^(\d+)/);
	return match ? match[1] : "";
}

async function runMigration(
	sql: ReturnType<typeof postgres>,
	filename: string,
): Promise<void> {
	const version = extractVersion(filename);
	const description = filename.replace(/^\d+_/, "").replace(/\.sql$/, "");
	const filepath = join(MIGRATIONS_DIR, filename);

	console.log(`📦 Running migration: ${filename}`);

	const content = await readFile(filepath, "utf-8");
	const startTime = Date.now();

	try {
		await sql.begin(async (tx) => {
			await tx.unsafe(content);

			await tx`
        INSERT INTO _sqlx_migrations (version, description, success, checksum, executionTime)
        VALUES (${version}::BIGINT, ${description}, TRUE, '', ${Date.now() - startTime})
        ON CONFLICT (version) DO NOTHING
      `;
		});

		console.log(`✅ Migration ${filename} completed in ${Date.now() - startTime}ms`);
	} catch (error) {
		console.error(`❌ Migration ${filename} failed:`, error);
		throw error;
	}
}

async function main(): Promise<void> {
	const databaseUrl = process.env.DATABASE_URL;

	if (!databaseUrl) {
		console.log("⚠️ DATABASE_URL not set, skipping migrations");
		return;
	}

	console.log("🚀 Starting database migrations...");
	console.log(`📁 Migrations directory: ${MIGRATIONS_DIR}`);

	const sql = postgres(databaseUrl, {
		ssl: databaseUrl.includes("sslmode=require") || databaseUrl.includes("neon.tech") ? "require" : undefined,
		max: 1,
		'idleTimeout': 20,
		'connectTimeout': 30,
	});

	try {
		await createMigrationsTable(sql);

		const appliedMigrations = await getAppliedMigrations(sql);
		console.log(`📋 Already applied: ${appliedMigrations.size} migrations`);

		const migrationFiles = await getMigrationFiles();
		console.log(`📄 Found ${migrationFiles.length} migration files`);

		let pendingCount = 0;
		if (migrationFiles.length === 0) {
			console.log("⚠️ No migration files found, skipping migration execution");
		} else {
			for (const file of migrationFiles) {
				const version = extractVersion(file);
				if (!version) {
					console.warn(`⚠️ Skipping migration file without version: ${file}`);
					continue;
				}
				if (!appliedMigrations.has(version)) {
					await runMigration(sql, file);
					pendingCount++;
				}
			}

			if (pendingCount === 0) {
				console.log("✅ No pending migrations");
			} else {
				console.log(`✅ Applied ${pendingCount} migrations`);
			}
		}
	} catch (error) {
		console.error("❌ Migration failed:", error);
		process.exit(1);
	} finally {
		await sql.end();
	}

	console.log("🎉 Migrations completed successfully!");
}

main();
