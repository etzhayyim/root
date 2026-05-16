DROP MATERIALIZED VIEW IF EXISTS mv_coverage_gap_minimax;

DROP TABLE IF EXISTS vertex_coverage_stats;

CREATE MATERIALIZED VIEW mv_coverage_gap_minimax AS
    SELECT
      r.domain, r.authority_kind, r.recipe_kind, r.source_url, r.llm_tier,
      r.langgraph_id, r.world_total, r.notes,
      CAST(r.world_total AS double precision) AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC;
