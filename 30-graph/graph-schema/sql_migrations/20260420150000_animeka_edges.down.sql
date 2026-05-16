DROP MATERIALIZED VIEW IF EXISTS mv_animeka_workload_by_assignee;

DROP MATERIALIZED VIEW IF EXISTS mv_animeka_frame_count_by_cut;

DROP MATERIALIZED VIEW IF EXISTS mv_animeka_retake_queue;

DROP INDEX IF EXISTS idx_edge_assigned_to_assignee;

DROP INDEX IF EXISTS idx_edge_assigned_to_cut_stage;

DROP INDEX IF EXISTS idx_edge_assigned_to_dst;

DROP INDEX IF EXISTS idx_edge_assigned_to_src;

DROP TABLE IF EXISTS edge_assigned_to;

DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_cut_kind;

DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_cut_frame;

DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_dst;

DROP INDEX IF EXISTS idx_edge_cut_has_keyframe_src;

DROP TABLE IF EXISTS edge_cut_has_keyframe;

DROP INDEX IF EXISTS idx_edge_retakes_status;

DROP INDEX IF EXISTS idx_edge_retakes_cut_stage;

DROP INDEX IF EXISTS idx_edge_retakes_dst;

DROP INDEX IF EXISTS idx_edge_retakes_src;

DROP TABLE IF EXISTS edge_retakes;
