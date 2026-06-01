import type { Kysely } from "kysely";
import { sql } from "kysely";

// Persist result_timeout_ms=0 (async fire-and-forget dispatch) for both
// maps coverage bindings. These were updated directly in the DB on 2026-05-03
// to fix CronJob 504 timeouts caused by broker saturation. This migration
// makes the change durable across DB restores / fresh migrations.
//
// result_timeout_ms=0 → dispatcher calls run_process() (async, no wait),
// returns {"asyncStarted":true} in ~6ms. The CronJob curl completes in <1s.
// The actual BPMN process runs asynchronously in the zeebe-worker pod.

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = 0
    WHERE nsid IN (
      'app.etzhayyim.apps.maps.batchCoverageCycle',
      'app.etzhayyim.apps.maps.refreshCoverageStats'
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET result_timeout_ms = CASE nsid
      WHEN 'app.etzhayyim.apps.maps.batchCoverageCycle'  THEN 120000
      WHEN 'app.etzhayyim.apps.maps.refreshCoverageStats' THEN 90000
      ELSE result_timeout_ms
    END
    WHERE nsid IN (
      'app.etzhayyim.apps.maps.batchCoverageCycle',
      'app.etzhayyim.apps.maps.refreshCoverageStats'
    )
  `.execute(db);
}
