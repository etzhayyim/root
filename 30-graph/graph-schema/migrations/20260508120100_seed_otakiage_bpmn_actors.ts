import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * otakiage.etzhayyim.com BPMN-as-actor seeding (ADR-2605081700 + ADR-0056 + ADR-2604282300).
 *
 * 4 BPMN process defs + 6 XRPC bindings.  T2 actor (pymagatama + Zeebe).
 * Lifecycle BPMN は autonomous (timer-start)、XRPC binding は bpmn-dispatcher
 * `http://dispatcher.etzhayyim.com:8080/xrpc/app.etzhayyim.apps.otakiage.*` から到達。
 *
 *  Process / NSID                              Trigger
 *  -----------------------------------------------------------------------
 *  otakiage_reuse_match        (autonomous)    R/PT1H
 *  otakiage_reuse_expire       (autonomous)    R/PT24H
 *  otakiage_matsuri_schedule   (autonomous)    cron 0 0 0 1 * ?  (月初 00:00 UTC)
 *  otakiage_social_announce    (XRPC fan-in)   handover/ritual 完了で内部呼出
 *
 *  XRPC binding NSIDs:
 *    app.etzhayyim.apps.otakiage.submitItem        → otakiage_submit_item (この migration では process_def 不要、handler 直接実装)
 *    app.etzhayyim.apps.otakiage.requestReuse      → otakiage_request_reuse
 *    app.etzhayyim.apps.otakiage.confirmHandover   → otakiage_confirm_handover
 *    app.etzhayyim.apps.otakiage.requestRitual     → otakiage_request_ritual
 *    app.etzhayyim.apps.otakiage.scheduleMatsuri   → otakiage_schedule_matsuri
 *    app.etzhayyim.apps.otakiage.issueCertificate  → otakiage_issue_certificate
 *
 * Phase 1 では 4 BPMN を deploy し、6 XRPC binding は pymagatama primitive 直接 dispatch
 * (BPMN process_def なしで bpmn-dispatcher が handler に forward) で実装する。
 * Phase 2 で必要に応じて proper BPMN flow に拡張。
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string; ownerDid: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T17:00:00Z";
const ownerDid = "did:web:otakiage.etzhayyim.com";
const actorTag = "sys.bpmn.seed.otakiage";

const processSeeds: P[] = [
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/otakiage-reuse-match-v1",
    bpmnProcessId: "otakiage_reuse_match",
    sourcePath: "00-contracts/bpmn/ai/gftd/otakiage/reuseMatch.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/otakiage-reuse-expire-v1",
    bpmnProcessId: "otakiage_reuse_expire",
    sourcePath: "00-contracts/bpmn/ai/gftd/otakiage/reuseExpire.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/otakiage-matsuri-schedule-v1",
    bpmnProcessId: "otakiage_matsuri_schedule",
    sourcePath: "00-contracts/bpmn/ai/gftd/otakiage/matsuriSchedule.bpmn", ownerDid },
  { vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/otakiage-social-announce-v1",
    bpmnProcessId: "otakiage_social_announce",
    sourcePath: "00-contracts/bpmn/ai/gftd/otakiage/socialAnnounce.bpmn", ownerDid },
];

async function insertProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${s.ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${s.ownerDid}, ${s.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
}
