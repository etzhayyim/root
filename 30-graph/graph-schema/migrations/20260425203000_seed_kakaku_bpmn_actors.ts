import { readFileSync } from "node:fs";
import * as path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type ProcessSeed = {
  vertexId: string;
  bpmnProcessId: string;
  sourcePath: string;
};

type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-25T20:30:00Z";
const ownerDid = "did:web:kakaku.etzhayyim.com";
const actorTag = "sys.bpmn.seed.kakaku";
const writeTableAllowlist = [
  "vertex_kakaku_product",
  "vertex_kakaku_merchant",
  "vertex_kakaku_offer",
  "vertex_kakaku_price_history",
  "vertex_kakaku_match_candidate",
].join(",");

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-upsertOffer-v1",
    bpmnProcessId: "kakaku_upsert_offer",
    sourcePath: "00-contracts/bpmn/ai/gftd/kakaku/upsertOffer.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-ingestOfferFromUrl-v1",
    bpmnProcessId: "kakaku_ingest_offer_from_url",
    sourcePath: "00-contracts/bpmn/ai/gftd/kakaku/ingestOfferFromUrl.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/kakaku-compareOffers-v1",
    bpmnProcessId: "kakaku_compare_offers",
    sourcePath: "00-contracts/bpmn/ai/gftd/kakaku/compareOffers.bpmn",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-upsertOffer-v1",
    nsid: "app.etzhayyim.apps.kakaku.upsertOffer",
    bpmnProcessId: "kakaku_upsert_offer",
    resultTimeoutMs: 90_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-ingestOfferFromUrl-v1",
    nsid: "app.etzhayyim.apps.kakaku.ingestOfferFromUrl",
    bpmnProcessId: "kakaku_ingest_offer_from_url",
    resultTimeoutMs: 120_000,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/kakaku-compareOffers-v1",
    nsid: "app.etzhayyim.apps.kakaku.compareOffers",
    bpmnProcessId: "kakaku_compare_offers",
    resultTimeoutMs: 60_000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 1, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: BindingSeed): Promise<void> {
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, write_table_allowlist
    )
    SELECT
      ${seed.vertexId}, ${ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active', ${createdAt}, 1,
      ${ownerDid}, ${ownerDid}, ${actorTag}, ${writeTableAllowlist}
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
