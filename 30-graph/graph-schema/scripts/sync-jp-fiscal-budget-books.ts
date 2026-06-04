#!/usr/bin/env node
/**
 * Extract JP fiscal budgetBook records from official MOF budget PDFs.
 *
 * This is deliberately narrow: it only writes rows when the official PDF text
 * contains the Article 1 total in 千円. No synthetic totals are allowed.
 */

import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { fileURLToPath } from 'node:url';
import {
  Kysely,
  PostgresAdapter,
  PostgresDialect,
  sql,
} from 'kysely';
import { Pool } from 'pg';

interface SourceManifest {
  sources: SourceRecord[];
}

interface SourceRecord {
  source_id: string;
  collection: string;
  title: string;
  source_url: string;
  access_kind: string;
}

interface BudgetBookRecord {
  source: SourceRecord;
  fiscalYear: number;
  docType: string;
  accountType: string;
  totalJpy: bigint;
  sourceUrl: string;
  sha256: string;
  byteLength: number;
  evidenceText: string;
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

const execFileAsync = promisify(execFile);
const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const defaultManifestPath = path.resolve(
  repoRoot,
  '60-apps/etzhayyim-project-states/data/jp_fiscal/sources.json',
);
const userAgent = 'etzhayyim-jp-fiscal-budget-book/0.1 (+https://etzhayyim.com)';

function parseArgs(argv: string[]): { apply: boolean; manifestPath: string; sourceId?: string } {
  let apply = false;
  let manifestPath = defaultManifestPath;
  let sourceId: string | undefined;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--') continue;
    if (arg === '--apply') {
      apply = true;
      continue;
    }
    if (arg === '--manifest') {
      const next = argv[i + 1];
      if (!next) throw new Error('--manifest requires a file path');
      manifestPath = path.resolve(next);
      i += 1;
      continue;
    }
    if (arg === '--source-id') {
      const next = argv[i + 1];
      if (!next) throw new Error('--source-id requires a source_id');
      sourceId = next;
      i += 1;
      continue;
    }
    if (arg === '--help' || arg === '-h') {
      console.log('usage: pnpm jp-fiscal:budget-books:sync [--apply] [--source-id id] [--manifest path]');
      process.exit(0);
    }
    throw new Error(`unknown argument: ${arg}`);
  }
  return { apply, manifestPath, sourceId };
}

function createDb(url: string): Kysely<unknown> {
  return new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 2 }),
    }),
  });
}

async function fetchBytes(url: string): Promise<Uint8Array> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(url, {
      redirect: 'follow',
      signal: controller.signal,
      headers: { 'user-agent': userAgent },
    });
    if (!response.ok) {
      throw new Error(`fetch failed ${response.status} ${response.statusText}`);
    }
    return new Uint8Array(await response.arrayBuffer());
  } finally {
    clearTimeout(timeout);
  }
}

async function pdfToText(bytes: Uint8Array): Promise<string> {
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'jp-fiscal-budget-'));
  try {
    const pdfPath = path.join(dir, 'budget.pdf');
    const textPath = path.join(dir, 'budget.txt');
    await fs.writeFile(pdfPath, bytes);
    await execFileAsync('pdftotext', ['-layout', pdfPath, textPath]);
    return await fs.readFile(textPath, 'utf8');
  } finally {
    await fs.rm(dir, { recursive: true, force: true });
  }
}

function inferFiscalYear(source: SourceRecord, text: string): number {
  const haystack = `${source.title}\n${text.slice(0, 20_000)}`;
  const reiwa = haystack.match(/令和\s*(\d+)\s*年度/);
  if (reiwa) return 2018 + Number(reiwa[1]);
  const western = haystack.match(/(?:fy)?(20\d{2})/i);
  if (western) return Number(western[1]);
  throw new Error(`cannot infer fiscal year for ${source.source_id}`);
}

function inferDocType(source: SourceRecord): string {
  if (source.title.includes('補正')) return 'supplementary';
  if (source.title.includes('決算')) return 'settlement';
  return 'initial';
}

function inferAccountType(source: SourceRecord, text: string): string {
  const haystack = `${source.title}\n${text.slice(0, 20_000)}`;
  if (haystack.includes('一般会計')) return 'general';
  if (haystack.includes('特別会計')) return 'special';
  return 'unknown';
}

