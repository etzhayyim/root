import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

/**
 * MS Graph mail subscription lifecycle table.
 * Persisted by lawfirm.msGraph.subscriptionEnsure / subscriptionRenew.
 *
 * BPMN seed uses canonical schema (bpmn_process_id / xml / xml_byte_size /
 * source_path / RLS columns).
 */

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-08T00:00:00Z";
const ownerDid = "did:web:lawfirm.etzhayyim.com";
const actorTag = "sys.bpmn.seed.lawfirm";

const PROCESS = {
  vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/lawfirm-msgraph-subscription-renew-tick-v1",
  bpmnProcessId: "lawfirm_msgraph_subscription_renew_tick",
  sourcePath: "00-contracts/bpmn/ai/gftd/lawfirm/msGraphSubscriptionRenewTick.bpmn",
};

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_lawfirm_msgraph_subscription (
      vertex_id        varchar PRIMARY KEY,
      subscription_id  varchar NOT NULL,
      user_upn         varchar NOT NULL,
      resource         varchar NOT NULL,
      notification_url varchar NOT NULL,
      client_state     varchar,
      expires_at       varchar,
      status           varchar DEFAULT 'active',
      last_renewed_at  varchar,
      created_at       varchar,
      sensitivity_ord  int DEFAULT 200,
      owner_did        varchar)
  `.execute(db);

  const xml = readContract(PROCESS.sourcePath);
  const size = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${PROCESS.vertexId}, ${ownerDid}, ${PROCESS.bpmnProcessId}, 1, ${xml}, CAST(${size} AS integer), ${PROCESS.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId})
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${PROCESS.vertexId}`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_lawfirm_msgraph_subscription`.execute(db);
}
