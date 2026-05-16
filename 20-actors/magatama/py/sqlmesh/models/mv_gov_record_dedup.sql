-- Gov record dedup: deduplicated government records from vertex_repo_record.
MODEL (
  name dev.mv_gov_record_dedup,
  kind FULL,
  dialect postgres,
  description 'Deduplicated gov records: one row per (entity_kind, entity_id) with latest seq and metadata.',
  grain [entity_kind, entity_id],
  tags [gov, record, dedup]
);

SELECT
  collection AS entity_kind,
  LOWER(COALESCE(NULLIF(repo, ''), rkey)) AS entity_id,
  MAX(_seq) AS last_seq,
  MAX(ts_ms) AS last_ts_ms,
  COUNT(*) AS record_count
FROM vertex_repo_record
WHERE collection IN (
  'ai.gftd.apps.gov.org',
  'ai.gftd.apps.gov.person',
  'ai.gftd.apps.gov.budget',
  'ai.gftd.apps.gov.contract',
  'ai.gftd.apps.states.org'
)
GROUP BY collection, LOWER(COALESCE(NULLIF(repo, ''), rkey))
