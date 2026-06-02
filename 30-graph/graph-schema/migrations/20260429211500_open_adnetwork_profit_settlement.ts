import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

const createdAt = "2026-04-29T21:15:00+09:00";
const ownerDid = "did:web:yoro.etzhayyim.com";
const actorTag = "sys.bpmn.seed.business-profit";
const sourcePath = "00-contracts/bpmn/com/etzhayyim/open-adnetwork/settleBusinessProfit.bpmn";
const bpmnProcessId = "open_adnetwork_settle_business_profit";
const nsid = "com.etzhayyim.apps.openAdnetwork.settleBusinessProfit";
const processVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-adnetwork-settle-business-profit-v1";
const bindingVertexId =
  "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/open-adnetwork-settle-business-profit-v1";

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_adnetwork_profit_settlement (
      vertex_id                 VARCHAR PRIMARY KEY,
      settlement_id             VARCHAR NOT NULL,
      publisher_did             VARCHAR NOT NULL,
      window_start_ms           BIGINT NOT NULL,
      window_end_ms             BIGINT NOT NULL,
      impressions               BIGINT NOT NULL DEFAULT 0,
      publisher_count           INTEGER NOT NULL DEFAULT 0,
      gross_revenue_usd         DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      publisher_share_pct       DOUBLE PRECISION NOT NULL DEFAULT 70.0,
      publisher_profit_usd      DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      platform_profit_usd       DOUBLE PRECISION NOT NULL DEFAULT 0.0,
      currency                  VARCHAR NOT NULL DEFAULT 'USD',
      chain_id                  INTEGER NOT NULL DEFAULT 260425,
      chain_receipt_submitted   BOOLEAN NOT NULL DEFAULT false,
      chain_receipt_tx          VARCHAR,
      chain_receipt_reason      VARCHAR,
      status                    VARCHAR NOT NULL DEFAULT 'settled',
      created_at                VARCHAR NOT NULL,
      sensitivity_ord           INTEGER NOT NULL DEFAULT 0,
      org_id                    VARCHAR,
      user_id                   VARCHAR,
      actor_id                  VARCHAR,
      actor_did                 VARCHAR,
      org_did                   VARCHAR
    )
  `.execute(db);
  await sql`FLUSH`.execute(db);

  const xml = readFileSync(path.resolve(repoRoot, sourcePath), "utf8");
  const size = Buffer.byteLength(xml, "utf8");
  const sizeRaw = sql.raw(String(size));

  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, actor_did, org_did
    )
    SELECT
      ${processVertexId}, ${ownerDid}, ${bpmnProcessId}, 1, ${xml},
      ${sizeRaw}, ${sourcePath}, 'active', ${createdAt}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag}, ${ownerDid}, ${ownerDid}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}
    )
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_process_def
    SET "xml" = ${xml},
        xml_byte_size = ${sizeRaw},
        source_path = ${sourcePath},
        status = 'active',
        deployed_at = NULL,
        deployed_zeebe_key = CAST(NULL AS BIGINT)
    WHERE vertex_id = ${processVertexId}
  `.execute(db);

  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, write_table_allowlist, status, created_at,
      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
    )
    SELECT
      ${bindingVertexId}, ${ownerDid}, ${nsid}, ${bpmnProcessId}, 1,
      180000, 'vertex_open_adnetwork_profit_settlement',
      'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag},
      ${ownerDid}, ${ownerDid}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}
    )
  `.execute(db);

  await sql`
    UPDATE vertex_bpmn_lexicon_binding
    SET write_table_allowlist = 'vertex_open_adnetwork_profit_settlement',
        result_timeout_ms = 180000,
        status = 'active'
    WHERE bpmn_process_id = ${bpmnProcessId}
      AND nsid = ${nsid}
  `.execute(db);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
  await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId}`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_adnetwork_profit_settlement`.execute(db);
}
