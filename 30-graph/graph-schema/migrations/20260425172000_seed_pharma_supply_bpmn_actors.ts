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
const createdAt = "2026-04-25T17:20:00Z";
const ownerDid = "did:web:open-pharma-supply.gftd.ai:ops";
const actorTag = "sys.bpmn.seed.pharma-supply";

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-pharma-supply-register-product-v1",
    bpmnProcessId: "open_pharma_supply_register_product",
    sourcePath: "00-contracts/bpmn/ai/gftd/open-pharma-supply/registerProduct.bpmn",
    ownerDid,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-shortage-v1",
    bpmnProcessId: "open_pharma_supply_flag_shortage",
    sourcePath: "00-contracts/bpmn/ai/gftd/open-pharma-supply/flagShortage.bpmn",
    ownerDid,
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-pharma-supply-registerProduct-v1",
    nsid: "ai.gftd.apps.pharmaSupply.registerProduct",
    bpmnProcessId: "open_pharma_supply_register_product",
    ownerDid,
    resultTimeoutMs: 15000,
  },
  {
    vertexId: "at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagShortage-v1",
    nsid: "ai.gftd.apps.pharmaSupply.flagShortage",
    bpmnProcessId: "open_pharma_supply_flag_shortage",
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
