import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_social_profile (
      vertex_id VARCHAR PRIMARY KEY,
      did VARCHAR,
      handle VARCHAR,
      display_name VARCHAR,
      description TEXT,
      status VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      actor_id VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      created_at VARCHAR,
      updated_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_maps_social_profile_did ON vertex_maps_social_profile (did)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_maps_social_profile_handle ON vertex_maps_social_profile (handle)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_maps_social_profile_status ON vertex_maps_social_profile (status)`.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_maps_actor_profile (
      edge_id VARCHAR PRIMARY KEY,
      src_vid VARCHAR,
      dst_vid VARCHAR,
      relation VARCHAR,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      actor_id VARCHAR,
      created_at VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_edge_maps_actor_profile_src ON edge_maps_actor_profile (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_maps_actor_profile_dst ON edge_maps_actor_profile (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_maps_actor_profile_relation ON edge_maps_actor_profile (relation)`.execute(db);

  await sql`
    INSERT INTO edge_maps_actor_profile (
      edge_id, src_vid, dst_vid, relation, sensitivity_ord, owner_did, actor_id, created_at
    )
    SELECT
      'edge:maps:actor-profile:' || p.did,
      p.did,
      p.vertex_id,
      'HAS_SOCIAL_PROFILE',
      2,
      p.owner_did,
      p.actor_id,
      p.created_at
    FROM vertex_maps_social_profile p
    ON CONFLICT (edge_id) DO NOTHING
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_social_profile_status AS
    SELECT
      status,
      count(*) AS profile_count,
      max(updated_at) AS latest_updated_at
    FROM vertex_maps_social_profile
    GROUP BY status
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_maps_spatial_label_counts AS
    SELECT
      label,
      status,
      count(*) AS entity_count,
      max(created_at) AS latest_created_at
    FROM vertex_spatial
    GROUP BY label, status
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_spatial_label_counts`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_maps_social_profile_status`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_maps_actor_profile`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_social_profile`.execute(db);
}
