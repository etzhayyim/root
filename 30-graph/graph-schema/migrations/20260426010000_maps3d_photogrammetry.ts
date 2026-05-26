import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// maps3d photogrammetry pipeline (Phase 2):
//   - vertex_maps3d_tile         — H3-cell registry the BPMN picker walks.
//   - vertex_langgraph_state     — checkpoint store for curator/replanner/actor-linker.
//   - vertex_bpmn_process_def    — registers processTile.bpmn so the F5
//                                  watcher in bpmn-dispatcher picks it up.
//   - vertex_bpmn_lexicon_binding — maps NSID `app.etzhayyim.apps.maps3d.processTile`
//                                  to the BPMN process id (BPMN-as-actor, ADR-0056).
//
// Lexicon contracts for the inner pipeline tasks (fetchMapillary,
// curateImages, colmapTile, simplifyAndExport, visionAnnotate, linkActor,
// replanReconstruction) live in 00-contracts/lexicons/ai/gftd/apps/maps3d/
// but are NOT BPMN entry points — they describe Zeebe service-task
// contracts implemented by pyzeebe workers in `50-infra/k8s/maps3d/`.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const createdAt = "2026-04-26T01:00:00+09:00";
const ownerDid = "did:web:bpmn.etzhayyim.com";
const actorTag = "sys.bpmn.seed.maps3d";

interface ProcessSeed {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/maps3d-process-tile-v1",
    bpmnProcessId: "maps3d_process_tile",
    sourcePath: "00-contracts/bpmn/ai/gftd/maps3d/processTile.bpmn",
  },
];

interface BindingSeed {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  resultTimeoutMs: number;
}

const bindingSeeds: BindingSeed[] = [
  {
    vertexId:
      "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/maps3d-process-tile-v1",
    nsid: "app.etzhayyim.apps.maps3d.processTile",
    bpmnProcessId: "maps3d_process_tile",
    // 90 min — covers the 60 min COLMAP boundary plus all surrounding
    // tasks. Tile is async-fire-and-forget anyway; XRPC caller only
    // waits for instanceKey.
    resultTimeoutMs: 5_400_000,
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

async function insertBinding(
  db: Kysely<unknown>,
  s: BindingSeed,
): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(${s.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  // ── Tile registry: BPMN picker walks this each R/PT15M tick. ──
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_maps3d_tile (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      tile_h3 VARCHAR NOT NULL,
      h3_resolution BIGINT,
      centroid_lat DOUBLE PRECISION,
      centroid_lng DOUBLE PRECISION,
      priority BIGINT,
      status VARCHAR NOT NULL,
      mesh_uri VARCHAR,
      image_count BIGINT,
      triangle_count BIGINT,
      reconstruction_ms BIGINT,
      last_attempt_at VARCHAR,
      attempt_count BIGINT,
      error_code VARCHAR,
      error_message VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps3d_tile_status ON vertex_maps3d_tile (status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps3d_tile_priority ON vertex_maps3d_tile (priority, status)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_maps3d_tile_h3 ON vertex_maps3d_tile (tile_h3)
  `.execute(db);

  // ── LangGraph checkpoint store. ──
  // Each row = one (run, node) state snapshot. Pod restart resumes from
  // the last checkpoint. attempt_count + parent_run_id let us reconstruct
  // a run lineage if the BPMN exclusive-gateway loops back.
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_langgraph_state (
      vertex_id VARCHAR PRIMARY KEY,
      _seq BIGINT,
      created_date DATE,
      sensitivity_ord BIGINT,
      owner_did VARCHAR,
      run_id VARCHAR NOT NULL,
      parent_run_id VARCHAR,
      graph_name VARCHAR NOT NULL,
      tile_h3 VARCHAR,
      node_name VARCHAR NOT NULL,
      checkpoint_seq BIGINT,
      state_json VARCHAR,
      audit_json VARCHAR,
      latency_ms BIGINT,
      status VARCHAR,
      created_at VARCHAR,
      org_id VARCHAR,
      user_id VARCHAR,
      actor_id VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_run ON vertex_langgraph_state (run_id, checkpoint_seq)
  `.execute(db);

  await sql`
    CREATE INDEX IF NOT EXISTS idx_langgraph_tile ON vertex_langgraph_state (tile_h3)
  `.execute(db);

  // ── BPMN-as-actor registration (ADR-0056). The bpmn-dispatcher F5
  //    watcher polls vertex_bpmn_process_def + vertex_bpmn_lexicon_binding
  //    every 30s and deploys to Zeebe; no manual deploy step. ──
  for (const s of processSeeds) await insertProcessDef(db, s);
  for (const s of bindingSeeds) await insertBinding(db, s);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
  for (const s of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
  await sql`DROP TABLE IF EXISTS vertex_langgraph_state`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_maps3d_tile`.execute(db);
}
