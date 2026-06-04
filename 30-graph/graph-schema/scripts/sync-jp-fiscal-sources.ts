#!/usr/bin/env node
/**
 * Sync JP fiscal public-source manifest into vertex_jp_fiscal_source.
 *
 * Default mode validates and prints a dry-run summary. Use --apply with
 * DATABASE_URL set to write rows. RisingWave does not support Postgres
 * ON CONFLICT in our write path, so this uses DELETE+INSERT per source_id.
 */

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
  publisher_did?: string;
  source_url: string;
  access_kind: string;
  cadence: string;
  license_note?: string;
  extractor: string;
  status: string;
  notes?: string;
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

function parseArgs(argv: string[]): { apply: boolean; manifestPath: string } {
  let apply = false;
  let manifestPath = defaultManifestPath;
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--') {
      continue;
    }
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
    if (arg === '--help' || arg === '-h') {
      console.log('usage: pnpm jp-fiscal:sources:sync [--apply] [--manifest path]');
      process.exit(0);
    }
    throw new Error(`unknown argument: ${arg}`);
  }
  return { apply, manifestPath };
}

function requiredString(value: unknown, field: string, sourceId: string): string {
  if (typeof value !== 'string' || value.trim() === '') {
    throw new Error(`source ${sourceId}: ${field} is required`);
  }
  return value;
}

function validateManifest(manifest: SourceManifest): void {
  requiredString(manifest.version, 'version', '<manifest>');
  requiredString(manifest.jurisdiction, 'jurisdiction', '<manifest>');
  if (!Array.isArray(manifest.sources)) {
    throw new Error('manifest.sources must be an array');
  }
  const seen = new Set<string>();
  for (const source of manifest.sources) {
    const sourceId = requiredString(source.source_id, 'source_id', '<unknown>');
    if (seen.has(sourceId)) {
      throw new Error(`duplicate source_id: ${sourceId}`);
    }
    seen.add(sourceId);
    requiredString(source.collection, 'collection', sourceId);
    requiredString(source.title, 'title', sourceId);
    requiredString(source.source_url, 'source_url', sourceId);
    requiredString(source.access_kind, 'access_kind', sourceId);
    requiredString(source.cadence, 'cadence', sourceId);
    requiredString(source.extractor, 'extractor', sourceId);
    requiredString(source.status, 'status', sourceId);
    if (!source.collection.startsWith('com.etzhayyim.apps.jpFiscal.')) {
      throw new Error(`source ${sourceId}: collection must be com.etzhayyim.apps.jpFiscal.*`);
    }
    try {
      new URL(source.source_url);
    } catch {
      throw new Error(`source ${sourceId}: source_url is not a valid URL`);
    }
  }
}

function createDb(url: string): Kysely<unknown> {
  return new Kysely<unknown>({
    dialect: new RisingWaveDialect({
      pool: new Pool({ connectionString: url, max: 2 }),
    }),
  });
}

async function upsertSource(db: Kysely<unknown>, manifest: SourceManifest, source: SourceRecord): Promise<void> {
  const now = new Date().toISOString();
  const createdDate = now.slice(0, 10);
  const vertexId = `vertex:jp_fiscal_source:${source.source_id}`;
  await sql`
    DELETE FROM vertex_jp_fiscal_source
    WHERE source_id = ${source.source_id}
  `.execute(db);
  await sql`
    INSERT INTO vertex_jp_fiscal_source (
      vertex_id, created_date, sensitivity_ord, owner_did,
      source_id, collection, jurisdiction, title, publisher_did, source_url,
      access_kind, cadence, license_note, extractor, status, notes,
      created_at, updated_at
    ) VALUES (
      ${vertexId}, ${createdDate}, 1, ${source.publisher_did ?? null},
      ${source.source_id}, ${source.collection}, ${manifest.jurisdiction}, ${source.title},
      ${source.publisher_did ?? null}, ${source.source_url}, ${source.access_kind},
      ${source.cadence}, ${source.license_note ?? null}, ${source.extractor},
      ${source.status}, ${source.notes ?? null}, ${now}, ${now}
    )
  `.execute(db);
}

async function main(): Promise<void> {
  const { apply, manifestPath } = parseArgs(process.argv.slice(2));
  const manifest = JSON.parse(await fs.readFile(manifestPath, 'utf8')) as SourceManifest;
  validateManifest(manifest);

  const byCollection = new Map<string, number>();
  for (const source of manifest.sources) {
    byCollection.set(source.collection, (byCollection.get(source.collection) ?? 0) + 1);
  }

  if (!apply) {
    console.log(JSON.stringify({
      ok: true,
      mode: 'dry-run',
      manifest: path.relative(repoRoot, manifestPath),
      version: manifest.version,
      jurisdiction: manifest.jurisdiction,
      sources: manifest.sources.length,
      collections: Object.fromEntries([...byCollection.entries()].sort()),
    }, null, 2));
    return;
  }

  const databaseUrl = process.env.DATABASE_URL;
  if (!databaseUrl) {
    throw new Error('DATABASE_URL is required when --apply is set');
  }
  const db = createDb(databaseUrl);
  try {
    await sql`SET RW_IMPLICIT_FLUSH = true`.execute(db);
    for (const source of manifest.sources) {
      await upsertSource(db, manifest, source);
    }
    await sql`FLUSH`.execute(db);
    console.log(JSON.stringify({
      ok: true,
      mode: 'apply',
      sources: manifest.sources.length,
      collections: Object.fromEntries([...byCollection.entries()].sort()),
    }, null, 2));
  } finally {
    await db.destroy();
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : error);
  process.exit(1);
});
