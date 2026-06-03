#!/usr/bin/env node
/**
 * Extract top-level JP fiscal appropriations from official MOF budget PDFs.
 *
 * Scope: general-account initial budget, top-level 所管/費合計 rows only.
 * Each parsed amount is sourced from the PDF text and validated against the
 * Article 1 budget total before writing.
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

interface AppropriationRecord {
  source: SourceRecord;
  fiscalYear: number;
  accountType: string;
  docType: string;
  code: string;
  ministryDid: string;
  programCode: string;
  programName: string;
  amountJpy: bigint;
  sourceUrl: string;
  sha256: string;
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
const userAgent = 'etzhayyim-jp-fiscal-appropriations/0.1 (+https://etzhayyim.com)';

const ministryDidByCode: Record<string, string> = {
  '01': 'did:web:gov-jpn.etzhayyim.com:imperial-household',
  '02': 'did:web:gov-jpn.etzhayyim.com:diet',
  '03': 'did:web:gov-jpn.etzhayyim.com:supreme-court',
  '04': 'did:web:gov-jpn.etzhayyim.com:boa',
  '05': 'did:web:gov-jpn.etzhayyim.com:cabinet',
  '06': 'did:web:gov-jpn.etzhayyim.com:cao',
  '07': 'did:web:gov-jpn.etzhayyim.com:digital',
  '08': 'did:web:gov-jpn.etzhayyim.com:mic',
  '09': 'did:web:gov-jpn.etzhayyim.com:moj',
  '10': 'did:web:gov-jpn.etzhayyim.com:mofa',
  '11': 'did:web:gov-jpn.etzhayyim.com:mof',
  '12': 'did:web:gov-jpn.etzhayyim.com:mext',
  '13': 'did:web:gov-jpn.etzhayyim.com:mhlw',
  '14': 'did:web:gov-jpn.etzhayyim.com:maff',
  '15': 'did:web:gov-jpn.etzhayyim.com:meti',
  '16': 'did:web:gov-jpn.etzhayyim.com:mlit',
  '17': 'did:web:gov-jpn.etzhayyim.com:moe',
  '18': 'did:web:gov-jpn.etzhayyim.com:mod',
};

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
      console.log('usage: pnpm jp-fiscal:appropriations:sync [--apply] [--source-id id] [--manifest path]');
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
  const dir = await fs.mkdtemp(path.join(os.tmpdir(), 'jp-fiscal-appropriation-'));
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

function normalizeName(value: string): string {
  return value.replace(/\s+/g, '');
}

function parseNumber(value: string): bigint {
  const normalized = value
    .replace(/[，,\s]/g, '')
    .replace(/[０-９]/g, (char) => String.fromCharCode(char.charCodeAt(0) - 0xfee0));
  return BigInt(normalized);
}

function parseBudgetTotalJpy(text: string): bigint {
  const compact = text.replace(/[ \t\r\n]+/g, ' ');
  const match = compact.match(/歳入歳出それぞれ\s*([0-9０-９,\s，]+)\s*千円/);
  if (!match) throw new Error('budget total not found');
  return parseNumber(match[1]) * 1000n;
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

function parseAppropriations(source: SourceRecord, text: string, sha256: string): AppropriationRecord[] {
  const fiscalYear = inferFiscalYear(source, text);
  const docType = inferDocType(source);
  const records: AppropriationRecord[] = [];
  const seen = new Set<string>();
  const linePattern = /^\s*(\d{2})\s+(.+?)\s*合\s*計\s+([0-9,]+)\s+/;
  for (const line of text.split(/\r?\n/)) {
    const match = line.match(linePattern);
    if (!match) continue;
    const [, code, rawName, rawAmount] = match;
    if (!ministryDidByCode[code] || seen.has(code)) continue;
    seen.add(code);
    const programName = normalizeName(rawName);
    records.push({
      source,
      fiscalYear,
      accountType: 'general',
      docType,
      code,
      ministryDid: ministryDidByCode[code],
      programCode: `topline:${code}`,
      programName,
      amountJpy: parseNumber(rawAmount) * 1000n,
      sourceUrl: source.source_url,
      sha256,
      evidenceText: line.trim().slice(0, 500),
    });
  }
  if (records.length !== 18) {
    throw new Error(`expected 18 top-level appropriation rows, got ${records.length}`);
  }
  const total = records.reduce((sum, record) => sum + record.amountJpy, 0n);
  const budgetTotal = parseBudgetTotalJpy(text);
  if (total !== budgetTotal) {
    throw new Error(`appropriation sum mismatch: rows=${total} budget=${budgetTotal}`);
  }
  return records;
}

async function findDocumentId(db: Kysely<unknown>, sourceId: string, sha256: string): Promise<string | null> {
  const result = await sql<{ vertex_id: string }>`
    SELECT vertex_id FROM vertex_jp_fiscal_document
    WHERE source_id = ${sourceId} AND sha256 = ${sha256}
    LIMIT 1
  `.execute(db);
  return result.rows[0]?.vertex_id ?? null;
}

async function syncAppropriations(db: Kysely<unknown>, records: AppropriationRecord[]): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  for (const record of records) {
    const vertexId = [
      'vertex:jp_fiscal_appropriation',
      record.fiscalYear,
      record.accountType,
      record.docType,
      record.code,
    ].join(':');
    const documentId = await findDocumentId(db, record.source.source_id, record.sha256);
    await sql`
      DELETE FROM vertex_jp_fiscal_appropriation
      WHERE vertex_id = ${vertexId}
    `.execute(db);
    await sql`
      INSERT INTO vertex_jp_fiscal_appropriation (
        vertex_id, created_date, sensitivity_ord, owner_did,
        fiscal_year, account_type, special_account_code, ministry_did,
        program_code, program_name, amount_jpy, diet_approval_id,
        doc_type, source_url, source_id, document_id, created_at
      ) VALUES (
        ${vertexId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:mof',
        ${record.fiscalYear}, ${record.accountType}, NULL, ${record.ministryDid},
        ${record.programCode}, ${record.programName}, ${record.amountJpy.toString()}, NULL,
        ${record.docType}, ${record.sourceUrl}, ${record.source.source_id}, ${documentId}, ${now}
      )
    `.execute(db);
  }
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

  const records: AppropriationRecord[] = [];
  const failures: Array<{ source_id: string; error: string }> = [];
  for (const source of sources) {
    try {
      const bytes = await fetchBytes(source.source_url);
      const sha256 = createHash('sha256').update(bytes).digest('hex');
      const text = await pdfToText(bytes);
      records.push(...parseAppropriations(source, text, sha256));
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
      await syncAppropriations(db, records);
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
    total_jpy: records.reduce((sum, record) => sum + record.amountJpy, 0n).toString(),
    failures,
    records: records.map((record) => ({
      code: record.code,
      ministry_did: record.ministryDid,
      program_name: record.programName,
      amount_jpy: record.amountJpy.toString(),
      evidence_text: record.evidenceText,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
