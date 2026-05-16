import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  sourcePath: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T09:08:00Z";
const ownerDid = "did:web:mangaka.gftd.ai";
const actorTag = "sys.bpmn.seed.mangaka.standalone";
// bpmn-coverage gate marker: project: "mangaka"
const project = "mangaka";

const seeds: Seed[] = [
  {
    proc: "generateImageStandalone",
    bpmnProcessId: "mangaka_generate_image_standalone",
    nsid: "ai.gftd.apps.mangaka.generateImage",
    sourcePath: "00-contracts/bpmn/ai/gftd/mangaka/generateImageStandalone.bpmn",
    resultTimeoutMs: 600000,
  },
  {
    proc: "realtimeDraw",
    bpmnProcessId: "mangaka_realtime_draw",
    nsid: "ai.gftd.apps.mangaka.realtimeDraw",
    sourcePath: "00-contracts/bpmn/ai/gftd/mangaka/realtimeDraw.bpmn",
    resultTimeoutMs: 600000,
  },
  {
    proc: "storyboardStandalone",
    bpmnProcessId: "mangaka_storyboard_standalone",
    nsid: "ai.gftd.apps.mangaka.storyboard",
    sourcePath: "00-contracts/bpmn/ai/gftd/mangaka/storyboardStandalone.bpmn",
    resultTimeoutMs: 180000,
  },
  {
    proc: "autoLayoutStandalone",
    bpmnProcessId: "mangaka_auto_layout_standalone",
    nsid: "ai.gftd.apps.mangaka.autoLayout",
    sourcePath: "00-contracts/bpmn/ai/gftd/mangaka/autoLayoutStandalone.bpmn",
    resultTimeoutMs: 180000,
  },
  {
    proc: "projectChatStandalone",
    bpmnProcessId: "mangaka_project_chat_standalone",
    nsid: "ai.gftd.apps.mangaka.projectChat",
    sourcePath: "00-contracts/bpmn/ai/gftd/mangaka/projectChatStandalone.bpmn",
    resultTimeoutMs: 180000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const processVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${project}-${s.proc}-v1`;
const bindingVertexId = (s: Seed) =>
  `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${project}-${s.proc}-v1`;

async function insertProcessDef(db: Kysely<unknown>, s: Seed): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${processVertexId(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
      ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: Seed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
      CAST(${s.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await insertProcessDef(db, s);
    await insertBinding(db, s);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
