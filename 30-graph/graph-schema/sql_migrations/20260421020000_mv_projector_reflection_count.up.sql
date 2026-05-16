CREATE MATERIALIZED VIEW IF NOT EXISTS mv_projector_reflection_count AS
    SELECT
      convo_id,
      COUNT(*)::bigint AS cnt
    FROM vertex_projector_reflection
    WHERE convo_id IS NOT NULL
    GROUP BY convo_id;
