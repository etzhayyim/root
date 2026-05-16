CREATE TABLE IF NOT EXISTS vertex_bluesky_post (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      source_rkey           VARCHAR,
      source_uri            VARCHAR,
      source_cid            VARCHAR,
      handle                VARCHAR,
      text                  VARCHAR,
      lang                  VARCHAR,
      lang_detected         VARCHAR,
      created_at            VARCHAR,
      indexed_at            VARCHAR,
      reply_root_uri        VARCHAR,
      reply_parent_uri      VARCHAR,
      embed_kind            VARCHAR,
      embed_media_cids      VARCHAR,
      embed_alt_text        VARCHAR,
      embed_external_uri    VARCHAR,
      labels                VARCHAR,
      embedding             VARCHAR,
      embedding_norm        DOUBLE PRECISION,
      ivf_cluster_id        BIGINT,
      actor_id              VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bluesky_profile (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      handle                VARCHAR,
      display_name          VARCHAR,
      description           VARCHAR,
      avatar_cid            VARCHAR,
      banner_cid            VARCHAR,
      pds                   VARCHAR,
      labels                VARCHAR,
      opt_out_signal        VARCHAR,
      indexed_at            VARCHAR,
      embedding             VARCHAR,
      embedding_norm        DOUBLE PRECISION,
      actor_id              VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bluesky_follow (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      subject_did           VARCHAR,
      source_rkey           VARCHAR,
      created_at            VARCHAR,
      indexed_at            VARCHAR,
      actor_id              VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bluesky_opt_out (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      handle                VARCHAR,
      reason                VARCHAR,
      labeler_did           VARCHAR,
      detected_at           VARCHAR,
      purged_at             VARCHAR,
      note                  VARCHAR,
      actor_id              VARCHAR
    );

CREATE TABLE IF NOT EXISTS vertex_bluesky_tombstone (
      vertex_id             VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      rkey                  VARCHAR,
      repo                  VARCHAR,
      source_did            VARCHAR,
      source_rkey           VARCHAR,
      source_collection     VARCHAR,
      event_kind            VARCHAR,
      detected_at           VARCHAR,
      cascade_completed_at  VARCHAR,
      actor_id              VARCHAR
    );

CREATE TABLE IF NOT EXISTS edge_bluesky_follows (
      edge_id               VARCHAR PRIMARY KEY,
      _seq                  BIGINT,
      created_date          DATE,
      sensitivity_ord       BIGINT,
      owner_did             VARCHAR,
      src_vid               VARCHAR,
      dst_vid               VARCHAR,
      source_did            VARCHAR,
      subject_did           VARCHAR,
      created_at            VARCHAR
    );
