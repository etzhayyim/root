import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-28T26:00:00Z";
const actorTag = "sys.bpmn.seed.business-person";
const ownerDid = "did:web:business-person.etzhayyim.com";
const project = "business-person";

const entries = [
  {
    proc: "scoreInfluence",
    bpmnProcessId: "business_person_score_influence",
    nsid: "ai.gftd.apps.businessPerson.scoreInfluence",
    resultTimeoutMs: 60000,
  },
  {
    proc: "enrichCareerLLM",
    bpmnProcessId: "business_person_enrich_career_llm",
    nsid: "ai.gftd.apps.businessPerson.enrichCareerLLM",
    resultTimeoutMs: 120000,
  },
] as const;

const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVid = (proc: string) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/${project}-${slug(proc)}-v1`;
const bindingVid = (proc: string) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/${project}-${proc}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const e of entries) {
    const rel = `00-contracts/bpmn/ai/gftd/${project}/${e.proc}.bpmn`;
    const xml = readContract(rel);
    const size = Buffer.byteLength(xml, "utf8");
    const pvid = processVid(e.proc);
    const bvid = bindingVid(e.proc);

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT
        ${pvid}, ${ownerDid}, ${e.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${rel}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${pvid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT
        ${bvid}, ${ownerDid}, ${e.nsid}, ${e.bpmnProcessId}, 1,
        CAST(${e.resultTimeoutMs} AS integer), 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bvid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const e of entries) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(e.proc)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(e.proc)}`.execute(db);
  }
}
