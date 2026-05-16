import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * Seed BPMN row for `adsk_ingest_3d_blob` (ADR-2605080700 Phase 2).
 *
 * Inserts the process_def into `vertex_bpmn_process_def` so the F5
 * watcher in `bpmn-dispatcher` picks it up and deploys to Zeebe within
 * ~30s. No `vertex_bpmn_lexicon_binding` row is added — this is a
 * timer-only BPMN (no XRPC entry).
 *
 * Phase A: the BPMN fires monthly and emits an audit row but does no
 * actual blob ingest until an operator manually calls
 * ``adsk.blob3d.ingest`` with a staged sample.  Phase B will swap the
 * audit task for a real ingest pipeline (HF Hub fetch → B2 → register).
 */
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = new Date().toISOString();
  const vid = 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/adsk-ingest-3d-blob-v1';
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, sensitivity_ord, owner_did,
      bpmn_process_id, version, source_path, xml,
      status, created_at)
    SELECT
      ${vid}, 1, 'did:web:adsk.gftd.ai',
      'adsk_ingest_3d_blob', 1,
      '00-contracts/bpmn/ai/gftd/adsk/ingest3DBlob.bpmn',
      '',
      'pending',
      ${now}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${vid})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_process_def
    WHERE bpmn_process_id = 'adsk_ingest_3d_blob'
  `.execute(db);
}
