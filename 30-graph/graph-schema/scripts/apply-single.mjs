#!/usr/bin/env node
/**
 * Out-of-band migration runner for a single file. Bypasses Kysely
 * Migrator's ordering checks (this DB has legacy 0xxx + timestamp
 * migrations mixed, see CLAUDE.md history for "Applied out-of-band via
 * psycopg2" precedent).
 *
 * Usage:
 *   DATABASE_URL=... node scripts/apply-single.mjs <migration_name_without_ts>
 */
import { Kysely, PostgresDialect, PostgresAdapter, sql } from 'kysely';
import { Pool } from 'pg';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

class RisingWaveAdapter extends PostgresAdapter {
  async acquireMigrationLock() {}
  async releaseMigrationLock() {}
}
class RisingWaveDialect extends PostgresDialect {
  createAdapter() { return new RisingWaveAdapter(); }
}

const name = process.argv[2];
if (!name) { console.error('usage: apply-single.mjs <migration_name>'); process.exit(2); }

const url = process.env.DATABASE_URL;
if (!url) { console.error('DATABASE_URL required'); process.exit(2); }

const db = new Kysely({
  dialect: new RisingWaveDialect({ pool: new Pool({ connectionString: url, max: 2 }) }),
});

try {
  if (process.env.RW_APPLY_SINGLE_IMPLICIT_FLUSH === '0') {
    await sql`SET RW_IMPLICIT_FLUSH = false`.execute(db);
  } else {
    await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
  }

  // Bootstrap bookkeeping tables (idempotent).
  await sql`CREATE TABLE IF NOT EXISTS "kysely_migration" (
    "name" VARCHAR NOT NULL PRIMARY KEY,
    "timestamp" VARCHAR NOT NULL
  )`.execute(db);

  // Check if already applied.
  const existing = await sql`
    SELECT "name" FROM "kysely_migration" WHERE "name" = ${name}
  `.execute(db);
  if (existing.rows.length > 0) {
    console.log(`[apply-single] ${name} already in kysely_migration — nothing to do`);
    process.exit(0);
  }

  // Load + run up().
  const migrationPath = path.resolve(__dirname, '..', 'migrations', `${name}.ts`);
  const mod = await import(pathToFileURL(migrationPath).href);
  if (typeof mod.up !== 'function') {
    console.error(`migration module ${name}.ts has no up() export`);
    process.exit(2);
  }

  console.log(`[apply-single] running up() for ${name}`);
  await mod.up(db);
  if (process.env.RW_APPLY_SINGLE_FLUSH !== '0') {
    await sql`FLUSH`.execute(db);
  }

  // Record in kysely_migration.
  const ts = new Date().toISOString();
  await sql`
    INSERT INTO "kysely_migration" ("name", "timestamp") VALUES (${name}, ${ts})
  `.execute(db);
  if (process.env.RW_APPLY_SINGLE_FLUSH !== '0') {
    await sql`FLUSH`.execute(db);
  }

  console.log(`[apply-single] ${name} applied @ ${ts}`);
} catch (e) {
  console.error('[apply-single] failed:', e);
  process.exit(1);
} finally {
  await db.destroy();
}
