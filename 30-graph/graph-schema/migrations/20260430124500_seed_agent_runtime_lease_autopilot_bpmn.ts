import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

// Seed the timer-started autonomous-agent runtime lease autopilot BPMN.
// ADR-2604301200 P3: every 15 minutes, renew near-expiring leases, hibernate
// expired leases after grace, and start missing active-profile runtime leases.

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const CREATED_AT = "2026-04-30T12:45:00Z";
const OWNER_DID = "did:web:agent.etzhayyim.com";
const ACTOR_TAG = "sys.bpmn.seed.agent.runtime.autopilot";

const VERTEX_ID =
  "at://did:web:agent.etzhayyim.com/ai.gftd.apps.bpmn.processDef/agent-runtime-lease-autopilot-v1";
const BPMN_PROCESS_ID = "agent_runtime_lease_autopilot";
const SOURCE_PATH =
  "00-contracts/bpmn/ai/gftd/agent/runtimeLeaseAutopilot.bpmn";

export async function up(db: Kysely<unknown>): Promise<void> {
  const xml = readFileSync(
    path.resolve(repoRoot, SOURCE_PATH),
    "utf8",
  );
  const size = Buffer.byteLength(xml, "utf8");

  await sql`
    INSERT INTO vertex_bpmn_process_def
      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${VERTEX_ID}, ${OWNER_DID}, ${BPMN_PROCESS_ID}, 1, ${xml},
           CAST(${size} AS integer), ${SOURCE_PATH}, 'active', ${CREATED_AT},
           1, ${OWNER_DID}, ${OWNER_DID}, ${ACTOR_TAG}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${VERTEX_ID}
    )
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`
    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${VERTEX_ID}
  `.execute(db);
}
