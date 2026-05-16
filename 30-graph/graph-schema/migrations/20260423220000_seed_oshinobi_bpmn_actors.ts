import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
  ownerDid: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  resultTimeoutMs: number | null;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const createdAt = "2026-04-23T22:00:00Z";
const ownerDid = "did:web:oshinobi.gftd.ai";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/oshinobi-subscribe-v1",
    bpmnProcessId: "oshinobi_subscribe",
    sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/subscribe.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/oshinobi-unsubscribe-v1",
    bpmnProcessId: "oshinobi_unsubscribe",
    sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/unsubscribe.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/oshinobi-publish-post-v1",
    bpmnProcessId: "oshinobi_publish_post",
    sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/publishPost.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/oshinobi-tip-creator-v1",
    bpmnProcessId: "oshinobi_tip_creator",
    sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/tipCreator.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/oshinobi-report-content-v1",
    bpmnProcessId: "oshinobi_report_content",
    sourcePath: "00-contracts/bpmn/ai/gftd/oshinobi/reportContent.bpmn",
    ownerDid,
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/oshinobi-subscribe-v1",
    nsid: "ai.gftd.apps.oshinobi.subscribe",
    bpmnProcessId: "oshinobi_subscribe",
    ownerDid,
    resultTimeoutMs: 15000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/oshinobi-cancelSubscription-v1",
    nsid: "ai.gftd.apps.oshinobi.cancelSubscription",
    bpmnProcessId: "oshinobi_unsubscribe",
    ownerDid,
    resultTimeoutMs: 5000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/oshinobi-publishPost-v1",
    nsid: "ai.gftd.apps.oshinobi.publishPost",
    bpmnProcessId: "oshinobi_publish_post",
    ownerDid,
    resultTimeoutMs: 10000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/oshinobi-tipCreator-v1",
    nsid: "ai.gftd.apps.oshinobi.tipCreator",
    bpmnProcessId: "oshinobi_tip_creator",
    ownerDid,
    resultTimeoutMs: 15000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/oshinobi-reportContent-v1",
    nsid: "ai.gftd.apps.oshinobi.reportContent",
    bpmnProcessId: "oshinobi_report_content",
    ownerDid,
    resultTimeoutMs: 15000,
  },
];

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id,
      owner_did,
      bpmn_process_id,
      version,
      xml,
      xml_byte_size,
      source_path,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.bpmnProcessId},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${seed.sourcePath},
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.oshinobi'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id,
      owner_did,
      nsid,
      bpmn_process_id,
      bpmn_version,
      result_timeout_ms,
      status,
      created_at,
      sensitivity_ord,
      org_id,
      user_id,
      actor_id
    )
    SELECT
      ${seed.vertexId},
      ${seed.ownerDid},
      ${seed.nsid},
      ${seed.bpmnProcessId},
      1,
      CAST(${seed.resultTimeoutMs} AS integer),
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      'sys.bpmn.seed.oshinobi'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of processSeeds) {
    await insertProcessDef(db, seed);
  }
  for (const seed of bindingSeeds) {
    await insertBinding(db, seed);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of bindingSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_lexicon_binding
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`
      DELETE FROM vertex_bpmn_process_def
      WHERE vertex_id = ${seed.vertexId}
    `.execute(db);
  }
}
