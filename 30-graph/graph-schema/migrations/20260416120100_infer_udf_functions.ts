import { Kysely, sql } from 'kysely';

/**
 * Migration: Register Python UDF functions for coverage infer.
 *
 * DEAD — superseded by 20260421170000_udf_external_python_fix_and_classify_t3.ts.
 * The DDL below uses `LANGUAGE python AS name USING LINK '...'` which RisingWave
 * rejects ("python UDF is not enabled in configuration") because `LANGUAGE python`
 * is reserved for embedded Python (disabled cluster-wide). External UDFs over
 * Arrow Flight must omit `LANGUAGE` and quote the symbol: `AS 'name' USING LINK '…'`.
 * Kept here only so the kysely_migration row remains linkable; the 4 functions
 * were never actually registered by this file. See ADR-0044 §D3/§E5.
 *
 * Design: 90-docs/260416-coverage-infer-statistical-entity-resolution.md
 */
export async function up(db: Kysely<any>): Promise<void> {
  const udfHost = process.env.RW_UDF_SERVER_HOST || 'risingwave-python-udf.risingwave.svc:8815';

  await db.executeQuery(sql`CREATE FUNCTION IF NOT EXISTS cosine_similarity(DOUBLE PRECISION[], DOUBLE PRECISION[])
    RETURNS DOUBLE PRECISION
    LANGUAGE python
    AS cosine_similarity
    USING LINK '${sql.raw(udfHost)}'`.compile(db));

  await db.executeQuery(sql`CREATE FUNCTION IF NOT EXISTS posterior_update(DOUBLE PRECISION, DOUBLE PRECISION)
    RETURNS DOUBLE PRECISION
    LANGUAGE python
    AS posterior_update
    USING LINK '${sql.raw(udfHost)}'`.compile(db));

  await db.executeQuery(sql`CREATE FUNCTION IF NOT EXISTS segment_hash(JSONB)
    RETURNS VARCHAR
    LANGUAGE python
    AS segment_hash
    USING LINK '${sql.raw(udfHost)}'`.compile(db));

  await db.executeQuery(sql`CREATE FUNCTION IF NOT EXISTS gmm_fit(DOUBLE PRECISION[], INT)
    RETURNS JSONB
    LANGUAGE python
    AS gmm_fit
    USING LINK '${sql.raw(udfHost)}'`.compile(db));
}

export async function down(db: Kysely<any>): Promise<void> {
  await db.executeQuery(sql`DROP FUNCTION IF EXISTS gmm_fit`.compile(db));
  await db.executeQuery(sql`DROP FUNCTION IF EXISTS segment_hash`.compile(db));
  await db.executeQuery(sql`DROP FUNCTION IF EXISTS posterior_update`.compile(db));
  await db.executeQuery(sql`DROP FUNCTION IF EXISTS cosine_similarity`.compile(db));
}
