import { Kysely, sql } from 'kysely';

/**
 * Oil coverage live read model.
 *
 * Kysely-facing MV that normalizes country x segment targets and compares them
 * to actual backbone entity counts from the oil supply chain tables.
 */
export async function up(db: Kysely<any>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS dim_oil_coverage_target (
    target_key text PRIMARY KEY,
    country_code text NOT NULL,
    segment text NOT NULL,
    actor_did text NOT NULL,
    app text NOT NULL,
    target_count bigint NOT NULL,
    priority bigint NOT NULL
  )`.execute(db);

  await sql`DELETE FROM dim_oil_coverage_target`.execute(db);

  await sql`INSERT INTO dim_oil_coverage_target (
    target_key, country_code, segment, actor_did, app, target_count, priority
  ) VALUES
    ('SA:upstream', 'SA', 'upstream', 'did:web:oil-upstream.etzhayyim.com', 'oil-upstream.etzhayyim.com', 25, 1),
    ('US:upstream', 'US', 'upstream', 'did:web:oil-upstream.etzhayyim.com', 'oil-upstream.etzhayyim.com', 40, 1),
    ('RU:upstream', 'RU', 'upstream', 'did:web:oil-upstream.etzhayyim.com', 'oil-upstream.etzhayyim.com', 25, 1),
    ('AE:upstream', 'AE', 'upstream', 'did:web:oil-upstream.etzhayyim.com', 'oil-upstream.etzhayyim.com', 15, 1),
    ('US:midstream', 'US', 'midstream', 'did:web:oil-midstream.etzhayyim.com', 'oil-midstream.etzhayyim.com', 30, 1),
    ('AE:midstream', 'AE', 'midstream', 'did:web:oil-midstream.etzhayyim.com', 'oil-midstream.etzhayyim.com', 12, 1),
    ('SG:midstream', 'SG', 'midstream', 'did:web:oil-midstream.etzhayyim.com', 'oil-midstream.etzhayyim.com', 10, 1),
    ('US:refining', 'US', 'refining', 'did:web:oil-refining.etzhayyim.com', 'oil-refining.etzhayyim.com', 25, 1),
    ('CN:refining', 'CN', 'refining', 'did:web:oil-refining.etzhayyim.com', 'oil-refining.etzhayyim.com', 20, 1),
    ('IN:refining', 'IN', 'refining', 'did:web:oil-refining.etzhayyim.com', 'oil-refining.etzhayyim.com', 12, 1),
    ('CH:trading', 'CH', 'trading', 'did:web:oil-trading.etzhayyim.com', 'oil-trading.etzhayyim.com', 10, 1),
    ('SG:trading', 'SG', 'trading', 'did:web:oil-trading.etzhayyim.com', 'oil-trading.etzhayyim.com', 10, 1),
    ('GR:shipping', 'GR', 'shipping', 'did:web:oil-shipping.etzhayyim.com', 'oil-shipping.etzhayyim.com', 15, 1),
    ('SG:shipping', 'SG', 'shipping', 'did:web:oil-shipping.etzhayyim.com', 'oil-shipping.etzhayyim.com', 12, 1),
    ('AE:shipping', 'AE', 'shipping', 'did:web:oil-shipping.etzhayyim.com', 'oil-shipping.etzhayyim.com', 12, 1),
    ('US:distribution', 'US', 'distribution', 'did:web:oil-distribution.etzhayyim.com', 'oil-distribution.etzhayyim.com', 20, 1),
    ('CN:distribution', 'CN', 'distribution', 'did:web:oil-distribution.etzhayyim.com', 'oil-distribution.etzhayyim.com', 20, 1),
    ('JP:distribution', 'JP', 'distribution', 'did:web:oil-distribution.etzhayyim.com', 'oil-distribution.etzhayyim.com', 10, 1)`.execute(db);

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
  await sql`DROP TABLE IF EXISTS dim_oil_coverage_target`.execute(db);
}
