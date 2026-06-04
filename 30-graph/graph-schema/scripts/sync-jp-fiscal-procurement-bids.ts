#!/usr/bin/env node
/**
 * Fetch Digital Agency procurement announcements and sync procurement bid vertices.
 */

import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import * as path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  Kysely,
  PostgresAdapter,
  PostgresDialect,
  sql,
} from 'kysely';
import { Pool } from 'pg';

interface SourceManifest {
  sources: SourceEntry[];
}

interface SourceEntry {
  source_id: string;
  collection: string;
  source_url: string;
  extractor: string;
}

interface ProcurementBidRecord {
  vertexId: string;
  tenderNo: string;
  title: string;
  tenderUrl: string;
  openedAt: string;
  fiscalYear: number;
  method: string;
  announcementType: string;
  wto: boolean | null;
  source: SourceEntry;
  documentSha256: string;
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

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, '../../..');
const defaultManifestPath = path.resolve(repoRoot, '60-apps/etzhayyim-project-states/data/jp_fiscal/sources.json');

function parseArgs(argv: string[]): { apply: boolean; manifestPath: string; limit: number } {
  let apply = false;
  let manifestPath = defaultManifestPath;
  let limit = Number.POSITIVE_INFINITY;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--') continue;
    if (arg === '--apply') {
      apply = true;
      continue;
    }
    if (arg === '--manifest') {
      const next = argv[i + 1];
      if (!next) throw new Error('--manifest requires a path');
      manifestPath = path.resolve(process.cwd(), next);
      i += 1;
      continue;
    }
    if (arg === '--limit') {
      const next = Number(argv[i + 1]);
      if (!Number.isInteger(next) || next < 1) throw new Error('--limit requires a positive integer');
      limit = next;
      i += 1;
      continue;
    }
    if (arg === '--help' || arg === '-h') {
      console.log('usage: pnpm jp-fiscal:procurement-bids:sync [--apply] [--limit 25] [--manifest path]');
      process.exit(0);
    }
    throw new Error(`unknown argument: ${arg}`);
  }
  return { apply, manifestPath, limit };
}

function createDb(url: string): Kysely<unknown> {
  return new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 2 }),
    }),
  });
}

function decodeHtml(value: string): string {
  return value
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&nbsp;/g, ' ');
}

function stripTags(value: string): string {
  return decodeHtml(value.replace(/<[^>]*>/g, ' '))
    .replace(/\s+/g, ' ')
    .trim();
}

function parseJapaneseDate(value: string): string {
  const match = value.match(/（(\d{4})年）\s*(\d{1,2})月(\d{1,2})日/);
  if (!match) throw new Error(`could not parse Japanese date: ${value}`);
  const [, year, month, day] = match;
  return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

function fiscalYearForDate(isoDate: string): number {
  const year = Number(isoDate.slice(0, 4));
  const month = Number(isoDate.slice(5, 7));
  return month >= 4 ? year : year - 1;
}

function methodForAnnouncement(announcementType: string): { method: string; wto: boolean | null } {
  if (announcementType.includes('WTO対象外')) return { method: 'open_competitive_non_wto', wto: false };
  if (announcementType.includes('WTO対象')) return { method: 'open_competitive_wto', wto: true };
  return { method: 'open_competitive', wto: null };
}

async function fetchText(url: string): Promise<{ text: string; finalUrl: string; sha256: string }> {
  const response = await fetch(url, {
    redirect: 'follow',
    headers: { 'user-agent': 'etzhayyim-jp-fiscal-ingest/0.1 (+https://etzhayyim.com)' },
  });
  if (!response.ok) throw new Error(`fetch failed ${response.status} ${response.statusText}: ${url}`);
  const bytes = new Uint8Array(await response.arrayBuffer());
  return {
    text: new TextDecoder('utf-8').decode(bytes),
    finalUrl: response.url,
    sha256: createHash('sha256').update(bytes).digest('hex'),
  };
}

function extractSection(html: string, id: string): string {
  const start = html.indexOf(`id="${id}"`);
  if (start < 0) throw new Error(`section not found: ${id}`);
  const next = html.slice(start + id.length).search(/<h[23][^>]+id="/);
  return next < 0 ? html.slice(start) : html.slice(start, start + id.length + next);
}

function parseDigitalAgencyBids(source: SourceEntry, html: string, documentSha256: string): ProcurementBidRecord[] {
  const section = extractSection(html, 'procurement-announcement');
  const records: ProcurementBidRecord[] = [];
  const itemPattern = /<li><a\b[^>]*href="([^"]+)"[^>]*>\s*<strong>(.*?)<\/strong>[\s\S]*?<\/a>(?:[^<]*?（[^<]*?更新）)?\s*<ul>([\s\S]*?)<\/ul><\/li>/g;
  for (const match of section.matchAll(itemPattern)) {
    const href = decodeHtml(match[1]);
    const title = stripTags(match[2]);
    const details = Array.from(match[3].matchAll(/<li>([\s\S]*?)<\/li>/g)).map((m) => stripTags(m[1]));
    const dateText = details.find((detail) => /（\d{4}年）\s*\d{1,2}月\d{1,2}日/.test(detail));
    const tenderText = details.find((detail) => detail.startsWith('調達案件番号:'));
    const announcementType = details.find((detail) => detail.includes('入札公告')) ?? '入札公告';
    if (!dateText || !tenderText) continue;
    const tenderNo = tenderText.replace(/^調達案件番号:/, '').trim();
    const openedDate = parseJapaneseDate(dateText);
    const { method, wto } = methodForAnnouncement(announcementType);
    records.push({
      vertexId: `vertex:jp_fiscal_procurement_bid:digital:${tenderNo}`,
      tenderNo,
      title,
      tenderUrl: href.startsWith('http') ? href : new URL(href, source.source_url).toString(),
      openedAt: `${openedDate}T00:00:00+09:00`,
      fiscalYear: fiscalYearForDate(openedDate),
      method,
      announcementType,
      wto,
      source,
      documentSha256,
    });
  }
  return records;
}

