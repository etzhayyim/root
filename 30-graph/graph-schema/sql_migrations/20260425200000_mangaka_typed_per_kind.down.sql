DROP VIEW IF EXISTS view_mangaka_episode_flat;

DROP INDEX IF EXISTS idx_edge_mangaka_page_contains_panel_dst;

DROP INDEX IF EXISTS idx_edge_mangaka_page_contains_panel_src;

DROP TABLE IF EXISTS edge_mangaka_page_contains_panel;

DROP INDEX IF EXISTS idx_edge_mangaka_work_contains_page_dst;

DROP INDEX IF EXISTS idx_edge_mangaka_work_contains_page_src;

DROP TABLE IF EXISTS edge_mangaka_work_contains_page;

DROP INDEX IF EXISTS idx_vertex_mangaka_panel_page_panelnum;

DROP TABLE IF EXISTS vertex_mangaka_panel;

DROP INDEX IF EXISTS idx_vertex_mangaka_page_act;

DROP INDEX IF EXISTS idx_vertex_mangaka_page_work_pagenum;

DROP TABLE IF EXISTS vertex_mangaka_page;

DROP INDEX IF EXISTS idx_vertex_mangaka_work_status_created;

DROP INDEX IF EXISTS idx_vertex_mangaka_work_genre;

DROP INDEX IF EXISTS idx_vertex_mangaka_work_protagonist;

DROP INDEX IF EXISTS idx_vertex_mangaka_work_repo_rkey;

DROP TABLE IF EXISTS vertex_mangaka_work;
