// Phase 2 cutover — sentinel BPMN XML update.
//
// Updates vertex_bpmn_process_def for sentinelIngest + sentinelAnalyze
// to Phase 2 XML (exporterVersion="2.0"):
//   - sentinelIngest: removes Task_PersistScenes fan-out (primitive writes
//     directly to vertex_satellite_scene), fixes snake_case ioMapping params,
//     renames scenesScanned → scenesFound.
//   - sentinelAnalyze: removes Task_PersistResult (primitive writes directly
//     to vertex_satellite_analysis), fixes Task_LoadScene table/whereExpr,
//     updates snake_case task inputs.
//
// F5 watcher detects xml column change and redeploys to Zeebe.
// ADR-2604271800.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const project = "maps";

const procs = ["sentinelIngest", "sentinelAnalyze"] as const;

const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (proc: string) =>
  `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${project}-${slug(proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const proc of procs) {
    const rel = `00-contracts/bpmn/ai/gftd/${project}/${proc}.bpmn`;
    const xml = readFileSync(path.resolve(repoRoot, rel), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      UPDATE vertex_bpmn_process_def
      SET "xml" = ${xml},
          "xml_byte_size" = CAST(${size} AS integer),
          "version" = 2,
          "source_path" = ${rel}
      WHERE "vertex_id" = ${processVertexId(proc)}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  // Phase 1 XML is in git history. Re-run the Phase 1 seed migration
  // (20260427230000_seed_sentinel_bpmn_actors.ts) to restore.
  for (const proc of procs) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET version = 1
      WHERE vertex_id = ${processVertexId(proc)}
    `.execute(db);
  }
}
