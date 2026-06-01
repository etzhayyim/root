import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; processId: string; nsid: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:arms.etzhayyim.com";
const createdAt = "2026-04-29T20:40:00+09:00";
const actorId = "sys.bpmn.seed.arms";
const project = "arms";

const seeds: Seed[] = [
  { slug: "register-firearm", processId: "arms_register_firearm", nsid: "app.etzhayyim.apps.arms.registerFirearm", sourcePath: "00-contracts/bpmn/ai/gftd/arms/registerFirearm.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_firearm,vertex_arms_firearm_pii,edge_arms_firearm_to_holder" },
  { slug: "authenticate-holder", processId: "arms_authenticate_holder", nsid: "app.etzhayyim.apps.arms.authenticateHolder", sourcePath: "00-contracts/bpmn/ai/gftd/arms/authenticateHolder.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_auth_session" },
  { slug: "verify-auth-challenge", processId: "arms_verify_auth_challenge", nsid: "app.etzhayyim.apps.arms.verifyAuthChallenge", sourcePath: "00-contracts/bpmn/ai/gftd/arms/verifyAuthChallenge.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_auth_session" },
  { slug: "issue-permit", processId: "arms_issue_permit", nsid: "app.etzhayyim.apps.arms.issuePermit", sourcePath: "00-contracts/bpmn/ai/gftd/arms/issuePermit.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_permit,vertex_arms_permit_pii" },
  { slug: "transfer-custody", processId: "arms_transfer_custody", nsid: "app.etzhayyim.apps.arms.transferCustody", sourcePath: "00-contracts/bpmn/ai/gftd/arms/transferCustody.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_custody_event,edge_arms_firearm_to_holder,edge_arms_firearm_to_permit" },
  { slug: "check-out-firearm", processId: "arms_check_out_firearm", nsid: "app.etzhayyim.apps.arms.checkOutFirearm", sourcePath: "00-contracts/bpmn/ai/gftd/arms/checkOutFirearm.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_custody_event,vertex_arms_firearm" },
  { slug: "check-in-firearm", processId: "arms_check_in_firearm", nsid: "app.etzhayyim.apps.arms.checkInFirearm", sourcePath: "00-contracts/bpmn/ai/gftd/arms/checkInFirearm.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_custody_event,vertex_arms_firearm" },
  { slug: "report-incident", processId: "arms_report_incident", nsid: "app.etzhayyim.apps.arms.reportIncident", sourcePath: "00-contracts/bpmn/ai/gftd/arms/reportIncident.bpmn", timeoutMs: 60000, writeTableAllowlist: "vertex_arms_custody_event,vertex_open_defence_event,vertex_arms_firearm" },
  { slug: "get-firearm", processId: "arms_get_firearm", nsid: "app.etzhayyim.apps.arms.getFirearm", sourcePath: "00-contracts/bpmn/ai/gftd/arms/getFirearm.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-firearms", processId: "arms_list_firearms", nsid: "app.etzhayyim.apps.arms.listFirearms", sourcePath: "00-contracts/bpmn/ai/gftd/arms/listFirearms.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-permits", processId: "arms_list_permits", nsid: "app.etzhayyim.apps.arms.listPermits", sourcePath: "00-contracts/bpmn/ai/gftd/arms/listPermits.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-audit-log", processId: "arms_get_audit_log", nsid: "app.etzhayyim.apps.arms.getAuditLog", sourcePath: "00-contracts/bpmn/ai/gftd/arms/getAuditLog.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${project}-${s.slug}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
