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
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-04-27T01:15:00Z";
const ownerDid = "did:web:tsukuru.gftd.ai:industry:isic:c";
const actorTag = "sys.bpmn.seed.tsukuru-euv";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tsukuru-euv-lithography-manufacturing-flow-v1",
    bpmnProcessId: "tsukuru_euv_lithography_manufacturing_flow",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/euv-lithography-manufacturing-flow.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tsukuru-normalize-supplier-exchange-package-v1",
    bpmnProcessId: "tsukuru_normalize_supplier_exchange_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/normalize-supplier-exchange-package.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tsukuru-prepare-euv-order-package-v1",
    bpmnProcessId: "tsukuru_prepare_euv_order_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/prepare-euv-order-package.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tsukuru-get-euv-implementation-coverage-v1",
    bpmnProcessId: "tsukuru_get_euv_implementation_coverage",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/get-euv-implementation-coverage.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/tsukuru-validate-supplier-exchange-package-v1",
    bpmnProcessId: "tsukuru_validate_supplier_exchange_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/validate-supplier-exchange-package.bpmn",
    ownerDid,
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tsukuru-euv-designManufacturingFlow-v1",
    nsid: "ai.gftd.apps.tsukuru.euv.designManufacturingFlow",
    bpmnProcessId: "tsukuru_euv_lithography_manufacturing_flow",
    ownerDid,
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tsukuru-supplierExchange-normalizePackage-v1",
    nsid: "ai.gftd.apps.tsukuru.supplierExchange.normalizePackage",
    bpmnProcessId: "tsukuru_normalize_supplier_exchange_package",
    ownerDid,
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tsukuru-euv-prepareOrderPackage-v1",
    nsid: "ai.gftd.apps.tsukuru.euv.prepareOrderPackage",
    bpmnProcessId: "tsukuru_prepare_euv_order_package",
    ownerDid,
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tsukuru-euv-getImplementationCoverage-v1",
    nsid: "ai.gftd.apps.tsukuru.euv.getImplementationCoverage",
    bpmnProcessId: "tsukuru_get_euv_implementation_coverage",
    ownerDid,
    resultTimeoutMs: 30000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/tsukuru-supplierExchange-validatePackage-v1",
    nsid: "ai.gftd.apps.tsukuru.supplierExchange.validatePackage",
    bpmnProcessId: "tsukuru_validate_supplier_exchange_package",
    ownerDid,
    resultTimeoutMs: 30000,
  },
];

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${seed.ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 2, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${seed.ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active',
      ${createdAt}, 2, ${seed.ownerDid}, ${seed.ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const seed of processSeeds) await insertProcessDef(db, seed);
  for (const seed of bindingSeeds) await insertBinding(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of bindingSeeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
  for (const seed of processSeeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}`.execute(db);
  }
}
