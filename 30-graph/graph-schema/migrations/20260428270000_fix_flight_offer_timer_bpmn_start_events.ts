// Fix flight-offer cleanupRuns + pollWatchlist BPMN: add Start_Manual none-start event.
//
// Both BPMNs previously had only a timer-start event. Zeebe's CreateProcessInstance
// API cannot instantiate timer-only processes, causing the BPMN dispatcher to throw
// an exception → 500 → dispatch.ts fallback to local → actor Worker 522.
//
// Fix: add Start_Manual none-start event (same pattern as crawlAds.bpmn).
// Both start events flow into Task_Health (the first service task).
//
// Also corrects result_timeout_ms in vertex_bpmn_lexicon_binding:
// the BPMN documentation block declares 300000ms, but the seed migration
// used the default 10000ms. 300s matches the intent for multi-watch scans.
//
// Migration clears deployed_at so the F5 watcher re-deploys the updated XML.

import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const project = "flight-offer";

const procs = ["cleanupRuns", "pollWatchlist"] as const;

const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const processVertexId = (proc: string) =>
  `at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/flight-offer-${slug(proc)}-v1`;
const nsid = (proc: string) => `ai.gftd.apps.flightOffer.${proc}`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const proc of procs) {
    const rel = `00-contracts/bpmn/ai/gftd/${project}/${proc}.bpmn`;
    const xml = readFileSync(path.resolve(repoRoot, rel), "utf8");
    const size = Buffer.byteLength(xml, "utf8");

    // Update XML and clear deployed_at so F5 watcher redeploys to Zeebe.
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

    // Fix result_timeout_ms: BPMN doc declares 300000ms; seed used default 10000ms.
    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET result_timeout_ms = 300000
      WHERE nsid = ${nsid(proc)}
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const proc of procs) {
    await sql`
      UPDATE vertex_bpmn_process_def
      SET version = 1,
          deployed_at = NULL,
          deployed_zeebe_key = NULL
      WHERE vertex_id = ${processVertexId(proc)}
    `.execute(db);
    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET result_timeout_ms = 10000
      WHERE nsid = ${nsid(proc)}
    `.execute(db);
  }
}
