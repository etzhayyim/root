import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Count rollup MVs for app/worker read paths that still issued ad hoc COUNT(*)
 * queries against RisingWave tables.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_actor_subject_engagement AS
    WITH actor_keys AS (
      SELECT split_part(subject_uri, '/', 3) AS actor_did
      FROM edge_likes
      WHERE subject_uri LIKE 'at://did:%'
      UNION
      SELECT split_part(subject_uri, '/', 3) AS actor_did
      FROM edge_reposts
      WHERE subject_uri LIKE 'at://did:%'
    ),
    like_counts AS (
      SELECT split_part(subject_uri, '/', 3) AS actor_did, COUNT(*)::bigint AS like_count
      FROM edge_likes
      WHERE subject_uri LIKE 'at://did:%'
      GROUP BY 1
    ),
    repost_counts AS (
      SELECT split_part(subject_uri, '/', 3) AS actor_did, COUNT(*)::bigint AS repost_count
      FROM edge_reposts
      WHERE subject_uri LIKE 'at://did:%'
      GROUP BY 1
    )
    SELECT
      k.actor_did,
      COALESCE(l.like_count, 0) AS like_count,
      COALESCE(r.repost_count, 0) AS repost_count
    FROM actor_keys k
    LEFT JOIN like_counts l ON l.actor_did = k.actor_did
    LEFT JOIN repost_counts r ON r.actor_did = k.actor_did
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_spatial_count AS
    SELECT
      COALESCE(label, '') AS label,
      COALESCE(collection, '') AS collection,
      COUNT(*)::bigint AS cnt
    FROM vertex_spatial
    GROUP BY 1, 2
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_article_count_by_repo AS
    SELECT
      COALESCE(repo, '') AS repo,
      COUNT(*)::bigint AS cnt
    FROM vertex_article
    GROUP BY 1
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_scaffold_item_count_by_category AS
    SELECT
      COALESCE(category, '') AS category,
      COUNT(*)::bigint AS cnt
    FROM "vertex_ScaffoldItem"
    GROUP BY 1
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_security_count AS
    SELECT
      COALESCE(source, '') AS source,
      COALESCE(severity, '') AS severity,
      COUNT(*)::bigint AS cnt
    FROM vertex_security
    GROUP BY 1, 2
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_natural_person_count AS
    SELECT
      COALESCE(label, '') AS label,
      COALESCE(vital_status, '') AS vital_status,
      COALESCE(country, '') AS country,
      COALESCE(era, '') AS era,
      COALESCE(source_app, '') AS source_app,
      COUNT(*)::bigint AS cnt
    FROM vertex_natural_person
    GROUP BY 1, 2, 3, 4, 5
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_gov_org_count_by_domain_tier AS
    SELECT
      domain_code,
      '__all__'::varchar AS org_tier,
      COUNT(*)::bigint AS cnt
    FROM vertex_gov_org
    WHERE COALESCE(name_en, '') <> ''
    GROUP BY domain_code

    UNION ALL

    SELECT
      domain_code,
      COALESCE(org_tier, '') AS org_tier,
      COUNT(*)::bigint AS cnt
    FROM vertex_gov_org
    WHERE COALESCE(name_en, '') <> ''
    GROUP BY domain_code, COALESCE(org_tier, '')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_legal_entity_count_stat AS
    SELECT 'total'::varchar AS metric, ''::varchar AS key, COUNT(*)::bigint AS cnt
    FROM vertex_legal_entity

    UNION ALL

    SELECT 'country'::varchar AS metric, COALESCE(country, '') AS key, COUNT(*)::bigint AS cnt
    FROM vertex_legal_entity
    GROUP BY COALESCE(country, '')

    UNION ALL

    SELECT 'source'::varchar AS metric, COALESCE(source, '') AS key, COUNT(*)::bigint AS cnt
    FROM vertex_legal_entity
    GROUP BY COALESCE(source, '')
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_project_child_count AS
    SELECT
      parent_id,
      COUNT(*)::bigint AS cnt
    FROM vertex_project_props
    WHERE parent_id IS NOT NULL
    GROUP BY parent_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_project_reflection_count AS
    SELECT
      convo_id,
      COUNT(*)::bigint AS cnt
    FROM vertex_convo
    WHERE kind = 'ai.gftd.projector.reflection'
      AND convo_id IS NOT NULL
    GROUP BY convo_id
  `.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_shinka_activity_hourly AS
    SELECT
      activity_hour,
      SUM(post_count)::bigint AS post_count,
      SUM(kyumei_count)::bigint AS kyumei_count
    FROM (
      SELECT
        date_trunc('hour', created_date) AS activity_hour,
        COUNT(*)::bigint AS post_count,
        0::bigint AS kyumei_count
      FROM vertex_shinka_evolution
      WHERE COALESCE(CAST(props AS varchar), '') LIKE '%"didPost":true%'
      GROUP BY 1

      UNION ALL

      SELECT
        date_trunc('hour', created_date) AS activity_hour,
        0::bigint AS post_count,
        COUNT(*)::bigint AS kyumei_count
      FROM vertex_shinka_knowledge
      GROUP BY 1
    ) s
    GROUP BY activity_hour
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_shinka_activity_hourly`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_scaffold_item_count_by_category`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_article_count_by_repo`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_project_reflection_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_project_child_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_legal_entity_count_stat`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_gov_org_count_by_domain_tier`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_natural_person_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_security_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_vertex_spatial_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_actor_subject_engagement`.execute(db);
}
