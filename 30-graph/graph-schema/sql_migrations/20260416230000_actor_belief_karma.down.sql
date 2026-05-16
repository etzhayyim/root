DROP MATERIALIZED VIEW IF EXISTS mv_belief_actor_coverage;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_karma_aggregate;

DROP MATERIALIZED VIEW IF EXISTS mv_actor_belief_karma;

DROP INDEX IF EXISTS idx_vertex_belief_system_tradition;

DROP INDEX IF EXISTS idx_edge_constrained_by_dst;

DROP INDEX IF EXISTS idx_edge_constrained_by_src;
