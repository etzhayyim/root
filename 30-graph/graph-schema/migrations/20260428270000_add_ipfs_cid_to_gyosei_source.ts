import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Add IPFS CID columns to vertex_gyosei_source_blob.
 *
 * These columns are populated by capture_gyosei_sources_to_b2.py after
 * uploading each WebP/gyotaku to ipfs.etzhayyim.com (ADR-2604261936 Phase 1.5).
 *
 * ipfs_cid_document — CIDv1 of the full-page WebP (document.webp / gyotaku.webp)
 * ipfs_cid_thumbnail — CIDv1 of the thumbnail WebP (thumb.webp)
 *
 * Both columns are nullable — NULL means the source was captured before IPFS
 * integration or IPFS upload was skipped (--skip-ipfs flag).
 *
 * Public URL pattern: https://ipfs.etzhayyim.com/ipfs/{cid}
 *
 * Heavy DDL: applied via out-of-band path per ADR-2604241342. Tables are
 * never empty so ALTER TABLE goes through the DDL queue. Run:
 *   pnpm db:migrate latest
 * and wait for SHOW JOBS to clear before any bulk INSERT.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_gyosei_source_blob
      ADD COLUMN IF NOT EXISTS ipfs_cid_document  VARCHAR,
      ADD COLUMN IF NOT EXISTS ipfs_cid_thumbnail VARCHAR
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    ALTER TABLE vertex_gyosei_source_blob
      DROP COLUMN IF EXISTS ipfs_cid_document,
      DROP COLUMN IF EXISTS ipfs_cid_thumbnail
  `.execute(db);
}
