-- Adds image_post_count to mv_shinshi_repo_stats.
-- post_count counted ALL posts (text-only + image-embedded), so models with 5
-- text-only posts from the old BPMN pipeline were incorrectly excluded from
-- coverage_gap_fill (post_count >= 5 → filtered out → never re-seeded).
-- image_post_count counts only posts with app.bsky.embed.images embeds.
--
-- DROP+CREATE required — RisingWave streaming MVs cannot be altered in-place.
-- Apply via psycopg2 in the multi-head Alembic workaround pattern (2026-05-12).
-- Phase order: DROP → CREATE (no index step needed, MV is small ~1649 rows).

DROP MATERIALIZED VIEW IF EXISTS mv_shinshi_repo_stats;

CREATE MATERIALIZED VIEW mv_shinshi_repo_stats AS
SELECT
  repo,
  COUNT(*) FILTER (WHERE collection = 'ai.gftd.apps.shinshi.modelProfile') AS model_profile_count,
  COUNT(*) FILTER (WHERE collection = 'app.bsky.feed.post') AS post_count,
  COUNT(*) FILTER (
    WHERE collection = 'app.bsky.feed.post'
      AND value_json LIKE '%"app.bsky.embed.images"%'
  ) AS image_post_count
FROM vertex_repo_record
WHERE repo LIKE 'did:web:sh1n5h1x.gftd.ai:%'
  AND repo != 'did:web:sh1n5h1x.gftd.ai'
  AND collection IN ('ai.gftd.apps.shinshi.modelProfile', 'app.bsky.feed.post')
GROUP BY repo;
