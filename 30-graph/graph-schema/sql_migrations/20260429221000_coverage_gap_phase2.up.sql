DROP MATERIALIZED VIEW IF EXISTS mv_coverage_gap_minimax;

CREATE TABLE IF NOT EXISTS vertex_coverage_stats (
      domain         text        NOT NULL,
      authority_kind text        NOT NULL DEFAULT 'world',
      collected      bigint      NOT NULL DEFAULT 0,
      world_total    bigint      NOT NULL DEFAULT 0,
      coverage_rate  double precision NOT NULL DEFAULT 0.0,
      updated_at     timestamptz NOT NULL DEFAULT now(),
      PRIMARY KEY (domain, authority_kind)
    );

DELETE FROM vertex_coverage_stats
    WHERE authority_kind = 'world'
      AND EXISTS (
        SELECT 1 FROM vertex_coverage_recipe r
        WHERE r.domain = vertex_coverage_stats.domain
          AND r.authority_kind = 'world'
      );

INSERT INTO vertex_coverage_stats (domain, authority_kind, collected, world_total, coverage_rate, updated_at)
    SELECT
      r.domain,
      r.authority_kind,
      0::bigint,
      r.world_total::bigint,
      0.0,
      now()
    FROM vertex_coverage_recipe r
    WHERE r.authority_kind = 'world';

CREATE MATERIALIZED VIEW mv_coverage_gap_minimax AS
    SELECT
      r.domain,
      r.authority_kind,
      r.recipe_kind,
      r.source_url,
      r.llm_tier,
      r.langgraph_id,
      COALESCE(s.world_total, r.world_total) AS world_total,
      COALESCE(s.collected, 0)               AS collected,
      COALESCE(s.coverage_rate, 0.0)         AS coverage_rate,
      r.notes,
      -- real regret = world_total * (1 - coverage_rate)
      CAST(COALESCE(s.world_total, r.world_total) AS double precision)
        * (1.0 - COALESCE(s.coverage_rate, 0.0))  AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    LEFT JOIN vertex_coverage_stats s
      ON s.domain = r.domain AND s.authority_kind = r.authority_kind
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC;
