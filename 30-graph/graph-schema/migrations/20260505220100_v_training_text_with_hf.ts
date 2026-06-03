import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Extend v_training_text to UNION ALL the HF dataset records that
 * landed via 20260505220000_vertex_hf_dataset. The existing
 * training-export pipeline (BPMN trainingExport.bpmn → pyzeebe
 * task_training_export_text → B2 → HF Hub push) reads from this
 * VIEW; once HF rows are visible here, they automatically flow into
 * the etzhayyim-corpus dataset on every R/PT* tick.
 *
 * RisingWave does not allow CREATE OR REPLACE VIEW with column-list
 * changes, so we DROP + CREATE.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS v_training_text`.execute(db);
  await sql`
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
        AND LENGTH(text_for_training) >= 20
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP VIEW IF EXISTS v_training_text`.execute(db);
  await sql`
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
  `.execute(db);
}
