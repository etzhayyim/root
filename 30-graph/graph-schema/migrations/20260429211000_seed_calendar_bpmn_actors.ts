import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; processId: string; nsid: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:calendar.etzhayyim.com";
const createdAt = "2026-04-29T21:10:00+09:00";
const actorId = "sys.bpmn.seed.calendar";
const project = "calendar";

const seeds: Seed[] = [
  { slug: "create-event", processId: "calendar_create_event", nsid: "com.etzhayyim.apps.calendar.createEvent", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/createEvent.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_calendar_event,vertex_calendar_invitation" },
  { slug: "update-event", processId: "calendar_update_event", nsid: "com.etzhayyim.apps.calendar.updateEvent", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/updateEvent.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_calendar_event" },
  { slug: "delete-event", processId: "calendar_delete_event", nsid: "com.etzhayyim.apps.calendar.deleteEvent", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/deleteEvent.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_calendar_event" },
  { slug: "list-events", processId: "calendar_list_events", nsid: "com.etzhayyim.apps.calendar.listEvents", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/listEvents.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "get-event", processId: "calendar_get_event", nsid: "com.etzhayyim.apps.calendar.getEvent", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/getEvent.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "create-recurring", processId: "calendar_create_recurring", nsid: "com.etzhayyim.apps.calendar.createRecurring", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/createRecurring.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_calendar_event,vertex_calendar_invitation" },
  { slug: "rsvp", processId: "calendar_rsvp", nsid: "com.etzhayyim.apps.calendar.rsvp", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/rsvp.bpmn", timeoutMs: 30000, writeTableAllowlist: "vertex_calendar_rsvp,vertex_calendar_invitation" },
  { slug: "list-invitations", processId: "calendar_list_invitations", nsid: "com.etzhayyim.apps.calendar.listInvitations", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/listInvitations.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "connect-account", processId: "calendar_connect_account", nsid: "com.etzhayyim.apps.calendar.connectAccount", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/connectAccount.bpmn", timeoutMs: 30000, writeTableAllowlist: "" },
  { slug: "oauth-callback", processId: "calendar_oauth_callback", nsid: "com.etzhayyim.apps.calendar.oauthCallback", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/oauthCallback.bpmn", timeoutMs: 120000, writeTableAllowlist: "vertex_gcal_oauth_token,vertex_gcal_account" },
  { slug: "sync-from-google", processId: "calendar_sync_from_google", nsid: "com.etzhayyim.apps.calendar.syncFromGoogle", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/syncFromGoogle.bpmn", timeoutMs: 180000, writeTableAllowlist: "vertex_gcal_oauth_token,vertex_gcal_account,vertex_gcal_event,vertex_gcal_attendee" },
  { slug: "cron-tick", processId: "calendar_cron_tick", nsid: "com.etzhayyim.apps.calendar.cronTick", sourcePath: "00-contracts/bpmn/com/etzhayyim/calendar/cronTick.bpmn", timeoutMs: 180000, writeTableAllowlist: "vertex_gcal_oauth_token,vertex_gcal_event,vertex_gcal_attendee" },
];

const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/${project}-${s.slug}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${project}-${s.slug}-v1`;

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
        ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1,
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
