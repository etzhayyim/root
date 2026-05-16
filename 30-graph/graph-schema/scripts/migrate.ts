#!/usr/bin/env node
/**
 * Kysely migration runner for @gftd/graph-schema.
 *
 * Replaces the archived Python `apply-migrations.py`. Uses the kysely
 * `Migrator` + `FileMigrationProvider` so migrations run as real TypeScript
 * modules against RisingWave over the PostgreSQL wire protocol.
 *
 * Usage:
 *   DATABASE_URL=postgres://user:pass@host:port/db node --loader=ts-node/esm scripts/migrate.ts
 *   DATABASE_URL=... pnpm db:migrate                       # → latest
 *   DATABASE_URL=... pnpm db:migrate up                    # → one step up
 *   DATABASE_URL=... pnpm db:migrate down                  # → one step down
 *   DATABASE_URL=... pnpm db:migrate to 20260415130900_xlsx_core_graph # → specific
 *   DATABASE_URL=... pnpm db:migrate list                  # → status only
 *
 * The default target for the `pnpm db:migrate` alias is `latest`.
 *
 * Migrations live next to this script in `../migrations/*.ts` and must
 * export `up(db)` and `down(db)`. New filenames are timestamp-based
 * (`YYYYMMDDHHMMSS_name.ts`). Legacy sequential filenames remain for
 * history integrity and still sort correctly before the timestamp era.
 */

import * as path from 'node:path';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import {
  Kysely,
  Migrator,
  FileMigrationProvider,
  PostgresDialect,
  PostgresAdapter,
  sql,
} from 'kysely';
import { Pool } from 'pg';

/**
 * RisingWave-specific Kysely adapter.
 *
 * Two differences from the vanilla Postgres adapter:
 *
 * 1. `pg_advisory_xact_lock` / `pg_advisory_unlock` are not implemented by
 *    RisingWave, so the default `acquireMigrationLock` fails with an
 *    "Expr error: Failed to bind expression" catalog error. We run a
 *    single migrator instance at a time, so safely no-op both hooks.
 *
 * 2. Kysely's internal bootstrap for `kysely_migration` uses
 *    `VARCHAR(255)`, which RisingWave rejects. We pre-create the
 *    bookkeeping tables ourselves in `ensureKyselyMigrationTables`
 *    (see below) so the adapter-level DDL is a no-op by the time
 *    Migrator.migrateToLatest runs.
 */
class RisingWaveAdapter extends PostgresAdapter {
  override async acquireMigrationLock(): Promise<void> { /* no-op */ }
  override async releaseMigrationLock(): Promise<void> { /* no-op */ }
}

class RisingWaveDialect extends PostgresDialect {
  override createAdapter(): PostgresAdapter { return new RisingWaveAdapter(); }
}

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const migrationsFolder = path.resolve(__dirname, '..', 'migrations');

type Command = 'latest' | 'up' | 'down' | 'to' | 'list';

interface ParsedArgs {
  command: Command;
  target?: string;
}

const migrateDebug = process.env.GFTD_MIGRATE_DEBUG === '1';
const migrateTimeoutMs = (() => {
  const raw = process.env.GFTD_MIGRATE_TIMEOUT_MS;
  if (!raw) return 180_000;
  const n = Number(raw);
  return Number.isFinite(n) && n > 0 ? Math.floor(n) : 180_000;
})();

function logStep(step: string): void {
  if (migrateDebug) {
    console.error(`[migrate-debug] ${new Date().toISOString()} ${step}`);
  }
}

async function withTimeout<T>(label: string, fn: () => Promise<T>): Promise<T> {
  return await Promise.race([
    fn(),
    new Promise<never>((_, reject) => {
      setTimeout(() => {
        reject(new Error(`${label} timed out after ${migrateTimeoutMs}ms (set GFTD_MIGRATE_TIMEOUT_MS to override)`));
      }, migrateTimeoutMs);
    }),
  ]);
}

function parseArgs(argv: string[]): ParsedArgs {
  const [cmd, target] = argv;
  const c = (cmd ?? 'latest') as Command;
  if (!['latest', 'up', 'down', 'to', 'list'].includes(c)) {
    console.error(`unknown command: ${cmd}`);
    process.exit(2);
  }
  if (c === 'to' && !target) {
    console.error(`'to' command requires a migration name (e.g. 20260415130900_xlsx_core_graph)`);
    process.exit(2);
  }
  return { command: c, target };
}

function newMigrator(): { db: Kysely<unknown>; migrator: Migrator } {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('DATABASE_URL is required (postgres://user:pass@host:port/db)');
    process.exit(2);
  }
  const db = new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 4 }),
    }),
  });
  // Wrap fs so FileMigrationProvider ignores `*.test.ts` vitest snapshot
  // files that live next to real migrations. Without the filter, kysely
  // tries to import them and dies at `describe(...)` outside the vitest
  // runtime (observed 2026-04-24: migrations/20260423180000_...test.ts
  // crashing `db:migrate` with `Cannot read properties of undefined
  // (reading 'config')` from @vitest/runner).
  const filteredFs = {
    ...fs,
    readdir: async (p: string) => {
      const entries = await fs.readdir(p);
      return entries.filter((name: string) => !name.endsWith('.test.ts'));
    },
  };
  const migrator = new Migrator({
    db,
    provider: new FileMigrationProvider({
      fs: filteredFs,
      path,
      migrationFolder: migrationsFolder,
    }),
    // Prod migration log has legacy `000N_` names interleaved with
    // timestamp-based names (out-of-order out-of-band applies). Kysely's
    // default strict ordering refuses to run in that state; allowing
    // unordered migrations lets new timestamp files apply regardless.
    allowUnorderedMigrations: true,
  });
  return { db, migrator };
}

