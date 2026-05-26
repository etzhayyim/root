#!/usr/bin/env node
/**
 * Schema drift detector for @etzhayyim/graph-schema.
 *
 * Compares live RisingWave `information_schema` against the hand-managed
 * `src/database.ts` SSoT and reports:
 *
 *  - Tables/views in RW but missing from `Database` interface (out-of-band
 *    migrations that skipped step 2/3 of the workflow).
 *  - Tables in `Database` but missing from RW (stale TypeScript).
 *  - For each overlapping table, columns present on one side but not the
 *    other.
 *
 * Output is a punch list for a human to paste into `database.ts`. This
 * tool does NOT rewrite `database.ts` — `database.ts` is hand-managed SSoT
 * by convention (see CLAUDE.md §"How to Add a New Table"). Writing a
 * full generator would violate that rule.
 *
 * Usage:
 *   DATABASE_URL=postgres://user:pass@host:4566/dev \
 *     node --loader=ts-node/esm scripts/drift-detect.ts
 *
 *   # JSON output (for piping / tooling):
 *   DATABASE_URL=... node --loader=ts-node/esm scripts/drift-detect.ts --json
 */

import * as path from 'node:path';
import { promises as fs } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { Pool } from 'pg';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const databaseTsPath = path.resolve(__dirname, '..', 'src', 'database.ts');

type RwColumn = { table_name: string; column_name: string; data_type: string };

interface ParsedRowIface {
  typeName: string;
  columns: Set<string>;
}

async function loadRwSchema(url: string): Promise<Map<string, Set<string>>> {
  const pool = new Pool({ connectionString: url, max: 2 });
  try {
    // RisingWave exposes MVs as "MATERIALIZED VIEW" in information_schema.tables
    // (table_type = 'MATERIALIZED VIEW'); plain views as 'VIEW'.
    // We include all three so the detector covers tables + MVs + views.
    const { rows } = await pool.query<RwColumn>(`
      SELECT c.table_name, c.column_name, c.data_type
      FROM information_schema.columns c
      JOIN information_schema.tables t
        ON t.table_schema = c.table_schema AND t.table_name = c.table_name
      WHERE c.table_schema = 'public'
        AND t.table_type IN ('BASE TABLE', 'VIEW', 'MATERIALIZED VIEW')
      ORDER BY c.table_name, c.ordinal_position
    `);
    const byTable = new Map<string, Set<string>>();
    for (const r of rows) {
      if (!byTable.has(r.table_name)) byTable.set(r.table_name, new Set());
      byTable.get(r.table_name)!.add(r.column_name);
    }
    return byTable;
  } finally {
    await pool.end();
  }
}

function parseDatabaseTs(src: string): {
  tableToType: Map<string, string>;
  typeToColumns: Map<string, Set<string>>;
} {
  // Parse `Database` interface block: lines of the form `  table_name: TypeRow;`
  const tableToType = new Map<string, string>();
  const dbIfaceStart = src.indexOf('export interface Database {');
  if (dbIfaceStart === -1) throw new Error('Database interface not found in database.ts');
  const dbIfaceEnd = src.indexOf('\n}', dbIfaceStart);
  const dbBody = src.slice(dbIfaceStart, dbIfaceEnd);
  const dbRe = /^\s*([a-z_][a-z0-9_]*)\s*:\s*([A-Z][A-Za-z0-9_]*Row)\s*;/gm;
  let m: RegExpExecArray | null;
  while ((m = dbRe.exec(dbBody)) !== null) {
    tableToType.set(m[1], m[2]);
  }

  // Parse each `export interface XxxRow { ... }` block.
  const typeToColumns = new Map<string, Set<string>>();
  const ifaceRe = /export interface ([A-Z][A-Za-z0-9_]*Row)\s*\{([\s\S]*?)\n\}/g;
  while ((m = ifaceRe.exec(src)) !== null) {
    const typeName = m[1];
    const body = m[2];
    const cols = new Set<string>();
    // Column names may be snake_case or camelCase; quoted if exotic.
    const colRe = /^\s*'?([A-Za-z_][A-Za-z0-9_]*)'?\??:\s*/gm;
    let cm: RegExpExecArray | null;
    while ((cm = colRe.exec(body)) !== null) cols.add(cm[1]);
    typeToColumns.set(typeName, cols);
  }
  return { tableToType, typeToColumns };
}

