CREATE TABLE IF NOT EXISTS "vertex_animeka" (
      "vertex_id"       VARCHAR PRIMARY KEY,
      "_seq"            BIGINT,
      "created_date"    DATE,
      "sensitivity_ord" BIGINT,
      "owner_did"       VARCHAR,
      "rkey"            VARCHAR,
      "repo"            VARCHAR,
      "did"             VARCHAR,
      "collection"      VARCHAR,
      "label"           VARCHAR,
      "kind"            VARCHAR,
      "title"           VARCHAR,
      "name"            VARCHAR,
      "display_name"    VARCHAR,
      "description"     TEXT,
      "parent_rkey"     VARCHAR,

      -- Anime pipeline foreign keys
      "work_id"         VARCHAR,
      "episode_id"      VARCHAR,
      "scene_id"        VARCHAR,
      "cut_id"          VARCHAR,
      "character_id"    VARCHAR,
      "project_id"      VARCHAR,
      "convo_id"        VARCHAR,
      "storyboard_id"   VARCHAR,
      "layout_id"       VARCHAR,
      "keyframe_id"     VARCHAR,
      "retake_id"       VARCHAR,
      "target_uri"      VARCHAR,

      -- Sequence + timing columns
      "episode_num"     BIGINT,
      "scene_num"       BIGINT,
      "cut_num"         BIGINT,
      "frame_num"       BIGINT,
      "duration_frames" BIGINT,
      "duration_sec"    DOUBLE PRECISION,
      "fps"             BIGINT,
      "in_frame"        BIGINT,
      "out_frame"       BIGINT,
      "timecode_frame"  BIGINT,

      -- Pipeline state
      "stage"           VARCHAR,
      "stage_status"    TEXT,   -- JSON map {script,storyboard,...,delivery → status}
      "assignees"       TEXT,   -- JSON map {stage → DID}
      "priority"        VARCHAR,
      "severity"        VARCHAR,
      "method"          VARCHAR,

      -- Camera + lighting + identity
      "camera_mode"     VARCHAR,
      "lighting_mood"   VARCHAR,
      "lighting_condition" VARCHAR,
      "slug"            VARCHAR,
      "author"          VARCHAR,
      "writer"          VARCHAR,
      "speaker"         VARCHAR,
      "track_type"      VARCHAR,
      "layer_role"      VARCHAR,

      -- Media / blob CIDs
      "image_cid"       VARCHAR,
      "thumb_cid"       VARCHAR,
      "master_cid"      VARCHAR,
      "layers_cid"      VARCHAR,
      "bg_cid"          VARCHAR,
      "color_layers_cid" VARCHAR,
      "flat_cid"        VARCHAR,
      "output_cid"      VARCHAR,
      "cover_cid"       VARCHAR,
      "ref_sheet_cid"   VARCHAR,
      "material_map_cid" VARCHAR,
      "asset_cid"       VARCHAR,
      "mime_type"       VARCHAR,
      "image_url"       VARCHAR,

      -- Geometry + aspect
      "width"           DOUBLE PRECISION,
      "height"          DOUBLE PRECISION,
      "x"               DOUBLE PRECISION,
      "y"               DOUBLE PRECISION,
      "w"               DOUBLE PRECISION,
      "h"               DOUBLE PRECISION,

      -- Heads-up fields
      "comment"         TEXT,
      "dialogue"        TEXT,
      "action"          TEXT,
      "camera_note"     TEXT,
      "sound_note"      TEXT,
      "body_cid"        VARCHAR,
      "heading_jp"      VARCHAR,
      "location"        VARCHAR,
      "time_of_day"     VARCHAR,
      "mood"            VARCHAR,

      -- Status + bookkeeping
      "cid"             VARCHAR,
      "status"          VARCHAR,
      "created_at"      VARCHAR,
      "props"           TEXT
    );

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_collection_created ON vertex_animeka (repo, collection, created_at);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_collection_rkey    ON vertex_animeka (repo, collection, rkey);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_parent_rkey        ON vertex_animeka (repo, parent_rkey);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_work_id            ON vertex_animeka (repo, work_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_episode_id         ON vertex_animeka (repo, episode_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_scene_id           ON vertex_animeka (repo, scene_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_cut_id             ON vertex_animeka (repo, cut_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_character_id       ON vertex_animeka (repo, character_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_project_id         ON vertex_animeka (repo, project_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_convo_id           ON vertex_animeka (repo, convo_id);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_stage              ON vertex_animeka (repo, stage);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_repo_priority           ON vertex_animeka (repo, priority);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_episode_cut_num         ON vertex_animeka (episode_id, cut_num);

CREATE INDEX IF NOT EXISTS idx_vertex_animeka_cut_frame_num           ON vertex_animeka (cut_id, frame_num);

CREATE VIEW IF NOT EXISTS view_animeka_record_flat AS
    SELECT
      vertex_id,
      _seq,
      created_date,
      sensitivity_ord,
      owner_did,
      rkey,
      repo,
      did,
      collection,
      label,
      COALESCE(kind, split_part(collection, '.', array_length(string_to_array(collection, '.'), 1)), '') AS kind,
      title,
      name,
      COALESCE(display_name, name, title) AS display_name,
      description,
      parent_rkey,
      work_id,
      episode_id,
      episode_num,
      scene_id,
      scene_num,
      cut_id,
      cut_num,
      frame_num,
      duration_frames,
      duration_sec,
      fps,
      in_frame,
      out_frame,
      timecode_frame,
      character_id,
      COALESCE(project_id, convo_id) AS project_id,
      COALESCE(convo_id, project_id) AS convo_id,
      storyboard_id,
      layout_id,
      keyframe_id,
      target_uri,
      stage,
      stage_status,
      assignees,
      COALESCE(priority, 'normal') AS priority,
      severity,
      method,
      camera_mode,
      lighting_mood,
      lighting_condition,
      slug,
      author,
      writer,
      speaker,
      track_type,
      layer_role,
      image_cid,
      thumb_cid,
      master_cid,
      layers_cid,
      bg_cid,
      color_layers_cid,
      flat_cid,
      output_cid,
      cover_cid,
      ref_sheet_cid,
      material_map_cid,
      asset_cid,
      mime_type,
      image_url,
      width,
      height,
      x,
      y,
      w,
      h,
      comment,
      dialogue,
      action,
      camera_note,
      sound_note,
      body_cid,
      heading_jp,
      location,
      time_of_day,
      mood,
      cid,
      status,
      created_at,
      rkey AS id,
      props
    FROM vertex_animeka;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_vertex_animeka_count AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(collection, '') AS collection,
      COALESCE(kind, split_part(collection, '.', array_length(string_to_array(collection, '.'), 1)), '') AS kind,
      COUNT(*)::bigint AS cnt
    FROM vertex_animeka
    GROUP BY 1, 2, 3;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_cut_progress AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(episode_id, '') AS episode_id,
      COUNT(*)::bigint AS cut_count,
      SUM(CASE WHEN priority = 'retake' THEN 1 ELSE 0 END)::bigint AS retake_count
    FROM vertex_animeka
    WHERE collection = 'com.etzhayyim.apps.animeka.cut'
    GROUP BY 1, 2;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_open_retake_by_cut AS
    SELECT
      COALESCE(repo, '') AS repo,
      COALESCE(cut_id, '') AS cut_id,
      COUNT(*)::bigint AS open_cnt
    FROM vertex_animeka
    WHERE collection = 'com.etzhayyim.apps.animeka.retake'
      AND COALESCE(status, 'open') = 'open'
    GROUP BY 1, 2;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_animeka_children_by_parent AS
    SELECT
      src_vid AS parent_vid,
      COALESCE(label, '') AS child_label,
      COUNT(*)::bigint AS cnt
    FROM edge_contains
    GROUP BY 1, 2;
