import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_kami_flow_node (
      vertex_id VARCHAR PRIMARY KEY,
      rkey VARCHAR,
      repo VARCHAR,
      node_label VARCHAR NOT NULL,
      did VARCHAR,
      collection VARCHAR,
      status VARCHAR,
      props TEXT,
      created_at VARCHAR,
      _alive BOOLEAN,
      _seq BIGINT,
      timestamp_ms BIGINT,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_kami_flow_relation (
      edge_id VARCHAR PRIMARY KEY,
      relation_label VARCHAR NOT NULL,
      rkey VARCHAR,
      repo VARCHAR,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_label VARCHAR,
      dst_label VARCHAR,
      weight DOUBLE PRECISION,
      props TEXT,
      created_at VARCHAR,
      _alive BOOLEAN,
      _seq BIGINT,
      timestamp_ms BIGINT,
      owner_did VARCHAR,
      actor_did VARCHAR,
      org_did VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_node_repo_label ON vertex_kami_flow_node (repo, node_label)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_node_collection ON vertex_kami_flow_node (collection)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_repo_label ON edge_kami_flow_relation (repo, relation_label)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_src ON edge_kami_flow_relation (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_dst ON edge_kami_flow_relation (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_src_label ON edge_kami_flow_relation (src_label)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_kami_flow_relation_dst_label ON edge_kami_flow_relation (dst_label)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_flow_node_label_counts AS
    SELECT repo, node_label, count(*) AS cnt
    FROM vertex_kami_flow_node
    WHERE _alive IS DISTINCT FROM false
    GROUP BY repo, node_label
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_kami_flow_relation_label_counts AS
    SELECT repo, relation_label, count(*) AS cnt
    FROM edge_kami_flow_relation
    WHERE _alive IS DISTINCT FROM false
    GROUP BY repo, relation_label
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kami_flow_relation_label_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_kami_flow_node_label_counts`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_kami_flow_relation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_kami_flow_node`.execute(db);
}
