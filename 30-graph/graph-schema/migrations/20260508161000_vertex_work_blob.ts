import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * vertex_work_blob — full-text store for copyright works.
 *
 * Populated by the copyright_fulltext LangGraph graph which calls the
 * Unpaywall API (https://api.unpaywall.org/v2/{doi}?email=jun@etzhayyim.com)
 * to discover open-access PDFs/HTML, then fetches and stores the
 * extracted text for CC-BY / CC0 / public-domain works.
 *
 * Only works with berne_automatic=true AND an open-access URL are
 * eligible. Fulltext is stored directly in RisingWave (VARCHAR) so
 * v_training_text can UNION ALL without external B2 fetches.
 *
 * status: pending → fetching → done | failed
 * license: e.g. cc-by, cc-by-sa, cc0, public-domain
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_work_blob (
      vertex_id       VARCHAR PRIMARY KEY,
      work_vertex_id  VARCHAR NOT NULL,
      doi             VARCHAR,
      source_url      VARCHAR,
      oa_url          VARCHAR,
      fulltext        VARCHAR,
      lang            VARCHAR,
      license         VARCHAR,
      fetched_at      VARCHAR,
      status          VARCHAR NOT NULL DEFAULT 'pending',
      error           VARCHAR,
      created_date    DATE,
      sensitivity_ord BIGINT DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE INDEX idx_vertex_work_blob_work_vertex_id
      ON vertex_work_blob(work_vertex_id)
  `.execute(db);

  await sql`
    CREATE INDEX idx_vertex_work_blob_status
      ON vertex_work_blob(status)
  `.execute(db);

  await sql`
    CREATE INDEX idx_vertex_work_blob_doi
      ON vertex_work_blob(doi)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_vertex_work_blob_doi`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_work_blob_status`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_vertex_work_blob_work_vertex_id`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_work_blob`.execute(db);
}
