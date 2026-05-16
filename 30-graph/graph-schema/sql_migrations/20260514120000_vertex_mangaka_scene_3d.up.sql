-- ADR-2605141200 — mangaka 3D scene composition Pregel + kami-mangaka-scene SDK.
-- vertex_mangaka_scene_3d holds one row per (panel, iteration) render
-- produced by lg_mangaka.compose_scene_3d.

CREATE TABLE vertex_mangaka_scene_3d (
  vertex_id        varchar PRIMARY KEY,
  _seq             bigint,
  created_date     date,
  sensitivity_ord  int,
  owner_did        varchar,
  rkey             varchar NOT NULL,
  work_id          varchar,
  chapter_id       varchar,
  page_id          varchar,
  panel_id         varchar NOT NULL,
  scene_jsonld     varchar,           -- kami-mangaka-scene::to_jsonld output (scene DAG + assets)
  camera_jsonld    varchar,           -- CameraSpec + lighting JSON
  pose_jsonld      varchar,           -- per-character PoseSpec JSON
  render_blob_key  varchar,           -- sha256 hex of base PNG (blobs/{repo}/{sha256hex})
  depth_blob_key   varchar,
  outline_blob_key varchar,
  score            double precision,  -- 7-axis critique score 0.0..1.0
  iteration        int,
  sim_seed         bigint,
  shot_grammar     varchar,           -- FullShot / MediumShot / Closeup / OverShoulder / Dutch / BirdsEye / WormsEye
  status           varchar NOT NULL,  -- 'rendered' | 'selected' | 'rejected'
  parent_scene_id  varchar,           -- vertex_id of refined-from row (refineFromRkey lineage)
  props            varchar,
  created_at       varchar NOT NULL,
  actor_did        varchar NOT NULL,
  org_did          varchar NOT NULL,
  at_did           varchar
);

CREATE INDEX idx_mangaka_scene_3d_panel  ON vertex_mangaka_scene_3d (panel_id, iteration);
CREATE INDEX idx_mangaka_scene_3d_work   ON vertex_mangaka_scene_3d (work_id, chapter_id);
CREATE INDEX idx_mangaka_scene_3d_status ON vertex_mangaka_scene_3d (status);
CREATE INDEX idx_mangaka_scene_3d_parent ON vertex_mangaka_scene_3d (parent_scene_id);
