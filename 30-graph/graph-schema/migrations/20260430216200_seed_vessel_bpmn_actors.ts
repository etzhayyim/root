import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { file: string; processId: string; nsid: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:v3ss3l01.etzhayyim.com";
const createdAt = "2026-04-30T22:02:00+09:00";
const actorId = "sys.bpmn.seed.vessel";

const seeds: Seed[] = [
  {
    "file": "registry/registerShip",
    "processId": "vessel_registry_registerShip",
    "nsid": "app.etzhayyim.apps.vessel.registry.registerShip",
    "writeTableAllowlist": "vertex_vessel_ship"
  },
  {
    "file": "registry/updateShip",
    "processId": "vessel_registry_updateShip",
    "nsid": "app.etzhayyim.apps.vessel.registry.updateShip",
    "writeTableAllowlist": "vertex_vessel_ship"
  },
  {
    "file": "registry/registerOwner",
    "processId": "vessel_registry_registerOwner",
    "nsid": "app.etzhayyim.apps.vessel.registry.registerOwner",
    "writeTableAllowlist": "vertex_vessel_shipowner"
  },
  {
    "file": "registry/transferOwnership",
    "processId": "vessel_registry_transferOwnership",
    "nsid": "app.etzhayyim.apps.vessel.registry.transferOwnership",
    "writeTableAllowlist": "vertex_vessel_owner_link,edge_vessel_owner_link"
  },
  {
    "file": "registry/registerRegistry",
    "processId": "vessel_registry_registerRegistry",
    "nsid": "app.etzhayyim.apps.vessel.registry.registerRegistry",
    "writeTableAllowlist": "vertex_vessel_ship_registry"
  },
  {
    "file": "registry/changeFlag",
    "processId": "vessel_registry_changeFlag",
    "nsid": "app.etzhayyim.apps.vessel.registry.changeFlag",
    "writeTableAllowlist": "vertex_vessel_ship"
  },
  {
    "file": "registry/getShip",
    "processId": "vessel_registry_getShip",
    "nsid": "app.etzhayyim.apps.vessel.registry.getShip",
    "writeTableAllowlist": ""
  },
  {
    "file": "registry/listShips",
    "processId": "vessel_registry_listShips",
    "nsid": "app.etzhayyim.apps.vessel.registry.listShips",
    "writeTableAllowlist": ""
  },
  {
    "file": "registry/searchShips",
    "processId": "vessel_registry_searchShips",
    "nsid": "app.etzhayyim.apps.vessel.registry.searchShips",
    "writeTableAllowlist": ""
  },
  {
    "file": "registry/getOwner",
    "processId": "vessel_registry_getOwner",
    "nsid": "app.etzhayyim.apps.vessel.registry.getOwner",
    "writeTableAllowlist": ""
  },
  {
    "file": "registry/getShipOwner",
    "processId": "vessel_registry_getShipOwner",
    "nsid": "app.etzhayyim.apps.vessel.registry.getShipOwner",
    "writeTableAllowlist": ""
  },
  {
    "file": "registry/getShipsByFlag",
    "processId": "vessel_registry_getShipsByFlag",
    "nsid": "app.etzhayyim.apps.vessel.registry.getShipsByFlag",
    "writeTableAllowlist": ""
  },
  {
    "file": "tracking/ingestPositions",
    "processId": "vessel_tracking_ingestPositions",
    "nsid": "app.etzhayyim.apps.vessel.tracking.ingestPositions",
    "writeTableAllowlist": "vertex_vessel_position"
  },
  {
    "file": "tracking/getVesselPosition",
    "processId": "vessel_tracking_getVesselPosition",
    "nsid": "app.etzhayyim.apps.vessel.tracking.getVesselPosition",
    "writeTableAllowlist": ""
  },
  {
    "file": "tracking/getPositionByMmsi",
    "processId": "vessel_tracking_getPositionByMmsi",
    "nsid": "app.etzhayyim.apps.vessel.tracking.getPositionByMmsi",
    "writeTableAllowlist": ""
  },
  {
    "file": "tracking/listVesselsInArea",
    "processId": "vessel_tracking_listVesselsInArea",
    "nsid": "app.etzhayyim.apps.vessel.tracking.listVesselsInArea",
    "writeTableAllowlist": ""
  },
  {
    "file": "tracking/getPositionHistory",
    "processId": "vessel_tracking_getPositionHistory",
    "nsid": "app.etzhayyim.apps.vessel.tracking.getPositionHistory",
    "writeTableAllowlist": ""
  },
  {
    "file": "tracking/listVesselsNearPort",
    "processId": "vessel_tracking_listVesselsNearPort",
    "nsid": "app.etzhayyim.apps.vessel.tracking.listVesselsNearPort",
    "writeTableAllowlist": ""
  },
  {
    "file": "voyage/registerVoyage",
    "processId": "vessel_voyage_registerVoyage",
    "nsid": "app.etzhayyim.apps.vessel.voyage.registerVoyage",
    "writeTableAllowlist": "vertex_vessel_voyage"
  },
  {
    "file": "voyage/updateVoyage",
    "processId": "vessel_voyage_updateVoyage",
    "nsid": "app.etzhayyim.apps.vessel.voyage.updateVoyage",
    "writeTableAllowlist": "vertex_vessel_voyage"
  },
  {
    "file": "voyage/listVoyages",
    "processId": "vessel_voyage_listVoyages",
    "nsid": "app.etzhayyim.apps.vessel.voyage.listVoyages",
    "writeTableAllowlist": ""
  },
  {
    "file": "voyage/recordPortCall",
    "processId": "vessel_voyage_recordPortCall",
    "nsid": "app.etzhayyim.apps.vessel.voyage.recordPortCall",
    "writeTableAllowlist": "vertex_vessel_port_call,edge_vessel_port_call_endpoint"
  },
  {
    "file": "voyage/listPortCalls",
    "processId": "vessel_voyage_listPortCalls",
    "nsid": "app.etzhayyim.apps.vessel.voyage.listPortCalls",
    "writeTableAllowlist": ""
  },
  {
    "file": "voyage/linkOwnerEntity",
    "processId": "vessel_voyage_linkOwnerEntity",
    "nsid": "app.etzhayyim.apps.vessel.voyage.linkOwnerEntity",
    "writeTableAllowlist": "vertex_vessel_owner_link,edge_vessel_owner_link"
  },
  {
    "file": "voyage/getVesselChain",
    "processId": "vessel_voyage_getVesselChain",
    "nsid": "app.etzhayyim.apps.vessel.voyage.getVesselChain",
    "writeTableAllowlist": ""
  },
  {
    "file": "seedMaritime",
    "processId": "vessel_seedMaritime",
    "nsid": "app.etzhayyim.apps.vessel.seedMaritime",
    "writeTableAllowlist": "vertex_vessel_ship,vertex_vessel_shipowner,vertex_vessel_ship_registry,vertex_vessel_position,vertex_vessel_voyage,vertex_vessel_port_call,vertex_vessel_owner_link,edge_vessel_owner_link,edge_vessel_port_call_endpoint"
  },
  {
    "file": "getDashboard",
    "processId": "vessel_getDashboard",
    "nsid": "app.etzhayyim.apps.vessel.getDashboard",
    "writeTableAllowlist": ""
  }
];

const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/vessel/${s.file}.bpmn`;
const slug = (s: Seed) => s.file.replace(/\//g, "-").replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/vessel-${slug(s)}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/vessel-${slug(s)}-v1`;

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8");
    const size = Buffer.byteLength(xml, "utf8");
    await sql`INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1, ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon' WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})`.execute(db);
    await sql`INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1, 30000, ${s.writeTableAllowlist}, 'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon' WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)})`.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  for (const s of seeds) {
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db);
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db);
  }
}
