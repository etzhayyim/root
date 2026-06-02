import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { op: string; fn: string; processId: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:vin.etzhayyim.com";
const createdAt = "2026-04-30T22:01:00+09:00";
const actorId = "sys.bpmn.seed.vin";

const seeds: Seed[] = [
  { op: "collectRecall", fn: "collect_recall", processId: "vin_collectRecall", writeTableAllowlist: "" },
  { op: "debugPds", fn: "debug_pds", processId: "vin_debugPds", writeTableAllowlist: "" },
  { op: "decodeVin", fn: "decode_vin", processId: "vin_decodeVin", writeTableAllowlist: "vertex_vin_vehicle" },
  { op: "exampleMethod", fn: "example_method", processId: "vin_exampleMethod", writeTableAllowlist: "" },
  { op: "getManufacturer", fn: "get_manufacturer", processId: "vin_getManufacturer", writeTableAllowlist: "" },
  { op: "getPlant", fn: "get_plant", processId: "vin_getPlant", writeTableAllowlist: "" },
  { op: "getShipmentFlow", fn: "get_shipment_flow", processId: "vin_getShipmentFlow", writeTableAllowlist: "" },
  { op: "getVehicle", fn: "get_vehicle", processId: "vin_getVehicle", writeTableAllowlist: "" },
  { op: "getVehicleHistory", fn: "get_vehicle_history", processId: "vin_getVehicleHistory", writeTableAllowlist: "" },
  { op: "ingestShipment", fn: "ingest_shipment", processId: "vin_ingestShipment", writeTableAllowlist: "vertex_vin_shipment_volume" },
  { op: "listCohort", fn: "list_cohort", processId: "vin_listCohort", writeTableAllowlist: "" },
  { op: "listJurisdictions", fn: "list_jurisdictions", processId: "vin_listJurisdictions", writeTableAllowlist: "" },
  { op: "listManufacturers", fn: "list_manufacturers", processId: "vin_listManufacturers", writeTableAllowlist: "" },
  { op: "listPlants", fn: "list_plants", processId: "vin_listPlants", writeTableAllowlist: "" },
  { op: "listShipmentCohorts", fn: "list_shipment_cohorts", processId: "vin_listShipmentCohorts", writeTableAllowlist: "" },
  { op: "listVehicleTypes", fn: "list_vehicle_types", processId: "vin_listVehicleTypes", writeTableAllowlist: "" },
  { op: "listVehicles", fn: "list_vehicles", processId: "vin_listVehicles", writeTableAllowlist: "" },
  { op: "lookupPlate", fn: "lookup_plate", processId: "vin_lookupPlate", writeTableAllowlist: "" },
  { op: "registerCohort", fn: "register_cohort", processId: "vin_registerCohort", writeTableAllowlist: "vertex_vin_cohort_registration" },
  { op: "registerPlate", fn: "register_plate", processId: "vin_registerPlate", writeTableAllowlist: "vertex_vin_license_plate" },
  { op: "searchVehicles", fn: "search_vehicles", processId: "vin_searchVehicles", writeTableAllowlist: "" },
  { op: "seedJurisdictions", fn: "seed_jurisdictions", processId: "vin_seedJurisdictions", writeTableAllowlist: "vertex_vin_jurisdiction_registry" },
  { op: "seedManufacturers", fn: "seed_manufacturers", processId: "vin_seedManufacturers", writeTableAllowlist: "vertex_vin_manufacturer" },
  { op: "seedProductionLines", fn: "seed_production_lines", processId: "vin_seedProductionLines", writeTableAllowlist: "vertex_vin_production_line" },
  { op: "seedProductionPlants", fn: "seed_production_plants", processId: "vin_seedProductionPlants", writeTableAllowlist: "vertex_vin_production_plant" },
  { op: "seedVehicleTypes", fn: "seed_vehicle_types", processId: "vin_seedVehicleTypes", writeTableAllowlist: "vertex_vin_vehicle_type" },
  { op: "seedWmiCodes", fn: "seed_wmi_codes", processId: "vin_seedWmiCodes", writeTableAllowlist: "vertex_vin_wmi_code" },
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/com/etzhayyim/vin/${s.op}.bpmn`;
const slug = (s: Seed) => s.op.replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/vin-${slug(s)}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/vin-${slug(s)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`
      INSERT INTO vertex_bpmn_process_def (
        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,
        actor_did, org_did
      )
      SELECT
        ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1,
        ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active',
        ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId},
        ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}
      )
    `.execute(db);

    await sql`
      INSERT INTO vertex_bpmn_lexicon_binding (
        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
        result_timeout_ms, write_table_allowlist, status, created_at,
        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did
      )
      SELECT
        ${bindingVertexId(s)}, ${ownerDid}, ${`com.etzhayyim.apps.vin.${s.op}`}, ${s.processId}, 1,
        30000, ${s.writeTableAllowlist}, 'active', ${createdAt},
        100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
