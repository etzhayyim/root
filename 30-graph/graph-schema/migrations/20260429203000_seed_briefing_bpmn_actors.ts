import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { slug: string; processId: string; nsid: string; sourcePath: string; timeoutMs: number; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:briefing.etzhayyim.com";
const createdAt = "2026-04-29T20:30:00+09:00";
const actorId = "sys.bpmn.seed.briefing";
const project = "briefing";

const seeds: Seed[] = [
  { slug: "create-agenda", processId: "briefing_create_agenda", nsid: "com.etzhayyim.apps.briefing.createAgenda", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/createAgenda.bpmn", timeoutMs: 60000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingAgenda" },
  { slug: "save-transcript", processId: "briefing_save_transcript", nsid: "com.etzhayyim.apps.briefing.saveTranscript", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/saveTranscript.bpmn", timeoutMs: 120000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingTranscript" },
  { slug: "extract-action-items", processId: "briefing_extract_action_items", nsid: "com.etzhayyim.apps.briefing.extractActionItems", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/extractActionItems.bpmn", timeoutMs: 120000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingActionItem" },
  { slug: "generate-summary", processId: "briefing_generate_summary", nsid: "com.etzhayyim.apps.briefing.generateSummary", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/generateSummary.bpmn", timeoutMs: 120000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingSummary" },
  { slug: "record-speaker-turn", processId: "briefing_record_speaker_turn", nsid: "com.etzhayyim.apps.briefing.recordSpeakerTurn", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/recordSpeakerTurn.bpmn", timeoutMs: 30000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingSpeakerTurn" },
  { slug: "record-decision", processId: "briefing_record_decision", nsid: "com.etzhayyim.apps.briefing.recordDecision", sourcePath: "00-contracts/bpmn/com/etzhayyim/briefing/recordDecision.bpmn", timeoutMs: 30000, writeTableAllowlist: "pds:com.etzhayyim.apps.briefing.briefingDecision" },
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

    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET write_table_allowlist = ${s.writeTableAllowlist}
      WHERE bpmn_process_id = ${s.processId}
        AND nsid = ${s.nsid}
        AND (write_table_allowlist IS NULL OR write_table_allowlist <> ${s.writeTableAllowlist})
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
