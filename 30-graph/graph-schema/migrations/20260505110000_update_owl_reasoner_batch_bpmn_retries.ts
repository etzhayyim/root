import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Update owlReasonerBatch.bpmn to add retries="0" on all service tasks.
//
// Root cause of the 2026-05-03 broker saturation: R/PT1H timer spawned new
// owl_reasoner_batch instances while prior instances were stuck waiting for
// owl.el.classify jobs. Default retries=3 meant each failed job sat in the
// broker queue for 3 cycles before the process instance failed, creating a
// >60-job backlog that triggered RESOURCE_EXHAUSTED on all other workers.
//
// Fix: retries="0" on owl.el.classify, owl.ql.precompute, owl.benchmark.compare
// (owl.dl.classify keeps retries=1+PT10M backoff since HermiT is expensive
// and one transient failure is worth retrying).
// With retries=0, a worker exception immediately fails the process instance —
// the next R/PT1H fire starts fresh, no accumulation.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const BPMN_PROCESS_ID = "owl_reasoner_batch";
const BPMN_FILE = path.resolve(
  repoRoot,
  "00-contracts/bpmn/ai/gftd/owl/owlReasonerBatch.bpmn",
);

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(BPMN_FILE, "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml"           = ${xml},
        xml_byte_size   = CAST(${size} AS integer),
        status          = 'active',
        deployed_at     = NULL,
        deployed_zeebe_key = NULL
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET status = 'inactive'
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}
