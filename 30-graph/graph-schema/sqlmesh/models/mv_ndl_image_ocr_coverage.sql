MODEL (
  name etzhayyim_graph_schema.mv_ndl_image_ocr_coverage,
  kind FULL
);

SELECT
  i.provider_id,
  COUNT(DISTINCT i.pid) AS item_count,
  COUNT(p.vertex_id) AS page_count,
  COUNT(o.vertex_id) AS ocr_page_count,
  SUM(p.webp_byte_size) AS webp_bytes
FROM vertex_ndl_digital_item AS i
LEFT JOIN vertex_ndl_digital_page AS p
  ON p.pid = i.pid
LEFT JOIN vertex_ndl_ocr_text AS o
  ON o.pid = p.pid
  AND o.page_index = p.page_index
WHERE i.status = 'active'
GROUP BY i.provider_id;