function parseTotalJpy(text: string): { totalJpy: bigint; evidenceText: string } {
  const compact = text.replace(/[ \t\r\n]+/g, ' ');
  const match = compact.match(/歳入歳出それぞれ\s*([0-9０-９,\s，]+)\s*千円/);
  if (!match) {
    throw new Error('budget total not found: expected Article 1 歳入歳出それぞれ ... 千円');
  }
  const rawNumber = match[1]
    .replace(/[，,\s]/g, '')
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0));
  const thousandYen = BigInt(rawNumber);
  return {
    totalJpy: thousandYen * 1000n,
    evidenceText: match[0].slice(0, 500),
  };
}

async function extractBudgetBook(source: SourceRecord): Promise<BudgetBookRecord> {
  const bytes = await fetchBytes(source.source_url);
  const text = await pdfToText(bytes);
  const { totalJpy, evidenceText } = parseTotalJpy(text);
  return {
    source,
    fiscalYear: inferFiscalYear(source, text),
    docType: inferDocType(source),
    accountType: inferAccountType(source, text),
    totalJpy,
    sourceUrl: source.source_url,
    sha256: createHash('sha256').update(bytes).digest('hex'),
    byteLength: bytes.byteLength,
    evidenceText,
  };
}

async function findDocumentId(db: Kysely<unknown>, sourceId: string, sha256: string): Promise<string | null> {
  const result = await sql<{ vertex_id: string }>`
    SELECT vertex_id FROM vertex_jp_fiscal_document
    WHERE source_id = ${sourceId} AND sha256 = ${sha256}
    LIMIT 1
  `.execute(db);
  return result.rows[0]?.vertex_id ?? null;
}

async function syncBudgetBook(db: Kysely<unknown>, record: BudgetBookRecord): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  const vertexId = [
    'vertex:jp_fiscal_budget_book',
    record.fiscalYear,
    record.accountType,
    record.docType,
  ].join(':');
  const documentId = await findDocumentId(db, record.source.source_id, record.sha256);
  await sql`
    DELETE FROM vertex_jp_fiscal_budget_book
    WHERE vertex_id = ${vertexId}
  `.execute(db);
  await sql`
    INSERT INTO vertex_jp_fiscal_budget_book (
      vertex_id, created_date, sensitivity_ord, owner_did,
      fiscal_year, doc_type, account_type, special_account_code,
      total_jpy, source_url, pdf_cid, xbrl_cid, source_id, document_id, created_at
    ) VALUES (
      ${vertexId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:mof',
      ${record.fiscalYear}, ${record.docType}, ${record.accountType}, NULL,
      ${record.totalJpy.toString()}, ${record.sourceUrl}, NULL, NULL,
      ${record.source.source_id}, ${documentId}, ${now}
    )
  `.execute(db);
}

async function main(): Promise<void> {
  const { apply, manifestPath, sourceId } = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8')) as SourceManifest;
  let sources = manifest.sources.filter((source) =>
    source.collection === 'com.etzhayyim.apps.jpFiscal.budgetBook'
    && source.access_kind === 'pdf'
  );
  if (sourceId) sources = sources.filter((source) => source.source_id === sourceId);
  if (sources.length === 0) throw new Error('no matching budgetBook PDF sources');

  const records: BudgetBookRecord[] = [];
  const failures: Array<{ source_id: string; error: string }> = [];
  for (const source of sources) {
    try {
      records.push(await extractBudgetBook(source));
    } catch (error) {
      failures.push({
        source_id: source.source_id,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  if (apply) {
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl) throw new Error('DATABASE_URL is required when --apply is set');
    const db = createDb(databaseUrl);
    try {
      await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
      for (const record of records) {
        await syncBudgetBook(db, record);
      }
      await sql`FLUSH`.execute(db);
    } finally {
      await db.destroy();
    }
  }

  console.log(JSON.stringify({
    ok: failures.length === 0,
    mode: apply ? 'apply' : 'dry-run',
    manifest: path.relative(repoRoot, manifestPath),
    extracted: records.length,
    written: apply ? records.length : 0,
    failures,
    records: records.map((record) => ({
      source_id: record.source.source_id,
      fiscal_year: record.fiscalYear,
      doc_type: record.docType,
      account_type: record.accountType,
      total_jpy: record.totalJpy.toString(),
      sha256: record.sha256,
      byte_length: record.byteLength,
      evidence_text: record.evidenceText,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
