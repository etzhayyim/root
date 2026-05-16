import { Kysely, sql } from 'kysely';

/**
 * Migration 0022: refresh oil coverage MVs for trading/distribution.
 *
 * Prod already has 0020 applied with earlier definitions where trading was
 * derived from trader companies and distribution from refineries. Recreate the
 * MVs so coverage reflects vertex_oil_trade and vertex_product_terminal.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_oil_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_oil_backbone_count`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_backbone_count AS
    SELECT country_code, 'upstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_field
    GROUP BY country_code

    UNION ALL

    SELECT COALESCE(split_part(locode, '-', 1), 'ZZ') AS country_code, 'midstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_terminal
    GROUP BY COALESCE(split_part(locode, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'refining'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_refinery
    GROUP BY country_code

    UNION ALL

    SELECT country_code, 'trading'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_trade
    GROUP BY country_code

    UNION ALL

    SELECT COALESCE(split_part(load_port, '-', 1), 'ZZ') AS country_code, 'shipping'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_cargo
    GROUP BY COALESCE(split_part(load_port, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'distribution'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_product_terminal
    GROUP BY country_code`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_coverage_live AS
    SELECT
      t.target_key,
      t.country_code,
      t.segment,
      t.actor_did,
      t.app,
      t.target_count,
      t.priority,
      COALESCE(b.actual_count, 0) AS actual_count,
      CASE
        WHEN t.target_count > 0 THEN COALESCE(b.actual_count, 0)::double precision / t.target_count::double precision
        ELSE 0.0
      END AS coverage_rate,
      GREATEST(t.target_count - COALESCE(b.actual_count, 0), 0) AS coverage_gap
    FROM dim_oil_coverage_target t
    LEFT JOIN mv_oil_backbone_count b
      ON b.country_code = t.country_code
     AND b.segment = t.segment`.execute(db);
}

export async function down(db: Kysely<any>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_oil_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_oil_backbone_count`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_backbone_count AS
    SELECT country_code, 'upstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_field
    GROUP BY country_code

    UNION ALL

    SELECT COALESCE(split_part(locode, '-', 1), 'ZZ') AS country_code, 'midstream'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_terminal
    GROUP BY COALESCE(split_part(locode, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'refining'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_refinery
    GROUP BY country_code

    UNION ALL

    SELECT hq_country AS country_code, 'trading'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_company
    WHERE company_type = 'trader'
    GROUP BY hq_country

    UNION ALL

    SELECT COALESCE(split_part(load_port, '-', 1), 'ZZ') AS country_code, 'shipping'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_oil_cargo
    GROUP BY COALESCE(split_part(load_port, '-', 1), 'ZZ')

    UNION ALL

    SELECT country_code, 'distribution'::text AS segment, COUNT(*)::bigint AS actual_count
    FROM vertex_refinery
    GROUP BY country_code`.execute(db);

  await sql`CREATE MATERIALIZED VIEW IF NOT EXISTS mv_oil_coverage_live AS
    SELECT
      t.target_key,
      t.country_code,
      t.segment,
      t.actor_did,
      t.app,
      t.target_count,
      t.priority,
      COALESCE(b.actual_count, 0) AS actual_count,
      CASE
        WHEN t.target_count > 0 THEN COALESCE(b.actual_count, 0)::double precision / t.target_count::double precision
        ELSE 0.0
      END AS coverage_rate,
      GREATEST(t.target_count - COALESCE(b.actual_count, 0), 0) AS coverage_gap
    FROM dim_oil_coverage_target t
    LEFT JOIN mv_oil_backbone_count b
      ON b.country_code = t.country_code
     AND b.segment = t.segment`.execute(db);
}
