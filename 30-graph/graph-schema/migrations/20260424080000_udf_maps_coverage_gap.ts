import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0040 vertex tier declarations for tables created in this migration.
// tier: C

/**
 * RisingWave SQL UDF — maps domain coverage gap scoring (ADR-0044 SQL UDF tier).
 *
 * Backs `com.etzhayyim.apps.maps.advanceCoverage` XRPC and the
 * `00-contracts/bpmn/com/etzhayyim/maps/advanceCoverage.bpmn` timer-start BPMN
 * process (R/PT2M) that picks the next coverage gap every 2 minutes.
 *
 * Design (ADR-0044 §"Rule/regex/aggregate → SQL UDF"):
 *   - gap scoring is a pure arithmetic rule → plan-time inlined, native
 *     vector eval inside RisingWave. No per-row language boundary.
 *   - avoids shipping `vertex_maps_coverage_target` rows to the Worker
 *     to compute ranking; ORDER BY gap_score DESC LIMIT 1 stays server-side.
 *
 * Schema (minimal coverage frontier registry, NOT 1NF — promoted columns):
 *   vertex_maps_coverage_target (
 *     vertex_id         varchar PRIMARY KEY
 *                         at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/{sourceSlug}:{label}
 *     source_did        varchar  NOT NULL   -- did:web:maps.etzhayyim.com:registry:gleif etc.
 *     label             varchar  NOT NULL   -- LegalEntity / AdminArea / Airport / ...
 *     world_total       bigint   NOT NULL   -- upper-bound estimate (see ADR maps CLAUDE.md §Coverage Targets)
 *     collected_count   bigint   NOT NULL   -- current graph row count for this (source, label)
 *     priority_weight   real     NOT NULL   -- P0=1.0 / P1=0.6 / P2=0.3
 *     last_fetched_at   timestamp           -- NULL = never fetched
 *     ttl_hours         real     NOT NULL   -- staleness horizon (e.g. 168 = 7d)
 *     -- RLS
 *     org_id            varchar  NOT NULL   -- 'anon' allowed
 *     user_id           varchar  NOT NULL
 *     actor_id          varchar  NOT NULL
 *     created_at        varchar  NOT NULL
 *   )
 *
 * UDF contract:
 *   maps_coverage_gap_score(collected, world_total, priority_weight, hours_since_fetch) → double precision
 *
 *   = priority_weight
 *     × (1.0 − min(1.0, collected / max(world_total,1)))            -- completeness deficit [0,1]
 *     × min(10.0, 1.0 + coalesce(hours_since_fetch, ttl_hours_proxy) / 24.0)  -- staleness boost [1,10]
 *
 *   Higher = more urgent. Zero when coverage = 100%.
 *
 * View:
 *   view_maps_coverage_gap_ranked — plain VIEW (not MV). NOW() is forbidden in
 *   streaming MV SELECT per `30-graph/graph-schema/CLAUDE.md §MV Memory Safety`,
 *   and the row count is bounded (~50 source×label pairs today, scales sub-linearly
 *   with coverage DID count), so query-time computation is cheap.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  // 1. coverage frontier registry
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps_coverage_target (
      vertex_id        varchar NOT NULL PRIMARY KEY,
      source_did       varchar NOT NULL,
      label            varchar NOT NULL,
      world_total      bigint  NOT NULL,
      collected_count  bigint  NOT NULL DEFAULT 0,
      priority_weight  real    NOT NULL DEFAULT 0.5,
      last_fetched_at  timestamp,
      ttl_hours        real    NOT NULL DEFAULT 168.0,
      org_id           varchar NOT NULL DEFAULT 'anon',
      user_id          varchar NOT NULL DEFAULT 'anon',
      actor_id         varchar NOT NULL DEFAULT '',
      created_at       varchar NOT NULL
    )
  `.execute(db);

  // 2. UDF — gap score. Drop any pre-existing overload (including the
  //    initial (bigint,bigint,real,real) version from a partially-failed
  //    first apply) before creating the canonical signature.
  await sql`DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, real)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, double precision)`.execute(db);
  await sql`
    CREATE FUNCTION maps_coverage_gap_score(
      collected         bigint,
      world_total       bigint,
      priority_weight   real,
      hours_since_fetch double precision
    ) RETURNS double precision
    LANGUAGE sql
    AS $$
      SELECT
        COALESCE(priority_weight, 0.5)::double precision
        * (1.0 - LEAST(1.0,
            COALESCE(collected, 0)::double precision
              / GREATEST(COALESCE(world_total, 1), 1)::double precision))
        * LEAST(10.0, 1.0 + COALESCE(hours_since_fetch, 24.0)::double precision / 24.0)
    $$
  `.execute(db);

  // 3. Ranked view (plain VIEW — NOW() required for staleness)
  await sql`DROP VIEW IF EXISTS view_maps_coverage_gap_ranked`.execute(db);
  await sql`
    CREATE VIEW view_maps_coverage_gap_ranked AS
    SELECT
      vertex_id,
      source_did,
      label,
      collected_count,
      world_total,
      priority_weight,
      last_fetched_at,
      ttl_hours,
      CASE
        WHEN last_fetched_at IS NULL THEN ttl_hours
        ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
      END AS hours_since_fetch,
      maps_coverage_gap_score(
        collected_count,
        world_total,
        priority_weight,
        CASE
          WHEN last_fetched_at IS NULL THEN ttl_hours
          ELSE EXTRACT(EPOCH FROM (NOW() - last_fetched_at))::real / 3600.0
        END
      ) AS gap_score
    FROM vertex_maps_coverage_target
    ORDER BY gap_score DESC
  `.execute(db);

  // 4. Seed — 12 initial source×label frontier rows.
  //    world_total estimates sourced from 60-apps/etzhayyim-project-maps/CLAUDE.md
  //    §Coverage Targets. priority_weight: P0=1.0 / P1=0.6 / P2=0.3.
  const now = new Date().toISOString();
  const seed: Array<[string, string, number, number]> = [
    ["did:web:maps.etzhayyim.com:registry:gleif",         "LegalEntity",    2_500_000, 1.0],
    ["did:web:maps.etzhayyim.com:registry:jp-nta",        "LegalEntity",    6_000_000, 1.0],
    ["did:web:maps.etzhayyim.com:registry:wikidata",      "LegalEntity",      500_000, 1.0],
    ["did:web:maps.etzhayyim.com:registry:openaddresses", "Place",      1_000_000_000, 0.6],
    ["did:web:maps.etzhayyim.com:registry:opencorporates","LegalEntity",  200_000_000, 0.6],
    ["did:web:maps.etzhayyim.com:registry:osm",           "Place",         50_000_000, 0.3],
    ["did:web:maps.etzhayyim.com:infrastructure",         "Building",      10_000_000, 0.6],
    ["did:web:maps.etzhayyim.com:infrastructure",         "Airport",            3_000, 1.0],
    ["did:web:maps.etzhayyim.com:infrastructure",         "Station",           10_000, 0.6],
    ["did:web:maps.etzhayyim.com:infrastructure",         "AdminArea",          7_800, 1.0],
    ["did:web:maps.etzhayyim.com:satellite",              "SatelliteScene",   500_000, 0.3],
    ["did:web:maps.etzhayyim.com:gtfs",                   "BusRoute",          50_000, 0.6],
  ];
  for (const [sourceDid, label, worldTotal, priority] of seed) {
    const sourceSlug = sourceDid.replace(/^did:web:maps\.etzhayyim\.ai:?/, "") || "primary";
    const vid = `at://did:web:maps.etzhayyim.com/com.etzhayyim.apps.maps.coverageTarget/${sourceSlug.replace(/:/g, "-")}:${label}`;
    await sql`
      INSERT INTO vertex_maps_coverage_target (
        vertex_id, source_did, label, world_total, priority_weight,
        ttl_hours, org_id, user_id, actor_id, created_at
      ) VALUES (
        ${vid}, ${sourceDid}, ${label}, ${worldTotal}, ${priority},
        168.0, 'anon', 'anon', ${sourceDid}, ${now}
      )
    `.execute(db);
  }
  await sql`FLUSH`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_maps_coverage_gap_ranked`.execute(db);
  await sql`DROP FUNCTION IF EXISTS maps_coverage_gap_score(bigint, bigint, real, double precision)`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps_coverage_target`.execute(db);
}
