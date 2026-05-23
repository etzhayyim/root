"""Captured from Kysely migration 20260505183100_seed_aircraft_phase3_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505183100_seed_aircraft_phase3_bpmn"
down_revision = 'r_20260505183000_aircraft_graph_phase3'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT $1, $2, $3, 1, $4,\n'
         "           CAST($5 AS integer), $6, 'active', $7,\n"
         '           1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-backfillAircraftRegistry-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_backfill_aircraft_registry',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — backfill vertex_aircraft from OpenSky aircraft database.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. flight.registry.refresh — fetch OpenSky aircraft DB CSV\n'
                 '       '
                 '(https://opensky-network.org/datasets/metadata/aircraft-database-complete-*.csv,\n'
                 '       ~620K rows, public, CC-BY 4.0). Parse + INSERT vertex_aircraft rows\n'
                 '       keyed by icao24 → DID. Resolve registration prefix → ISO 3166-1 alpha-2.\n'
                 '    2. flight.registry.linkLive — find vertex_aircraft_state rows whose\n'
                 '       aircraft_did is NULL but icao24 matches a vertex_aircraft.icao24,\n'
                 '       UPDATE the column + INSERT edge_aircraft_state_for_aircraft.\n'
                 '\n'
                 '  Cadence: R/P7D. 620K rows / 7d ingest amortizes RW Hummock pressure.\n'
                 '  This runs out of band from the live tracker R/PT10S poll.\n'
                 '\n'
                 '  ai.gftd.apps.maps.backfillAircraftRegistry\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-backfillAircraftRegistry-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_backfill_aircraft_registry"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_backfill_aircraft_registry" name="maps backfill '
                 'aircraft registry" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.backfillAircraftRegistry", "version": 1, '
                 '"resultTimeoutMs": 1800000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_P7D">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh" sourceRef="Start_Timer" '
                 'targetRef="Task_Refresh"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Refresh"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Refresh" name="OpenSky aircraft DB CSV → '
                 'vertex_aircraft">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.registry.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=null" target="csv_url"/>\n'
                 '          <zeebe:input source="=200000" target="max_rows"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=aircraftIngested" target="aircraftIngested"/>\n'
                 '          <zeebe:output source="=skipped" target="skipped"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRefresh</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToRefresh_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToLink</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToLink" sourceRef="Task_Refresh" '
                 'targetRef="Task_LinkLive"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_LinkLive" name="link live state → registered '
                 '(icao24 join)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.registry.linkLive"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=50000" target="max_links"/>\n'
                 '          <zeebe:output source="=linksWritten" target="linksWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToLink</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_LinkLive" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit registry-refresh OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.maps.backfillAircraftRegistry&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;aircraftIngested&quot;: aircraftIngested, &quot;skipped&quot;: skipped, '
                 '&quot;linksWritten&quot;: linksWritten }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4591,
                 '00-contracts/bpmn/ai/gftd/maps/backfillAircraftRegistry.bpmn',
                 '2026-05-05T18:31:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-aircraft-phase3',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-backfillAircraftRegistry-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '       org_id, user_id, actor_id, actor_did, org_did)\n'
         '    SELECT $1, $2, $3, $4, 1,\n'
         '           CAST($5 AS integer), $6,\n'
         "           'active', $7, 1,\n"
         "           $8, $9, $10, $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-backfillAircraftRegistry-v1',
                 'did:web:maps.etzhayyim.com',
                 'ai.gftd.apps.maps.backfillAircraftRegistry',
                 'maps_backfill_aircraft_registry',
                 1800000,
                 'vertex_aircraft,edge_aircraft_state_for_aircraft',
                 '2026-05-05T18:31:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-aircraft-phase3',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-backfillAircraftRegistry-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-backfillAircraftRegistry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-backfillAircraftRegistry-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
