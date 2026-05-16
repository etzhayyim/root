/**
 * Seed outlook_triage_tick BPMN (R/PT15M timer-only, no XRPC binding).
 *
 * Phase 4 mirror of gmail_triage_tick. Same architectural pattern as
 * shinshi seedGapFill: timer-start BPMN, no vertex_bpmn_lexicon_binding.
 *
 * F5 watcher (`bpmn-dispatcher`) auto-deploys to Zeebe within ~30s.
 */
import { readFileSync } from "fs";
import path from "path";
import { fileURLToPath } from "url";

import { Kysely, sql } from "kysely";

const here = fileURLToPath(import.meta.url);
const repoRoot = path.resolve(path.dirname(here), "..", "..", "..");

const sourcePath = "00-contracts/bpmn/ai/gftd/outlook/triageTick.bpmn";
const processId = "outlook_triage_tick";
const ownerDid = "did:web:outlook.gftd.ai";
const actorId = "sys.outlook";
const createdAt = "2026-05-08T15:30:00Z";
const vertexId = `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/outlook-triage-tick-v1`;

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

  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml}, xml_byte_size = CAST(${size} AS integer), source_path = ${sourcePath}
    WHERE vertex_id = ${vertexId}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}`.execute(db);
}
