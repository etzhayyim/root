#!/usr/bin/env node
/**
 * Generate `src/database.ts` from live RisingWave `information_schema`.
 *
 * Kysely best practice: the DB is the source of truth for column names,
 * types, and nullability. Hand-maintaining TS row interfaces alongside
 * DDL invariably drifts (observed 2026-04-17: 279 tables missing, 47
 * stale, 29 column-level diffs). This generator makes the live DB the
 * SSoT and runs every time schema changes.
 *
 * Usage:
 *   DATABASE_URL=postgres://user:pass@host:4566/db \
 *     node --loader=ts-node/esm scripts/gen-database-ts.ts
 *
 * Writes to `src/database.ts` (overwrites). Commit the result.
 * Verify with `pnpm db:drift` (should report OK).
 *
 * Naming conventions (preserve existing):
 *   vertex_actor           -> VertexActorRow
 *   edge_follows           -> EdgeFollowsRow
 *   mv_actor_social_stats  -> MvActorSocialStatsRow
 *   view_cc_page_canonical -> ViewCcPageCanonicalRow
 *   (other)                -> <PascalCase>Row
 *
 * Type mapping (RisingWave / Postgres -> TS):
 *   varchar, text, character, char            -> string
 *   bigint, int8                              -> number | bigint
 *   integer, int, int4, smallint, int2        -> number
 *   double precision, real, numeric, decimal  -> number
 *   boolean, bool                             -> boolean
 *   date                                      -> Date | string
 *   timestamp*                                -> Date | string
 *   json, jsonb, struct                       -> unknown
 *   bytea                                     -> Uint8Array
 *   anything else                             -> string  (safe default)
 *
 * Nullability: all columns emitted as `?: T | null` to match the existing
 * loose style (INSERT-friendly; RisingWave rarely enforces NOT NULL on
 * MV/view columns anyway).
 */

import * as path from 'node:path';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const outPath = path.resolve(__dirname, '..', 'src', 'database.ts');

interface Col {
  table_name: string;
  table_type: 'BASE TABLE' | 'VIEW' | 'MATERIALIZED VIEW';
  column_name: string;
  data_type: string;
  is_nullable: 'YES' | 'NO';
  ordinal_position: number;
}

function pascal(s: string): string {
  return s
    .split(/[_\s]+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join('');
}

function typeName(table: string): string {
  return `${pascal(table)}Row`;
}

function mapType(dataType: string): string {
  const t = dataType.toLowerCase();
  if (t.includes('varchar') || t === 'text' || t === 'character' || t === 'char' || t.startsWith('character varying')) {
    return 'string';
  }
  if (t === 'bigint' || t === 'int8') return 'number | bigint';
  if (t === 'integer' || t === 'int' || t === 'int4' || t === 'smallint' || t === 'int2') {
    return 'number';
  }
  if (
    t.includes('double precision') ||
    t === 'real' ||
    t === 'float4' ||
    t === 'float8' ||
    t.startsWith('numeric') ||
    t.startsWith('decimal')
  ) {
    return 'number';
  }
  if (t === 'boolean' || t === 'bool') return 'boolean';
  if (t === 'date') return 'Date | string';
  if (t.startsWith('timestamp')) return 'Date | string';
  if (t === 'json' || t === 'jsonb' || t.startsWith('struct')) return 'unknown';
  if (t === 'bytea') return 'Uint8Array';
  return 'string';
}

async function loadColumns(url: string): Promise<Col[]> {
  const pool = new Pool({ connectionString: url, max: 2 });
  try {
    const { rows } = await pool.query<Col>(`
      SELECT
        c.table_name,
        t.table_type,
        c.column_name,
        c.data_type,
        c.is_nullable,
        c.ordinal_position
      FROM information_schema.columns c
      JOIN information_schema.tables t
        ON t.table_schema = c.table_schema AND t.table_name = c.table_name
      WHERE c.table_schema = 'public'
        AND t.table_type IN ('BASE TABLE', 'VIEW', 'MATERIALIZED VIEW')
        AND c.table_name NOT LIKE 'kysely_migration%'
        AND c.table_name NOT LIKE 'rw_%'
      ORDER BY c.table_name, c.ordinal_position
    `);
    return rows;
  } finally {
    await pool.end();
  }
}

function render(cols: Col[]): string {
  const byTable = new Map<string, Col[]>();
  for (const c of cols) {
    if (!byTable.has(c.table_name)) byTable.set(c.table_name, []);
    byTable.get(c.table_name)!.push(c);
  }

  const tables = [...byTable.keys()].sort();
  const lines: string[] = [];

  lines.push(`/* eslint-disable */`);
  lines.push(`/**`);
  lines.push(` * Kysely database types for the etzhayyim graph DB (RisingWave).`);
  lines.push(` *`);
  lines.push(` * GENERATED FILE — do not edit by hand.`);
  lines.push(` * Regenerate with: DATABASE_URL=... pnpm db:gen`);
  lines.push(` * Verify with:    DATABASE_URL=... pnpm db:drift`);
  lines.push(` *`);
  lines.push(` * Source: live RisingWave \`information_schema.columns\`.`);
  lines.push(` * Schema SSoT is the DB itself; migrations under \`migrations/\` are the`);
  lines.push(` * only durable source of schema change. See \`CLAUDE.md\`.`);
  lines.push(` */`);
  lines.push(``);
  lines.push(`import type { ColumnType } from 'kysely';`);
  lines.push(``);
  lines.push(`// Silence unused-import warning when no generated column uses ColumnType.`);
  lines.push(`type _KeepColumnType = ColumnType<never, never, never>;`);
  lines.push(``);
  lines.push(`// --- Row interfaces (one per table / view / MV) ---`);
  lines.push(``);

  for (const table of tables) {
    const tcols = byTable.get(table)!;
    lines.push(`export interface ${typeName(table)} {`);
    for (const c of tcols) {
      const ts = mapType(c.data_type);
      // Quote identifier if it contains non-ident chars or is a reserved-like name.
      const needsQuote = !/^[A-Za-z_][A-Za-z0-9_]*$/.test(c.column_name);
      const key = needsQuote ? `'${c.column_name.replace(/'/g, "\\'")}'` : c.column_name;
      lines.push(`  ${key}?: ${ts} | null;`);
    }
    lines.push(`}`);
    lines.push(``);
  }

  lines.push(`// --- Database interface (table name -> Row type) ---`);
  lines.push(``);
  lines.push(`export interface Database {`);
  for (const table of tables) {
    const needsQuote = !/^[A-Za-z_][A-Za-z0-9_]*$/.test(table);
    const key = needsQuote ? `'${table.replace(/'/g, "\\'")}'` : table;
    lines.push(`  ${key}: ${typeName(table)};`);
  }
  lines.push(`}`);
  lines.push(``);

  return lines.join('\n');
}

async function main(): Promise<void> {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('DATABASE_URL is required (postgres://user:pass@host:4566/db)');
    process.exit(2);
  }
  const cols = await loadColumns(url);
  const out = render(cols);
  await fs.writeFile(outPath, out, 'utf8');
  const tables = new Set(cols.map((c) => c.table_name));
  console.error(`wrote ${outPath}: ${tables.size} tables, ${cols.length} columns, ${out.length} bytes`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
