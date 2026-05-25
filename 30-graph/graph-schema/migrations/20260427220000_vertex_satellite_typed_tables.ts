// ADR-2604271800 — maps L8 Sentinel pipeline Phase 2 typed tables.
//
// Pre-staged DDL for vertex_satellite_scene + vertex_satellite_analysis.
// Apply only after the RisingWave Smooth Scaling Gate clears
// (rw-health-gate.sh exit 0, no SlowDown/recovery in last 5 min).
//
// Phase 1 writes to vertex_repo_record with collections:
//   app.etzhayyim.apps.maps.satelliteScene
//   app.etzhayyim.apps.maps.satelliteAnalysis
//
// Phase 2 (this migration) adds typed tables. Once applied, update
// maps_sentinel.py to use vertex_satellite_scene / vertex_satellite_analysis
// via createKyselyDb(env.HYPERDRIVE) per ADR-0036.
//
// RisingWave constraints: no ON CONFLICT, no transactions. `CREATE TABLE IF
// NOT EXISTS` is idempotent DDL here; use `WHERE NOT EXISTS` for any seed INSERTs.

import type { Kysely } from "kysely";
import { sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_satellite_scene (
      vertex_id          VARCHAR PRIMARY KEY,
      repo               VARCHAR NOT NULL,
      scene_id           VARCHAR,
      platform           VARCHAR,
      date_time          VARCHAR,
      cloud_cover        DOUBLE PRECISION,
      bbox               VARCHAR,
      stac_collection_id VARCHAR,
      stac_self_url      VARCHAR,
      source_did         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR,
      created_at         VARCHAR,
      _seq               BIGINT,
      sensitivity_ord    INTEGER,
      owner_did          VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_scene_repo
      ON vertex_satellite_scene (repo)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_scene_platform
      ON vertex_satellite_scene (platform)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_scene_date_time
      ON vertex_satellite_scene (date_time)
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_satellite_analysis (
      vertex_id       VARCHAR PRIMARY KEY,
      repo            VARCHAR NOT NULL,
      scene_uri       VARCHAR,
      analysis_type   VARCHAR,
      baseline_uri    VARCHAR,
      model_version   VARCHAR,
      summary         VARCHAR,
      confidence      DOUBLE PRECISION,
      ok              BOOLEAN,
      source_did      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      created_at      VARCHAR,
      _seq            BIGINT,
      sensitivity_ord INTEGER,
      owner_did       VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_analysis_repo
      ON vertex_satellite_analysis (repo)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_analysis_scene_uri
      ON vertex_satellite_analysis (scene_uri)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_satellite_analysis_type
      ON vertex_satellite_analysis (analysis_type)
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP TABLE IF EXISTS vertex_satellite_analysis`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_satellite_scene`.execute(db);
}
