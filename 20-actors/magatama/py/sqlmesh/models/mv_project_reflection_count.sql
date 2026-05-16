-- Project reflection count: per-convo projector reflection count.
MODEL (
  name dev.mv_project_reflection_count,
  kind FULL,
  dialect postgres,
  description 'Per convo_id: count of ai.gftd.projector.reflection records.',
  grain [convo_id],
  tags [project, reflection, count]
);

SELECT
  convo_id,
  COUNT(*)::BIGINT AS cnt
FROM vertex_convo
WHERE kind = 'ai.gftd.projector.reflection'
  AND convo_id IS NOT NULL
GROUP BY convo_id
