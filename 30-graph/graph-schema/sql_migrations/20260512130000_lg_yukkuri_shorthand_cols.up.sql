-- Migration 20260512130000: Add LangGraph shorthand columns to yukkuri vertex tables.
--
-- Context: migration 0059 created vertex_yukkuri_* using vertex_id (AT URI) as PK
-- and video_uri/scene_uri as references. The lg-yukkuri LangGraph server uses
-- shorter rkey-based IDs (video_id, scene_id, line_id, asset_id) and index
-- columns (scene_index, line_index) for readability. This migration adds those
-- columns alongside the existing schema so both the CF Worker and LangGraph can
-- operate on the same tables.
--
-- RisingWave: no IF NOT EXISTS on ALTER TABLE ADD COLUMN; run idempotently only
-- on fresh installs.

-- vertex_yukkuri_video
ALTER TABLE vertex_yukkuri_video ADD COLUMN video_id         VARCHAR;
ALTER TABLE vertex_yukkuri_video ADD COLUMN repo             VARCHAR;
ALTER TABLE vertex_yukkuri_video ADD COLUMN outline          VARCHAR;
ALTER TABLE vertex_yukkuri_video ADD COLUMN render_url       VARCHAR;
ALTER TABLE vertex_yukkuri_video ADD COLUMN render_blob_key  VARCHAR;

-- vertex_yukkuri_scene
ALTER TABLE vertex_yukkuri_scene ADD COLUMN scene_id         VARCHAR;
ALTER TABLE vertex_yukkuri_scene ADD COLUMN video_id         VARCHAR;
ALTER TABLE vertex_yukkuri_scene ADD COLUMN scene_index      INT;
ALTER TABLE vertex_yukkuri_scene ADD COLUMN location         VARCHAR;
ALTER TABLE vertex_yukkuri_scene ADD COLUMN action           VARCHAR;

-- vertex_yukkuri_line
ALTER TABLE vertex_yukkuri_line ADD COLUMN line_id           VARCHAR;
ALTER TABLE vertex_yukkuri_line ADD COLUMN video_id          VARCHAR;
ALTER TABLE vertex_yukkuri_line ADD COLUMN scene_index       INT;
ALTER TABLE vertex_yukkuri_line ADD COLUMN line_index        INT;

-- vertex_yukkuri_asset
ALTER TABLE vertex_yukkuri_asset ADD COLUMN asset_id         VARCHAR;
ALTER TABLE vertex_yukkuri_asset ADD COLUMN video_id         VARCHAR;
ALTER TABLE vertex_yukkuri_asset ADD COLUMN meta_json        VARCHAR;
