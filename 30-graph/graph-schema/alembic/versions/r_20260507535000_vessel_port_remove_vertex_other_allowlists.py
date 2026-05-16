"""Captured from Kysely migration 20260507535000_vessel_port_remove_vertex_other_allowlists."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507535000_vessel_port_remove_vertex_other_allowlists"
down_revision = 'r_20260507534000_gov_actor_manifest_vertex'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_ship', 'vessel_registry_registerShip']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_ship', 'vessel_registry_updateShip']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_shipowner', 'vessel_registry_registerOwner']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_owner_link,edge_vessel_owner_link',
                 'vessel_registry_transferOwnership']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_ship_registry', 'vessel_registry_registerRegistry']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_ship', 'vessel_registry_changeFlag']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_position', 'vessel_tracking_ingestPositions']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_voyage', 'vessel_voyage_registerVoyage']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_voyage', 'vessel_voyage_updateVoyage']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_port_call,edge_vessel_port_call_endpoint',
                 'vessel_voyage_recordPortCall']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_owner_link,edge_vessel_owner_link',
                 'vessel_voyage_linkOwnerEntity']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_vessel_ship,vertex_vessel_shipowner,vertex_vessel_ship_registry,vertex_vessel_position,vertex_vessel_voyage,vertex_vessel_port_call,vertex_vessel_owner_link,edge_vessel_owner_link,edge_vessel_port_call_endpoint',
                 'vessel_seedMaritime']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_port_berth,edge_port_infrastructure',
                 'port_infrastructure_registerBerth']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_port_terminal,edge_port_infrastructure',
                 'port_infrastructure_registerTerminal']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_port_call_event,edge_port_call_event',
                 'port_portCallTracking_receivePortCallEvent']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist = $1\n'
         '      WHERE bpmn_process_id = $2\n'
         '    ',
  'parameters': ['vertex_transport,vertex_port_berth,vertex_port_terminal,vertex_port_call_event,edge_port_infrastructure,edge_port_call_event',
                 'port_seedPorts']}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
