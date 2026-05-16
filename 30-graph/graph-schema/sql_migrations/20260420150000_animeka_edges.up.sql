CREATE TABLE IF NOT EXISTS "edge_retakes" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "stage"           VARCHAR,
      "severity"        VARCHAR,
      "status"          VARCHAR,
      "timecode_frame"  BIGINT,
      "author"          VARCHAR,
      "assignee"        VARCHAR,
      "created_at"      VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_retakes_src       ON edge_retakes (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_retakes_dst       ON edge_retakes (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_retakes_cut_stage ON edge_retakes (cut_id, stage);

CREATE INDEX IF NOT EXISTS idx_edge_retakes_status    ON edge_retakes (status, severity);

CREATE TABLE IF NOT EXISTS "edge_cut_has_keyframe" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "frame_num"       BIGINT,
      "kind"            VARCHAR,
      "layer_role"      VARCHAR,
      "created_at"      VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_src           ON edge_cut_has_keyframe (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_dst           ON edge_cut_has_keyframe (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_cut_frame     ON edge_cut_has_keyframe (cut_id, frame_num);

CREATE INDEX IF NOT EXISTS idx_edge_cut_has_keyframe_cut_kind      ON edge_cut_has_keyframe (cut_id, kind);

CREATE TABLE IF NOT EXISTS "edge_assigned_to" (
      "edge_id"         VARCHAR PRIMARY KEY,
      "src_vid"         VARCHAR,
      "dst_vid"         VARCHAR,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "cut_id"          VARCHAR,
      "stage"           VARCHAR,
      "assignee_did"    VARCHAR,
      "created_at"      VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_src       ON edge_assigned_to (src_vid);

CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_dst       ON edge_assigned_to (dst_vid);

CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_cut_stage ON edge_assigned_to (cut_id, stage);

CREATE INDEX IF NOT EXISTS idx_edge_assigned_to_assignee  ON edge_assigned_to (assignee_did, stage);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_retake_queue AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COALESCE(stage, '') AS stage,
      COALESCE(severity, 'minor') AS severity,
      COUNT(*)::bigint AS open_cnt
    FROM edge_retakes
    WHERE COALESCE(status, 'open') = 'open'
    GROUP BY 1, 2, 3, 4;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_frame_count_by_cut AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COALESCE(kind, 'unknown') AS kind,
      COUNT(*)::bigint AS frame_cnt
    FROM edge_cut_has_keyframe
    GROUP BY 1, 2, 3;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_workload_by_assignee AS
    SELECT
      COALESCE(assignee_did, '') AS assignee_did,
      COALESCE(stage, '') AS stage,
      COUNT(*)::bigint AS cnt
    FROM edge_assigned_to
    GROUP BY 1, 2;