interface Drift {
  tablesMissingFromTs: string[];
  tablesMissingFromRw: string[];
  columnDiffs: Array<{
    table: string;
    type: string;
    missingFromTs: string[];
    missingFromRw: string[];
  }>;
}

function diff(
  rw: Map<string, Set<string>>,
  tableToType: Map<string, string>,
  typeToColumns: Map<string, Set<string>>,
): Drift {
  const tablesMissingFromTs: string[] = [];
  const tablesMissingFromRw: string[] = [];
  const columnDiffs: Drift['columnDiffs'] = [];

  for (const table of rw.keys()) {
    if (table.startsWith('kysely_migration')) continue; // bookkeeping
    if (table.startsWith('rw_')) continue; // RW internal
    if (!tableToType.has(table)) tablesMissingFromTs.push(table);
  }
  for (const table of tableToType.keys()) {
    if (!rw.has(table)) tablesMissingFromRw.push(table);
  }
  for (const [table, typeName] of tableToType.entries()) {
    const rwCols = rw.get(table);
    const tsCols = typeToColumns.get(typeName);
    if (!rwCols || !tsCols) continue;
    const missingFromTs = [...rwCols].filter((c) => !tsCols.has(c));
    const missingFromRw = [...tsCols].filter((c) => !rwCols.has(c));
    if (missingFromTs.length || missingFromRw.length) {
      columnDiffs.push({ table, type: typeName, missingFromTs, missingFromRw });
    }
  }
  tablesMissingFromTs.sort();
  tablesMissingFromRw.sort();
  columnDiffs.sort((a, b) => a.table.localeCompare(b.table));
  return { tablesMissingFromTs, tablesMissingFromRw, columnDiffs };
}

function renderText(drift: Drift): string {
  const out: string[] = [];
  out.push(`# graph-schema drift report\n`);
  out.push(`Tables in RisingWave but missing from Database interface: ${drift.tablesMissingFromTs.length}`);
  for (const t of drift.tablesMissingFromTs) out.push(`  + ${t}`);
  out.push('');
  out.push(`Tables in Database interface but missing from RisingWave: ${drift.tablesMissingFromRw.length}`);
  for (const t of drift.tablesMissingFromRw) out.push(`  - ${t}`);
  out.push('');
  out.push(`Tables with column drift: ${drift.columnDiffs.length}`);
  for (const d of drift.columnDiffs) {
    out.push(`  ~ ${d.table} (${d.type})`);
    for (const c of d.missingFromTs) out.push(`      + RW has, TS missing: ${c}`);
    for (const c of d.missingFromRw) out.push(`      - TS has, RW missing: ${c}`);
  }
  out.push('');
  const clean =
    drift.tablesMissingFromTs.length === 0 &&
    drift.tablesMissingFromRw.length === 0 &&
    drift.columnDiffs.length === 0;
  out.push(clean ? 'OK: no drift detected.' : 'DRIFT: see above.');
  return out.join('\n');
}

async function main(): Promise<void> {
  const url = process.env.DATABASE_URL;
  if (!url) {
    console.error('DATABASE_URL is required (postgres://user:pass@host:4566/db)');
    process.exit(2);
  }
  const json = process.argv.includes('--json');

  const [rw, src] = await Promise.all([
    loadRwSchema(url),
    fs.readFile(databaseTsPath, 'utf8'),
  ]);
  const { tableToType, typeToColumns } = parseDatabaseTs(src);
  const drift = diff(rw, tableToType, typeToColumns);

  if (json) {
    console.log(JSON.stringify(drift, null, 2));
  } else {
    console.log(renderText(drift));
  }
  const hasDrift =
    drift.tablesMissingFromTs.length > 0 ||
    drift.tablesMissingFromRw.length > 0 ||
    drift.columnDiffs.length > 0;
  process.exit(hasDrift ? 1 : 0);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
