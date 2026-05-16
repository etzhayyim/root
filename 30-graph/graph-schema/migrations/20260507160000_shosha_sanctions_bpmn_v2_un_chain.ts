import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * shosha.gftd.ai Phase 2b-ext — refreshSanctionsList BPMN v2.
 *
 * Adds Task_Un (`shosha.sanctions.refreshUn`) between Task_Ofac and
 * Task_Audit. Audit eventType + attributes now also include UN counts.
 *
 * UPDATE in place + version bump + reset deployed_zeebe_key so the F5
 * watcher re-deploys to Zeebe on its next tick (≤30s).
 *
 * RW SQL parser treats `xml` and `version` as reserved keywords; quote
 * every column for safety (Phase 1 v2 migration learning).
 */

type P = { vertexId: string; bpmnProcessId: string; sourcePath: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");

const seeds: P[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/shosha-refresh-sanctions-list-v1",
    bpmnProcessId: "shosha_refresh_sanctions_list",
    sourcePath: "00-contracts/bpmn/ai/gftd/shosha/refreshSanctionsList.bpmn",
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
  // No-op — v1 XML cannot be reconstructed without git history.
}
