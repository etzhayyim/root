import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type ProcessSeed = {
  vertexId: string;
  ownerDid: string;
  bpmnProcessId: string;
  sourcePath: string;
  sensitivityOrd: number;
  actorTag: string;
};

type BindingSeed = {
  vertexId: string;
  ownerDid: string;
  nsid: string;
  bpmnProcessId: string;
  resultTimeoutMs: number;
  sensitivityOrd: number;
  actorTag: string;
  writeTableAllowlist: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "2026-04-27T04:00:00Z";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/fund-managerDiscovery-v1",
    ownerDid: "did:web:fund.etzhayyim.com",
    bpmnProcessId: "fund_manager_discovery",
    sourcePath: "00-contracts/bpmn/ai/gftd/fund/managerDiscovery.bpmn",
    sensitivityOrd: 2,
    actorTag: "sys.bpmn.seed.fund",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/ma-startDealWorkflow-v1",
    ownerDid: "did:web:ma.etzhayyim.com",
    bpmnProcessId: "ma_start_deal_workflow",
    sourcePath: "00-contracts/bpmn/ai/gftd/ma/startDealWorkflow.bpmn",
    sensitivityOrd: 3,
    actorTag: "sys.bpmn.seed.ma",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/fund-managerDiscovery-v1",
    ownerDid: "did:web:fund.etzhayyim.com",
    nsid: "app.etzhayyim.apps.fund.managerDiscovery",
    bpmnProcessId: "fund_manager_discovery",
    resultTimeoutMs: 600_000,
    sensitivityOrd: 2,
    actorTag: "sys.bpmn.seed.fund",
    writeTableAllowlist: [
      "vertex_fund",
      "vertex_fund_manager",
      "vertex_fund_investor",
      "vertex_fund_investee",
      "edge_fund_managed_by",
      "edge_fund_backed_by",
      "edge_fund_invests_in",
      "edge_fund_sponsored_by",
    ].join(","),
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/ma-startDealWorkflow-v1",
    ownerDid: "did:web:ma.etzhayyim.com",
    nsid: "app.etzhayyim.apps.ma.startDealWorkflow",
    bpmnProcessId: "ma_start_deal_workflow",
    resultTimeoutMs: 900_000,
    sensitivityOrd: 3,
    actorTag: "sys.bpmn.seed.ma",
    writeTableAllowlist: [
      "vertex_ma_deal",
      "vertex_ma_candidate",
      "vertex_ma_valuation",
      "vertex_ma_match",
      "edge_ma_deal_candidate",
      "edge_ma_deal_buyer",
    ].join(","),
  },
];

async function createMaGraphSpine(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ma_deal (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      deal_id              VARCHAR,
      side                 VARCHAR,
      client_name          VARCHAR,
      target_name          VARCHAR,
      sector               VARCHAR,
      jurisdiction         VARCHAR,
      expected_value_usd   DOUBLE PRECISION,
      status               VARCHAR,
      stage                VARCHAR,
      operator_did         VARCHAR,
      source_url           VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ma_candidate (
      vertex_id            VARCHAR PRIMARY KEY,
      _seq                 BIGINT,
      created_date         TIMESTAMP,
      sensitivity_ord      BIGINT,
      owner_did            VARCHAR,
      rkey                 VARCHAR,
      repo                 VARCHAR,
      did                  VARCHAR,
      candidate_id         VARCHAR,
      candidate_name       VARCHAR,
      candidate_kind       VARCHAR,
      sector               VARCHAR,
      jurisdiction         VARCHAR,
      legal_entity_did     VARCHAR,
      screening_score      DOUBLE PRECISION,
      source_url           VARCHAR,
      confidence           DOUBLE PRECISION,
      notes                VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ma_valuation (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT,
      created_date           TIMESTAMP,
      sensitivity_ord        BIGINT,
      owner_did              VARCHAR,
      rkey                   VARCHAR,
      repo                   VARCHAR,
      did                    VARCHAR,
      valuation_id           VARCHAR,
      deal_id                VARCHAR,
      method                 VARCHAR,
      low_usd                DOUBLE PRECISION,
      high_usd               DOUBLE PRECISION,
      midpoint_usd           DOUBLE PRECISION,
      currency               VARCHAR,
      as_of_date             VARCHAR,
      source_url             VARCHAR,
      confidence             DOUBLE PRECISION,
      notes                  VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_ma_match (
      vertex_id              VARCHAR PRIMARY KEY,
      _seq                   BIGINT,
      created_date           TIMESTAMP,
      sensitivity_ord        BIGINT,
      owner_did              VARCHAR,
      rkey                   VARCHAR,
      repo                   VARCHAR,
      did                    VARCHAR,
      match_id               VARCHAR,
      deal_id                VARCHAR,
      buyer_candidate_id     VARCHAR,
      rank                   INTEGER,
      fit_score              DOUBLE PRECISION,
      status                 VARCHAR,
      source_url             VARCHAR,
      confidence             DOUBLE PRECISION,
      notes                  VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_ma_deal_candidate (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      role                 VARCHAR,
      score                DOUBLE PRECISION,
      created_at           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_ma_deal_buyer (
      edge_id              VARCHAR PRIMARY KEY,
      src_vid              VARCHAR NOT NULL,
      dst_vid              VARCHAR NOT NULL,
      relationship         VARCHAR,
      rank                 INTEGER,
      fit_score            DOUBLE PRECISION,
      status               VARCHAR,
      created_at           VARCHAR
    )
  `.execute(db);
}

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
      ${seed.vertexId}, ${seed.ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${xmlByteSize} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, CAST(${seed.sensitivityOrd} AS integer), ${seed.ownerDid},
      ${seed.ownerDid}, ${seed.actorTag}
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
      ${seed.vertexId}, ${seed.ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(${seed.resultTimeoutMs} AS integer), 'active', ${createdAt},
      CAST(${seed.sensitivityOrd} AS integer), ${seed.ownerDid}, ${seed.ownerDid},
      ${seed.actorTag}, ${seed.writeTableAllowlist}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createMaGraphSpine(db);
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
  await sql`DROP TABLE IF EXISTS edge_ma_deal_buyer`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_ma_deal_candidate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ma_match`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ma_valuation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ma_candidate`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_ma_deal`.execute(db);
}
