import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Registers science BPMN workers with the BPMN-as-actor framework (ADR-0056).
// The bpmn-dispatcher F5 watcher polls vertex_bpmn_process_def every 30s and
// deploys to Zeebe automatically.
//
// kamiSeedScientific.bpmn  — Timer-start R/PT6H: seed CPK sphere + vegetation
//   kami model instances for all 118 elements and known taxa.
// sciencePaperIngest.bpmn  — Timer-start R/PT24H: fetch arXiv → embed →
//   linkGraph for one domain/query pair per fire.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-29T09:00:00+09:00";
const ownerDid = "did:web:bpmn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.science";

interface ProcessSeed {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-kami-seed-v1",
    bpmnProcessId: "science_kami_seed_scientific",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/science/kamiSeedScientific.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/science-paper-ingest-v1",
    bpmnProcessId: "science_paper_ingest",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/science/sciencePaperIngest.bpmn",
  },
];

async function insertProcessDef(
  db: Kysely<unknown>,
  s: ProcessSeed,
): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) await insertProcessDef(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
}
