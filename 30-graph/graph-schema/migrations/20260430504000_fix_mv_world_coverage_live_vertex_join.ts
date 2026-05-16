import { Kysely, sql } from "kysely";

/**
 * Fix mv_world_coverage_live: vertex_count was hardcoded to CAST(0 AS BIGINT).
 * The view was missing the LEFT JOIN to mv_world_vertex_per_host, so all domains
 * showed vertex_count=0 even after mv_world_vertex_per_host was recreated.
 * Applied out-of-band 2026-04-30 after mv_world_vertex_per_host was restored
 * (migration 20260430502000). Insert kysely_migration row manually after apply.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);

  await sql`
    CREATE VIEW mv_world_coverage_live AS
    WITH gov_override AS (
      SELECT CAST('gov' AS CHARACTER VARYING) AS domain,
             government_org_count AS record_count,
             CAST(0 AS BIGINT) AS vertex_count
      FROM mv_gov_coverage_dedup
      UNION ALL
      SELECT CAST('gov_admin_area' AS CHARACTER VARYING),
             admin_area_count,
             CAST(0 AS BIGINT)
      FROM mv_gov_coverage_dedup
    ),
    domain_counts AS (
      SELECT d.domain, d.app_host, d.world_total, d.unit, d.sector,
        CAST(COALESCE(p.did_count, 0) AS BIGINT) AS did_count,
        CASE WHEN go.domain IS NOT NULL THEN go.record_count
             ELSE CAST(COALESCE(r.record_count, 0) AS BIGINT) END AS record_count,
        CAST(COALESCE(v.vertex_count, 0) AS BIGINT) AS vertex_count
      FROM dim_world_domain AS d
      LEFT JOIN mv_world_did_per_host    AS p  ON p.app_host = d.app_host
      LEFT JOIN mv_world_record_per_host AS r  ON r.app_host = d.app_host
      LEFT JOIN gov_override             AS go ON go.domain  = d.domain
      LEFT JOIN mv_world_vertex_per_host AS v  ON v.app_host = d.app_host
    )
    SELECT domain, app_host, world_total, unit, sector,
      did_count, record_count, vertex_count,
      GREATEST(did_count, record_count, vertex_count) AS collected,
      CASE WHEN world_total > 0
           THEN CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 0.0 END AS coverage_rate,
      CASE WHEN world_total > 0
           THEN 1.0 - CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 1.0 END AS gap_rate,
      CAST(GREATEST(world_total - GREATEST(did_count, record_count, vertex_count), 0) AS BIGINT) AS remaining
    FROM domain_counts
  `.execute(db);

  await sql`
    CREATE VIEW view_world_coverage_live AS SELECT * FROM mv_world_coverage_live
  `.execute(db);

  // Grant to non-superuser roles (rw_admin is owner; root/kaisya_app need explicit grants)
  await sql`GRANT SELECT ON mv_world_coverage_live TO root`.execute(db);
  await sql`GRANT SELECT ON view_world_coverage_live TO root`.execute(db);
  await sql`GRANT SELECT ON mv_world_coverage_live TO kaisya_app`.execute(db);
  await sql`GRANT SELECT ON view_world_coverage_live TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS view_world_coverage_live`.execute(db);
  await sql`DROP VIEW IF EXISTS mv_world_coverage_live`.execute(db);

  // Restore the broken version (vertex_count hardcoded to 0) for rollback parity.
  await sql`
    CREATE VIEW mv_world_coverage_live AS
    WITH gov_override AS (
      SELECT CAST('gov' AS CHARACTER VARYING) AS domain,
             government_org_count AS record_count,
             CAST(0 AS BIGINT) AS vertex_count
      FROM mv_gov_coverage_dedup
      UNION ALL
      SELECT CAST('gov_admin_area' AS CHARACTER VARYING),
             admin_area_count,
             CAST(0 AS BIGINT)
      FROM mv_gov_coverage_dedup
    ),
    domain_counts AS (
      SELECT d.domain, d.app_host, d.world_total, d.unit, d.sector,
        CAST(COALESCE(p.did_count, 0) AS BIGINT) AS did_count,
        CASE WHEN go.domain IS NOT NULL THEN go.record_count
             ELSE CAST(COALESCE(r.record_count, 0) AS BIGINT) END AS record_count,
        CAST(0 AS BIGINT) AS vertex_count
      FROM dim_world_domain AS d
      LEFT JOIN mv_world_did_per_host    AS p  ON p.app_host = d.app_host
      LEFT JOIN mv_world_record_per_host AS r  ON r.app_host = d.app_host
      LEFT JOIN gov_override             AS go ON go.domain  = d.domain
    )
    SELECT domain, app_host, world_total, unit, sector,
      did_count, record_count, vertex_count,
      GREATEST(did_count, record_count, vertex_count) AS collected,
      CASE WHEN world_total > 0
           THEN CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 0.0 END AS coverage_rate,
      CASE WHEN world_total > 0
           THEN 1.0 - CAST(GREATEST(did_count, record_count, vertex_count) AS DOUBLE) / CAST(world_total AS DOUBLE)
           ELSE 1.0 END AS gap_rate,
      CAST(GREATEST(world_total - GREATEST(did_count, record_count, vertex_count), 0) AS BIGINT) AS remaining
    FROM domain_counts
  `.execute(db);

  await sql`
    CREATE VIEW view_world_coverage_live AS SELECT * FROM mv_world_coverage_live
  `.execute(db);
}
