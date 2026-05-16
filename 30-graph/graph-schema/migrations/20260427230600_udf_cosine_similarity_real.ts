import type { Kysely } from "kysely";
import { sql } from "kysely";

// ADR-0044 SQL UDF strategy — rule-based / aggregate compute = SQL UDF,
// plan-time inlined to native vector eval.
//
// `cosine_similarity_real(a real[], b real[]) -> real` returns
// dot(a,b) / (||a|| * ||b||). Brute-force O(N) over `vertex_legal_corpus_document`
// is acceptable until N > ~100K; IVF acceleration (vertex_legal_corpus_centroid +
// ivf_cluster_id assignment workflow + in-app top-cluster pruning) is deferred
// to Phase B+.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE FUNCTION cosine_similarity_real(a real[], b real[]) RETURNS real
    LANGUAGE sql IMMUTABLE AS $$
      SELECT CASE
        WHEN COALESCE(array_length(a, 1), 0) = 0 OR COALESCE(array_length(b, 1), 0) = 0 THEN 0::real
        ELSE (
          SELECT (
            SUM(av.v::double precision * bv.v::double precision)
            / NULLIF(
                sqrt(SUM(av.v::double precision * av.v::double precision))
                * sqrt(SUM(bv.v::double precision * bv.v::double precision)),
                0
              )
          )::real
          FROM unnest(a) WITH ORDINALITY AS av(v, i)
          JOIN unnest(b) WITH ORDINALITY AS bv(v, i) USING (i)
        )
      END
    $$
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP FUNCTION IF EXISTS cosine_similarity_real(real[], real[])`.execute(db);
}
