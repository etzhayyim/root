"""Captured from Kysely migration 20260501180200_seed_live_tracker_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501180200_seed_live_tracker_bpmn"
down_revision = 'r_20260501180100_mv_live_tracker'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-liveTrackAircraft-v1',
                 'did:web:maps.gftd.ai',
                 'maps_live_track_aircraft',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — live aircraft state ingest (Flightradar24-equivalent).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. flight.live.poll — single OpenSky /states/all GET, all aircraft\n'
                 '       (~12k rows). Writes vertex_aircraft_state via sync_cursor.\n'
                 '       Returns rowsIngested + sourcedFrom.\n'
                 '    2. exclusive gateway — short-circuit when 0 rows ingested (rate limit hit).\n'
                 '    3. generic.audit.emit — OCEL event with aggregate stats.\n'
                 '\n'
                 '  Cadence: R/PT10S. OpenSky anonymous rate limit is 10s/req. One BPMN\n'
                 '  instance per tick; pyzeebe handler retries with adsb-fi if OpenSky 429.\n'
                 '\n'
                 '  ai.gftd.apps.maps.liveTrackAircraft.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-liveTrackAircraft-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_live_track_aircraft"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_live_track_aircraft" name="maps live track aircraft" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.liveTrackAircraft", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 10 seconds">\n'
                 '      <bpmn:outgoing>Flow_ToPoll</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT10S">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT10S</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToPoll_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPoll" sourceRef="Start_Timer" '
                 'targetRef="Task_Poll"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPoll_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Poll"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Poll" name="OpenSky /states/all + persist">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.live.poll"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=null" target="bbox"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=rowsIngested" target="rowsIngested"/>\n'
                 '          <zeebe:output source="=sourcedFrom" target="sourcedFrom"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPoll</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToPoll_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToGate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGate" sourceRef="Task_Poll" '
                 'targetRef="Gateway_Has"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_Has" name="any rows?">\n'
                 '      <bpmn:incoming>Flow_ToGate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_HasRows</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_NoRows</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_HasRows" sourceRef="Gateway_Has" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=rowsIngested '
                 '&gt; 0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoRows" sourceRef="Gateway_Has" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">=rowsIngested '
                 '&lt;= 0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit live-track OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.maps.liveTrackAircraft&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;rowsIngested&quot;: rowsIngested, &quot;sourcedFrom&quot;: sourcedFrom }" '
                 'target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_HasRows</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_NoRows</bpmn:incoming>\n'
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
                 4322,
                 '00-contracts/bpmn/ai/gftd/maps/liveTrackAircraft.bpmn',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-liveTrackAircraft-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-liveTrackAircraft-v1',
                 'did:web:maps.gftd.ai',
                 'ai.gftd.apps.maps.liveTrackAircraft',
                 'maps_live_track_aircraft',
                 30000,
                 'vertex_aircraft_state',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'did:web:maps.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-liveTrackAircraft-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-computeAircraftTrack-v1',
                 'did:web:maps.gftd.ai',
                 'maps_compute_aircraft_track',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — compact recent state vectors into per-flight tracks.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. flight.track.compact — group last 5 minutes of vertex_aircraft_state\n'
                 '       by icao24 + callsign, build LineString GeoJSON (max 500 sample points\n'
                 '       per flight), write vertex_aircraft_track.\n'
                 '\n'
                 '  Cadence: R/PT5M. Independent from polling cron.\n'
                 '\n'
                 '  ai.gftd.apps.maps.computeAircraftTrack.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-computeAircraftTrack-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_compute_aircraft_track"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_compute_aircraft_track" name="maps compute aircraft '
                 'track" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.computeAircraftTrack", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 5 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToCompact</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT5M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToCompact_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCompact" sourceRef="Start_Timer" '
                 'targetRef="Task_Compact"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToCompact_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Compact"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Compact" name="compact state vectors → tracks">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="flight.track.compact"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=300" target="window_sec"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=tracksWritten" target="tracksWritten"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToCompact</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToCompact_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Compact" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit track-compact OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.maps.computeAircraftTrack&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;tracksWritten&quot;: tracksWritten }" target="attributes"/>\n'
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
                 3320,
                 '00-contracts/bpmn/ai/gftd/maps/computeAircraftTrack.bpmn',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-computeAircraftTrack-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-computeAircraftTrack-v1',
                 'did:web:maps.gftd.ai',
                 'ai.gftd.apps.maps.computeAircraftTrack',
                 'maps_compute_aircraft_track',
                 120000,
                 'vertex_aircraft_track',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'did:web:maps.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-computeAircraftTrack-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-refreshTleCatalog-v1',
                 'did:web:maps.gftd.ai',
                 'maps_refresh_tle_catalog',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — TLE catalog refresh (CelesTrak primary).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. satellite.tle.refresh — fetch CelesTrak gp.php?GROUP={active,starlink,\n'
                 '       gnss,iss}&FORMAT=tle, parse two-line elements, write '
                 'vertex_satellite_tle.\n'
                 '       Idempotent on (norad_id, epoch_ms) PK.\n'
                 '\n'
                 '  Cadence: R/PT6H. CelesTrak refreshes ~every 4-8h, our cycle stays fresh.\n'
                 '\n'
                 '  ai.gftd.apps.maps.refreshTleCatalog.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-refreshTleCatalog-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_refresh_tle_catalog"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_refresh_tle_catalog" name="maps refresh tle catalog" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.refreshTleCatalog", "version": 1, '
                 '"resultTimeoutMs": 300000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 6 hours">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT6H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT6H</bpmn:timeCycle>\n'
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
                 '    <bpmn:serviceTask id="Task_Refresh" name="CelesTrak fetch + persist TLE">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="satellite.tle.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=null" target="groups"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=tleIngested" target="tleIngested"/>\n'
                 '          <zeebe:output source="=byGroup" target="byGroup"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRefresh</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToRefresh_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Refresh" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit tle-refresh OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;ai.gftd.apps.maps.refreshTleCatalog&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;tleIngested&quot;: tleIngested, &quot;byGroup&quot;: byGroup }" '
                 'target="attributes"/>\n'
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
                 3390,
                 '00-contracts/bpmn/ai/gftd/maps/refreshTleCatalog.bpmn',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-refreshTleCatalog-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-refreshTleCatalog-v1',
                 'did:web:maps.gftd.ai',
                 'ai.gftd.apps.maps.refreshTleCatalog',
                 'maps_refresh_tle_catalog',
                 300000,
                 'vertex_satellite_tle',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'did:web:maps.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-refreshTleCatalog-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT $1, $2, $3, 1, $4,\n'
         "             CAST($5 AS integer), $6, 'active', $7,\n"
         '             1, $8, $9, $10\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-precomputeSatellitePasses-v1',
                 'did:web:maps.gftd.ai',
                 'maps_precompute_satellite_passes',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — pre-compute satellite passes for popular observer cells.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. satellite.pass.precompute — for each observer H3 cell in\n'
                 '       SATELLITE_OBSERVER_CELLS_JSON (defaults to 12 KAMI bay centroids\n'
                 '       from sentinel pipeline), SGP4-propagate every TLE in the active\n'
                 '       group across the next 24h, find AOS/LOS pairs above min elevation,\n'
                 '       write to vertex_satellite_pass.\n'
                 '\n'
                 '  Cadence: R/PT1H. New TLEs every 6h, but observer-cell list can grow,\n'
                 '  so 1h cycle keeps cache warm.\n'
                 '\n'
                 '  ai.gftd.apps.maps.precomputeSatellitePasses.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-precomputeSatellitePasses-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_precompute_satellite_passes"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/maps"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_precompute_satellite_passes" name="maps precompute '
                 'satellite passes" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.maps.precomputeSatellitePasses", "version": 1, '
                 '"resultTimeoutMs": 600000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 1 hour">\n'
                 '      <bpmn:outgoing>Flow_ToPrecompute</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT1H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual">\n'
                 '      <bpmn:outgoing>Flow_ToPrecompute_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPrecompute" sourceRef="Start_Timer" '
                 'targetRef="Task_Precompute"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPrecompute_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Precompute"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Precompute" name="SGP4 propagate + persist '
                 'passes">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="satellite.pass.precompute"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=null" target="observers"/>\n'
                 '          <zeebe:input source="=24" target="window_h"/>\n'
                 '          <zeebe:input source="=10" target="min_elevation_deg"/>\n'
                 '          <zeebe:input source="=&quot;active&quot;" target="catalog_group"/>\n'
                 '          <zeebe:output source="=runId" target="runId"/>\n'
                 '          <zeebe:output source="=passesWritten" target="passesWritten"/>\n'
                 '          <zeebe:output source="=observersCovered" target="observersCovered"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPrecompute</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToPrecompute_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Precompute" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit pass-precompute OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;ai.gftd.apps.maps.precomputeSatellitePasses&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;runId&quot;: runId, '
                 '&quot;passesWritten&quot;: passesWritten, &quot;observersCovered&quot;: '
                 'observersCovered }" target="attributes"/>\n'
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
                 3888,
                 '00-contracts/bpmn/ai/gftd/maps/precomputeSatellitePasses.bpmn',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-precomputeSatellitePasses-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding\n'
         '        (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '         write_table_allowlist, status, created_at, sensitivity_ord,\n'
         '         org_id, user_id, actor_id, actor_did, org_did)\n'
         '      SELECT $1, $2, $3, $4, 1,\n'
         '             CAST($5 AS integer), $6,\n'
         "             'active', $7, 1,\n"
         "             $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-precomputeSatellitePasses-v1',
                 'did:web:maps.gftd.ai',
                 'ai.gftd.apps.maps.precomputeSatellitePasses',
                 'maps_precompute_satellite_passes',
                 600000,
                 'vertex_satellite_pass',
                 '2026-05-01T17:00:00Z',
                 'did:web:maps.gftd.ai',
                 'did:web:maps.gftd.ai',
                 'sys.bpmn.seed.maps-live-tracker',
                 'did:web:maps.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-precomputeSatellitePasses-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-liveTrackAircraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-liveTrackAircraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-computeAircraftTrack-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-computeAircraftTrack-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-refreshTleCatalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-refreshTleCatalog-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.lexiconBinding/maps-precomputeSatellitePasses-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def   WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/maps-precomputeSatellitePasses-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
