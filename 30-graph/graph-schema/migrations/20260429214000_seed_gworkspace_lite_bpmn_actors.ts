import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  app: string;
  slug: string;
  processId: string;
  nsid: string;
  sourcePath: string;
  timeoutMs: number;
  writeTableAllowlist: string;
  updateExisting?: boolean;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-29T21:40:00+09:00";
const actorId = "sys.bpmn.seed.gworkspace_lite";

const tableNames: Record<string, { token: string; account: string }> = {
  tasks: { token: "vertex_gtasks_oauth_token", account: "vertex_gtasks_account" },
  sheets: { token: "vertex_gsheets_oauth_token", account: "vertex_gsheets_account" },
  drive: { token: "vertex_gdrive_oauth_token", account: "vertex_gdrive_account" },
  contacts: { token: "vertex_gcontacts_oauth_token", account: "vertex_gcontacts_account" },
  meet: { token: "vertex_gmeet_oauth_token", account: "vertex_gmeet_account" },
  docs: { token: "vertex_gdocs_oauth_token", account: "vertex_gdocs_account" },
  slides: { token: "vertex_gslides_oauth_token", account: "vertex_gslides_account" },
  gmail: { token: "vertex_gmail_oauth_token", account: "vertex_gmail_account" },
};

const apps = Object.keys(tableNames).filter((app) => app !== "gmail");

const seeds: Seed[] = apps.flatMap((app) => {
  const tables = tableNames[app];
  return [
    {
      app,
      slug: "connect-account",
      processId: `${app}_connect_account`,
      nsid: `ai.gftd.apps.${app}.connectAccount`,
      sourcePath: `00-contracts/bpmn/ai/gftd/${app}/connectAccount.bpmn`,
      timeoutMs: 30000,
      writeTableAllowlist: "",
    },
    {
      app,
      slug: "oauth-callback",
      processId: `${app}_oauth_callback`,
      nsid: `ai.gftd.apps.${app}.oauthCallback`,
      sourcePath: `00-contracts/bpmn/ai/gftd/${app}/oauthCallback.bpmn`,
      timeoutMs: 120000,
      writeTableAllowlist: `${tables.token},${tables.account}`,
    },
    {
      app,
      slug: "sync-from-google",
      processId: `${app}_sync_from_google`,
      nsid: `ai.gftd.apps.${app}.syncFromGoogle`,
      sourcePath: `00-contracts/bpmn/ai/gftd/${app}/syncFromGoogle.bpmn`,
      timeoutMs: 120000,
      writeTableAllowlist: `${tables.token},${tables.account}`,
    },
    {
      app,
      slug: "cron-tick",
      processId: `${app}_cron_tick`,
      nsid: `ai.gftd.apps.${app}.cronTick`,
      sourcePath: `00-contracts/bpmn/ai/gftd/${app}/cronTick.bpmn`,
      timeoutMs: 120000,
      writeTableAllowlist: `${tables.token},${tables.account}`,
      updateExisting: true,
    },
  ];
});

seeds.push(
  ...[
    ["connect-account", "connectAccount", 30000, ""],
    ["oauth-callback", "oauthCallback", 120000, "vertex_gmail_oauth_token,vertex_gmail_account"],
    ["disconnect-account", "disconnectAccount", 30000, "vertex_gmail_oauth_token,vertex_gmail_account_binding"],
    ["sync-inbox", "syncInbox", 180000, "vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert"],
    ["send-email", "sendEmail", 120000, "vertex_gmail_oauth_token,vertex_gmail_outbound_email"],
    ["reply-to-thread", "replyToThread", 120000, "vertex_gmail_oauth_token,vertex_gmail_outbound_email"],
    ["list-accounts", "listAccounts", 30000, ""],
    ["list-threads", "listThreads", 30000, ""],
    ["search-emails", "searchEmails", 30000, ""],
    ["get-thread", "getThread", 120000, ""],
    ["triage", "triage", 30000, ""],
  ].map(([slug, op, timeoutMs, writeTableAllowlist]) => ({
    app: "gmail",
    slug: String(slug),
    processId: `gmail_${String(slug).replace(/-/g, "_")}`,
    nsid: `ai.gftd.apps.gmail.${op}`,
    sourcePath: `00-contracts/bpmn/ai/gftd/gmail/${op}.bpmn`,
    timeoutMs: Number(timeoutMs),
    writeTableAllowlist: String(writeTableAllowlist),
  })),
  {
    app: "gmail",
    slug: "cron-tick",
    processId: "gmail_cron_tick",
    nsid: "ai.gftd.apps.gmail.cronTick",
    sourcePath: "00-contracts/bpmn/ai/gftd/gmail/cronTick.bpmn",
    timeoutMs: 180000,
    writeTableAllowlist: "vertex_gmail_oauth_token,vertex_gmail_email,vertex_gmail_sync_job,vertex_gmail_phishing_alert",
    updateExisting: true,
  },
);

const processVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/${s.app}-${s.slug}-v1`;
const bindingSlug = (s: Seed) => s.slug === "cron-tick" ? "cronTick" : s.slug;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/${s.app}-${bindingSlug(s)}-v1`;
const ownerDid = (app: string) => `did:web:${app}.gftd.ai`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, s.sourcePath), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    const owner = ownerDid(s.app);

    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${owner}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${s.sourcePath}, 'active',
        ${createdAt}, 1, ${owner}, ${owner}, ${actorId},
        ${owner}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    if (s.updateExisting) {
      await sql`
        UPDATE vertex_bpmn_process_def
        SET xml = ${xml}, xml_byte_size = CAST(${size} AS integer), source_path = ${s.sourcePath}
        WHERE vertex_id = ${processVertexId(s)}
      `.execute(db);
    }

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${owner}, ${s.nsid}, ${s.processId}, 1,
        CAST(${s.timeoutMs} AS integer), ${s.writeTableAllowlist}, 'active', ${createdAt},
        1, ${owner}, ${owner}, ${actorId}, ${owner}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);

    if (s.updateExisting) {
      await sql`
        UPDATE vertex_bpmn_lexicon_binding
        SET result_timeout_ms = CAST(${s.timeoutMs} AS integer),
            write_table_allowlist = ${s.writeTableAllowlist}
        WHERE vertex_id = ${bindingVertexId(s)}
      `.execute(db);
    }
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    if (!s.updateExisting) {
      await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
      await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
    }
  }
}
