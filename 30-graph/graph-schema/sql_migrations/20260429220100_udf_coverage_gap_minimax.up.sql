DROP FUNCTION IF EXISTS classify_coverage_recipe(text);

CREATE FUNCTION classify_coverage_recipe(p_domain text)
    RETURNS text
    LANGUAGE sql
    AS $$
      SELECT COALESCE(
        (SELECT recipe_kind FROM vertex_coverage_recipe
         WHERE domain = p_domain AND authority_kind = 'world'
         LIMIT 1),
        'defer'
      )
    $$;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_coverage_gap_minimax AS
    SELECT
      r.domain,
      r.authority_kind,
      r.recipe_kind,
      r.source_url,
      r.llm_tier,
      r.langgraph_id,
      r.world_total,
      r.notes,
      -- regret = world_total * (1 - estimated_coverage)
      -- Phase 1: coverage estimated as 0 for zero-collected domains
      CAST(r.world_total AS double precision) AS regret,
      r.created_at
    FROM vertex_coverage_recipe r
    WHERE r.recipe_kind != 'defer'
    ORDER BY regret DESC;
