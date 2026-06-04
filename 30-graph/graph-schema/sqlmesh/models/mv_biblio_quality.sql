MODEL (
  name etzhayyim_graph_schema.mv_biblio_quality,
  kind FULL
);

SELECT
  s.source_id,
  s.country_code,
  s.geopolitical_group,
  COUNT(DISTINCT r.vertex_id) AS raw_records,
  COUNT(DISTINCT e.vertex_id) AS normalized_entities,
  SUM(CASE WHEN e.canonical_label IS NULL OR e.canonical_label = '' THEN 1 ELSE 0 END) AS missing_label_entities,
  SUM(CASE WHEN e.publication_year IS NULL THEN 1 ELSE 0 END) AS missing_year_entities,
  SUM(CASE WHEN i.vertex_id IS NULL THEN 1 ELSE 0 END) AS entities_without_identifier,
  MAX(r.fetched_at) AS last_fetched_at
FROM vertex_biblio_source AS s
LEFT JOIN vertex_biblio_raw_record AS r
  ON r.source_id = s.source_id
LEFT JOIN vertex_biblio_entity AS e
  ON e.source_id = s.source_id
LEFT JOIN vertex_biblio_identifier AS i
  ON i.entity_vertex_id = e.vertex_id
WHERE s.status = 'active'
GROUP BY s.source_id, s.country_code, s.geopolitical_group
