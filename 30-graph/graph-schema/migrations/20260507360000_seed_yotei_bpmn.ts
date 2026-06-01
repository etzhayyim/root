import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  resultTimeoutMs: number;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:yotei.etzhayyim.com";
const createdAt = "2026-05-07T00:20:00Z";
const actorId = "sys.bpmn.seed.yotei";

const snake = (proc: string) => proc.replace(/([A-Z])/g, "_$1").toLowerCase();
const slug = (proc: string) => proc.replace(/([A-Z])/g, "-$1").toLowerCase();
const writeAllowlist = "vertex_yotei_calendar,vertex_yotei_availability,vertex_yotei_event,vertex_yotei_booking";
const writeProcs = new Set([
  "cancelBooking",
  "cancelEvent",
  "confirmBooking",
  "createCalendar",
  "createEvent",
  "deleteCalendar",
  "proposeBooking",
  "removeAvailability",
  "setAvailability",
  "updateEvent",
]);

const seeds: Seed[] = [
  "analyzeSchedule",
  "autoReschedule",
  "cancelBooking",
  "cancelEvent",
  "confirmBooking",
  "createCalendar",
  "createEvent",
  "deleteCalendar",
  "describe",
  "getAvailability",
  "getBooking",
  "getCalendar",
  "getEvent",
  "getOpenSlots",
  "health",
  "listBookings",
  "listCalendars",
  "listEvents",
  "proposeBooking",
  "removeAvailability",
  "setAvailability",
  "suggestSlots",
  "updateEvent",
].map((proc) => ({
  proc,
  bpmnProcessId: `yotei_${snake(proc)}`,
  nsid: `app.etzhayyim.apps.yotei.${proc}`,
  resultTimeoutMs: 30000,
  writeTableAllowlist: writeProcs.has(proc) ? writeAllowlist : "",
}));

const bpmnPath = (s: Seed) => `00-contracts/bpmn/ai/gftd/yotei/${s.proc}.bpmn`;
const processVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/yotei-${slug(s.proc)}-v1`;
const bindingVid = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/yotei-${slug(s.proc)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, bpmnPath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml,
        source_path, status, created_at, sensitivity_ord,
        org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${processVid(s)}, ${ownerDid}, ${s.bpmnProcessId}, 1,
        ${xml}, ${bpmnPath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}
      )
    `.execute(db);
    await sql`
      UPDATE vertex_bpmn_process_def
      SET xml_byte_size = ${size}
      WHERE vertex_id = ${processVid(s)} AND xml_byte_size IS NULL
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVid(s)}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1,
        ${sql.raw(String(s.resultTimeoutMs))}, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVid(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVid(s)}`.execute(db);
  }
}
