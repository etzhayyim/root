import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lora_adapter (
      vertex_id VARCHAR PRIMARY KEY,
      did VARCHAR NOT NULL,
      rkey VARCHAR NOT NULL,
      adapter_id VARCHAR NOT NULL,
      domain VARCHAR,
      status VARCHAR,
      value_json TEXT,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_lora_adapter_affinity (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR NOT NULL,
      dst_vid VARCHAR NOT NULL,
      src_label VARCHAR,
      dst_label VARCHAR,
      relation VARCHAR NOT NULL,
      weight DOUBLE PRECISION,
      created_at VARCHAR,
      owner_did VARCHAR,
      actor_id VARCHAR,
      sensitivity_ord BIGINT
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_did_status ON vertex_lora_adapter (did, status)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_adapter_id ON vertex_lora_adapter (adapter_id)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_lora_adapter_domain ON vertex_lora_adapter (domain)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_lora_adapter_affinity_dst ON edge_lora_adapter_affinity (dst_vid, dst_label)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_lora_adapter_affinity_src_label ON edge_lora_adapter_affinity (src_label)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_lora_adapter_actor_status AS
    SELECT did, status, count(*) AS adapter_count, max(created_at) AS latest_created_at
    FROM vertex_lora_adapter
    GROUP BY did, status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_lora_adapter_actor_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_lora_adapter_affinity`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lora_adapter`.execute(db);
}
