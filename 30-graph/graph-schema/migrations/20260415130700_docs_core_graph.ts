import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: B

/**
 * Migration 0074: docs core graph spine.
 *
 * Source collections:
 *   - app.etzhayyim.apps.docs.docsEntity
 *   - app.etzhayyim.apps.docs.docsEvent
 *   - app.etzhayyim.apps.docs.docsReport
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_docs_entity (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      entity_id         VARCHAR,
      doc_id            VARCHAR,
      title             VARCHAR,
      doc_type          VARCHAR,
      status            VARCHAR,
      author_did        VARCHAR,
      parent_entity_id  VARCHAR,
      tags_json         VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_entity_entity_id ON vertex_docs_entity (entity_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_entity_doc_type ON vertex_docs_entity (doc_type)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_docs_event (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      event_id          VARCHAR,
      entity_id         VARCHAR,
      event_type        VARCHAR,
      summary           VARCHAR,
      actor_did         VARCHAR,
      occurred_at       VARCHAR,
      created_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_event_event_id ON vertex_docs_event (event_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_event_entity_id ON vertex_docs_event (entity_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_docs_report (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      report_id         VARCHAR,
      entity_id         VARCHAR,
      report_type       VARCHAR,
      title             VARCHAR,
      status            VARCHAR,
      period_start      VARCHAR,
      period_end        VARCHAR,
      generated_by_did  VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_report_report_id ON vertex_docs_report (report_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_vertex_docs_report_entity_id ON vertex_docs_report (entity_id)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_docs_event_entity (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      relation_kind     VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_docs_event_entity_src ON edge_docs_event_entity (src_vid)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_docs_report_entity (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      relation_kind     VARCHAR,
      linked_at         VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_docs_report_entity_src ON edge_docs_report_entity (src_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_docs_entity_activity AS
    SELECT
      e.entity_id,
      COUNT(*) AS event_count,
      MAX(e.occurred_at) AS last_event_at,
      MAX(e._seq) AS last_seq
    FROM vertex_docs_event e
    WHERE e.entity_id IS NOT NULL
    GROUP BY e.entity_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_docs_report_freshness AS
    SELECT
      r.entity_id,
      COUNT(*) AS report_count,
      MAX(r.updated_at) AS last_report_at,
      MAX(r._seq) AS last_seq
    FROM vertex_docs_report r
    WHERE r.entity_id IS NOT NULL
    GROUP BY r.entity_id
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_docs_report_freshness`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_docs_entity_activity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_docs_report_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_docs_event_entity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_docs_report`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_docs_event`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_docs_entity`.execute(db);
}
