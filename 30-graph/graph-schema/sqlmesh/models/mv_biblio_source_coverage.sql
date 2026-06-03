MODEL (
  name etzhayyim_graph_schema.mv_biblio_source_coverage,
  kind FULL
);

SELECT
  s.geopolitical_group,
  s.country_code,
  s.country_name,
  s.source_id,
  s.institution_name,
  s.service_name,
  s.machine_readability,
  s.access_protocols,
  COUNT(DISTINCT r.vertex_id) AS raw_record_count,
  COUNT(DISTINCT e.vertex_id) AS entity_count,
  COUNT(DISTINCT i.vertex_id) AS identifier_count,
  COUNT(DISTINCT rel.edge_id) AS relation_count,
  MAX(r.fetched_at) AS last_fetched_at
FROM vertex_biblio_source AS s
LEFT JOIN vertex_biblio_raw_record AS r
  ON r.source_id = s.source_id
LEFT JOIN vertex_biblio_entity AS e
  ON e.source_id = s.source_id
LEFT JOIN vertex_biblio_identifier AS i
  ON i.source_id = s.source_id
LEFT JOIN edge_biblio_relation AS rel
  ON rel.source_id = s.source_id
WHERE s.status = 'active'
GROUP BY
  s.geopolitical_group,
  s.country_code,
  s.country_name,
  s.source_id,
  s.institution_name,
  s.service_name,
  s.machine_readability,
  s.access_protocols
