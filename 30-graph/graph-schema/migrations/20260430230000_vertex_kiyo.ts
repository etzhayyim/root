import type { Kysely } from "kysely";
import { sql } from "kysely";

// kiyo.etzhayyim.com — self-hosted research archive (紀要)
// paper_id format: kiyo:{YYYY}:{TID}
// file storage: ipfs.etzhayyim.com (CIDv1 content-addressed)
// ADR: 90-docs/adr/2604300000-kiyo-research-archive.md

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kiyo_paper (
      vertex_id         VARCHAR PRIMARY KEY,
      paper_id          VARCHAR NOT NULL,
      title             VARCHAR NOT NULL,
      abstract          TEXT    NOT NULL,
      subject           VARCHAR[],
      status            VARCHAR NOT NULL DEFAULT 'active',
      ipfs_cid          VARCHAR,
      source_ipfs_cid   VARCHAR,
      latest_version    INT     NOT NULL DEFAULT 1,
      embedding         double precision[],
      author_type       VARCHAR NOT NULL DEFAULT 'human',
      submitted_at      VARCHAR NOT NULL,
      owner_did         VARCHAR NOT NULL,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL DEFAULT 'anon',
      created_at        VARCHAR NOT NULL,
      sensitivity_ord   INT     NOT NULL DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kiyo_revision (
      vertex_id         VARCHAR PRIMARY KEY,
      paper_id          VARCHAR NOT NULL,
      version           INT     NOT NULL,
      ipfs_cid          VARCHAR NOT NULL,
      content_hash      VARCHAR NOT NULL,
      source_ipfs_cid   VARCHAR,
      submitted_at      VARCHAR NOT NULL,
      owner_did         VARCHAR NOT NULL,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL DEFAULT 'anon',
      created_at        VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kiyo_review (
      vertex_id         VARCHAR PRIMARY KEY,
      paper_id          VARCHAR NOT NULL,
      reviewer_did      VARCHAR NOT NULL,
      rating            INT,
      body              TEXT    NOT NULL,
      review_type       VARCHAR NOT NULL DEFAULT 'comment',
      owner_did         VARCHAR NOT NULL,
      actor_did         VARCHAR NOT NULL,
      org_did           VARCHAR NOT NULL DEFAULT 'anon',
      created_at        VARCHAR NOT NULL,
      sensitivity_ord   INT     NOT NULL DEFAULT 0
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_kiyo_authored_by (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      role              VARCHAR NOT NULL DEFAULT 'lead',
      order_num         INT     NOT NULL DEFAULT 0,
      created_at        VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_kiyo_cites (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      ref_label         VARCHAR,
      confidence        double precision NOT NULL DEFAULT 1.0,
      resolved_doi      VARCHAR,
      created_at        VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_kiyo_endorses (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR NOT NULL,
      dst_vid           VARCHAR NOT NULL,
      created_at        VARCHAR NOT NULL
    )
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kiyo_paper_stats AS
    SELECT
      p.paper_id,
      p.vertex_id,
      COUNT(DISTINCT c.edge_id)  AS citation_in_count,
      COUNT(DISTINCT r.vertex_id) AS review_count,
      COUNT(DISTINCT e.edge_id)  AS endorsement_count,
      MAX(v.version)              AS revision_count
    FROM vertex_kiyo_paper p
    LEFT JOIN edge_kiyo_cites      c ON c.dst_vid = p.vertex_id
    LEFT JOIN vertex_kiyo_review   r ON r.paper_id = p.paper_id
    LEFT JOIN edge_kiyo_endorses   e ON e.dst_vid  = p.vertex_id
    LEFT JOIN vertex_kiyo_revision v ON v.paper_id = p.paper_id
    GROUP BY p.paper_id, p.vertex_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kiyo_author_hindex AS
    SELECT
      a.dst_vid                              AS author_did,
      COUNT(DISTINCT a.src_vid)              AS total_papers,
      COALESCE(SUM(s.citation_in_count), 0)  AS total_citations
    FROM edge_kiyo_authored_by a
    LEFT JOIN mv_kiyo_paper_stats s ON s.vertex_id = a.src_vid
    GROUP BY a.dst_vid
  `.execute(db);

  // mv_kiyo_subject_stats omitted: RisingWave does not yet support
  // table functions (unnest) inside GROUP BY in streaming MVs.
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kiyo_author_hindex`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kiyo_paper_stats`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kiyo_endorses`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kiyo_cites`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kiyo_authored_by`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kiyo_review`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kiyo_revision`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kiyo_paper`.execute(db);
}
