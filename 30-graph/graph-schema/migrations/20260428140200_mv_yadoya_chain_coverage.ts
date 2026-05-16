import type { Kysely } from "kysely";
import { sql } from "kysely";

// yadoya Phase 8 — chain resolution coverage MV. Surfaces the result of
// the chain_did resolver (20260428140000) so we can answer "how many
// yadoya hotels resolved to which chain?" with a single SELECT, without
// scanning vertex_yadoya_hotel.
//
// Pre-flight: GROUP BY (chain_did, country, region) — small cardinality
// (chains × countries × few regions). Trivial cost.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_yadoya_chain_coverage AS
    SELECT
      COALESCE(chain_did, 'independent') AS chain_did,
      country,
      region,
      COUNT(*) AS hotel_count
    FROM vertex_yadoya_hotel
    WHERE status = 'published'
    GROUP BY COALESCE(chain_did, 'independent'), country, region
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_yadoya_chain_coverage`.execute(db);
}
