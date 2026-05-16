CREATE TABLE IF NOT EXISTS vertex_pptx_presentation (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      presentation_id   VARCHAR,
      title             VARCHAR,
      width             DOUBLE PRECISION,
      height            DOUBLE PRECISION,
      slide_count       BIGINT,
      theme_ref         VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_presentation_id ON vertex_pptx_presentation (presentation_id);

CREATE TABLE IF NOT EXISTS vertex_pptx_slide (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      slide_id          VARCHAR,
      presentation_id   VARCHAR,
      layout_ref        VARCHAR,
      slide_index       BIGINT,
      title             VARCHAR,
      notes             VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_slide_id ON vertex_pptx_slide (slide_id);

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_slide_presentation ON vertex_pptx_slide (presentation_id, slide_index);

CREATE TABLE IF NOT EXISTS vertex_pptx_shape (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      shape_id          VARCHAR,
      presentation_id   VARCHAR,
      slide_id          VARCHAR,
      shape_type        VARCHAR,
      x                 DOUBLE PRECISION,
      y                 DOUBLE PRECISION,
      w                 DOUBLE PRECISION,
      h                 DOUBLE PRECISION,
      rotation          DOUBLE PRECISION,
      z_index           BIGINT,
      style_json        VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_shape_id ON vertex_pptx_shape (shape_id);

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_shape_slide ON vertex_pptx_shape (slide_id);

CREATE TABLE IF NOT EXISTS vertex_pptx_text_run (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      text_run_id       VARCHAR,
      shape_id          VARCHAR,
      presentation_id   VARCHAR,
      slide_id          VARCHAR,
      text              VARCHAR,
      font_family       VARCHAR,
      font_size         DOUBLE PRECISION,
      color             VARCHAR,
      bold              BOOLEAN,
      italic            BOOLEAN,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_text_run_id ON vertex_pptx_text_run (text_run_id);

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_text_run_shape ON vertex_pptx_text_run (shape_id);

CREATE TABLE IF NOT EXISTS vertex_pptx_image (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      image_id          VARCHAR,
      shape_id          VARCHAR,
      presentation_id   VARCHAR,
      slide_id          VARCHAR,
      blob_cid          VARCHAR,
      mime              VARCHAR,
      x                 DOUBLE PRECISION,
      y                 DOUBLE PRECISION,
      w                 DOUBLE PRECISION,
      h                 DOUBLE PRECISION,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_image_id ON vertex_pptx_image (image_id);

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_image_slide ON vertex_pptx_image (slide_id);

CREATE TABLE IF NOT EXISTS vertex_pptx_slide_template (
      vertex_id         VARCHAR PRIMARY KEY,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      rkey              VARCHAR,
      repo              VARCHAR,
      collection        VARCHAR,
      template_id       VARCHAR,
      name              VARCHAR,
      category          VARCHAR,
      theme_ref         VARCHAR,
      status            VARCHAR,
      created_at        VARCHAR,
      updated_at        VARCHAR,
      org_id            VARCHAR,
      user_id           VARCHAR,
      actor_id          VARCHAR,
      props             VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_vertex_pptx_slide_template_id ON vertex_pptx_slide_template (template_id);

CREATE TABLE IF NOT EXISTS edge_pptx_presentation_slide (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      slide_index       BIGINT,
      linked_at         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_pptx_presentation_slide_src ON edge_pptx_presentation_slide (src_vid);

CREATE TABLE IF NOT EXISTS edge_pptx_slide_shape (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      z_index           BIGINT,
      linked_at         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_pptx_slide_shape_src ON edge_pptx_slide_shape (src_vid);

CREATE TABLE IF NOT EXISTS edge_pptx_shape_text_run (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      linked_at         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_pptx_shape_text_run_src ON edge_pptx_shape_text_run (src_vid);

CREATE TABLE IF NOT EXISTS edge_pptx_shape_image (
      edge_id           VARCHAR PRIMARY KEY,
      src_vid           VARCHAR,
      dst_vid           VARCHAR,
      _seq              BIGINT,
      created_date      DATE,
      sensitivity_ord   BIGINT,
      owner_did         VARCHAR,
      linked_at         VARCHAR
    );

CREATE INDEX IF NOT EXISTS idx_edge_pptx_shape_image_src ON edge_pptx_shape_image (src_vid);

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pptx_slide_stats AS
    SELECT
      s.presentation_id,
      s.slide_id,
      COUNT(DISTINCT sh.shape_id) AS shape_count,
      COUNT(DISTINCT tr.text_run_id) AS text_run_count,
      COUNT(DISTINCT im.image_id) AS image_count,
      MAX(GREATEST(COALESCE(s._seq, 0), COALESCE(sh._seq, 0), COALESCE(tr._seq, 0), COALESCE(im._seq, 0))) AS last_seq
    FROM vertex_pptx_slide s
    LEFT JOIN vertex_pptx_shape sh ON sh.slide_id = s.slide_id
    LEFT JOIN vertex_pptx_text_run tr ON tr.slide_id = s.slide_id
    LEFT JOIN vertex_pptx_image im ON im.slide_id = s.slide_id
    WHERE s.slide_id IS NOT NULL
    GROUP BY s.presentation_id, s.slide_id;

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_pptx_text_index AS
    SELECT
      presentation_id,
      slide_id,
      COUNT(*) AS text_run_count,
      STRING_AGG(COALESCE(text, ''), ' ' ORDER BY text_run_id) AS concatenated_text,
      MAX(_seq) AS last_seq
    FROM vertex_pptx_text_run
    WHERE presentation_id IS NOT NULL
    GROUP BY presentation_id, slide_id;
