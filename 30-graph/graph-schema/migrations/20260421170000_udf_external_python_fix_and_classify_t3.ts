import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * External Python UDF registration — fix + expand.
 *
 * Supersedes `20260416120100_infer_udf_functions.ts` silent failure.
 *
 * Background (2026-04-21 audit per ADR-0044):
 *   The 2026-04-16 migration logged as applied in `kysely_migration` but
 *   NONE of its 4 CREATE FUNCTION statements actually registered in
 *   `rw_catalog.rw_functions`. Root cause: the DDL included
 *     `LANGUAGE python AS fn_name USING LINK '...'`
 *   which RisingWave rejects with
 *     "Invalid Parameter Value: python UDF is not enabled in configuration"
 *   because `LANGUAGE python` is reserved for **embedded** Python UDFs
 *   (disabled at cluster level for security). External UDFs over gRPC
 *   Arrow Flight must use
 *     `AS 'fn_name' USING LINK 'http://host:port'`
 *   with NO `LANGUAGE` clause. See ADR-0044 §D3 + §E5.
 *
 * This migration:
 *   1. DROP the 4 original functions (no-op — they never existed)
 *   2. CREATE them with correct external UDF DDL
 *   3. Add yabai T3 LLM classifier `classify_t3` (ADR-0032 gray-zone tier)
 *
 * The UDF server implementation lives at `30-graph/risingwave-udf/`
 * (arrow_udf 0.3.1 SDK, all functions use @udf(io_threads=N) per ADR-0044).
 * Deploy via K8s manifest `30-graph/risingwave-udf/deploy/risingwave-udf.yaml`
 * on the same Linode LKE cluster as RW compute (same namespace, 1 replica
 * Service exposing :8815 Arrow Flight gRPC).
 *
 * ENV `RW_UDF_SERVER_HOST` (default `risingwave-udf.risingwave.svc:8815`)
 * points at the in-cluster Service. For dev, override to host IP + port.
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const udfHost =
    process.env.RW_UDF_SERVER_HOST || "risingwave-udf.risingwave.svc:8815";
  const link = udfHost.startsWith("http")
    ? udfHost
    : `http://${udfHost}`;

  // ─────────────────────────────────────────────
  // 1) Drop any pre-existing broken signatures.
  //    rw_functions audit 2026-04-21 shows these are absent in prod;
  //    DROP IF EXISTS is a safety no-op.
  // ─────────────────────────────────────────────
  await sql`DROP FUNCTION IF EXISTS cosine_similarity(double precision[], double precision[])`.execute(db);
  await sql`DROP FUNCTION IF EXISTS posterior_update(double precision, double precision)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS segment_hash(jsonb)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS gmm_fit(double precision[], int)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS classify_t3(varchar, varchar, varchar)`.execute(db);

  // ─────────────────────────────────────────────
  // 2) Re-register with correct external UDF DDL
  //    (NO `LANGUAGE` clause; `AS 'remote_fn_name' USING LINK '...'`)
  // ─────────────────────────────────────────────
  await sql`
    CREATE FUNCTION cosine_similarity(a double precision[], b double precision[])
      RETURNS double precision
      AS 'cosine_similarity'
      USING LINK ${sql.lit(link)}
  `.execute(db);

  await sql`
    CREATE FUNCTION posterior_update(prior double precision, likelihood double precision)
      RETURNS double precision
      AS 'posterior_update'
      USING LINK ${sql.lit(link)}
  `.execute(db);

  await sql`
    CREATE FUNCTION segment_hash(features_json jsonb)
      RETURNS varchar
      AS 'segment_hash'
      USING LINK ${sql.lit(link)}
  `.execute(db);

  await sql`
    CREATE FUNCTION gmm_fit(features double precision[], k int)
      RETURNS jsonb
      AS 'gmm_fit'
      USING LINK ${sql.lit(link)}
  `.execute(db);

  // ─────────────────────────────────────────────
  // 3) yabai T3 LLM classifier (ADR-0032 gray-zone tier)
  //    Input: email row (subject, from_addr, body_preview)
  //    Output: JSON varchar {"label","confidence","reason"}
  //    io_threads=50 on server side → 95 rps at 500ms LLM latency
  // ─────────────────────────────────────────────
  await sql`
    CREATE FUNCTION classify_t3(subject varchar, from_addr varchar, body_preview varchar)
      RETURNS varchar
      AS 'classify_t3'
      USING LINK ${sql.lit(link)}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS classify_t3(varchar, varchar, varchar)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS gmm_fit(double precision[], int)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS segment_hash(jsonb)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS posterior_update(double precision, double precision)`.execute(db);
  await sql`DROP FUNCTION IF EXISTS cosine_similarity(double precision[], double precision[])`.execute(db);
}
