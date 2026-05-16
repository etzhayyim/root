SET BACKGROUND_DDL = true;

CREATE INDEX IF NOT EXISTS idx_vertex_page_vertex_id_cover
    ON vertex_page(vertex_id)
    INCLUDE (rkey, url, domain, title, status_code, content_type)
    DISTRIBUTED BY (vertex_id);
