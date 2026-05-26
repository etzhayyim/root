"""Captured from Kysely migration 20260427073000_seed_extended_infra_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427073000_seed_extended_infra_bpmn_actors"
down_revision = 'r_20260427070000_jp_fiscal_graph'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-recordMechanism-v1',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'open_electricity_market_record_mechanism',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_electricity_market_record_mechanism" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-electricity-market" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_electricity_market_record_mechanism" '
                 'name="recordMechanism" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_electricity_market&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, mechanism_id: '
                 'mechanismId, country_iso3: countryIso3, mechanism_kind: mechanismKind, '
                 'technology_kind: technologyKind, stranded_vid: strandedVid, introduced_at: '
                 'introducedAt, status: &quot;active&quot;, created_at: string(now()), owner_did: '
                 'callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-electricity-market&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-electricity-market.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.electricityMarket.recordMechanism&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2380,
                 '00-contracts/bpmn/ai/gftd/open-electricity-market/recordMechanism.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-recordMechanism-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-flagMissingMoney-v1',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'open_electricity_market_flag_missing_money',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_electricity_market_flag_missing_money" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-electricity-market" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_electricity_market_flag_missing_money" '
                 'name="flagMissingMoney" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_electricity_market&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, flag_id: flagId, '
                 'mechanism_vid: mechanismVid, issue_kind: issueKind, reported_at: reportedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-electricity-market&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-electricity-market.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.electricityMarket.flagMissingMoney&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2306,
                 '00-contracts/bpmn/ai/gftd/open-electricity-market/flagMissingMoney.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-flagMissingMoney-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-recordCrossBorderFlow-v1',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'open_power_grid_interconnect_record_cross_border_flow',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_power_grid_interconnect_record_cross_border_flow" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-power-grid-interconnect" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_power_grid_interconnect_record_cross_border_flow" '
                 'name="recordCrossBorderFlow" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_power_grid_interconnect&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, flow_id: flowId, '
                 'interconnect_name: interconnectName, export_system_operator_lei: '
                 'exportSystemOperatorLei, import_system_operator_lei: importSystemOperatorLei, '
                 'export_iso3: exportIso3, import_iso3: importIso3, period_hour: periodHour, '
                 'flow_mwh: flowMwh, marginal_gen_fuel: marginalGenFuel, congestion_pct: '
                 'congestionPct, price_eur_mwh: priceEurMwh, recorded_at: recordedAt, '
                 'congestion_tier: if congestionPct != null and congestionPct &gt;= 80 then '
                 '&quot;saturated&quot; else if congestionPct != null and congestionPct &gt;= 50 '
                 'then &quot;stressed&quot; else &quot;normal&quot;, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-power-grid-interconnect&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-power-grid-interconnect.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.powerGridInterconnect.recordCrossBorderFlow&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2846,
                 '00-contracts/bpmn/ai/gftd/open-power-grid-interconnect/recordCrossBorderFlow.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-recordCrossBorderFlow-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-flagCurtailment-v1',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'open_power_grid_interconnect_flag_curtailment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_power_grid_interconnect_flag_curtailment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-power-grid-interconnect" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_power_grid_interconnect_flag_curtailment" '
                 'name="flagCurtailment" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_power_grid_interconnect&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, event_id: eventId, '
                 'flow_vid: flowVid, region_iso3: regionIso3, event_kind: eventKind, '
                 'space_wx_event_vid: spaceWxEventVid, energy_mwh: energyMwh, duration_minutes: '
                 'durationMinutes, occurred_at: occurredAt, impact_tier: if eventKind = '
                 '&quot;grid_separation&quot; or (durationMinutes != null and durationMinutes '
                 '&gt;= 180) then &quot;major&quot; else if durationMinutes != null and '
                 'durationMinutes &gt;= 30 then &quot;significant&quot; else &quot;routine&quot;, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-power-grid-interconnect&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-power-grid-interconnect.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.powerGridInterconnect.flagCurtailment&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2700,
                 '00-contracts/bpmn/ai/gftd/open-power-grid-interconnect/flagCurtailment.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-flagCurtailment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-recordBasinMetric-v1',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'open_water_scarcity_record_basin_metric',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_water_scarcity_record_basin_metric" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-water-scarcity" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_water_scarcity_record_basin_metric" '
                 'name="recordBasinMetric" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_water_scarcity&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, metric_id: metricId, basin_name: basinName, '
                 'riparians_iso3: ripariansIso3, baseline_water_stress: baselineWaterStress, '
                 'drought_risk: droughtRisk, regulatory_instrument: regulatoryInstrument, '
                 'agri_harvest_vid: agriHarvestVid, measured_year: measuredYear, stress_tier: if '
                 'baselineWaterStress &gt;= 4 then &quot;extreme&quot; else if baselineWaterStress '
                 '&gt;= 3 then &quot;high&quot; else if baselineWaterStress &gt;= 2 then '
                 '&quot;medium_high&quot; else if baselineWaterStress &gt;= 1 then '
                 '&quot;medium_low&quot; else &quot;low&quot;, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-water-scarcity&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-water-scarcity.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.waterScarcity.recordBasinMetric&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2720,
                 '00-contracts/bpmn/ai/gftd/open-water-scarcity/recordBasinMetric.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-recordBasinMetric-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-flagTreatyDispute-v1',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'open_water_scarcity_flag_treaty_dispute',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_water_scarcity_flag_treaty_dispute" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-water-scarcity" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_water_scarcity_flag_treaty_dispute" '
                 'name="flagTreatyDispute" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_water_scarcity&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, dispute_id: disputeId, basin_metric_vid: '
                 'basinMetricVid, complainant_iso3: complainantIso3, respondent_iso3: '
                 'respondentIso3, issue: issue, wto_dispute_vid: wtoDisputeVid, filed_at: filedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-water-scarcity&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-water-scarcity.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.waterScarcity.flagTreatyDispute&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2378,
                 '00-contracts/bpmn/ai/gftd/open-water-scarcity/flagTreatyDispute.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-flagTreatyDispute-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-recordStewardshipPlan-v1',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'open_water_stewardship_record_stewardship_plan',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_water_stewardship_record_stewardship_plan" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-water-stewardship" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_water_stewardship_record_stewardship_plan" '
                 'name="recordStewardshipPlan" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_water_stewardship&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, plan_id: planId, operator_lei: operatorLei, '
                 'regime: regime, basin_name: basinName, risk_basin_stress_level: '
                 'riskBasinStressLevel, sbtn_miss_vid: sbtnMissVid, committed_at: committedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-water-stewardship&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-water-stewardship.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.waterStewardship.recordStewardshipPlan&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2410,
                 '00-contracts/bpmn/ai/gftd/open-water-stewardship/recordStewardshipPlan.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-recordStewardshipPlan-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-flagBasinStress-v1',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'open_water_stewardship_flag_basin_stress',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_water_stewardship_flag_basin_stress" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-water-stewardship" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_water_stewardship_flag_basin_stress" '
                 'name="flagBasinStress" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_water_stewardship&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, flag_id: flagId, plan_vid: planVid, stress_kind: '
                 'stressKind, affected_persons: affectedPersons, reported_at: reportedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-water-stewardship&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-water-stewardship.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.waterStewardship.flagBasinStress&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2322,
                 '00-contracts/bpmn/ai/gftd/open-water-stewardship/flagBasinStress.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-flagBasinStress-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-registerFacility-v1',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'open_wastewater_reuse_register_facility',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_wastewater_reuse_register_facility" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-wastewater-reuse" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_wastewater_reuse_register_facility" '
                 'name="registerFacility" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_wastewater_reuse&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, facility_id: facilityId, operator_lei: '
                 'operatorLei, country_iso3: countryIso3, treatment_tier: treatmentTier, '
                 'capacity_m3_day: capacityM3Day, end_use: endUse, commissioned_at: '
                 'commissionedAt, status: &quot;active&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-wastewater-reuse&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-wastewater-reuse.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.wastewaterReuse.registerFacility&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2388,
                 '00-contracts/bpmn/ai/gftd/open-wastewater-reuse/registerFacility.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-registerFacility-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-recordMonitoringMetric-v1',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'open_wastewater_reuse_record_monitoring_metric',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_wastewater_reuse_record_monitoring_metric" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-wastewater-reuse" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_wastewater_reuse_record_monitoring_metric" '
                 'name="recordMonitoringMetric" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_wastewater_reuse&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, metric_id: metricId, facility_vid: facilityVid, '
                 'period_month: periodMonth, reuse_volume_m3: reuseVolumeM3, bod_mg_l: bodMgL, '
                 'cod_mg_l: codMgL, tss_mg_l: tssMgL, ecoli_per100ml: ecoliPer100ml, '
                 'micropollutant_exceedances: micropollutantExceedances, recorded_at: recordedAt, '
                 'quality_tier: if micropollutantExceedances != null and micropollutantExceedances '
                 '&gt;= 5 then &quot;non_compliant&quot; else if bodMgL != null and bodMgL &gt; 20 '
                 'then &quot;marginal&quot; else &quot;compliant&quot;, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-wastewater-reuse&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-wastewater-reuse.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.wastewaterReuse.recordMonitoringMetric&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2710,
                 '00-contracts/bpmn/ai/gftd/open-wastewater-reuse/recordMonitoringMetric.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-recordMonitoringMetric-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-registerCable-v1',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'open_telecom_infra_register_cable',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_telecom_infra_register_cable" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-telecom-infra" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_telecom_infra_register_cable" name="registerCable" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_telecom_infra&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, cable_id: cableId, cable_name: cableName, '
                 'consortium_lei: consortiumLei, landing_points_iso3: landingPointsIso3, '
                 'length_km: lengthKm, design_capacity_tbps: designCapacityTbps, rfs_year: '
                 'rfsYear, status: status, registered_at: registeredAt, capacity_tier: if '
                 'designCapacityTbps != null and designCapacityTbps &gt;= 200 then '
                 '&quot;mega&quot; else if designCapacityTbps != null and designCapacityTbps &gt;= '
                 '50 then &quot;major&quot; else &quot;standard&quot;, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-telecom-infra&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-telecom-infra.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.telecomInfra.registerCable&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2620,
                 '00-contracts/bpmn/ai/gftd/open-telecom-infra/registerCable.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-registerCable-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-flagCableFault-v1',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'open_telecom_infra_flag_cable_fault',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_telecom_infra_flag_cable_fault" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-telecom-infra" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_telecom_infra_flag_cable_fault" name="flagCableFault" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_telecom_infra&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, fault_id: faultId, cable_vid: cableVid, '
                 'fault_type: faultType, location_lat: locationLat, location_lon: locationLon, '
                 'repair_ship_eta: repairShipEta, cyber_incident_vid: cyberIncidentVid, '
                 'detected_at: detectedAt, severity_tier: if faultType = '
                 '&quot;sabotage_confirmed&quot; then &quot;state_sponsored&quot; else if '
                 'faultType = &quot;sabotage_suspected&quot; then &quot;investigation&quot; else '
                 '&quot;routine&quot;, status: &quot;active&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-telecom-infra&quot;}" '
                 'target="values"/><zeebe:input source="=&quot;ignore&quot;" '
                 'target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-telecom-infra.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.telecomInfra.flagCableFault&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2583,
                 '00-contracts/bpmn/ai/gftd/open-telecom-infra/flagCableFault.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-flagCableFault-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-registerDeployment-v1',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'open_rural_broadband_register_deployment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_rural_broadband_register_deployment" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-rural-broadband" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rural_broadband_register_deployment" '
                 'name="registerDeployment" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_rural_broadband&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, deployment_id: deploymentId, provider_lei: '
                 'providerLei, country_iso3: countryIso3, program: program, technology: '
                 'technology, premises_passed: premisesPassed, investment_usd: investmentUsd, '
                 'target_speed_mbps_down: targetSpeedMbpsDown, launched_at: launchedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rural-broadband&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-rural-broadband.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.ruralBroadband.registerDeployment&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2456,
                 '00-contracts/bpmn/ai/gftd/open-rural-broadband/registerDeployment.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-registerDeployment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-flagDigitalDivideGap-v1',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'open_rural_broadband_flag_digital_divide_gap',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_rural_broadband_flag_digital_divide_gap" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-rural-broadband" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rural_broadband_flag_digital_divide_gap" '
                 'name="flagDigitalDivideGap" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_rural_broadband&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, gap_id: gapId, deployment_vid: deploymentVid, '
                 'indicator: indicator, value_numeric: valueNumeric, benchmark_value: '
                 'benchmarkValue, reporting_year: reportingYear, reported_at: reportedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rural-broadband&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-rural-broadband.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.ruralBroadband.flagDigitalDivideGap&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2395,
                 '00-contracts/bpmn/ai/gftd/open-rural-broadband/flagDigitalDivideGap.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-flagDigitalDivideGap-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-recordCorridorFlow-v1',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'open_rail_cross_border_record_corridor_flow',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_rail_cross_border_record_corridor_flow" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-rail-cross-border" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rail_cross_border_record_corridor_flow" '
                 'name="recordCorridorFlow" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_rail_cross_border&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, flow_id: flowId, operator_lei: operatorLei, '
                 'corridor_name: corridorName, origin_iso3: originIso3, destination_iso3: '
                 'destinationIso3, regime_document: regimeDocument, gauge_profile: gaugeProfile, '
                 'wagon_count: wagonCount, tonnes_net: tonnesNet, transit_hours: transitHours, '
                 'period_month: periodMonth, recorded_at: recordedAt, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rail-cross-border&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-rail-cross-border.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.railCrossBorder.recordCorridorFlow&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2536,
                 '00-contracts/bpmn/ai/gftd/open-rail-cross-border/recordCorridorFlow.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-recordCorridorFlow-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-flagInteropFailure-v1',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'open_rail_cross_border_flag_interop_failure',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_rail_cross_border_flag_interop_failure" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-rail-cross-border" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_rail_cross_border_flag_interop_failure" '
                 'name="flagInteropFailure" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_rail_cross_border&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, failure_id: failureId, flow_vid: flowVid, '
                 'failure_kind: failureKind, delay_hours: delayHours, reported_at: reportedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-rail-cross-border&quot;}" target="values"/><zeebe:input '
                 'source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;did:web:open-rail-cross-border.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.railCrossBorder.flagInteropFailure&quot;" '
                 'target="action"/><zeebe:input source="={vertexId: vertexId}" '
                 'target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2331,
                 '00-contracts/bpmn/ai/gftd/open-rail-cross-border/flagInteropFailure.bpmn',
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-flagInteropFailure-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-recordMechanism-v1',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'app.etzhayyim.apps.electricityMarket.recordMechanism',
                 'open_electricity_market_record_mechanism',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-recordMechanism-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-flagMissingMoney-v1',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'app.etzhayyim.apps.electricityMarket.flagMissingMoney',
                 'open_electricity_market_flag_missing_money',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'did:web:open-electricity-market.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-flagMissingMoney-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-recordCrossBorderFlow-v1',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'app.etzhayyim.apps.powerGridInterconnect.recordCrossBorderFlow',
                 'open_power_grid_interconnect_record_cross_border_flow',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-recordCrossBorderFlow-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-flagCurtailment-v1',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'app.etzhayyim.apps.powerGridInterconnect.flagCurtailment',
                 'open_power_grid_interconnect_flag_curtailment',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'did:web:open-power-grid-interconnect.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-flagCurtailment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-recordBasinMetric-v1',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'app.etzhayyim.apps.waterScarcity.recordBasinMetric',
                 'open_water_scarcity_record_basin_metric',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-recordBasinMetric-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-flagTreatyDispute-v1',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'app.etzhayyim.apps.waterScarcity.flagTreatyDispute',
                 'open_water_scarcity_flag_treaty_dispute',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'did:web:open-water-scarcity.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-flagTreatyDispute-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-recordStewardshipPlan-v1',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'app.etzhayyim.apps.waterStewardship.recordStewardshipPlan',
                 'open_water_stewardship_record_stewardship_plan',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-recordStewardshipPlan-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-flagBasinStress-v1',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'app.etzhayyim.apps.waterStewardship.flagBasinStress',
                 'open_water_stewardship_flag_basin_stress',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'did:web:open-water-stewardship.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-flagBasinStress-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-registerFacility-v1',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'app.etzhayyim.apps.wastewaterReuse.registerFacility',
                 'open_wastewater_reuse_register_facility',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-registerFacility-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-recordMonitoringMetric-v1',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'app.etzhayyim.apps.wastewaterReuse.recordMonitoringMetric',
                 'open_wastewater_reuse_record_monitoring_metric',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'did:web:open-wastewater-reuse.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-recordMonitoringMetric-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-registerCable-v1',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'app.etzhayyim.apps.telecomInfra.registerCable',
                 'open_telecom_infra_register_cable',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-registerCable-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-flagCableFault-v1',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'app.etzhayyim.apps.telecomInfra.flagCableFault',
                 'open_telecom_infra_flag_cable_fault',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'did:web:open-telecom-infra.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-flagCableFault-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-registerDeployment-v1',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'app.etzhayyim.apps.ruralBroadband.registerDeployment',
                 'open_rural_broadband_register_deployment',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-registerDeployment-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-flagDigitalDivideGap-v1',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'app.etzhayyim.apps.ruralBroadband.flagDigitalDivideGap',
                 'open_rural_broadband_flag_digital_divide_gap',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'did:web:open-rural-broadband.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-flagDigitalDivideGap-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-recordCorridorFlow-v1',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'app.etzhayyim.apps.railCrossBorder.recordCorridorFlow',
                 'open_rail_cross_border_record_corridor_flow',
                 15000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-recordCorridorFlow-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-flagInteropFailure-v1',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'app.etzhayyim.apps.railCrossBorder.flagInteropFailure',
                 'open_rail_cross_border_flag_interop_failure',
                 30000,
                 '2026-04-27T07:30:00Z',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'did:web:open-rail-cross-border.etzhayyim.com',
                 'sys.bpmn.seed.extended-infra',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-flagInteropFailure-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-recordMechanism-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-electricity-market-flagMissingMoney-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-recordCrossBorderFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-power-grid-interconnect-flagCurtailment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-recordBasinMetric-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-scarcity-flagTreatyDispute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-recordStewardshipPlan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-water-stewardship-flagBasinStress-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-registerFacility-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-wastewater-reuse-recordMonitoringMetric-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-registerCable-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-telecom-infra-flagCableFault-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-registerDeployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rural-broadband-flagDigitalDivideGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-recordCorridorFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-rail-cross-border-flagInteropFailure-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-recordMechanism-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-electricity-market-flagMissingMoney-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-recordCrossBorderFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-power-grid-interconnect-flagCurtailment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-recordBasinMetric-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-scarcity-flagTreatyDispute-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-recordStewardshipPlan-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-water-stewardship-flagBasinStress-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-registerFacility-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-wastewater-reuse-recordMonitoringMetric-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-registerCable-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-telecom-infra-flagCableFault-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-registerDeployment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rural-broadband-flagDigitalDivideGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-recordCorridorFlow-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-rail-cross-border-flagInteropFailure-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
