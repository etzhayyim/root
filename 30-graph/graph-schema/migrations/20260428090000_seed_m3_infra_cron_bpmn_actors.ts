import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

// M3: Seed BPMN process_def + lexicon_binding for magatama organizer and graph consumer.
// Replaces CF Worker triggers.crons with Zeebe timer-start BPMN (ADR-0056/ADR-2604251801).
export async function up(db: Kysely<unknown>): Promise<void> {
  const now = "2026-04-28T09:00:00Z";

  const entries = [
    {
      vid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/magatama-cron-tick-v1",
      ownerDid: "did:web:magatama.etzhayyim.com",
      bpmnProcessId: "com.etzhayyim.magatama.cronTick",
      rel: "00-contracts/bpmn/com/etzhayyim/magatama/cronTick.bpmn",
      nsid: "com.etzhayyim.apps.magatama.cronTick",
      bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/magatama-cron-tick-v1",
      httpUrl: "https://magatama.etzhayyim.com/xrpc/com.etzhayyim.apps.magatama.cronTick",
      actorTag: "sys.bpmn.seed.magatama",
    },
    {
      vid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/graph-cron-tick-v1",
      ownerDid: "did:web:graph.etzhayyim.com",
      bpmnProcessId: "com.etzhayyim.graph.cronTick",
      rel: "00-contracts/bpmn/com/etzhayyim/graph/cronTick.bpmn",
      nsid: "com.etzhayyim.apps.graph.cronTick",
      bindingVid: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/graph-cron-tick-v1",
      httpUrl: "https://graph.etzhayyim.com/xrpc/com.etzhayyim.apps.graph.cronTick",
      actorTag: "sys.bpmn.seed.graph",
    },
  ] as const;

  for (const e of entries) {
    const xml = readFileSync(path.resolve(repoRoot, e.rel), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT
        ${e.vid}, ${e.ownerDid}, ${e.bpmnProcessId}, 1,
        ${xml}, CAST(${size} AS integer), ${e.rel}, 'active',
        ${now}, 1, ${e.ownerDid}, ${e.ownerDid}, ${e.actorTag}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${e.vid}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
      )
      SELECT
        ${e.bindingVid}, ${e.ownerDid}, ${e.nsid}, ${e.bpmnProcessId}, 1,
        30000, 'active', ${now}, 1, ${e.ownerDid}, ${e.ownerDid}, ${e.actorTag}
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${e.bindingVid}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  const bindingVids = [
    "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/magatama-cron-tick-v1",
    "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/graph-cron-tick-v1",
  ] as const;
  const processVids = [
    "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/magatama-cron-tick-v1",
    "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/graph-cron-tick-v1",
  ] as const;
  for (const v of bindingVids) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${v}`.execute(db);
  }
  for (const v of processVids) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${v}`.execute(db);
  }
}
