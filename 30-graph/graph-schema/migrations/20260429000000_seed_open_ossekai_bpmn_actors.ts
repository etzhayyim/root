import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-29T00:00:00Z";
const actorTag = "sys.bpmn.seed.open-ossekai";
const ownerDid = "did:web:open-ossekai.etzhayyim.com:ops";

type ProcessSeed = { vertexId: string; bpmnProcessId: string; sourcePath: string };

// Timer-start BPMNs (no lexicon binding needed — fired by Zeebe timer)
const timerProcesses: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-observeActor-v1",
    bpmnProcessId: "open_ossekai_observe_actor",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/observeActor.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-matchArbitrage-v1",
    bpmnProcessId: "open_ossekai_match_arbitrage",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/matchArbitrage.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-trackKyuDanProgress-v1",
    bpmnProcessId: "open_ossekai_track_kyu_dan_progress",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/trackKyuDanProgress.bpmn",
  },
];

// XRPC-triggered BPMNs (need lexicon binding)
type XrpcSeed = ProcessSeed & { nsid: string };

const xrpcProcesses: XrpcSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-generateIntelBrief-v1",
    bpmnProcessId: "open_ossekai_generate_intel_brief",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/generateIntelBrief.bpmn",
    nsid: "com.etzhayyim.apps.openOssekai.generateIntelBrief",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-proposeArbitrageBrief-v1",
    bpmnProcessId: "open_ossekai_propose_arbitrage_brief",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/proposeArbitrageBrief.bpmn",
    nsid: "com.etzhayyim.apps.openOssekai.proposeArbitrageBrief",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-requestOssekaiConsent-v1",
    bpmnProcessId: "open_ossekai_request_ossekai_consent",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/requestOssekaiConsent.bpmn",
    nsid: "com.etzhayyim.apps.openOssekai.requestOssekaiConsent",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-scoreJocho-v1",
    bpmnProcessId: "open_ossekai_score_jocho",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/scoreJocho.bpmn",
    nsid: "com.etzhayyim.apps.openOssekai.scoreJocho",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/open-ossekai-generateWellBecomingPlan-v1",
    bpmnProcessId: "open_ossekai_generate_wellbecoming_plan",
    sourcePath: "00-contracts/bpmn/com/etzhayyim/open-ossekai/generateWellBecomingPlan.bpmn",
    nsid: "com.etzhayyim.apps.openOssekai.generateWellBecomingPlan",
  },
];

async function insertProcessDef(db: Kysely<unknown>, s: ProcessSeed): Promise<void> {
  const xmlContent = readContract(s.sourcePath);
  const size = Buffer.byteLength(xmlContent, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${s.vertexId}, ${ownerDid}, ${s.bpmnProcessId}, 1, ${xmlContent}, CAST(${size} AS integer), ${s.sourcePath}, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId})
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, s: XrpcSeed): Promise<void> {
  const bindingVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${s.nsid.replace(/\./g, "-")}-v1`;
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id)
    SELECT ${bindingVertexId}, ${ownerDid}, ${s.nsid}, ${s.bpmnProcessId}, 1, CAST(60000 AS integer), NULL, 'active', ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId})
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of timerProcesses) await insertProcessDef(db, s);
  for (const s of xrpcProcesses) {
    await insertProcessDef(db, s);
    await insertBinding(db, s);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of xrpcProcesses) {
    const bindingVertexId = `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${s.nsid.replace(/\./g, "-")}-v1`;
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
  for (const s of timerProcesses) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${s.vertexId}`.execute(db);
  }
}
