DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_generated_image_by_panel;

DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_members_by_project;

DROP MATERIALIZED VIEW IF EXISTS mv_mangaka_children_by_parent;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_mangaka_count;

DROP VIEW IF EXISTS view_mangaka_record_flat;

DROP INDEX IF EXISTS idx_edge_membership_src_vid;

DROP INDEX IF EXISTS idx_edge_in_project_src_vid;

DROP INDEX IF EXISTS idx_edge_contains_src_vid;

DROP INDEX IF EXISTS idx_vertex_record_attribute_name_value_num;

DROP INDEX IF EXISTS idx_vertex_record_attribute_name_value_text;

DROP INDEX IF EXISTS idx_vertex_record_attribute_record_vid_name;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_convo_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_project_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_panel_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_page_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_chapter_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_work_id;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_parent_rkey;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_collection_rkey;

DROP INDEX IF EXISTS idx_vertex_mangaka_repo_collection_created;
