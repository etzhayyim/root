CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_tier_coverage AS
    SELECT
      CASE split_part(split_part(did, ':actor:', 2), ':', 1)
        WHEN 'assoc'    THEN 'R1'
        WHEN 'ota'      THEN 'R2'
        WHEN 'chain'    THEN 'R3'
        WHEN 'cruise'   THEN 'R3'
        WHEN 'property' THEN 'R4'
        ELSE 'unknown'
      END                                                   AS tier,
      split_part(split_part(did, ':actor:', 2), ':', 1)     AS kind,
      COUNT(*)                                              AS actor_cnt
    FROM vertex_profile
    WHERE did LIKE 'did:web:hospitality.etzhayyim.com:actor:%'
    GROUP BY tier, kind;
