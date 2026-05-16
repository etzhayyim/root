CREATE TABLE IF NOT EXISTS vertex_cad_model (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      workspace_id     VARCHAR,
      name             VARCHAR,
      description      VARCHAR,
      units            VARCHAR,
      head_revision_id VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_model_workspace ON vertex_cad_model (workspace_id);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_cad_revision (
      vertex_id          VARCHAR PRIMARY KEY,
      _seq               BIGINT,
      created_date       DATE,
      sensitivity_ord    BIGINT,
      owner_did          VARCHAR,
      rkey               VARCHAR,
      repo               VARCHAR,
      model_id           VARCHAR,
      parent_revision_id VARCHAR,
      source_format      VARCHAR,
      source_blob_key    VARCHAR,
      tessellation_key   VARCHAR,
      tessellation_tol   DOUBLE PRECISION,
      bbox_min_x         DOUBLE PRECISION,
      bbox_min_y         DOUBLE PRECISION,
      bbox_min_z         DOUBLE PRECISION,
      bbox_max_x         DOUBLE PRECISION,
      bbox_max_y         DOUBLE PRECISION,
      bbox_max_z         DOUBLE PRECISION,
      status             VARCHAR,
      units              VARCHAR,
      message            VARCHAR,
      created_at         VARCHAR,
      org_id             VARCHAR,
      user_id            VARCHAR,
      actor_id           VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_revision_model ON vertex_cad_revision (model_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_revision_status ON vertex_cad_revision (status);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_cad_feature (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      feature_type     VARCHAR,
      feature_index    BIGINT,
      parent_feature_id VARCHAR,
      params_json      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_feature_revision ON vertex_cad_feature (revision_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_feature_type ON vertex_cad_feature (feature_type);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_cad_comment (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         DATE,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      revision_id          VARCHAR,
      part_occurrence_path VARCHAR,
      topology_kind        VARCHAR,
      topology_id          VARCHAR,
      world_pos_x          DOUBLE PRECISION,
      world_pos_y          DOUBLE PRECISION,
      world_pos_z          DOUBLE PRECISION,
      camera_snapshot_json VARCHAR,
      text                 VARCHAR,
      reply_to             VARCHAR,
      status               VARCHAR,
      created_at           VARCHAR,
      org_id               VARCHAR,
      user_id              VARCHAR,
      actor_id             VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_comment_revision ON vertex_cad_comment (revision_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_comment_part ON vertex_cad_comment (part_occurrence_path);

FLUSH;

CREATE TABLE IF NOT EXISTS vertex_cad_export_job (
      vertex_id        VARCHAR PRIMARY KEY,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      rkey             VARCHAR,
      repo             VARCHAR,
      revision_id      VARCHAR,
      target           VARCHAR,
      units            VARCHAR,
      tessellation_tol DOUBLE PRECISION,
      status           VARCHAR,
      output_blob_key  VARCHAR,
      error_message    VARCHAR,
      estimated_secs   BIGINT,
      started_at       VARCHAR,
      finished_at      VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_export_job_revision ON vertex_cad_export_job (revision_id);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_vertex_cad_export_job_status ON vertex_cad_export_job (status);

FLUSH;

CREATE TABLE IF NOT EXISTS edge_cad_has_revision (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_cad_has_revision_src ON edge_cad_has_revision (src_vid);

FLUSH;

CREATE TABLE IF NOT EXISTS edge_cad_has_feature (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_cad_has_feature_src ON edge_cad_has_feature (src_vid);

FLUSH;

CREATE TABLE IF NOT EXISTS edge_cad_commented_on (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_cad_commented_on_src ON edge_cad_commented_on (src_vid);

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_cad_commented_on_dst ON edge_cad_commented_on (dst_vid);

FLUSH;

CREATE TABLE IF NOT EXISTS edge_cad_derives_from (
      edge_id          VARCHAR PRIMARY KEY,
      src_vid          VARCHAR,
      dst_vid          VARCHAR,
      _seq             BIGINT,
      created_date     DATE,
      sensitivity_ord  BIGINT,
      owner_did        VARCHAR,
      created_at       VARCHAR,
      org_id           VARCHAR,
      user_id          VARCHAR,
      actor_id         VARCHAR
    );

FLUSH;

CREATE INDEX IF NOT EXISTS idx_edge_cad_derives_from_src ON edge_cad_derives_from (src_vid);

FLUSH;
