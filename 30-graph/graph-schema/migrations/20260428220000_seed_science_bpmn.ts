import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Registers 3 science knowledge BPMN actors (ADR-0056):
//   sciencePaperIngest  — arXiv ingest → Murakumo embed → KG link (R/PT6H)
//   scienceElementSeed  — 118 periodic elements + PBR materials (R/P1D)
//   scienceTaxonSync    — NCBI taxonomy subtree + vegetation render profiles (R/PT12H)
//
// All 3 task types are handled by science_knowledge.py pymagatama primitives
// (maps.building.*, science.paper.*, science.element.*, science.taxon.*).
// The bpmn-dispatcher F5 watcher picks these up within 30 s.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-28T22:00:00+09:00";
const ownerDid = "did:web:bpmn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.maps";

interface ProcessSeed {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/science-paper-ingest-v1",
    bpmnProcessId: "science_paper_ingest",
    sourcePath: "00-contracts/bpmn/ai/gftd/maps/sciencePaperIngest.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/science-element-seed-v1",
    bpmnProcessId: "science_element_seed",
    sourcePath: "00-contracts/bpmn/ai/gftd/maps/scienceElementSeed.bpmn",
  },
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/science-taxon-sync-v1",
    bpmnProcessId: "science_taxon_sync",
    sourcePath: "00-contracts/bpmn/ai/gftd/maps/scienceTaxonSync.bpmn",
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
