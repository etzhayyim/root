#!/usr/bin/env node
/**
 * Fetch JP fiscal public source URLs and sync document evidence vertices.
 *
 * Default mode fetches sources and prints a dry-run summary. Use --apply with
 * DATABASE_URL set to write vertex_jp_fiscal_document plus source evidence
 * edges. This intentionally stores metadata/hash/excerpt only; blob storage is
 * a later B2/IPFS step.
 */

import { createHash } from 'node:crypto';
import { promises as fs } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import {
  Kysely,
  PostgresAdapter,
  PostgresDialect,
  sql,
} from 'kysely';
import { Pool } from 'pg';

interface SourceManifest {
  version: string;
  jurisdiction: string;
  sources: SourceRecord[];
}

interface SourceRecord {
  source_id: string;
  collection: string;
  title: string;
  source_url: string;
}

interface FetchedDocument {
  source: SourceRecord;
  status: number;
  finalUrl: string;
  mediaType: string | null;
  byteLength: number;
  sha256: string;
  excerpt: string | null;
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
const repoRoot = path.resolve(__dirname, '..', '..', '..');
const defaultManifestPath = path.resolve(
  repoRoot,
  '60-apps/etzhayyim-project-states/data/jp_fiscal/sources.json',
);
const userAgent = 'etzhayyim-jp-fiscal-source-audit/0.1 (+https://etzhayyim.com)';

function parseArgs(argv: string[]): { apply: boolean; manifestPath: string; limit: number; sourceId?: string } {
  let apply = false;
  let manifestPath = defaultManifestPath;
  let limit = Number.POSITIVE_INFINITY;
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
    if (arg === '--limit') {
      const next = Number(argv[i + 1]);
      if (!Number.isFinite(next) || next < 1) throw new Error('--limit requires a positive number');
      limit = Math.floor(next);
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
      console.log('usage: pnpm jp-fiscal:documents:sync [--apply] [--limit N] [--source-id id] [--manifest path]');
      process.exit(0);
    }
    throw new Error(`unknown argument: ${arg}`);
  }
  return { apply, manifestPath, limit, sourceId };
}

function createDb(url: string): Kysely<unknown> {
  return new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 2 }),
    }),
  });
}

function cleanExcerpt(mediaType: string | null, bytes: Uint8Array): string | null {
  if (!mediaType?.includes('html') && !mediaType?.startsWith('text/')) return null;
  const raw = new TextDecoder('utf-8', { fatal: false }).decode(bytes.slice(0, 80_000));
  const withoutTags = raw
    .replace(/<script[\s\S]*?<\/script>/gi, ' ')
    .replace(/<style[\s\S]*?<\/style>/gi, ' ')
    .replace(/<[^>]+>/g, ' ');
  const compact = withoutTags.replace(/\s+/g, ' ').trim();
  return compact ? compact.slice(0, 1_000) : null;
}

async function fetchDocument(source: SourceRecord): Promise<FetchedDocument> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch(source.source_url, {
      redirect: 'follow',
      signal: controller.signal,
      headers: { 'user-agent': userAgent },
    });
    const bytes = new Uint8Array(await response.arrayBuffer());
    const mediaType = response.headers.get('content-type')?.split(';')[0]?.trim().toLowerCase() ?? null;
    return {
      source,
      status: response.status,
      finalUrl: response.url,
      mediaType,
      byteLength: bytes.byteLength,
      sha256: createHash('sha256').update(bytes).digest('hex'),
      excerpt: cleanExcerpt(mediaType, bytes),
    };
  } finally {
    clearTimeout(timeout);
  }
}

async function syncDocument(db: Kysely<unknown>, doc: FetchedDocument): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  const documentId = `vertex:jp_fiscal_document:${doc.sha256}`;
  const sourceVertexId = `vertex:jp_fiscal_source:${doc.source.source_id}`;
  const edgeId = `edge:jp_fiscal_evidence:${doc.source.source_id}:${doc.sha256}`;
  await sql`
    DELETE FROM vertex_jp_fiscal_document
    WHERE vertex_id = ${documentId}
  `.execute(db);
  await sql`
    INSERT INTO vertex_jp_fiscal_document (
      vertex_id, created_date, sensitivity_ord, owner_did,
      source_id, collection, source_url, fetched_at, media_type, sha256,
      byte_length, storage_uri, title, text_excerpt, created_at
    ) VALUES (
      ${documentId}, ${createdDate}, 1, NULL,
      ${doc.source.source_id}, ${doc.source.collection}, ${doc.finalUrl}, ${now},
      ${doc.mediaType}, ${doc.sha256}, ${doc.byteLength}, NULL,
      ${doc.source.title}, ${doc.excerpt}, ${now}
    )
  `.execute(db);
  await sql`
    DELETE FROM edge_jp_fiscal_evidence
    WHERE edge_id = ${edgeId}
  `.execute(db);
  await sql`
    INSERT INTO edge_jp_fiscal_evidence (
      edge_id, created_date, sensitivity_ord, owner_did,
      src_vid, dst_vid, evidence_kind, source_url, confidence, created_at
    ) VALUES (
      ${edgeId}, ${createdDate}, 1, NULL,
      ${sourceVertexId}, ${documentId}, 'SOURCE_DOCUMENT',
      ${doc.finalUrl}, 1.0, ${now}
    )
  `.execute(db);
}

async function main(): Promise<void> {
  const { apply, manifestPath, limit, sourceId } = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8')) as SourceManifest;
  let sources = manifest.sources;
  if (sourceId) {
    sources = sources.filter((source) => source.source_id === sourceId);
    if (sources.length === 0) throw new Error(`source_id not found: ${sourceId}`);
  }
  sources = sources.slice(0, limit);

  const documents: FetchedDocument[] = [];
  const failures: Array<{ source_id: string; source_url: string; error: string }> = [];
  for (const source of sources) {
    try {
      documents.push(await fetchDocument(source));
    } catch (error) {
      failures.push({
        source_id: source.source_id,
        source_url: source.source_url,
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
      for (const doc of documents) {
        if (doc.status >= 200 && doc.status < 400) {
          await syncDocument(db, doc);
        }
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
    fetched: documents.length,
    written: apply ? documents.filter((doc) => doc.status >= 200 && doc.status < 400).length : 0,
    failures,
    documents: documents.map((doc) => ({
      source_id: doc.source.source_id,
      status: doc.status,
      media_type: doc.mediaType,
      byte_length: doc.byteLength,
      sha256: doc.sha256,
      final_url: doc.finalUrl,
      has_excerpt: doc.excerpt !== null,
    })),
  }, null, 2));
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
