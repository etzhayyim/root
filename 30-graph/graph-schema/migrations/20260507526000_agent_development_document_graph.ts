import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: C

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_development_document (
      vertex_id VARCHAR PRIMARY KEY,
      doc_id VARCHAR NOT NULL,
      doc_type VARCHAR NOT NULL,
      title TEXT,
      summary TEXT,
      body_text TEXT,
      source_path VARCHAR,
      status VARCHAR,
      agent_did VARCHAR,
      topic VARCHAR,
      tags_json TEXT,
      related_ref VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR,
      sensitivity_ord BIGINT,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_agent_development_document_ref (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      relation_kind VARCHAR NOT NULL,
      ref_kind VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      updated_at VARCHAR,
      owner_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_id ON vertex_agent_development_document (doc_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_topic_status ON vertex_agent_development_document (topic, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_doc_updated ON vertex_agent_development_document (updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_src ON edge_agent_development_document_ref (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_dst ON edge_agent_development_document_ref (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_dev_edge_kind ON edge_agent_development_document_ref (relation_kind, ref_kind)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_status_counts`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_agent_development_document_status_counts AS
    SELECT topic, doc_type, status, count(*)::BIGINT AS document_count
    FROM vertex_agent_development_document
    GROUP BY topic, doc_type, status
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_latest`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_agent_development_document_latest AS
    SELECT doc_id, doc_type, title, topic, status, updated_at, agent_did, related_ref
    FROM vertex_agent_development_document
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_latest`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_development_document_status_counts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_agent_development_document_ref`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_development_document`.execute(db);
}
