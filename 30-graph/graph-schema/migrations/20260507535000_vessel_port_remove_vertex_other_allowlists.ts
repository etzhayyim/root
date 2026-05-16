import type { Kysely } from "kysely";
import { sql } from "kysely";

const replacements: Array<[string, string]> = [
  ["vessel_registry_registerShip", "vertex_vessel_ship"],
  ["vessel_registry_updateShip", "vertex_vessel_ship"],
  ["vessel_registry_registerOwner", "vertex_vessel_shipowner"],
  ["vessel_registry_transferOwnership", "vertex_vessel_owner_link,edge_vessel_owner_link"],
  ["vessel_registry_registerRegistry", "vertex_vessel_ship_registry"],
  ["vessel_registry_changeFlag", "vertex_vessel_ship"],
  ["vessel_tracking_ingestPositions", "vertex_vessel_position"],
  ["vessel_voyage_registerVoyage", "vertex_vessel_voyage"],
  ["vessel_voyage_updateVoyage", "vertex_vessel_voyage"],
  ["vessel_voyage_recordPortCall", "vertex_vessel_port_call,edge_vessel_port_call_endpoint"],
  ["vessel_voyage_linkOwnerEntity", "vertex_vessel_owner_link,edge_vessel_owner_link"],
  [
    "vessel_seedMaritime",
    "vertex_vessel_ship,vertex_vessel_shipowner,vertex_vessel_ship_registry,vertex_vessel_position,vertex_vessel_voyage,vertex_vessel_port_call,vertex_vessel_owner_link,edge_vessel_owner_link,edge_vessel_port_call_endpoint",
  ],
  ["port_infrastructure_registerBerth", "vertex_port_berth,edge_port_infrastructure"],
  ["port_infrastructure_registerTerminal", "vertex_port_terminal,edge_port_infrastructure"],
  ["port_portCallTracking_receivePortCallEvent", "vertex_port_call_event,edge_port_call_event"],
  [
    "port_seedPorts",
    "vertex_transport,vertex_port_berth,vertex_port_terminal,vertex_port_call_event,edge_port_infrastructure,edge_port_call_event",
  ],
];

export async function up(db: Kysely<unknown>): Promise<void> {
  for (const [processId, allowlist] of replacements) {
    await sql`
      UPDATE vertex_bpmn_lexicon_binding
      SET write_table_allowlist = ${allowlist}
      WHERE bpmn_process_id = ${processId}
    `.execute(db);
  }
}

export async function down(_db: Kysely<unknown>): Promise<void> {
  // No down migration: restoring catch_all_vertex write permissions is intentionally disallowed.
}
