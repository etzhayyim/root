import { Kysely, sql } from "kysely";

// Training data export schema (ADR-0044 extended use).
// Two plain VIEWs (not MVs — avoids memory pressure on large UNION ALL scans)
// + one progress-tracking table for shard state.
//
// v_training_text: public-only (sensitivity_ord=0), no signal:v1: ciphertext.
// v_training_triple: graph edge triples for relational-reasoning tasks.
// vertex_training_shard: per-shard export progress (dataset_name/label/shard_index).

export async function up(db: Kysely<unknown>): Promise<void> {
  // Text corpus VIEW — UNION ALL of content-bearing vertex tables.
  // Restricted to: sensitivity_ord=0, non-empty, non-encrypted content.
  // Starts with vertex_wet_chunk (985M rows, CommonCrawl markdown) as Phase 1.
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

  // Graph triple VIEW — (head, relation, tail) for relational reasoning.
  // Three edge types as initial seed; extend by editing this VIEW.
  await sql`
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
      FROM edge_classified_as
  `.execute(db);

  // Shard progress table — one row per completed export shard.
  // vertex_id = "training-shard:{dataset_name}:{label}:{shard_index}"
  await sql`
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
    )
  `.execute(db);

  await sql`GRANT SELECT, INSERT ON vertex_training_shard TO root`.execute(db);
  await sql`GRANT SELECT, INSERT ON vertex_training_shard TO kaisya_app`.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`REVOKE ALL ON vertex_training_shard FROM root`.execute(db);
  await sql`REVOKE ALL ON vertex_training_shard FROM kaisya_app`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_training_shard`.execute(db);
  await sql`DROP VIEW IF EXISTS v_training_triple`.execute(db);
  await sql`DROP VIEW IF EXISTS v_training_text`.execute(db);
}
