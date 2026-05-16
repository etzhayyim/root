#!/usr/bin/env node
/**
 * Like run-one-migration.mjs but uses simple query protocol (no prepared
 * statements) to work around RisingWave's inability to infer BIGINT for
 * untyped $N parameters.  Inlines $N parameters as SQL literals before
 * sending, so no extended query Parse message is issued.
 *
 * Usage:
 *   DATABASE_URL=... node scripts/apply-simple.mjs <name1> [<name2> ...]
 */
import { Kysely, PostgresAdapter, PostgresDialect } from 'kysely';
import pg from 'pg';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { register } from 'node:module';

register('ts-node/esm', pathToFileURL('./'));

const __dirname = path.dirname(fileURLToPath(import.meta.url));

function inlineParams(sql, params) {
  if (!params || params.length === 0) return sql;
  return sql.replace(/\$(\d+)/g, (_, idx) => {
    const val = params[parseInt(idx, 10) - 1];
    if (val === null || val === undefined) return 'NULL';
    if (typeof val === 'number') return String(val);
    if (typeof val === 'boolean') return val ? 'TRUE' : 'FALSE';
    return "'" + String(val).replace(/'/g, "''") + "'";
  });
}

function patchClient(client) {
  const origQuery = client.query.bind(client);
  client.query = function (textOrConfig, valuesOrCallback, callback) {
    if (textOrConfig && typeof textOrConfig === 'object' && Array.isArray(textOrConfig.values) && textOrConfig.values.length > 0) {
      const inlined = inlineParams(textOrConfig.text, textOrConfig.values);
      return origQuery({ ...textOrConfig, text: inlined, values: undefined }, valuesOrCallback);
    }
    if (typeof textOrConfig === 'string' && Array.isArray(valuesOrCallback) && valuesOrCallback.length > 0) {
      const inlined = inlineParams(textOrConfig, valuesOrCallback);
      return origQuery(inlined, undefined, callback);
    }
    return origQuery(textOrConfig, valuesOrCallback, callback);
  };
  return client;
}

class SimplePool extends pg.Pool {
  async connect() {
    const client = await super.connect();
    return patchClient(client);
  }
}

class RisingWaveAdapter extends PostgresAdapter {
  async acquireMigrationLock() {}
  async releaseMigrationLock() {}
}
class RisingWaveDialect extends PostgresDialect {
  createAdapter() { return new RisingWaveAdapter(); }
}

const url = process.env.DATABASE_URL;
if (!url) { console.error('DATABASE_URL required'); process.exit(2); }

async function rawQuery(pool, sql) {
  const client = await pool.connect();
  try { await client.query(sql); } finally { client.release(); }
}

async function applyOne(name) {
  const pool = new SimplePool({ connectionString: url, max: 2 });
  const db = new Kysely({ dialect: new RisingWaveDialect({ pool }) });

  try {
    await rawQuery(pool, 'SET RW_IMPLICIT_FLUSH = true');

    const existing = await db
      .selectFrom('kysely_migration')
      .select('name')
      .where('name', '=', name)
      .executeTakeFirst();
    if (existing) {
      console.log('[apply-simple] ' + name + ' already registered — skip');
      return;
    }

    const migrationPath = path.resolve(__dirname, '..', 'migrations', name + '.ts');
    const mod = await import(pathToFileURL(migrationPath).href);
    if (typeof mod.up !== 'function') throw new Error(name + ' has no up()');

    console.log('[apply-simple] up() ' + name);
    await mod.up(db);
    await rawQuery(pool, 'FLUSH');

    const ts = new Date().toISOString();
    await db.insertInto('kysely_migration').values({ name, timestamp: ts }).execute();
    await rawQuery(pool, 'FLUSH');

    console.log('[apply-simple] ' + name + ' done @ ' + ts);
  } catch (e) {
    console.error('[apply-simple] FAILED ' + name + ':', e.message || e);
    throw e;
  } finally {
    await db.destroy();
  }
}

const args = process.argv.slice(2);
if (args.length === 0) {
  console.error('usage: apply-simple.mjs <name> [<name>...]');
  process.exit(2);
}

let failed = 0;
for (const name of args) {
  try {
    await applyOne(name);
  } catch {
    failed++;
  }
}
process.exit(failed > 0 ? 1 : 0);
