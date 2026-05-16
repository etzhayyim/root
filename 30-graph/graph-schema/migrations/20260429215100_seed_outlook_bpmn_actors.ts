import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:outlook.gftd.ai";
const createdAt = "2026-04-29T21:51:00+09:00";
const actorId = "sys.bpmn.seed.outlook";

const seeds: Seed[] = [
  { slug: "get-oauth-config", op: "getOauthConfig", processId: "outlook_get_oauth_config", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/getOauthConfig.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-auth-status", op: "getAuthStatus", processId: "outlook_get_auth_status", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/getAuthStatus.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "start-auth", op: "startAuth", processId: "outlook_start_auth", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/startAuth.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_outlook_pending_oauth" },
  { slug: "exchange-code", op: "exchangeCode", processId: "outlook_exchange_code", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/exchangeCode.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_outlook_pending_oauth,vertex_outlook_oauth_connection,vertex_outlook_sync_job" },
  { slug: "get-connection", op: "getConnection", processId: "outlook_get_connection", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/getConnection.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_outlook_oauth_connection" },
  { slug: "sync-mailbox", op: "syncMailbox", processId: "outlook_sync_mailbox", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/syncMailbox.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_outlook_oauth_connection,vertex_outlook_sync_job" },
  { slug: "disconnect", op: "disconnect", processId: "outlook_disconnect", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/disconnect.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_outlook_pending_oauth,vertex_outlook_oauth_connection" },
  { slug: "card-home", op: "cardHome", processId: "outlook_card_home", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/cardHome.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "card-compose", op: "cardCompose", processId: "outlook_card_compose", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/cardCompose.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "card-action", op: "cardAction", processId: "outlook_card_action", sourcePath: "00-contracts/bpmn/ai/gftd/outlook/cardAction.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/outlook-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/outlook-${s.op}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
        ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`ai.gftd.apps.outlook.${s.op}`}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
