import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.etzhayyim.com Phase 3 step 1.1 — coverage BPMN v2 drops audit step.
 *
 * coverage probes are high-frequency (soak monitor will hit hourly).
 * The audit step (generic.audit.emit) was hitting Zeebe broker
 * back-pressure ("Maximum number of jobs running"), causing the
 * dispatcher's 15s result timeout to fire. Coverage is stateless and
 * doesn't need OCEL audit on every probe — drop the step.
 *
 * UPDATE in place + version bump + reset deployed_zeebe_key so the F5
 * watcher re-deploys to Zeebe on its next tick.
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const seeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/shosha-coverage-v1",
    bpmnProcessId: "shosha_coverage",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/coverage.bpmn",
  },
];

async function updateProcessDef(db: Kysely<unknown>, s: P): Promise<void> {
  const xml = readContract(s.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        "xml_byte_size" = CAST(${size} AS integer),
        "version" = 2,
        "deployed_zeebe_key" = NULL,
        "deployed_at" = NULL
    WHERE "vertex_id" = ${s.vertexId}
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) await updateProcessDef(db, s);
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No-op — v1 XML is in git history.
}
