"""Captured from Kysely migration 20260505100000_seed_purge_live_tracker_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260505100000_seed_purge_live_tracker_bpmn"
down_revision = 'r_20260503120000_vertex_page_domain_index_and_extract_columns'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-purgeStaleLiveTracker-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_purge_stale_live_tracker',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — purge stale live tracker rows.\n'
                 '\n'
                 '  RisingWave has no native TTL. This BPMN runs daily and deletes rows older\n'
                 '  than the per-table retention window:\n'
                 '\n'
                 '    vertex_aircraft_state  : 24h (state vectors are 1-tick snapshots)\n'
                 '    vertex_satellite_pass  : 48h (los_ms in the past, no longer visible)\n'
                 '    vertex_satellite_tle   : 14d (keep 2-week catalog history, fresh\n'
                 '                                   epoch always wins via PK overwrite)\n'
                 '\n'
                 '  vertex_aircraft_track is NOT purged here — flight trajectories are\n'
                 '  long-term archive (history.etzhayyim.com may consume these).\n'
                 '\n'
                 '  Cadence: R/PT24H. Single instance per day.\n'
                 '\n'
                 '  ai.gftd.apps.maps.purgeStaleLiveTracker.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-purgeStaleLiveTracker-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_purge_stale_live_tracker"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_purge_stale_live_tracker" name="maps purge stale live '
                 'tracker" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.purgeStaleLiveTracker", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 24 hours">\n'
                 '      <bpmn:outgoing>Flow_ToPurge</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT24H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToPurge_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPurge" sourceRef="Start_Timer" '
                 'targetRef="Task_PurgeState"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPurge_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_PurgeState"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PurgeState" name="purge vertex_aircraft_state '
                 '&gt;24h">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.delete"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_aircraft_state&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;ts_ms &lt; (extract(epoch from now() - '
                 'INTERVAL \'24 hours\') * 1000)::bigint&quot;" target="whereExpr"/>\n'
                 '          <zeebe:output source="=rowsDeleted" target="aircraftStateDeleted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPurge</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToPurge_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToPurgePass</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPurgePass" sourceRef="Task_PurgeState" '
                 'targetRef="Task_PurgePass"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PurgePass" name="purge vertex_satellite_pass '
                 'los_ms&lt;now-48h">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.delete"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_satellite_pass&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;los_ms &lt; (extract(epoch from now() - '
                 'INTERVAL \'48 hours\') * 1000)::bigint&quot;" target="whereExpr"/>\n'
                 '          <zeebe:output source="=rowsDeleted" target="satellitePassDeleted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPurgePass</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToPurgeTle</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPurgeTle" sourceRef="Task_PurgePass" '
                 'targetRef="Task_PurgeTle"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_PurgeTle" name="purge vertex_satellite_tle '
                 'epoch&gt;14d old">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.delete"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_satellite_tle&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;epoch_ms &lt; (extract(epoch from now() - '
                 'INTERVAL \'14 days\') * 1000)::bigint&quot;" target="whereExpr"/>\n'
                 '          <zeebe:output source="=rowsDeleted" target="satelliteTleDeleted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPurgeTle</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_PurgeTle" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit purge OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.maps.purgeStaleLiveTracker&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;aircraftStateDeleted&quot;: '
                 'aircraftStateDeleted, &quot;satellitePassDeleted&quot;: satellitePassDeleted, '
                 '&quot;satelliteTleDeleted&quot;: satelliteTleDeleted }" target="attributes"/>\n'
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
                 5428,
                 '00-contracts/bpmn/ai/gftd/maps/purgeStaleLiveTracker.bpmn',
                 '2026-05-05T10:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-purge-live-tracker',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-purgeStaleLiveTracker-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-purgeStaleLiveTracker-v1',
                 'did:web:maps.etzhayyim.com',
                 'ai.gftd.apps.maps.purgeStaleLiveTracker',
                 'maps_purge_stale_live_tracker',
                 300000,
                 'vertex_aircraft_state,vertex_satellite_pass,vertex_satellite_tle',
                 '2026-05-05T10:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps-purge-live-tracker',
                 'did:web:maps.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-purgeStaleLiveTracker-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/maps-purgeStaleLiveTracker-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/maps-purgeStaleLiveTracker-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
