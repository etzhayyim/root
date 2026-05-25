import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = {
  project: string;
  proc: string;
  bpmnProcessId: string;
  nsid: string;
  ownerDid: string;
  resultTimeoutMs: number;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T07:40:00Z";
const actorTag = "sys.bpmn.seed.pharma-policy";

const seeds: Seed[] = [
  {
    project: "open-drug-price-negotiation",
    proc: "recordRound",
    bpmnProcessId: "open_drug_price_negotiation_record_round",
    nsid: "app.etzhayyim.apps.drugPriceNegotiation.recordRound",
    ownerDid: "did:web:open-drug-price-negotiation.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-drug-price-negotiation",
    proc: "flagAccessGap",
    bpmnProcessId: "open_drug_price_negotiation_flag_access_gap",
    nsid: "app.etzhayyim.apps.drugPriceNegotiation.flagAccessGap",
    ownerDid: "did:web:open-drug-price-negotiation.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-jp-mhlw",
    proc: "recordAction",
    bpmnProcessId: "open_jp_mhlw_record_action",
    nsid: "app.etzhayyim.apps.jpMhlw.recordAction",
    ownerDid: "did:web:open-jp-mhlw.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-jp-mhlw",
    proc: "flagPolicyConcern",
    bpmnProcessId: "open_jp_mhlw_flag_policy_concern",
    nsid: "app.etzhayyim.apps.jpMhlw.flagPolicyConcern",
    ownerDid: "did:web:open-jp-mhlw.etzhayyim.com",
    resultTimeoutMs: 30000,
  },
  {
    project: "open-jp-mhlw",
    proc: "regulateNarcotics",
    bpmnProcessId: "open_jp_mhlw_regulate_narcotics",
    nsid: "app.etzhayyim.apps.jpMhlw.regulateNarcotics",
    ownerDid: "did:web:open-jp-mhlw.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
  {
    project: "open-jp-mhlw",
    proc: "administerInfluenzaVaccine",
    bpmnProcessId: "open_jp_mhlw_administer_influenza_vaccine",
    nsid: "app.etzhayyim.apps.jpMhlw.administerInfluenzaVaccine",
    ownerDid: "did:web:open-jp-mhlw.etzhayyim.com",
    resultTimeoutMs: 15000,
  },
];

function readContract(relPath: string): string {
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}

function sourcePath(seed: Seed): string {
  return `00-contracts/bpmn/ai/gftd/${seed.project}/${seed.proc}.bpmn`;
}

function processVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/${seed.project}-${seed.proc}-v1`;
}

function bindingVertexId(seed: Seed): string {
  return `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/${seed.project}-${seed.proc}-v1`;
}

async function createPharmaPolicyTables(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_drug_price_negotiation (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      round_id           varchar,
      regime_kind        varchar,
      therapeutic_area   varchar,
      pharma_company_lei varchar,
      published_at       varchar,
      flag_id            varchar,
      round_vid          varchar,
      gap_kind           varchar,
      reported_at        varchar,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_open_jp_mhlw (
      vertex_id          varchar PRIMARY KEY,
      _seq               bigint,
      created_date       date,
      sensitivity_ord    int,
      owner_did          varchar,
      action_id          varchar,
      bureau             varchar,
      action_kind        varchar,
      related_actor_vid  varchar,
      issued_at          varchar,
      flag_id            varchar,
      action_vid         varchar,
      concern_kind       varchar,
      reported_at        varchar,
      status             varchar,
      created_at         varchar,
      org_id             varchar,
      user_id            varchar,
      actor_id           varchar
    )
  `.execute(db);
}

async function insertProcessDef(db: Kysely<unknown>, seed: Seed): Promise<void> {
  const relPath = sourcePath(seed);
  const xml = readContract(relPath);
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
      ${processVertexId(seed)},
      ${seed.ownerDid},
      ${seed.bpmnProcessId},
      1,
      ${xml},
      CAST(${xmlByteSize} AS integer),
      ${relPath},
      'active',
      ${createdAt},
      1,
      ${seed.ownerDid},
      ${seed.ownerDid},
      ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}
    )
  `.execute(db);
}

async function insertBinding(db: Kysely<unknown>, seed: Seed): Promise<void> {
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
      ${bindingVertexId(seed)},
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
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createPharmaPolicyTables(db);
  for (const seed of seeds) await insertProcessDef(db, seed);
  for (const seed of seeds) await insertBinding(db, seed);
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(seed)}`.execute(db);
  }
  for (const seed of seeds) {
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(seed)}`.execute(db);
  }
  await sql`DROP TABLE IF EXISTS vertex_open_jp_mhlw`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_open_drug_price_negotiation`.execute(db);
}
