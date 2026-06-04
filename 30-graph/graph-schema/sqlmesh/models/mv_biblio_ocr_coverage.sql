MODEL (
  name etzhayyim_graph_schema.mv_biblio_ocr_coverage,
  kind FULL
);

SELECT
  p.source_id,
  s.country_code,
  s.country_name,
  COUNT(DISTINCT p.vertex_id) AS page_asset_count,
  COUNT(DISTINCT o.vertex_id) AS ocr_text_count,
  SUM(p.webp_byte_size) AS webp_bytes,
  MAX(p.updated_at) AS last_page_updated_at,
  MAX(o.created_at) AS last_ocr_created_at
FROM vertex_biblio_page_asset AS p
LEFT JOIN vertex_biblio_ocr_text AS o
  ON o.source_id = p.source_id
  AND o.source_record_id = p.source_record_id
  AND o.page_index = p.page_index
LEFT JOIN vertex_biblio_source AS s
  ON s.source_id = p.source_id
WHERE p.status = 'active'
GROUP BY p.source_id, s.country_code, s.country_name
