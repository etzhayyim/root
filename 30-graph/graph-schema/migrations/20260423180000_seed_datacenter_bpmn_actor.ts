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

const createdAt = "2026-04-23T18:00:00Z";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/datacenter-operate-facility-v1",
    bpmnProcessId: "datacenter_operate_facility",
    sourcePath: "00-contracts/bpmn/ai/gftd/datacenter/operateFacility.bpmn",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/datacenter-access-review-v1",
    bpmnProcessId: "datacenter_access_review",
    sourcePath: "00-contracts/bpmn/ai/gftd/datacenter/accessReview.bpmn",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/datacenter-reserve-capacity-v1",
    bpmnProcessId: "datacenter_reserve_capacity",
    sourcePath: "00-contracts/bpmn/ai/gftd/datacenter/reserveCapacity.bpmn",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/datacenter-purge-access-pii-v1",
    bpmnProcessId: "datacenter_purge_access_pii",
    sourcePath: "00-contracts/bpmn/ai/gftd/datacenter/purgeAccessPii.bpmn",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/datacenter-startOperation-v1",
    nsid: "ai.gftd.apps.datacenter.startOperation",
    bpmnProcessId: "datacenter_operate_facility",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
    resultTimeoutMs: 0,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/datacenter-requestAccess-v1",
    nsid: "ai.gftd.apps.datacenter.requestAccess",
    bpmnProcessId: "datacenter_access_review",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
    resultTimeoutMs: 0,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/datacenter-reserveCapacity-v1",
    nsid: "ai.gftd.apps.datacenter.reserveCapacity",
    bpmnProcessId: "datacenter_reserve_capacity",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
    resultTimeoutMs: 0,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/datacenter-purgeAccessPii-v1",
    nsid: "ai.gftd.apps.datacenter.purgeAccessPii",
    bpmnProcessId: "datacenter_purge_access_pii",
    ownerDid: "did:web:infra.gftd.ai:datacenter",
    resultTimeoutMs: 120_000,
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
      'sys.bpmn.seed.datacenter'
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
      'sys.bpmn.seed.datacenter'
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
