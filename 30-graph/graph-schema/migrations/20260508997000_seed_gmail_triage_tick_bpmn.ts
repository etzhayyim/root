/**
 * Seed gmail_triage_tick BPMN (R/PT15M timer-only, no XRPC binding).
 *
 * Phase 2 of the gmail triage rollout (ADR-0032 + ADR-2605072000):
 *   - Phase 1 (already deployed): gmail.triage XRPC primitive backed by
 *     gmail.triage.v1 LangGraph agent.
 *   - Phase 2 (this migration): timer-only BPMN that fires the same task
 *     every 15 minutes so newly-synced emails are triaged autonomously.
 *
 * Mirrors the shinshi `seedGapFill` pattern: timer-start BPMN with no
 * `vertex_bpmn_lexicon_binding` row (binding is only required for XRPC
 * dispatch, not for autonomous timer fires).
 *
 * F5 watcher (`bpmn-dispatcher`) picks up the new
 * `vertex_bpmn_process_def` row within ~30s and deploys the BPMN to
 * Zeebe; the broker then schedules the R/PT15M timer.
 */
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { Kysely, sql } from "kysely";

const here = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(here), "..", "..", "..");

const sourcePath = "00-contracts/bpmn/ai/gftd/gmail/triageTick.bpmn";
const processId = "gmail_triage_tick";
const ownerDid = "did:web:gmail.etzhayyim.com";
const actorId = "sys.gmail";
const createdAt = "2026-05-08T15:00:00Z";
const vertexId = `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/gmail-triage-tick-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
      actor_did, org_did
    )
    SELECT
      ${vertexId}, ${ownerDid}, ${processId}, 1,
      ${xml}, CAST(${size} AS integer), ${sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
      ${ownerDid}, 'anon'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}
    )
  `.execute(db);

  // Idempotent re-apply: refresh xml if the file moves on
  // RW reserves "xml" as a keyword; quote it.
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml}, xml_byte_size = CAST(${size} AS integer), source_path = ${sourcePath}
    WHERE vertex_id = ${vertexId}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}`.execute(db);
}
