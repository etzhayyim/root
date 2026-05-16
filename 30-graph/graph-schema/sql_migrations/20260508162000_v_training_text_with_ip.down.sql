DROP VIEW IF EXISTS v_training_text;

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
        AND LENGTH(description) >= 20
    UNION ALL
      SELECT
        vertex_id,
        'hf:' || slug                    AS label,
        text_for_training                AS content,
        lang                             AS lang,
        CAST(created_date AS VARCHAR)    AS created_date
      FROM vertex_hf_dataset_record
      WHERE sensitivity_ord = 0
        AND text_for_training IS NOT NULL
        AND text_for_training NOT LIKE 'signal:v1:%'
        AND LENGTH(text_for_training) >= 20;
