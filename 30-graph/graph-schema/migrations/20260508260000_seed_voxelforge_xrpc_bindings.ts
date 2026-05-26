import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * ADR-2605080700 — seed 4 ``vertex_bpmn_lexicon_binding`` rows so
 * ``bpmn-dispatcher`` routes ``app.etzhayyim.apps.voxelforge.*`` to the
 * voxelforge LangGraph Server pod.
 *
 * No corresponding ``vertex_bpmn_process_def`` rows are created —
 * voxelforge runs on LangGraph Server (Granian), not Zeebe / pyzeebe,
 * so the langgraph branch in ``_dispatch_langgraph`` (dispatcher_main.py)
 * is the only consumer of these bindings.  ``bpmn_process_id`` is used
 * as the assistant_id passed to the LangGraph ``/runs`` POST and is
 * informational at the server side (server.py accepts any value).
 *
 * URL override points at the dedicated mitama-voxelforge-pool service
 * (Helm chart ``50-infra/vultr/mitama-voxelforge-pool/``).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const url = "http://voxelforge-langgraph.mitama-udf.svc.cluster.local:8000";
  const rows: Array<{ nsid: string; processId: string; timeoutMs: number }> = [
    { nsid: "app.etzhayyim.apps.voxelforge.generate", processId: "voxelforge_generate", timeoutMs: 30_000 },
    { nsid: "app.etzhayyim.apps.voxelforge.getRun", processId: "voxelforge_get_run", timeoutMs: 5_000 },
    { nsid: "app.etzhayyim.apps.voxelforge.listArtifacts", processId: "voxelforge_list_artifacts", timeoutMs: 5_000 },
    { nsid: "app.etzhayyim.apps.voxelforge.coverage", processId: "voxelforge_coverage", timeoutMs: 5_000 },
  ];
  for (const r of rows) {
    const vid = `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${r.nsid}`;
    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, sensitivity_ord, owner_did,
        nsid, bpmn_process_id, bpmn_version, result_timeout_ms,
        status, routing_target, langgraph_url, created_at)
      SELECT
        ${vid}, 1, 'did:web:voxelforge.etzhayyim.com',
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
      'app.etzhayyim.apps.voxelforge.generate',
      'app.etzhayyim.apps.voxelforge.getRun',
      'app.etzhayyim.apps.voxelforge.listArtifacts',
      'app.etzhayyim.apps.voxelforge.coverage'
    )
  `.execute(db);
}
