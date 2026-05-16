CREATE TABLE IF NOT EXISTS "vertex_mangaka_work" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "protagonist_did"  VARCHAR,
      "protagonist"      VARCHAR,
      "title"            VARCHAR,
      "genre"            VARCHAR,
      "setting"          VARCHAR,
      "page_count"       BIGINT,
      "panel_count"      BIGINT,
      "status"           VARCHAR,
      "cover_cid"        VARCHAR,
      "script_cid"       VARCHAR,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_repo_rkey      ON vertex_mangaka_work (repo, rkey);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_protagonist    ON vertex_mangaka_work (protagonist_did);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_genre          ON vertex_mangaka_work (genre, created_at);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_work_status_created ON vertex_mangaka_work (status, created_at);

CREATE TABLE IF NOT EXISTS "vertex_mangaka_page" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "work_uri"         VARCHAR,
      "page_num"         BIGINT,
      "act"              VARCHAR,
      "panel_count"      BIGINT,
      "width"            BIGINT,
      "height"           BIGINT,
      "image_cid"        VARCHAR,
      "image_size"       BIGINT,
      "alt_text"         TEXT,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_page_work_pagenum ON vertex_mangaka_page (work_uri, page_num);

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_page_act          ON vertex_mangaka_page (act);

CREATE TABLE IF NOT EXISTS "vertex_mangaka_panel" (
      "vertex_id"        VARCHAR PRIMARY KEY,
      "rkey"             VARCHAR,
      "repo"             VARCHAR,
      "owner_did"        VARCHAR,
      "page_uri"         VARCHAR,
      "panel_num"        BIGINT,
      "panel_order"      BIGINT,
      "prompt"           TEXT,
      "dialogue_json"    TEXT,
      "image_cid"        VARCHAR,
      "x"                DOUBLE PRECISION,
      "y"                DOUBLE PRECISION,
      "w"                DOUBLE PRECISION,
      "h"                DOUBLE PRECISION,
      "sensitivity_ord"  BIGINT,
      "created_at"       VARCHAR,
      "org_id"           VARCHAR,
      "user_id"          VARCHAR,
      "actor_id"         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_mangaka_panel_page_panelnum ON vertex_mangaka_panel (page_uri, panel_num);

CREATE TABLE IF NOT EXISTS "edge_mangaka_work_contains_page" (
      "edge_id"   VARCHAR PRIMARY KEY,
      "src_vid"   VARCHAR,
      "dst_vid"   VARCHAR,
      "page_num"  BIGINT,
      "created_at" VARCHAR,
      "org_id"    VARCHAR,
      "user_id"   VARCHAR,
      "actor_id"  VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_mangaka_work_contains_page_src ON edge_mangaka_work_contains_page (src_vid, page_num);

CREATE INDEX IF NOT EXISTS idx_edge_mangaka_work_contains_page_dst ON edge_mangaka_work_contains_page (dst_vid);

CREATE TABLE IF NOT EXISTS "edge_mangaka_page_contains_panel" (
      "edge_id"   VARCHAR PRIMARY KEY,
      "src_vid"   VARCHAR,
      "dst_vid"   VARCHAR,
      "panel_num" BIGINT,
      "created_at" VARCHAR,
      "org_id"    VARCHAR,
      "user_id"   VARCHAR,
      "actor_id"  VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_mangaka_page_contains_panel_src ON edge_mangaka_page_contains_panel (src_vid, panel_num);

CREATE INDEX IF NOT EXISTS idx_edge_mangaka_page_contains_panel_dst ON edge_mangaka_page_contains_panel (dst_vid);

CREATE VIEW IF NOT EXISTS view_mangaka_episode_flat AS
    SELECT
      w.vertex_id   AS work_uri,
      w.rkey        AS work_rkey,
      w.protagonist_did,
      w.protagonist,
      w.title,
      w.genre,
      w.setting,
      w.page_count,
      w.panel_count,
      w.status,
      w.cover_cid,
      w.created_at,
      w.org_id,
      (SELECT COUNT(*) FROM vertex_mangaka_page p WHERE p.work_uri = w.vertex_id)  AS page_records,
      (SELECT COUNT(*) FROM vertex_mangaka_panel pn JOIN vertex_mangaka_page p
         ON pn.page_uri = p.vertex_id WHERE p.work_uri = w.vertex_id)              AS panel_records
    FROM vertex_mangaka_work w;
