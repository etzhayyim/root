#!/usr/bin/env node
/**
 * Materialize top-level appropriation rows as resource-flow edges.
 *
 * Source vertices are the budgetBook records; destination vertices are the
 * appropriation rows. This feeds mv_jp_fiscal_flow_by_actor_year.
 */

import {
  Kysely,
  PostgresAdapter,
  PostgresDialect,
  sql,
} from 'kysely';
import { Pool } from 'pg';

interface AppropriationRow {
  vertex_id: string;
  fiscal_year: number;
  account_type: string;
  doc_type: string;
  ministry_did: string;
  program_code: string;
  program_name: string | null;
  amount_jpy: string;
  source_url: string | null;
  source_id: string | null;
  document_id: string | null;
}

class RisingWaveAdapter extends PostgresAdapter {
  override async acquireMigrationLock(): Promise<void> {}
  override async releaseMigrationLock(): Promise<void> {}
}

class RisingWaveDialect extends PostgresDialect {
  override createAdapter(): PostgresAdapter {
    return new RisingWaveAdapter();
  }
}

function parseArgs(argv: string[]): { apply: boolean; fiscalYear: number; accountType: string; docType: string } {
  let apply = false;
  let fiscalYear = 2025;
  let accountType = 'general';
  let docType = 'initial';
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--') continue;
    if (arg === '--apply') {
      apply = true;
      continue;
    }
    if (arg === '--fiscal-year') {
      const next = Number(argv[i + 1]);
      if (!Number.isInteger(next)) throw new Error('--fiscal-year requires an integer');
      fiscalYear = next;
      i += 1;
      continue;
    }
    if (arg === '--account-type') {
      const next = argv[i + 1];
      if (!next) throw new Error('--account-type requires a value');
      accountType = next;
      i += 1;
      continue;
    }
    if (arg === '--doc-type') {
      const next = argv[i + 1];
      if (!next) throw new Error('--doc-type requires a value');
      docType = next;
      i += 1;
      continue;
    }
    if (arg === '--help' || arg === '-h') {
      console.log('usage: pnpm jp-fiscal:appropriation-flows:sync [--apply] [--fiscal-year 2025] [--account-type general] [--doc-type initial]');
      process.exit(0);
    }
    throw new Error(`unknown argument: ${arg}`);
  }
  return { apply, fiscalYear, accountType, docType };
}

function createDb(url: string): Kysely<unknown> {
  return new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 2 }),
    }),
  });
}

async function loadBudgetBook(db: Kysely<unknown>, fiscalYear: number, accountType: string, docType: string) {
  const result = await sql<{ vertex_id: string; total_jpy: string }>`
    SELECT vertex_id, total_jpy::text AS total_jpy
    FROM vertex_jp_fiscal_budget_book
    WHERE fiscal_year = ${fiscalYear}
      AND account_type = ${accountType}
      AND doc_type = ${docType}
    LIMIT 1
  `.execute(db);
  const row = result.rows[0];
  if (!row) {
    throw new Error(`budgetBook not found for ${fiscalYear}/${accountType}/${docType}`);
  }
  return row;
}

async function loadAppropriations(db: Kysely<unknown>, fiscalYear: number, accountType: string, docType: string): Promise<AppropriationRow[]> {
  const result = await sql<AppropriationRow>`
    SELECT
      vertex_id,
      fiscal_year,
      account_type,
      doc_type,
      ministry_did,
      program_code,
      program_name,
      amount_jpy::text AS amount_jpy,
      source_url,
      source_id,
      document_id
    FROM vertex_jp_fiscal_appropriation
    WHERE fiscal_year = ${fiscalYear}
      AND account_type = ${accountType}
      AND doc_type = ${docType}
    ORDER BY program_code
  `.execute(db);
  if (result.rows.length === 0) {
    throw new Error(`no appropriations found for ${fiscalYear}/${accountType}/${docType}`);
  }
  return result.rows;
}

async function syncFlows(db: Kysely<unknown>, budgetBookVertexId: string, rows: AppropriationRow[]): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  for (const row of rows) {
    const edgeId = [
      'edge:jp_fiscal_flow:appropriation',
      row.fiscal_year,
      row.account_type,
      row.doc_type,
      row.program_code.replace(/[^a-zA-Z0-9:_-]/g, '_'),
    ].join(':');
    await sql`
      DELETE FROM edge_jp_fiscal_flow
      WHERE edge_id = ${edgeId}
    `.execute(db);
    await sql`
      INSERT INTO edge_jp_fiscal_flow (
        edge_id, created_date, sensitivity_ord, owner_did,
        src_vid, dst_vid, flow_type, collection,
        source_did, dest_did, amount_jpy, fiscal_year,
        program_code, contract_ref, procurement_id, procurement_method,
        recipient_id, recipient_name, recipient_kind, corporate_number,
        source_url, published_date, data_source, derivation_stage,
        confidence, created_at
      ) VALUES (
        ${edgeId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:mof',
        ${budgetBookVertexId}, ${row.vertex_id}, 'appropriation', 'ai.gftd.apps.jpFiscal.appropriation',
        'did:web:gov-jpn.etzhayyim.com:treasury', ${row.ministry_did}, ${row.amount_jpy}, ${row.fiscal_year},
        ${row.program_code}, NULL, NULL, NULL,
        ${row.ministry_did}, ${row.program_name}, 'government_ministry', NULL,
        ${row.source_url}, NULL, ${row.source_id}, 'L7_TO_L5_APPROPRIATION',
        1.0, ${now}
      )
    `.execute(db);
  }
}

async function main(): Promise<void> {
  const { apply, fiscalYear, accountType, docType } = parseArgs(process.argv.slice(2));
  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) throw new Error('DATABASE_URL is required');
  const db = createDb(databaseUrl);
  try {
    const budgetBook = await loadBudgetBook(db, fiscalYear, accountType, docType);
    const rows = await loadAppropriations(db, fiscalYear, accountType, docType);
    const total = rows.reduce((sum, row) => sum + BigInt(row.amount_jpy), 0n);
    if (total !== BigInt(budgetBook.total_jpy)) {
      throw new Error(`appropriation total mismatch: rows=${total} budgetBook=${budgetBook.total_jpy}`);
    }

    if (apply) {
      await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
      await syncFlows(db, budgetBook.vertex_id, rows);
      await sql`FLUSH`.execute(db);
    }

    console.log(JSON.stringify({
      ok: true,
      mode: apply ? 'apply' : 'dry-run',
      budget_book_vertex_id: budgetBook.vertex_id,
      fiscal_year: fiscalYear,
      account_type: accountType,
      doc_type: docType,
      flows: rows.length,
      total_jpy: total.toString(),
      top5: rows
        .slice()
        .sort((a, b) => Number(BigInt(b.amount_jpy) - BigInt(a.amount_jpy)))
        .slice(0, 5)
        .map((row) => ({
          program_code: row.program_code,
          ministry_did: row.ministry_did,
          amount_jpy: row.amount_jpy,
        })),
    }, null, 2));
  } finally {
    await db.destroy();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
