CREATE VIEW v_training_text AS
      SELECT
        vertex_id,
        'wet_chunk'                      AS label,
        markdown                         AS content,
        language                         AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_wet_chunk
      WHERE sensitivity_ord = 0
        AND markdown IS NOT NULL
        AND markdown NOT LIKE 'signal:v1:%'
        AND LENGTH(markdown) >= 100
    UNION ALL
      SELECT
        vertex_id,
        'profile'                        AS label,
        description                      AS content,
        NULL                             AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_actor_profile
      WHERE sensitivity_ord = 0
        AND description IS NOT NULL
        AND description NOT LIKE 'signal:v1:%'
        AND LENGTH(description) >= 20;

CREATE VIEW v_training_triple AS
      SELECT
        src_vid,
        'follows'                        AS relation,
        dst_vid,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM edge_follows
    UNION ALL
      SELECT
        src_vid,
        'authored_by'                    AS relation,
        dst_vid,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM edge_authored_by
    UNION ALL
      SELECT
        src_vid,
        'classified_as'                  AS relation,
        dst_vid,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM edge_classified_as;

CREATE TABLE IF NOT EXISTS vertex_training_shard (
      vertex_id       VARCHAR PRIMARY KEY,
      dataset_name    VARCHAR NOT NULL,
      label           VARCHAR NOT NULL,
      shard_index     BIGINT  NOT NULL,
      row_count       BIGINT,
      b2_key          VARCHAR,
      status          VARCHAR DEFAULT 'pending',
      created_date    VARCHAR NOT NULL,
      sensitivity_ord INT     DEFAULT 0,
      owner_did       VARCHAR,
      _seq            BIGINT
    );

GRANT SELECT, INSERT ON vertex_training_shard TO root;

GRANT SELECT, INSERT ON vertex_training_shard TO kaisya_app;
