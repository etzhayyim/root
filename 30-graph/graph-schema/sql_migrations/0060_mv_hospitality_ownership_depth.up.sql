CREATE MATERIALIZED VIEW IF NOT EXISTS mv_hospitality_ownership_depth AS
    SELECT
      src_vid           AS parent_did,
      COUNT(*)          AS direct_children,
      MAX(_seq)         AS last_seq
    FROM edge_owned_by
    WHERE src_vid LIKE 'did:web:hospitality.etzhayyim.com:%'
    GROUP BY src_vid;
