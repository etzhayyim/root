/**
 * ADR-2605080600 Phase 4 — Activate ki / saikin / webmk BPMNs + seed newsletter_weekly_send.
 *
 * ki_vascular_synthesis_cycle, saikin_horizontal_transfer_cycle,
 * webmk_create_proposal were seeded as 'inactive'; activate them so the
 * F5 watcher deploys them to Zeebe.
 *
 * newsletter_weekly_send is a timer-start (0 0 * * 2 = Tuesday 00:00 JST);
 * no lexicon binding needed (no XRPC entry point).
 */
import { type Kysely, sql } from "kysely";
import * as fs from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";

const ownerDid = "did:web:bpmn.etzhayyim.com";
const createdAt = "2026-05-08T09:45:00Z";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

export async function up(db: Kysely<unknown>): Promise<void> {
  // Activate previously-inactive BPMNs so the F5 watcher picks them up.
  for (const bpmnProcessId of [
    "ki_vascular_synthesis_cycle",
    "saikin_horizontal_transfer_cycle",
    "webmk_create_proposal",
  ]) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'active'
      WHERE bpmn_process_id = ${bpmnProcessId}
        AND status = 'inactive'
    `.execute(db);
  }

  // Seed newsletter_weekly_send (timer-start, no XRPC binding).
  const sourcePath = "00-contracts/bpmn/com/etzhayyim/newsletter/weeklySend.bpmn";
  const xml = fs.readFileSync(path.resolve(repoRoot, sourcePath), "utf-8");
  const byteSize = Buffer.byteLength(xml, "utf8");
  const vertexId =
    "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/newsletter-weeklySend-v1";

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT
      ${vertexId}, ${ownerDid}, 'newsletter_weekly_send', 1,
      ${xml}, CAST(${byteSize} AS integer),
      ${sourcePath}, 'active', ${createdAt},
      1, ${ownerDid}, ${ownerDid}, 'sys.bpmn.seed.newsletter'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${vertexId}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const bpmnProcessId of [
    "ki_vascular_synthesis_cycle",
    "saikin_horizontal_transfer_cycle",
    "webmk_create_proposal",
  ]) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET status = 'inactive'
      WHERE bpmn_process_id = ${bpmnProcessId}
    `.execute(db);
  }
  await sql`
    DELETE FROM vertex_bpmn_process_def
    WHERE vertex_id = 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/newsletter-weeklySend-v1'
  `.execute(db);
}
