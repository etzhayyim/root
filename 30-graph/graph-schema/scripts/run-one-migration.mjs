#!/usr/bin/env node
// One-off runner: apply a single migration's up() bypassing kysely migrator's
// missing-history guard. Mirrors the "applied out-of-band via psql" pattern
// documented in CLAUDE.md, then inserts the kysely_migration row.
import { Kysely, PostgresDialect } from 'kysely';
import pg from 'pg';
import { register } from 'node:module';
import { pathToFileURL } from 'node:url';

register('ts-node/esm', pathToFileURL('./'));

const name = process.argv[2];
if (!name) {
  console.error('usage: run-one-migration.mjs <migration-name-without-extension>');
  process.exit(1);
}

const url = process.env.DATABASE_URL;
if (!url) throw new Error('DATABASE_URL required');

const pool = new pg.Pool({ connectionString: url, max: 4 });
const db = new Kysely({ dialect: new PostgresDialect({ pool }) });

try {
  const mod = await import(`../migrations/${name}.ts`);
  if (typeof mod.up !== 'function') throw new Error(`${name} has no up()`);
  console.log(`[apply] ${name}.up()`);
  await mod.up(db);
  console.log(`[apply] ${name} up() complete`);

  // Record in kysely_migration so future migrator runs stay consistent.
  // RisingWave does not parse `ON CONFLICT` in raw SQL, so check-then-insert.
  const existing = await db
    .selectFrom('kysely_migration')
    .select('name')
    .where('name', '=', name)
    .executeTakeFirst();
  if (!existing) {
    await db
      .insertInto('kysely_migration')
      .values({ name, timestamp: new Date().toISOString() })
      .execute();
    console.log(`[apply] kysely_migration row recorded`);
  } else {
    console.log(`[apply] kysely_migration row already present — skip`);
  }
} catch (err) {
  console.error('[apply] ERROR:', err);
  process.exitCode = 1;
} finally {
  await db.destroy();
}
