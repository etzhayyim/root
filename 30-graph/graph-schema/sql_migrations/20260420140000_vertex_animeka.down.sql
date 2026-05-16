DROP MATERIALIZED VIEW IF EXISTS mv_animeka_children_by_parent;

DROP MATERIALIZED VIEW IF EXISTS mv_animeka_open_retake_by_cut;

DROP MATERIALIZED VIEW IF EXISTS mv_animeka_cut_progress;

DROP MATERIALIZED VIEW IF EXISTS mv_vertex_animeka_count;

DROP VIEW IF EXISTS view_animeka_record_flat;

DROP INDEX IF EXISTS idx_vertex_animeka_cut_frame_num;

DROP INDEX IF EXISTS idx_vertex_animeka_episode_cut_num;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_priority;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_stage;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_convo_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_project_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_character_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_cut_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_scene_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_episode_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_work_id;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_parent_rkey;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_collection_rkey;

DROP INDEX IF EXISTS idx_vertex_animeka_repo_collection_created;

DROP TABLE IF EXISTS vertex_animeka;
