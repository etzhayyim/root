import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Registers buildingIngest3d.bpmn with the BPMN-as-actor framework (ADR-0056).
// The bpmn-dispatcher F5 watcher polls vertex_bpmn_process_def every 30s and
// deploys to Zeebe automatically. No manual deploy step required.
//
// Timer-start R/PT1H: fetches H3 cells from vertex_spatial (label=Building),
// enriches to vertex_maps_building_3d, updates vertex_maps_building_coverage.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-28T21:00:00+09:00";
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
      "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/maps-building-ingest-3d-v1",
    bpmnProcessId: "maps_building_ingest_3d",
    sourcePath: "00-contracts/bpmn/ai/gftd/maps/buildingIngest3d.bpmn",
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
