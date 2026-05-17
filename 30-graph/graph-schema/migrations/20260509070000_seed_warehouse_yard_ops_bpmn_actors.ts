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
  actorTag: string;
};
type BindingSeed = {
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  ownerDid: string;
  actorTag: string;
};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const readContract = (p: string) => readFileSync(path.resolve(repoRoot, p), "utf8");
const createdAt = "2026-05-09T07:00:00Z";

const warehouseDid = "did:web:warehouse.etzhayyim.com";
const yardOpsDid = "did:web:yard-ops.etzhayyim.com";
const warehouseTag = "sys.bpmn.seed.warehouse";
const yardOpsTag = "sys.bpmn.seed.yard-ops";

const processSeeds: ProcessSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/warehouse-register-sku-v1",
    bpmnProcessId: "warehouse_register_sku",
    sourcePath: "00-contracts/bpmn/ai/gftd/warehouse/registerSku.bpmn",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/warehouse-putaway-v1",
    bpmnProcessId: "warehouse_putaway",
    sourcePath: "00-contracts/bpmn/ai/gftd/warehouse/putaway.bpmn",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/warehouse-pick-v1",
    bpmnProcessId: "warehouse_pick",
    sourcePath: "00-contracts/bpmn/ai/gftd/warehouse/pick.bpmn",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/warehouse-get-inventory-v1",
    bpmnProcessId: "warehouse_get_inventory",
    sourcePath: "00-contracts/bpmn/ai/gftd/warehouse/getInventory.bpmn",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yard-ops-check-in-trailer-v1",
    bpmnProcessId: "yard_ops_check_in_trailer",
    sourcePath: "00-contracts/bpmn/ai/gftd/yard-ops/checkInTrailer.bpmn",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yard-ops-assign-door-v1",
    bpmnProcessId: "yard_ops_assign_door",
    sourcePath: "00-contracts/bpmn/ai/gftd/yard-ops/assignDoor.bpmn",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yard-ops-complete-dock-job-v1",
    bpmnProcessId: "yard_ops_complete_dock_job",
    sourcePath: "00-contracts/bpmn/ai/gftd/yard-ops/completeDockJob.bpmn",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/yard-ops-get-dock-schedule-v1",
    bpmnProcessId: "yard_ops_get_dock_schedule",
    sourcePath: "00-contracts/bpmn/ai/gftd/yard-ops/getDockSchedule.bpmn",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
];

const bindingSeeds: BindingSeed[] = [
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/warehouse-registerSku-v1",
    nsid: "ai.gftd.apps.warehouse.registerSku",
    bpmnProcessId: "warehouse_register_sku",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/warehouse-putaway-v1",
    nsid: "ai.gftd.apps.warehouse.putaway",
    bpmnProcessId: "warehouse_putaway",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/warehouse-pick-v1",
    nsid: "ai.gftd.apps.warehouse.pick",
    bpmnProcessId: "warehouse_pick",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/warehouse-getInventory-v1",
    nsid: "ai.gftd.apps.warehouse.getInventory",
    bpmnProcessId: "warehouse_get_inventory",
    ownerDid: warehouseDid,
    actorTag: warehouseTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yardOps-checkInTrailer-v1",
    nsid: "ai.gftd.apps.yardOps.checkInTrailer",
    bpmnProcessId: "yard_ops_check_in_trailer",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yardOps-assignDoor-v1",
    nsid: "ai.gftd.apps.yardOps.assignDoor",
    bpmnProcessId: "yard_ops_assign_door",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yardOps-completeDockJob-v1",
    nsid: "ai.gftd.apps.yardOps.completeDockJob",
    bpmnProcessId: "yard_ops_complete_dock_job",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
  {
    vertexId: "at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/yardOps-getDockSchedule-v1",
    nsid: "ai.gftd.apps.yardOps.getDockSchedule",
    bpmnProcessId: "yard_ops_get_dock_schedule",
    ownerDid: yardOpsDid,
    actorTag: yardOpsTag,
  },
];

async function createRuntimeTables(db: Kysely<unknown>): Promise<void> {
  for (const table of [
    "vertex_warehouse_sku",
    "vertex_warehouse_putaway",
    "vertex_warehouse_pick",
    "vertex_yard_ops_trailer",
    "vertex_yard_ops_dock_job",
    "vertex_yard_ops_dock_completion",
  ]) {
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
  for (const table of [
    "edge_warehouse_sku_putaway",
    "edge_warehouse_sku_pick",
    "edge_yard_ops_trailer_dock_job",
    "edge_yard_ops_dock_job_loading_mission",
    "edge_yard_ops_dock_job_completion",
  ]) {
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

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {
  const xml = readContract(seed.sourcePath);
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${seed.vertexId}, ${seed.ownerDid}, ${seed.bpmnProcessId}, 1,
      ${xml}, CAST(${Buffer.byteLength(xml, "utf8")} AS integer), ${seed.sourcePath}, 'active',
      ${createdAt}, 2, ${seed.ownerDid}, ${seed.ownerDid}, ${seed.actorTag}
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
      CAST(30000 AS integer), 'active',
      ${createdAt}, 2, ${seed.ownerDid}, ${seed.ownerDid}, ${seed.actorTag}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${seed.vertexId}
    )
  `.execute(db);
}

export async function up(db: Kysely<unknown>): Promise<void> {
  await createRuntimeTables(db);
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
  await sql`DROP TABLE IF EXISTS edge_yard_ops_dock_job_completion`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yard_ops_dock_job_loading_mission`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_yard_ops_trailer_dock_job`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_warehouse_sku_pick`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_warehouse_sku_putaway`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yard_ops_dock_completion`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yard_ops_dock_job`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_yard_ops_trailer`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_warehouse_pick`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_warehouse_putaway`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_warehouse_sku`.execute(db);
}
