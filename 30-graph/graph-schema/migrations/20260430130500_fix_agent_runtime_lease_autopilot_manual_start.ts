import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Refresh autopilot BPMN with an operator manual start event in addition to
// the timer start, so rollout can trigger one immediate lifecycle tick.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const BPMN_PROCESS_ID = "agent_runtime_lease_autopilot";
const SOURCE_PATH =
  "00-contracts/bpmn/com/etzhayyim/agent/runtimeLeaseAutopilot.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, SOURCE_PATH),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        xml_byte_size = CAST(${size} AS integer),
        "status" = 'active',
        deployed_at = NULL,
        deployed_zeebe_key = NULL
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    UPDATE vertex_bpmn_process_def
    SET deployed_at = NULL,
        deployed_zeebe_key = NULL
    WHERE bpmn_process_id = ${BPMN_PROCESS_ID}
  `.execute(db);
}
