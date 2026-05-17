#!/usr/bin/env node
/**
 * Materialize document-to-record evidence edges for JP fiscal graph records.
 *
 * Source/document fetch sync creates SOURCE_DOCUMENT edges. This script links
 * those fetched document vertices to parsed budgetBook and appropriation rows.
 */

import {
  Kysely,
  PostgresAdapter,
  PostgresDialect,
  sql,
} from 'kysely';
import { Pool } from 'pg';

interface SupportedRecord {
  vertex_id: string;
  collection: string;
  source_url: string | null;
  source_id: string | null;
  document_id: string | null;
  fiscal_year: number;
  account_type: string;
  doc_type: string | null;
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
      console.log('usage: pnpm jp-fiscal:record-evidence:sync [--apply] [--fiscal-year 2025] [--account-type general] [--doc-type initial]');
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

function stableEdgeId(record: SupportedRecord): string {
  return [
    'edge:jp_fiscal_evidence:document_supports_record',
    record.document_id?.replace(/^vertex:/, ''),
    record.vertex_id.replace(/^vertex:/, ''),
  ].join(':').replace(/[^a-zA-Z0-9:_-]/g, '_');
}

async function loadSupportedRecords(
  db: Kysely<unknown>,
  fiscalYear: number,
  accountType: string,
  docType: string,
): Promise<SupportedRecord[]> {
  const result = await sql<SupportedRecord>`
    SELECT
      vertex_id,
      'ai.gftd.apps.jpFiscal.budgetBook' AS collection,
      source_url,
      source_id,
      document_id,
      fiscal_year,
      account_type,
      doc_type
    FROM vertex_jp_fiscal_budget_book
    WHERE fiscal_year = ${fiscalYear}
      AND account_type = ${accountType}
      AND doc_type = ${docType}
    UNION ALL
    SELECT
      vertex_id,
      'ai.gftd.apps.jpFiscal.appropriation' AS collection,
      source_url,
      source_id,
      document_id,
      fiscal_year,
      account_type,
      doc_type
    FROM vertex_jp_fiscal_appropriation
    WHERE fiscal_year = ${fiscalYear}
      AND account_type = ${accountType}
      AND doc_type = ${docType}
    ORDER BY collection, vertex_id
  `.execute(db);
  return result.rows;
}

async function assertDocumentsExist(db: Kysely<unknown>, records: SupportedRecord[]): Promise<void> {
  const missingDocumentIds = records
    .filter((record) => !record.document_id)
    .map((record) => record.vertex_id);
  if (missingDocumentIds.length > 0) {
    throw new Error(`records missing document_id: ${missingDocumentIds.join(', ')}`);
  }

  for (const record of records) {
    const result = await sql<{ vertex_id: string }>`
      SELECT vertex_id
      FROM vertex_jp_fiscal_document
      WHERE vertex_id = ${record.document_id}
      LIMIT 1
    `.execute(db);
    if (!result.rows[0]) {
      throw new Error(`document vertex not found for ${record.vertex_id}: ${record.document_id}`);
    }
  }
}

async function syncRecordEvidence(db: Kysely<unknown>, records: SupportedRecord[]): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  for (const record of records) {
    const edgeId = stableEdgeId(record);
    await sql`
      DELETE FROM edge_jp_fiscal_evidence
      WHERE edge_id = ${edgeId}
    `.execute(db);
    await sql`
      INSERT INTO edge_jp_fiscal_evidence (
        edge_id, created_date, sensitivity_ord, owner_did,
        src_vid, dst_vid, evidence_kind, source_url, confidence, created_at
      ) VALUES (
        ${edgeId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:mof',
        ${record.document_id}, ${record.vertex_id}, 'DOCUMENT_SUPPORTS_RECORD',
        ${record.source_url}, 1.0, ${now}
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
    const records = await loadSupportedRecords(db, fiscalYear, accountType, docType);
    if (records.length === 0) {
      throw new Error(`no supported records found for ${fiscalYear}/${accountType}/${docType}`);
    }
    await assertDocumentsExist(db, records);

    if (apply) {
      await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
      await syncRecordEvidence(db, records);
      await sql`FLUSH`.execute(db);
    }

    const byCollection = records.reduce<Record<string, number>>((acc, record) => {
      acc[record.collection] = (acc[record.collection] ?? 0) + 1;
      return acc;
    }, {});
    console.log(JSON.stringify({
      ok: true,
      mode: apply ? 'apply' : 'dry-run',
      fiscal_year: fiscalYear,
      account_type: accountType,
      doc_type: docType,
      records: records.length,
      written: apply ? records.length : 0,
      by_collection: byCollection,
      document_ids: Array.from(new Set(records.map((record) => record.document_id))),
    }, null, 2));
  } finally {
    await db.destroy();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
