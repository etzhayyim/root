CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_actor_coverage AS
    SELECT
      split_part(split_part(did, ':actor:', 2), ':', 1) AS kind,
      COUNT(*) AS actor_cnt
    FROM vertex_profile
    WHERE did LIKE 'did:web:hospitality.gftd.ai:actor:%'
    GROUP BY kind;