/**
 * Pre-create Kysely's bookkeeping tables (`kysely_migration`,
 * `kysely_migration_lock`) with RisingWave-compatible unbounded VARCHAR.
 * Kysely's internal `#createIfNotExists` uses `VARCHAR(255)` which RW
 * rejects, so we head it off here.
 */
async function ensureKyselyMigrationTables(db: Kysely<unknown>): Promise<void> {
  logStep('ensure:start');
  // RisingWave defaults to eventual visibility for batch writes.
  // Force read-after-write semantics for migration bookkeeping.
  logStep('ensure:set-implicit-flush:start');
  await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
  logStep('ensure:set-implicit-flush:done');

  logStep('ensure:create-migration:start');
  await sql`CREATE TABLE IF NOT EXISTS "kysely_migration" (
    "name" VARCHAR NOT NULL PRIMARY KEY,
    "timestamp" VARCHAR NOT NULL
  )`.execute(db);
  logStep('ensure:create-migration:done');
  logStep('ensure:create-lock:start');
  await sql`CREATE TABLE IF NOT EXISTS "kysely_migration_lock" (
    "id" VARCHAR NOT NULL PRIMARY KEY,
    "is_locked" INTEGER NOT NULL DEFAULT 0
  )`.execute(db);
  logStep('ensure:create-lock:done');
  logStep('ensure:seed-lock:start');
  await sql`INSERT INTO "kysely_migration_lock" ("id", "is_locked")
    SELECT 'migration_lock', 0
    WHERE NOT EXISTS (SELECT 1 FROM "kysely_migration_lock" WHERE "id" = 'migration_lock')`.execute(db);
  logStep('ensure:seed-lock:done');

  // Ensure bootstrap DDL/seed row is visible before migrator state checks.
  logStep('ensure:flush:start');
  await sql`FLUSH`.execute(db);
  logStep('ensure:flush:done');
  logStep('ensure:done');
}

function printResults(results: Awaited<ReturnType<Migrator['migrateToLatest']>>['results']): void {
  for (const r of results ?? []) {
    const icon = r.status === 'Success' ? '✓' : r.status === 'Error' ? '✗' : '·';
    console.log(`  ${icon} ${r.migrationName} [${r.direction} ${r.status}]`);
  }
}

async function run(): Promise<void> {
  logStep('run:start');
  const { command, target } = parseArgs(process.argv.slice(2));
  logStep(`args:command=${command}${target ? ` target=${target}` : ''}`);
  const { db, migrator } = newMigrator();
  logStep('db:newMigrator:done');

  try {
    await ensureKyselyMigrationTables(db);

    if (command === 'list') {
      logStep('list:fallback:start');
      // Match the filter FileMigrationProvider sees (above) — skip
      // vitest snapshot files so they don't show up as stray "pending"
      // entries in the list output.
      const files = (await fs.readdir(migrationsFolder))
        .filter((name) => name.endsWith('.ts') && !name.endsWith('.test.ts'))
        .map((name) => name.slice(0, -3))
        .sort();
      const executedRes = await sql<{ name: string; timestamp: string }>`
        SELECT "name", "timestamp"
        FROM "kysely_migration"
      `.execute(db);
      const executed = new Map<string, string>();
      for (const row of executedRes.rows) {
        executed.set(row.name, row.timestamp);
      }
      for (const name of files) {
        const ts = executed.get(name);
        const state = ts ? `applied@${ts}` : 'pending';
        console.log(`  ${name} — ${state}`);
      }
      logStep(`list:fallback:done count=${files.length}`);
      logStep('list:return');
      return;
    }

    logStep('migrate:run:start');
    const { error, results } = await withTimeout(`migrate:${command}`, async () =>
      command === 'latest' ? await migrator.migrateToLatest()
      : command === 'up'   ? await migrator.migrateUp()
      : command === 'down' ? await migrator.migrateDown()
      :                      await migrator.migrateTo(target!)
    );
    logStep('migrate:run:done');

    printResults(results);

    await sql`FLUSH`.execute(db);
    logStep('post-migrate:flush:done');

    if (error) {
      console.error('migration failed:', error);
      process.exit(1);
    }
    console.log(`[migrate] ${command}${target ? ` → ${target}` : ''} complete`);
  } finally {
    logStep('db:destroy:start');
    await db.destroy();
    logStep('db:destroy:done');
  }
}

run().catch((e) => {
  console.error(e);
  process.exit(1);
});
