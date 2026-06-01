import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import type { Kysely } from "kysely";
import { sql } from "kysely";

type Seed = { file: string; processId: string; nsid: string; writeTableAllowlist: string };

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const ownerDid = "did:web:p0rt7890.etzhayyim.com";
const createdAt = "2026-04-30T22:03:00+09:00";
const actorId = "sys.bpmn.seed.port";
const seeds: Seed[] = [
  {
    "file": "infrastructure/registerPort",
    "processId": "port_infrastructure_registerPort",
    "nsid": "app.etzhayyim.apps.port.infrastructure.registerPort",
    "writeTableAllowlist": "vertex_transport"
  },
  {
    "file": "infrastructure/updatePort",
    "processId": "port_infrastructure_updatePort",
    "nsid": "app.etzhayyim.apps.port.infrastructure.updatePort",
    "writeTableAllowlist": "vertex_transport"
  },
  {
    "file": "infrastructure/registerBerth",
    "processId": "port_infrastructure_registerBerth",
    "nsid": "app.etzhayyim.apps.port.infrastructure.registerBerth",
    "writeTableAllowlist": "vertex_port_berth,edge_port_infrastructure"
  },
  {
    "file": "infrastructure/registerTerminal",
    "processId": "port_infrastructure_registerTerminal",
    "nsid": "app.etzhayyim.apps.port.infrastructure.registerTerminal",
    "writeTableAllowlist": "vertex_port_terminal,edge_port_infrastructure"
  },
  {
    "file": "infrastructure/getPort",
    "processId": "port_infrastructure_getPort",
    "nsid": "app.etzhayyim.apps.port.infrastructure.getPort",
    "writeTableAllowlist": ""
  },
  {
    "file": "infrastructure/listPorts",
    "processId": "port_infrastructure_listPorts",
    "nsid": "app.etzhayyim.apps.port.infrastructure.listPorts",
    "writeTableAllowlist": ""
  },
  {
    "file": "infrastructure/searchPorts",
    "processId": "port_infrastructure_searchPorts",
    "nsid": "app.etzhayyim.apps.port.infrastructure.searchPorts",
    "writeTableAllowlist": ""
  },
  {
    "file": "infrastructure/getPortBerths",
    "processId": "port_infrastructure_getPortBerths",
    "nsid": "app.etzhayyim.apps.port.infrastructure.getPortBerths",
    "writeTableAllowlist": ""
  },
  {
    "file": "infrastructure/getPortTerminals",
    "processId": "port_infrastructure_getPortTerminals",
    "nsid": "app.etzhayyim.apps.port.infrastructure.getPortTerminals",
    "writeTableAllowlist": ""
  },
  {
    "file": "portCallTracking/receivePortCallEvent",
    "processId": "port_portCallTracking_receivePortCallEvent",
    "nsid": "app.etzhayyim.apps.port.portCallTracking.receivePortCallEvent",
    "writeTableAllowlist": "vertex_port_call_event,edge_port_call_event"
  },
  {
    "file": "portCallTracking/listPortCallEvents",
    "processId": "port_portCallTracking_listPortCallEvents",
    "nsid": "app.etzhayyim.apps.port.portCallTracking.listPortCallEvents",
    "writeTableAllowlist": ""
  },
  {
    "file": "portCallTracking/getVesselsAtPort",
    "processId": "port_portCallTracking_getVesselsAtPort",
    "nsid": "app.etzhayyim.apps.port.portCallTracking.getVesselsAtPort",
    "writeTableAllowlist": ""
  },
  {
    "file": "portCallTracking/getPortOccupancy",
    "processId": "port_portCallTracking_getPortOccupancy",
    "nsid": "app.etzhayyim.apps.port.portCallTracking.getPortOccupancy",
    "writeTableAllowlist": ""
  },
  {
    "file": "seedPorts",
    "processId": "port_seedPorts",
    "nsid": "app.etzhayyim.apps.port.seedPorts",
    "writeTableAllowlist": "vertex_transport,vertex_port_berth,vertex_port_terminal,vertex_port_call_event,edge_port_infrastructure,edge_port_call_event"
  },
  {
    "file": "getDashboard",
    "processId": "port_getDashboard",
    "nsid": "app.etzhayyim.apps.port.getDashboard",
    "writeTableAllowlist": ""
  }
];
const sourcePath = (s: Seed) => `00-contracts/bpmn/ai/gftd/port/${s.file}.bpmn`;
const slug = (s: Seed) => s.file.replace(/\//g, "-").replace(/[A-Z]/g, (m) => `-${m.toLowerCase()}`);
const processVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/port-${slug(s)}-v1`;
const bindingVertexId = (s: Seed) => `at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/port-${slug(s)}-v1`;
export async function up(db: Kysely<unknown>): Promise<void> { for (const s of seeds) { const xml = readFileSync(path.resolve(repoRoot, sourcePath(s)), "utf8"); const size = Buffer.byteLength(xml, "utf8"); await sql`INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT ${processVertexId(s)}, ${ownerDid}, ${s.processId}, 1, ${xml}, CAST(${size} AS integer), ${sourcePath(s)}, 'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon' WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)})`.execute(db); await sql`INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms, write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did) SELECT ${bindingVertexId(s)}, ${ownerDid}, ${s.nsid}, ${s.processId}, 1, 30000, ${s.writeTableAllowlist}, 'active', ${createdAt}, 100, ${ownerDid}, ${ownerDid}, ${actorId}, ${ownerDid}, 'anon' WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)})`.execute(db); }}
export async function down(db: Kysely<unknown>): Promise<void> { for (const s of seeds) { await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${bindingVertexId(s)}`.execute(db); await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${processVertexId(s)}`.execute(db); }}
