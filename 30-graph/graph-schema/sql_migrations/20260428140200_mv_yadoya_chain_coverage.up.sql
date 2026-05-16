CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yadoya_chain_coverage AS
    SELECT
      COALESCE(chain_did, 'independent') AS chain_did,
      country,
      region,
      COUNT(*) AS hotel_count
    FROM vertex_yadoya_hotel
    WHERE status = 'published'
    GROUP BY COALESCE(chain_did, 'independent'), country, region;
