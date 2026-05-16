import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Restore domain coverage materialized views when they are missing/drifted.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`CREATE TABLE IF NOT EXISTS dim_domain_coverage_target (
    kind text PRIMARY KEY,
    repo text NOT NULL,
    app text NOT NULL,
    authority_target bigint NOT NULL,
    rule_target bigint NOT NULL,
    scope_target bigint NOT NULL,
    total_target bigint NOT NULL,
    authority_seed bigint NOT NULL,
    rule_seed bigint NOT NULL,
    scope_seed bigint NOT NULL,
    total_seed bigint NOT NULL,
    authority_table text NOT NULL,
    authority_kind text NOT NULL
  )`.execute(db);

  await sql`DELETE FROM dim_domain_coverage_target`.execute(db);

  await sql`INSERT INTO dim_domain_coverage_target (
    kind, repo, app,
    authority_target, rule_target, scope_target, total_target,
    authority_seed, rule_seed, scope_seed, total_seed,
    authority_table, authority_kind
  ) VALUES
    ('sovereign', 'did:web:states.gftd.ai', 'states.gftd.ai', 195, 195000, 195, 195390, 195, 390, 195, 780, 'vertex_authority_sovereign', 'sovereign'),
    ('treaty', 'did:web:treaty.gftd.ai', 'treaty.gftd.ai', 500, 5000, 50, 5550, 48, 85, 18, 151, 'vertex_authority_treaty', 'treaty'),
    ('religious', 'did:web:religious.gftd.ai', 'religious.gftd.ai', 30, 3000, 10, 3040, 25, 60, 10, 95, 'vertex_authority_religious', 'religious'),
    ('community', 'did:web:communities.gftd.ai', 'communities.gftd.ai', 100, 1000, 20, 1120, 69, 35, 8, 112, 'vertex_authority_community', 'community'),
    ('customary', 'did:web:customary.gftd.ai', 'customary.gftd.ai', 100, 500, 50, 650, 28, 40, 12, 80, 'vertex_authority_customary', 'customary'),
    ('family', 'did:web:tradition.gftd.ai', 'tradition.gftd.ai', 500, 2000, 100, 2600, 25, 30, 12, 67, 'vertex_authority_customary', 'customary'),
    ('cultural', 'did:web:tradition.gftd.ai', 'tradition.gftd.ai', 200, 1000, 50, 1250, 30, 24, 12, 66, 'vertex_authority_customary', 'customary'),
    ('professional', 'did:web:ethics.gftd.ai', 'ethics.gftd.ai', 100, 500, 30, 630, 24, 48, 12, 84, 'vertex_authority_professional', 'professional'),
    ('academic', 'did:web:ethics.gftd.ai', 'ethics.gftd.ai', 50, 200, 10, 260, 10, 18, 5, 33, 'vertex_authority_professional', 'professional'),
    ('industry', 'did:web:industry-standard.gftd.ai', 'industry-standard.gftd.ai', 200, 3000, 50, 3250, 42, 60, 15, 117, 'vertex_authority_industry', 'industry'),
    ('blockchain', 'did:web:blockchain.gftd.ai', 'blockchain.gftd.ai', 100, 5000, 200, 5300, 30, 65, 20, 115, 'vertex_authority_blockchain', 'blockchain')`.execute(db);

  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_repo_authority_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_repo_did_count`.execute(db);

  await sql`CREATE MATERIALIZED VIEW mv_domain_repo_did_count AS
    SELECT t.kind, t.repo, COUNT(*)::bigint AS did_count
    FROM dim_domain_coverage_target t
    LEFT JOIN vertex_did d ON d.repo = t.repo
    GROUP BY t.kind, t.repo`.execute(db);

  await sql`CREATE MATERIALIZED VIEW mv_domain_repo_authority_count AS
    SELECT 'sovereign'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_sovereign GROUP BY repo
    UNION ALL
    SELECT 'treaty'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_treaty GROUP BY repo
    UNION ALL
    SELECT 'religious'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_religious GROUP BY repo
    UNION ALL
    SELECT 'customary'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_customary GROUP BY repo
    UNION ALL
    SELECT 'community'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_community GROUP BY repo
    UNION ALL
    SELECT 'professional'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_professional GROUP BY repo
    UNION ALL
    SELECT 'industry'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_industry GROUP BY repo
    UNION ALL
    SELECT 'blockchain'::text AS authority_kind, repo, COUNT(*)::bigint AS authority_count FROM vertex_authority_blockchain GROUP BY repo`.execute(db);

  await sql`CREATE MATERIALIZED VIEW mv_domain_coverage_live AS
    SELECT
      t.kind,
      t.repo,
      t.app,
      t.authority_kind,
      t.authority_seed,
      t.rule_seed,
      t.scope_seed,
      t.total_seed,
      t.authority_target,
      t.rule_target,
      t.scope_target,
      t.total_target,
      COALESCE(d.did_count, 0) AS did_count,
      COALESCE(a.authority_count, 0) AS authority_count,
      COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0) AS live_record_count,
      CASE WHEN t.total_target > 0
        THEN COALESCE(d.did_count, 0)::double precision / t.total_target::double precision
        ELSE 0.0
      END AS live_coverage_did,
      CASE WHEN t.total_target > 0
        THEN (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS live_coverage_record,
      CASE WHEN t.total_target > 0
        THEN t.total_seed::double precision / t.total_target::double precision
        ELSE 0.0
      END AS authority_rate,
      CASE WHEN t.total_target > 0
        THEN (t.total_seed - COALESCE(d.did_count, 0))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS delta_did,
      CASE WHEN t.total_target > 0
        THEN (t.total_seed - (COALESCE(d.did_count, 0) + COALESCE(a.authority_count, 0)))::double precision / t.total_target::double precision
        ELSE 0.0
      END AS delta_record
    FROM dim_domain_coverage_target t
    LEFT JOIN mv_domain_repo_did_count d ON d.kind = t.kind AND d.repo = t.repo
    LEFT JOIN mv_domain_repo_authority_count a ON a.authority_kind = t.authority_kind AND a.repo = t.repo`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_coverage_live`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_repo_authority_count`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_repo_did_count`.execute(db);
}

