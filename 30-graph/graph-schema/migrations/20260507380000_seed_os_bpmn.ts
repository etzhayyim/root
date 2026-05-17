import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:os.etzhayyim.com";
const createdAt = "2026-05-07T00:50:00Z";
const actorId = "sys.bpmn.seed.os";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeProcs = new Set([
  "agentMigrate",
  "agentPause",
  "agentResume",
  "agentSpawn",
  "agentStop",
  "budgetAllocate",
  "consentApprove",
  "consentDeny",
  "consentSubmit",
  "directoryRegister",
  "syncPush",
  "windowClose",
  "windowOpen",
]);
const writeTableAllowlist = [
  "vertex_os_agent",
  "vertex_os_agent_event",
  "vertex_os_audit_entry",
  "vertex_os_consent_request",
  "vertex_os_consent_response",
  "vertex_os_budget_allocation",
  "vertex_os_directory_entry",
  "vertex_os_sync_event",
  "vertex_os_window_event",
  "edge_os_agent_event",
  "edge_os_agent_audit_entry",
  "edge_os_consent_response",
  "edge_os_budget_agent",
].join(",");

const seeds: Seed[] = [
  "agentList",
  "agentMigrate",
  "agentPause",
  "agentResume",
  "agentSpawn",
  "agentStop",
  "auditTrail",
  "budgetAllocate",
  "budgetBalance",
  "consentApprove",
  "consentDeny",
  "consentPending",
  "consentSubmit",
  "directoryRegister",
  "directorySearch",
  "health",
  "syncPull",
  "syncPush",
  "windowClose",
  "windowOpen",
].map((proc) => ({
  proc,
  bpmnProcessId: `os_${snake(proc)}`,
  nsid: `ai.gftd.apps.os.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeProcs.has(proc) ? writeTableAllowlist : "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/ai/gftd/os/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/os-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/os-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);
    await sql`
      UPDATE vertex_bpmn_process_def
      SET xml_byte_size = ${size}
      WHERE vertex_id = ${processVid(s)} AND xml_byte_size IS NULL
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${sql.raw(String(s.resultTimeoutMs))}, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
