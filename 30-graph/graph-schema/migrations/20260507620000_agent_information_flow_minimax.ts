import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_agent_information_node (
      vertex_id VARCHAR PRIMARY KEY,
      agent_did VARCHAR NOT NULL,
      info_ref VARCHAR NOT NULL,
      info_kind VARCHAR NOT NULL,
      abstraction_level BIGINT NOT NULL DEFAULT 0,
      confidence DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      uncertainty DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      protected_asset_ref VARCHAR,
      counterparty_ref VARCHAR,
      value_json VARCHAR NOT NULL,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      sensitivity_ord BIGINT DEFAULT 1,
      actor_id VARCHAR,
      owner_did VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_agent_information_depends_on (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      dependency_kind VARCHAR NOT NULL,
      weight DOUBLE PRECISION NOT NULL DEFAULT 1.0,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT DEFAULT 1
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_agent_information_flows_to (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      flow_kind VARCHAR NOT NULL,
      bandwidth_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      control_score DOUBLE PRECISION NOT NULL DEFAULT 0.5,
      created_at VARCHAR NOT NULL,
      updated_at VARCHAR NOT NULL,
      owner_did VARCHAR,
      sensitivity_ord BIGINT DEFAULT 1
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_node_agent_level ON vertex_agent_information_node (agent_did, abstraction_level)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_node_counterparty ON vertex_agent_information_node (counterparty_ref, info_kind)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_dep_src ON edge_agent_information_depends_on (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_dep_dst ON edge_agent_information_depends_on (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_flow_src ON edge_agent_information_flows_to (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_agent_info_flow_dst ON edge_agent_information_flows_to (dst_vid)`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_height`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_agent_information_height AS
    SELECT agent_did, counterparty_ref, info_kind,
           MAX(abstraction_level) AS max_information_height,
           COUNT(*)::BIGINT AS node_count
    FROM vertex_agent_information_node
    GROUP BY agent_did, counterparty_ref, info_kind
  `.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_flow_control`.execute(db);
  await sql`
    CREATE MATERIALIZED VIEW mv_agent_information_flow_control AS
    SELECT src_vid, COUNT(*)::BIGINT AS out_flow_count,
           AVG(control_score) AS avg_control_score,
           AVG(bandwidth_score) AS avg_bandwidth_score
    FROM edge_agent_information_flows_to
    GROUP BY src_vid
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_flow_control`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_agent_information_height`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_agent_information_flows_to`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_agent_information_depends_on`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_agent_information_node`.execute(db);
}
