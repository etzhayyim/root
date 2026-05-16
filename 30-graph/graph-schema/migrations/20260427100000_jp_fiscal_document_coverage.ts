import type { Kysely } from "kysely";
import { sql } from "kysely";

// JP fiscal source/document coverage projection.
// Keeps source registry, fetched document hash, and evidence edge status queryable.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE INDEX IF NOT EXISTS idx_jp_fiscal_document_sha
      ON vertex_jp_fiscal_document (sha256)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_evidence_src_kind
      ON edge_jp_fiscal_evidence (src_vid, evidence_kind)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_edge_jp_fiscal_evidence_dst_kind
      ON edge_jp_fiscal_evidence (dst_vid, evidence_kind)
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_source_document_coverage AS
    SELECT
      s.source_id,
      s.collection,
      s.title,
      s.publisher_did,
      s.source_url AS registered_source_url,
      s.access_kind,
      s.cadence,
      s.status AS source_status,
      d.vertex_id AS document_vertex_id,
      d.source_url AS fetched_source_url,
      d.fetched_at,
      d.media_type,
      d.sha256,
      d.byte_length,
      CASE WHEN d.vertex_id IS NULL THEN false ELSE true END AS fetched,
      CASE WHEN e.edge_id IS NULL THEN false ELSE true END AS has_evidence_edge
    FROM vertex_jp_fiscal_source s
    LEFT JOIN vertex_jp_fiscal_document d
      ON d.source_id = s.source_id
    LEFT JOIN edge_jp_fiscal_evidence e
      ON e.src_vid = s.vertex_id
     AND e.dst_vid = d.vertex_id
     AND e.evidence_kind = 'SOURCE_DOCUMENT'
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_jp_fiscal_collection_ingest_coverage AS
    SELECT
      collection,
      COUNT(*) AS source_count,
      SUM(CASE WHEN fetched THEN 1 ELSE 0 END) AS fetched_source_count,
      SUM(CASE WHEN has_evidence_edge THEN 1 ELSE 0 END) AS evidenced_source_count,
      SUM(COALESCE(byte_length, 0)) AS fetched_bytes
    FROM mv_jp_fiscal_source_document_coverage
    GROUP BY collection
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_collection_ingest_coverage`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_jp_fiscal_source_document_coverage`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jp_fiscal_evidence_dst_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_edge_jp_fiscal_evidence_src_kind`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_jp_fiscal_document_sha`.execute(db);
}
