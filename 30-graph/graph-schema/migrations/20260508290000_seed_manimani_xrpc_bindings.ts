import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2605080800 — seed 6 ``vertex_bpmn_lexicon_binding`` rows so
 * ``bpmn-dispatcher`` routes ``ai.gftd.apps.manimani.*`` to the
 * manimani LangGraph Server pod (Helm release
 * ``50-infra/vultr/mitama-manimani-pool/``).
 *
 * No corresponding ``vertex_bpmn_process_def`` rows are created —
 * manimani runs on LangGraph Server (Granian), not Zeebe / pyzeebe,
 * so the langgraph branch in ``_dispatch_langgraph`` (dispatcher_main.py)
 * is the only consumer of these bindings.  ``bpmn_process_id`` is used
 * as the assistant_id passed to the LangGraph ``/runs`` POST and is
 * informational at the server side (server.py accepts any value).
 *
 * Idempotency: relies on RisingWave's implicit PK upsert (re-insert with
 * the same vertex_id overwrites). Per repo convention we do NOT use
 * ``ON CONFLICT DO NOTHING`` (RW treats it as a no-op and emits a
 * notice; ADR-2604241342 §rw-no-onconflict).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const url = "http://manimani-langgraph.mitama-udf.svc.cluster.local:8000";
  const rows: Array<{ nsid: string; processId: string; timeoutMs: number }> = [
    { nsid: "ai.gftd.apps.manimani.ingest",        processId: "manimani_ingest",         timeoutMs: 30_000 },
    { nsid: "ai.gftd.apps.manimani.classify",      processId: "manimani_classify",       timeoutMs: 10_000 },
    { nsid: "ai.gftd.apps.manimani.process",       processId: "manimani_process",        timeoutMs: 30_000 },
    { nsid: "ai.gftd.apps.manimani.getProject",    processId: "manimani_get_project",    timeoutMs: 5_000 },
    { nsid: "ai.gftd.apps.manimani.listProjects",  processId: "manimani_list_projects",  timeoutMs: 5_000 },
    { nsid: "ai.gftd.apps.manimani.coverage",      processId: "manimani_coverage",       timeoutMs: 5_000 },
  ];
  for (const r of rows) {
    const vid = `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${r.nsid}`;
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, sensitivity_ord, owner_did,
        nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
        status, routing_target, langgraph_url, created_at)
      SELECT
        ${vid}, 1, 'did:web:manimani.etzhayyim.com',
        ${r.nsid}, ${r.processId}, 1, CAST(${r.timeoutMs} AS integer),
        'active', 'langgraph', ${url}, ${now}
      WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${vid})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_lexicon_binding
    WHERE nsid IN (
      'ai.gftd.apps.manimani.ingest',
      'ai.gftd.apps.manimani.classify',
      'ai.gftd.apps.manimani.process',
      'ai.gftd.apps.manimani.getProject',
      'ai.gftd.apps.manimani.listProjects',
      'ai.gftd.apps.manimani.coverage'
    )
  `.execute(db);
}
