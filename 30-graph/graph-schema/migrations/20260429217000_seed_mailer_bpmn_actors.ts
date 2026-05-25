import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; op: string; processId: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:mailer.etzhayyim.com";
const createdAt = "2026-04-29T22:10:00+09:00";
const actorId = "sys.bpmn.seed.mailer";

const seeds: Seed[] = [
  { slug: "health", op: "health", processId: "mailer_health", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/health.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-emails", op: "listEmails", processId: "mailer_list_emails", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/listEmails.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "list-bindings", op: "listBindings", processId: "mailer_list_bindings", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/listBindings.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "stats", op: "stats", processId: "mailer_stats", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/stats.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "send-email", op: "sendEmail", processId: "mailer_send_email", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/sendEmail.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_mailer_outbound_email" },
  { slug: "provision-mailbox", op: "provisionMailbox", processId: "mailer_provision_mailbox", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/provisionMailbox.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_mailer_email_binding" },
  { slug: "handle-commit", op: "handleCommit", processId: "mailer_handle_commit", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/handleCommit.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "heartbeat", op: "heartbeat", processId: "mailer_heartbeat", sourcePath: "00-contracts/bpmn/ai/gftd/mailer/heartbeat.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/mailer-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/mailer-${s.op}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${`app.etzhayyim.apps.mailer.${s.op}`}, ${s.processId}, 1,
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
