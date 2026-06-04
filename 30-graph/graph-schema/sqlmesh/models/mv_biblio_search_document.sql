MODEL (
  name etzhayyim_graph_schema.mv_biblio_search_document,
  kind FULL
);

SELECT
  e.vertex_id,
  e.entity_type,
  e.canonical_label,
  e.normalized_label,
  e.language,
  e.country_code,
  e.publication_year,
  e.source_id,
  s.country_name,
  s.institution_name,
  s.service_name,
  e.source_record_id,
  e.source_url,
  e.metadata_json,
  i.identifier_scheme,
  i.normalized_value AS identifier_value
FROM vertex_biblio_entity AS e
LEFT JOIN vertex_biblio_source AS s
  ON s.source_id = e.source_id
LEFT JOIN vertex_biblio_identifier AS i
  ON i.entity_vertex_id = e.vertex_id
WHERE e.status = 'active'
