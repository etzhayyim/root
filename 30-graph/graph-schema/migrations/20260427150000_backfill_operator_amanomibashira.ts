// tier: C
// Backfill: vertex_actor.operator legacy "gftd.co.jp" / "gftd" → "amanomibashira".
//
// Companion to the CLI-default rebrand (build.go / coverage_actors.go /
// coverage_infer.go shipped 2026-04-27). After this migration, the live
// graph matches what new deploys + healing cycles will write going
// forward.
//
// Audit (2026-04-27, live RisingWave):
//   vertex_actor.operator distribution before backfill:
//     <empty>      784,956 rows  ← left unchanged; healing populates per-actor
//     'gftd'        20,820 rows  ← rewritten
//     'gftd.co.jp'   2,307 rows  ← rewritten
//   Total rewritten: 23,127 rows.
//
//   vertex_api_key.operator: 18 rows, all empty → nothing to backfill.
//   No other table in information_schema has an `operator` column.
//
// Empty `operator` rows are intentionally left alone: those were never
// explicitly attributed to gftd, and rewriting 784K unrelated rows to
// `amanomibashira` would be a much larger blast radius than the rebrand
// requires. `gftd coverage actors heal` will fill them in over time
// using the new default.
//
// Operating entity = amanomibashira (עץ חיים), a religious voluntary
// association (宗教法人・任意団体). Constitution and member roster are
// recorded on a public blockchain. Not an incorporated 宗教法人 under
// the Japanese 宗教法人法 — no 所轄庁 registration, no associated tax
// or legal privileges claimed.
//
// Idempotent: second apply matches 0 rows. Forward-only — `down()` is a
// no-op because the reverse mapping after the rewrite is ambiguous
// (a row reading `amanomibashira` could have been any of three legacy values).
//
// Apply via:
//   bash 30-graph/graph-schema/scripts/apply-pending.sh \
//     20260427150000_backfill_operator_amanomibashira
//
// Verify:
//   psql ... -c "SELECT operator, COUNT(*) FROM vertex_actor GROUP BY operator ORDER BY 2 DESC;"
//   Expect: 'amanomibashira' ≥ 23,127 ; 'gftd' and 'gftd.co.jp' rows absent.
import { Kysely, sql } from "kysely";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`UPDATE vertex_actor SET operator = 'amanomibashira' WHERE operator IN ('gftd.co.jp', 'gftd')`.execute(db);
  await sql`FLUSH`.execute(db);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // Forward-only. The reverse mapping is ambiguous — amanomibashira rows after
  // this migration include rows that were already amanomibashira before it
  // and rows that were 'gftd' or 'gftd.co.jp' before it.
}
