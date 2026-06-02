"""Captured from Kysely migration 20260501180300_seed_aismarine_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260501180300_seed_aismarine_bpmn_actors"
down_revision = 'r_20260501180200_seed_live_tracker_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-ais-stream-consumer-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_aismarine_consumer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Catalog stub — aisstream.io WebSocket consumer (ADR-2605011500).\n'
                 '\n'
                 '  This BPMN exists for actor-discovery uniformity (ADR-0056 §INSERT N rows\n'
                 '  regime). It contains NO executable serviceTask. The actual long-running\n'
                 '  consumer is the K8s Deployment at:\n'
                 '\n'
                 '    50-infra/vultr/bulk-ingest/aismarine-consumer/\n'
                 '\n'
                 '  The Deployment runs `pymagatama` with env AISMARINE_CONSUMER_MODE=1 which\n'
                 '  switches main entry to `aismarine_consumer_loop()` — a persistent WebSocket\n'
                 '  client that subscribes to aisstream.io with no BoundingBoxes filter\n'
                 '  (global), batches 5s/500-msg, and flushes via:\n'
                 '\n'
                 '    POST '
                 'http://dispatcher.etzhayyim.com:8080/xrpc/com.etzhayyim.apps.maps.aismarine.ingestAisStream\n'
                 '    (x-internal-trust HMAC, ADR-2604241038 invariant 3)\n'
                 '\n'
                 '  which fans out to `aismarine.position.batchInsert` + '
                 '`aismarine.master.upsert`\n'
                 '  pyzeebe handlers (registered in zeebe_worker_main.py).\n'
                 '\n'
                 '  Why a manual-only BPMN exists at all: ADR-0056 wants every aismarine actor\n'
                 '  identifiable by a row in vertex_bpmn_process_def. A manual-only flow is\n'
                 '  the cheapest way to keep the actor table dense without a fake timer.\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.maps.aismarine.aisStreamConsumer\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-ais-stream-consumer-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_aismarine_consumer"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps/aismarine"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_aismarine_consumer" name="maps aismarine consumer" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.maps.aismarine.aisStreamConsumer", "version": 1, '
                 '"resultTimeoutMs": 30000, "stub": true, "implementedBy": "k8s-deployment", '
                 '"deployment": "50-infra/vultr/bulk-ingest/aismarine-consumer/" }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / catalog placeholder">\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Start_Manual" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="catalog only — see K8s Deployment">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2420,
                 '00-contracts/bpmn/com/etzhayyim/maps/aismarine/aisStreamConsumer.bpmn',
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-ais-stream-consumer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-voyage-detector-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_aismarine_voyage_detector',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — Voyage detector (R/PT5M).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. aismarine.voyage.detectWindow — scan last 5min vertex_vessel_position,\n'
                 '                                        join against vertex_open_ports_port,\n'
                 '                                        derive arrivals (nav_status ∈ {1,5,15}\n'
                 '                                        + sog ≤ 0.5kn + within 5km of port).\n'
                 '                                        Returns scanned/arrivals_recorded/\n'
                 '                                        voyages_opened.\n'
                 '    2. exclusive gateway              — short-circuit when nothing happened.\n'
                 '    3. generic.audit.emit             — OCEL event with stats.\n'
                 '\n'
                 '  ADR-2605011500. NSID: com.etzhayyim.apps.maps.aismarine.voyageDetector.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-voyage-detector-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_aismarine_voyage_detector"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps/aismarine"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_aismarine_voyage_detector" name="maps aismarine voyage '
                 'detector" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.maps.aismarine.voyageDetector", "version": 1, '
                 '"resultTimeoutMs": 240000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 5 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToDetect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT5M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT5M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToDetect_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDetect" sourceRef="Start_Timer" '
                 'targetRef="Task_DetectWindow"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDetect_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_DetectWindow"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_DetectWindow" name="detect arrivals in 5-min '
                 'window">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aismarine.voyage.detectWindow"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=5"     target="window_minutes"/>\n'
                 '          <zeebe:input source="=50000" target="limit"/>\n'
                 '          <zeebe:output source="=scanned"           target="scanned"/>\n'
                 '          <zeebe:output source="=arrivals_recorded" target="arrivalsRecorded"/>\n'
                 '          <zeebe:output source="=voyages_opened"    target="voyagesOpened"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDetect</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToDetect_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToGate</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToGate" sourceRef="Task_DetectWindow" '
                 'targetRef="Gateway_HasArrivals"/>\n'
                 '\n'
                 '    <bpmn:exclusiveGateway id="Gateway_HasArrivals" name="anything written?">\n'
                 '      <bpmn:incoming>Flow_ToGate</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_HasArrivals</bpmn:outgoing>\n'
                 '      <bpmn:outgoing>Flow_NoArrivals</bpmn:outgoing>\n'
                 '    </bpmn:exclusiveGateway>\n'
                 '    <bpmn:sequenceFlow id="Flow_HasArrivals" sourceRef="Gateway_HasArrivals" '
                 'targetRef="Task_Audit">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=(arrivalsRecorded + voyagesOpened) &gt; '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '    <bpmn:sequenceFlow id="Flow_NoArrivals" sourceRef="Gateway_HasArrivals" '
                 'targetRef="End">\n'
                 '      <bpmn:conditionExpression '
                 'xsi:type="bpmn:tFormalExpression">=(arrivalsRecorded + voyagesOpened) &lt;= '
                 '0</bpmn:conditionExpression>\n'
                 '    </bpmn:sequenceFlow>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit voyage.detect OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.maps.aismarine.voyage.detect&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;scanned&quot;: scanned, '
                 '&quot;arrivalsRecorded&quot;: arrivalsRecorded, &quot;voyagesOpened&quot;: '
                 'voyagesOpened }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_HasArrivals</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_NoArrivals</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4768,
                 '00-contracts/bpmn/com/etzhayyim/maps/aismarine/voyageDetector.bpmn',
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-voyage-detector-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-master-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_aismarine_refresh_vessel_master',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — Vessel master backfill (R/PT24H).\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. aismarine.master.refresh — backfill flag_iso / flag_mid / type_class\n'
                 '                                   for vertex_vessel rows missing them.\n'
                 '                                   Open-data only (vessel_flag_iso UDF +\n'
                 '                                   vessel_type_class UDF, ADR-2605011500).\n'
                 '                                   Returns rows_scanned/rows_updated.\n'
                 '    2. generic.audit.emit        — OCEL event with stats.\n'
                 '\n'
                 '  ADR-2605011500. NSID: com.etzhayyim.apps.maps.aismarine.refreshVesselMaster.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-refresh-vessel-master-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_aismarine_refresh_vessel_master"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps/aismarine"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_aismarine_refresh_vessel_master" name="maps aismarine '
                 'refresh vessel master" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.maps.aismarine.refreshVesselMaster", "version": 1, '
                 '"resultTimeoutMs": 240000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 24 hours">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT24H">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT24H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToRefresh_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh" sourceRef="Start_Timer" '
                 'targetRef="Task_Refresh"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRefresh_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Refresh"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Refresh" name="backfill flag_iso / type_class">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aismarine.master.refresh"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=5000" target="limit"/>\n'
                 '          <zeebe:output source="=rows_scanned" target="rowsScanned"/>\n'
                 '          <zeebe:output source="=rows_updated" target="rowsUpdated"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRefresh</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToRefresh_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Refresh" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit master.refresh OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.maps.aismarine.master.refresh&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;rowsScanned&quot;: rowsScanned, '
                 '&quot;rowsUpdated&quot;: rowsUpdated }" target="attributes"/>\n'
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
                 3586,
                 '00-contracts/bpmn/com/etzhayyim/maps/aismarine/refreshVesselMaster.bpmn',
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-master-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-density-v1',
                 'did:web:maps.etzhayyim.com',
                 'maps_aismarine_refresh_vessel_density',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — Vessel density verify (R/PT15M).\n'
                 '\n'
                 '  The density MV (mv_vessel_density_h3_r6) is autonomous (RisingWave streaming\n'
                 '  MV). This BPMN is observability only — periodically samples row count + the\n'
                 '  latest bucket_ms to confirm the MV is being updated. Alerts on stale MV are\n'
                 '  routed via the OCEL audit event.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. aismarine.density.verify — SELECT COUNT(*) + MAX(bucket_ms).\n'
                 '    2. generic.audit.emit        — OCEL event with row_count + '
                 'latest_bucket_ms.\n'
                 '\n'
                 '  ADR-2605011500. NSID: com.etzhayyim.apps.maps.aismarine.refreshVesselDensity.\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-refresh-vessel-density-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_maps_aismarine_refresh_vessel_density"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/maps/aismarine"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="maps_aismarine_refresh_vessel_density" name="maps aismarine '
                 'refresh vessel density" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.maps.aismarine.refreshVesselDensity", "version": '
                 '1, "resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="every 15 minutes">\n'
                 '      <bpmn:outgoing>Flow_ToVerify</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_PT15M">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start_Manual" name="manual / on-demand">\n'
                 '      <bpmn:outgoing>Flow_ToVerify_Manual</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToVerify" sourceRef="Start_Timer" '
                 'targetRef="Task_Verify"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToVerify_Manual" sourceRef="Start_Manual" '
                 'targetRef="Task_Verify"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Verify" name="verify density MV freshness">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="aismarine.density.verify"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=row_count"        target="rowCount"/>\n'
                 '          <zeebe:output source="=latest_bucket_ms" target="latestBucketMs"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToVerify</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_ToVerify_Manual</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Verify" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit density.verify OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.maps.aismarine.density.verify&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;rowCount&quot;: rowCount, '
                 '&quot;latestBucketMs&quot;: latestBucketMs }" target="attributes"/>\n'
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
                 3530,
                 '00-contracts/bpmn/com/etzhayyim/maps/aismarine/refreshVesselDensity.bpmn',
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-density-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-aisStreamConsumer-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.aismarine.aisStreamConsumer',
                 'maps_aismarine_consumer',
                 30000,
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-aisStreamConsumer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-voyageDetector-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.aismarine.voyageDetector',
                 'maps_aismarine_voyage_detector',
                 240000,
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-voyageDetector-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselMaster-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.aismarine.refreshVesselMaster',
                 'maps_aismarine_refresh_vessel_master',
                 240000,
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselMaster-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id, actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active',\n"
         '      $6, 1, $7, $8, $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselDensity-v1',
                 'did:web:maps.etzhayyim.com',
                 'com.etzhayyim.apps.maps.aismarine.refreshVesselDensity',
                 'maps_aismarine_refresh_vessel_density',
                 30000,
                 '2026-05-01T18:00:00Z',
                 'did:web:maps.etzhayyim.com',
                 'did:web:maps.etzhayyim.com',
                 'sys.bpmn.seed.maps.aismarine',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselDensity-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-aisStreamConsumer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-voyageDetector-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselMaster-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/maps-aismarine-refreshVesselDensity-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-ais-stream-consumer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-voyage-detector-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-master-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/maps-aismarine-refresh-vessel-density-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
