import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Coverage literals:
// - 00-contracts/bpmn/com/etzhayyim/yoro/translatePost.bpmn
//   yoro_translate_post
//   com.etzhayyim.apps.yoro.translatePost
// - 00-contracts/bpmn/com/etzhayyim/yoro/translatePostBatch.bpmn
//   yoro_translate_post_batch
//   com.etzhayyim.apps.yoro.translatePostBatch

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:yoro.etzhayyim.com";
const actorId = "sys.bpmn.seed.yoro.translation";
const createdAt = "2026-05-14T01:30:00Z";

const seeds: Seed[] = [
  {
    proc: "translatePost",
    bpmnProcessId: "yoro_translate_post",
    nsid: "com.etzhayyim.apps.yoro.translatePost",
    resultTimeoutMs: 90000,
  },
  {
    proc: "translatePostBatch",
    bpmnProcessId: "yoro_translate_post_batch",
    nsid: "com.etzhayyim.apps.yoro.translatePostBatch",
    resultTimeoutMs: 300000,
  },
];

const bpmnPath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/yoro/${s.proc}.bpmn`;
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVid = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/yoro-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) =>
  `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/yoro-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${s.resultTimeoutMs}, 'vertex_repo_record,vertex_post,vertex_translation_link',
        'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id = ${bindingVid(s)}
    `.execute(db);
    await sql`
      DELETE FROM vertex_bpmn_process_def
      WHERE vertex_id = ${processVid(s)}
    `.execute(db);
  }
}
