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
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-25T17:00:00Z";
const actorTag = "sys.bpmn.seed.open-org";

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-org-takeda-gmp-batch-release-v1",
    bpmnProcessId: "open_org_takeda_gmp_batch_release",
    sourcePath: "00-contracts/bpmn/ai/gftd/open-org-takeda/gmpBatchRelease.bpmn",
    ownerDid: "did:web:open-org-takeda.etzhayyim.com",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-org-toyota-line-stop-escalation-v1",
    bpmnProcessId: "open_org_toyota_line_stop_escalation",
    sourcePath: "00-contracts/bpmn/ai/gftd/open-org-toyota/lineStopEscalation.bpmn",
    ownerDid: "did:web:open-org-toyota.etzhayyim.com",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-org-yamato-cold-chain-delivery-exception-v1",
    bpmnProcessId: "open_org_yamato_cold_chain_delivery_exception",
    sourcePath: "00-contracts/bpmn/ai/gftd/open-org-yamato/coldChainDeliveryException.bpmn",
    ownerDid: "did:web:open-org-yamato.etzhayyim.com",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-org-takeda-gmpBatchRelease-v1",
    nsid: "app.etzhayyim.apps.orgTakeda.gmpBatchRelease",
    bpmnProcessId: "open_org_takeda_gmp_batch_release",
    ownerDid: "did:web:open-org-takeda.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-org-toyota-lineStopEscalation-v1",
    nsid: "app.etzhayyim.apps.orgToyota.lineStopEscalation",
    bpmnProcessId: "open_org_toyota_line_stop_escalation",
    ownerDid: "did:web:open-org-toyota.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-org-yamato-coldChainDeliveryException-v1",
    nsid: "app.etzhayyim.apps.orgYamato.coldChainDeliveryException",
    bpmnProcessId: "open_org_yamato_cold_chain_delivery_exception",
    ownerDid: "did:web:open-org-yamato.etzhayyim.com",
    resultTimeoutMs: 30000,
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
      ${actorTag}
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
      ${actorTag}
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
