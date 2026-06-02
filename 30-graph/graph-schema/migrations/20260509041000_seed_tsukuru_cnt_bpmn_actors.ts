import { readFileSync } from "node:fs";
import path from "node:path";
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
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-09T04:00:00Z";
const ownerDid = "did:web:tsukuru.etzhayyim.com:industry:isic:c";
const actorTag = "sys.bpmn.seed.tsukuru-cnt";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-cnt-fiber-manufacturing-flow-v1",
    bpmnProcessId: "tsukuru_cnt_fiber_manufacturing_flow",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/cnt-fiber-manufacturing-flow.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-cnt-automation-plan-v1",
    bpmnProcessId: "tsukuru_cnt_automation_plan",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/cnt-automation-plan.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-prepare-cnt-order-package-v1",
    bpmnProcessId: "tsukuru_prepare_cnt_order_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/prepare-cnt-order-package.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-get-cnt-automation-coverage-v1",
    bpmnProcessId: "tsukuru_get_cnt_automation_coverage",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/get-cnt-automation-coverage.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-prepare-cnt-run-package-v1",
    bpmnProcessId: "tsukuru_prepare_cnt_run_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/prepare-cnt-run-package.bpmn",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/tsukuru-validate-cnt-run-package-v1",
    bpmnProcessId: "tsukuru_validate_cnt_run_package",
    sourcePath: "00-contracts/bpmn/ai/gftd/tsukuru/validate-cnt-run-package.bpmn",
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-designManufacturingFlow-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.designManufacturingFlow",
    bpmnProcessId: "tsukuru_cnt_fiber_manufacturing_flow",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-planAutomation-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.planAutomation",
    bpmnProcessId: "tsukuru_cnt_automation_plan",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-prepareOrderPackage-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.prepareOrderPackage",
    bpmnProcessId: "tsukuru_prepare_cnt_order_package",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-getAutomationCoverage-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.getAutomationCoverage",
    bpmnProcessId: "tsukuru_get_cnt_automation_coverage",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-prepareRunPackage-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.prepareRunPackage",
    bpmnProcessId: "tsukuru_prepare_cnt_run_package",
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/tsukuru-cnt-validateRunPackage-v1",
    nsid: "com.etzhayyim.apps.tsukuru.cnt.validateRunPackage",
    bpmnProcessId: "tsukuru_validate_cnt_run_package",
  },
];

async function createTsukuruRuntimeTables(db: Kysely<unknown>): Promise<void> {
  for (const table of ["vertex_tsukuru_cnt_manufacturing_flow", "vertex_tsukuru_cnt_automation_plan", "vertex_tsukuru_cnt_process_catalog", "vertex_tsukuru_cnt_run_package", "vertex_tsukuru_cnt_run_validation"]) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
        vertex_id VARCHAR PRIMARY KEY,
        vertex_key VARCHAR,
        label VARCHAR,
        status VARCHAR,
        value_json TEXT,
        created_at VARCHAR,
        updated_at VARCHAR,
        org_id VARCHAR,
        user_id VARCHAR,
        actor_id VARCHAR,
        actor_did VARCHAR,
        org_did VARCHAR,
        owner_did VARCHAR,
        sensitivity_ord BIGINT
      )
    `.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_key`)} ON ${sql.table(table)} (vertex_key)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_status`)} ON ${sql.table(table)} (status)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_owner`)} ON ${sql.table(table)} (owner_did)`.execute(db);
  }
  for (const table of ["edge_tsukuru_order_cnt_flow", "edge_tsukuru_order_cnt_automation", "edge_tsukuru_order_cnt_run_package", "edge_tsukuru_order_cnt_run_validation"]) {
    await sql`
      CREATE TABLE IF NOT EXISTS ${sql.table(table)} (
        edge_id VARCHAR PRIMARY KEY,
        edge_key VARCHAR,
        src_vid VARCHAR,
        dst_vid VARCHAR,
        relation VARCHAR,
        value_json TEXT,
        created_at VARCHAR,
        updated_at VARCHAR,
        owner_did VARCHAR,
        sensitivity_ord BIGINT
      )
    `.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_src`)} ON ${sql.table(table)} (src_vid)`.execute(db);
    await sql`CREATE INDEX IF NOT EXISTS ${sql.ref(`idx_${table}_dst`)} ON ${sql.table(table)} (dst_vid)`.execute(db);
  }
}

async function seedCntProcessCatalog(db: Kysely<unknown>): Promise<void> {
  const sourcePath = "00-contracts/catalogs/ai/gftd/tsukuru/cnt/process-catalog.v1.json";
  const catalogJson = readContract(sourcePath);
  const vid = 'at://did:web:tsukuru.etzhayyim.com/com.etzhayyim.apps.tsukuru.cntProcessCatalog/tsukuru-cnt-process-catalog-v1';
  // RW does not support ON CONFLICT; same-PK INSERT overwrites by spec.
  await sql`
    INSERT INTO vertex_tsukuru_cnt_process_catalog (
      vertex_id, vertex_key, label, status, value_json, created_at, updated_at,
      org_id, user_id, actor_id, actor_did, org_did, owner_did, sensitivity_ord
    )
    VALUES (
      ${vid},
      'tsukuru-cnt-process-catalog-v1',
      'Tsukuru CNT process catalog v1',
      'active',
      ${catalogJson},
      ${createdAt},
      ${createdAt},
      ${ownerDid},
      ${ownerDid},
      ${actorTag},
      'did:web:tsukuru.etzhayyim.com',
      ${ownerDid},
      ${ownerDid},
      2
    )
  `.execute(db);
}

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${Buffer.byteLength(xml, "utf8")} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 2, ${ownerDid}, ${ownerDid}, ${actorTag}
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
      ${seed.vertexId}, ${ownerDid}, ${seed.nsid}, ${seed.bpmnProcessId}, 1,
      CAST(30000 AS integer), 'active',
      ${createdAt}, 2, ${ownerDid}, ${ownerDid}, ${actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createTsukuruRuntimeTables(db);
  await seedCntProcessCatalog(db);
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
  await sql`DROP TABLE IF EXISTS edge_tsukuru_order_cnt_automation`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_tsukuru_order_cnt_flow`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_tsukuru_order_cnt_run_package`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_tsukuru_order_cnt_run_validation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_tsukuru_cnt_run_validation`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_tsukuru_cnt_run_package`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_tsukuru_cnt_process_catalog`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_tsukuru_cnt_automation_plan`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_tsukuru_cnt_manufacturing_flow`.execute(db);
}