async function findDocumentId(db: Kysely<unknown>, sourceId: string, sha256: string): Promise<string | null> {
  const result = await sql<{ vertex_id: string }>`
    SELECT vertex_id
    FROM vertex_jp_fiscal_document
    WHERE source_id = ${sourceId}
      AND sha256 = ${sha256}
    ORDER BY fetched_at DESC
    LIMIT 1
  `.execute(db);
  return result.rows[0]?.vertex_id ?? null;
}

async function syncBid(db: Kysely<unknown>, record: ProcurementBidRecord, documentId: string | null): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  const externalRefs = JSON.stringify({
    source: 'digital-agency-procurement',
    announcementType: record.announcementType,
    wto: record.wto,
    tenderUrl: record.tenderUrl,
    documentSha256: record.documentSha256,
  });
  await sql`
    DELETE FROM vertex_jp_fiscal_procurement_bid
    WHERE vertex_id = ${record.vertexId}
  `.execute(db);
  await sql`
    INSERT INTO vertex_jp_fiscal_procurement_bid (
      vertex_id, created_date, sensitivity_ord, owner_did,
      tender_no, issuer_did, method, title,
      estimated_jpy, currency, opened_at, closed_at,
      awarded_at, awarded_contract_did, awarded_amount_jpy,
      bidders_json, tender_url, external_refs_json, source_id,
      document_id, created_at
    ) VALUES (
      ${record.vertexId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:digital',
      ${record.tenderNo}, 'did:web:gov-jpn.etzhayyim.com:digital', ${record.method}, ${record.title},
      NULL, 'JPY', ${record.openedAt}, NULL,
      NULL, NULL, NULL,
      NULL, ${record.tenderUrl}, ${externalRefs}, ${record.source.source_id},
      ${documentId}, ${now}
    )
  `.execute(db);

  if (documentId) {
    const edgeId = `edge:jp_fiscal_evidence:document_supports_record:${documentId.replace(/^vertex:/, '')}:${record.vertexId.replace(/^vertex:/, '')}`;
    await sql`
      DELETE FROM edge_jp_fiscal_evidence
      WHERE edge_id = ${edgeId}
    `.execute(db);
    await sql`
      INSERT INTO edge_jp_fiscal_evidence (
        edge_id, created_date, sensitivity_ord, owner_did,
        src_vid, dst_vid, evidence_kind, source_url, confidence, created_at
      ) VALUES (
        ${edgeId}, ${createdDate}, 1, 'did:web:gov-jpn.etzhayyim.com:digital',
        ${documentId}, ${record.vertexId}, 'DOCUMENT_SUPPORTS_RECORD',
        ${record.source.source_url}, 0.95, ${now}
      )
    `.execute(db);
  }
}

async function main(): Promise<void> {
  const { apply, manifestPath, limit } = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8')) as SourceManifest;
  const source = manifest.sources.find((entry) => entry.extractor === 'digital_agency_procurement');
  if (!source) throw new Error('digital_agency_procurement source not found in manifest');

  const fetched = await fetchText(source.source_url);
  const records = parseDigitalAgencyBids(source, fetched.text, fetched.sha256).slice(0, limit);
  if (records.length === 0) throw new Error('no procurement announcements parsed');

  let documentId: string | null = null;
  if (apply) {
    const databaseUrl = process.env.DATABASE_URL;
    if (!databaseUrl) throw new Error('DATABASE_URL is required when --apply is set');
    const db = createDb(databaseUrl);
    try {
      await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
      documentId = await findDocumentId(db, source.source_id, fetched.sha256);
      for (const record of records) {
        await syncBid(db, record, documentId);
      }
      await sql`FLUSH`.execute(db);
    } finally {
      await db.destroy();
    }
  }

  console.log(JSON.stringify({
    ok: true,
    mode: apply ? 'apply' : 'dry-run',
    source_id: source.source_id,
    source_url: source.source_url,
    fetched_url: fetched.finalUrl,
    sha256: fetched.sha256,
    parsed: records.length,
    written: apply ? records.length : 0,
    document_id: documentId,
    first5: records.slice(0, 5).map((record) => ({
      tender_no: record.tenderNo,
      opened_at: record.openedAt,
      fiscal_year: record.fiscalYear,
      method: record.method,
      title: record.title,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
