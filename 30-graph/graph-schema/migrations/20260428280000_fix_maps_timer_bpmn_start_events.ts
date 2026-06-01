// Fix all maps timer-start BPMNs: add Start_Manual none-start event.
//
// All 11 maps BPMNs with timer-start events previously had only the
// timer-start. Zeebe's CreateProcessInstanceWithResult cannot instantiate
// timer-only processes → on-demand XRPC calls fail with 500 → fallback.
//
// Fix: add Start_Manual none-start event (same pattern as flight-offer fix
// in migration 20260428270000). Each BPMN's first service task now accepts
// both incoming flows.
//
// Affected BPMNs (11 total, sentinelAnalyze skipped — already none-start only):
//   advanceCoverage, bulkRefreshFerryRoutes, bulkRefreshGeonames,
//   bulkRefreshGtfsJp, bulkRefreshOpenflights, bulkRefreshOsmPlanet,
//   bulkRefreshWikidata, bulkRefreshWikipedia, refreshCoverageStats,
//   runPendingCoverageJobs, sentinelIngest
//
// Clears deployed_at so F5 watcher re-deploys updated XML to Zeebe.
// Bumps version 1 → 2.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const project = "maps";

const procs = [
  "advanceCoverage",
  "bulkRefreshFerryRoutes",
  "bulkRefreshGeonames",
  "bulkRefreshGtfsJp",
  "bulkRefreshOpenflights",
  "bulkRefreshOsmPlanet",
  "bulkRefreshWikidata",
  "bulkRefreshWikipedia",
  "refreshCoverageStats",
  "runPendingCoverageJobs",
  "sentinelIngest",
] as const;

const slug = (proc: string) =>
  proc.replace(/([A-Z])/g, "-$1").toLowerCase();

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
          "source_path" = ${rel},
          "deployed_at" = NULL,
          "deployed_zeebe_key" = NULL
      WHERE "vertex_id" = ${processVertexId(proc)}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const proc of procs) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET "version" = 1,
          "deployed_at" = NULL,
          "deployed_zeebe_key" = NULL
      WHERE "vertex_id" = ${processVertexId(proc)}
    `.execute(db);
  }
}
