"""Captured from Kysely migration 20260427074000_seed_pharma_policy_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427074000_seed_pharma_policy_bpmn_actors"
down_revision = 'r_20260427073000_seed_extended_infra_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_drug_price_negotiation (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      round_id           varchar,\n'
         '      regime_kind        varchar,\n'
         '      therapeutic_area   varchar,\n'
         '      pharma_company_lei varchar,\n'
         '      published_at       varchar,\n'
         '      flag_id            varchar,\n'
         '      round_vid          varchar,\n'
         '      gap_kind           varchar,\n'
         '      reported_at        varchar,\n'
         '      status             varchar,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_open_jp_mhlw (\n'
         '      vertex_id          varchar PRIMARY KEY,\n'
         '      _seq               bigint,\n'
         '      created_date       date,\n'
         '      sensitivity_ord    int,\n'
         '      owner_did          varchar,\n'
         '      action_id          varchar,\n'
         '      bureau             varchar,\n'
         '      action_kind        varchar,\n'
         '      related_actor_vid  varchar,\n'
         '      issued_at          varchar,\n'
         '      flag_id            varchar,\n'
         '      action_vid         varchar,\n'
         '      concern_kind       varchar,\n'
         '      reported_at        varchar,\n'
         '      status             varchar,\n'
         '      created_at         varchar,\n'
         '      org_id             varchar,\n'
         '      user_id            varchar,\n'
         '      actor_id           varchar\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-recordRound-v1',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'open_drug_price_negotiation_record_round',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_drug_price_negotiation_record_round" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-drug-price-negotiation" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_drug_price_negotiation_record_round" name="recordRound" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_drug_price_negotiation&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, round_id: roundId, '
                 'regime_kind: regimeKind, therapeutic_area: therapeuticArea, pharma_company_lei: '
                 'pharmaCompanyLei, published_at: publishedAt, status: &quot;active&quot;, '
                 'created_at: string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: '
                 'callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-drug-price-negotiation&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-drug-price-negotiation.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.drugPriceNegotiation.recordRound&quot;" '
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
                 2361,
                 '00-contracts/bpmn/ai/gftd/open-drug-price-negotiation/recordRound.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-recordRound-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-flagAccessGap-v1',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'open_drug_price_negotiation_flag_access_gap',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_drug_price_negotiation_flag_access_gap" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-drug-price-negotiation" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_drug_price_negotiation_flag_access_gap" '
                 'name="flagAccessGap" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_drug_price_negotiation&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, flag_id: flagId, '
                 'round_vid: roundVid, gap_kind: gapKind, reported_at: reportedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-drug-price-negotiation&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-drug-price-negotiation.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.drugPriceNegotiation.flagAccessGap&quot;" '
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
                 2309,
                 '00-contracts/bpmn/ai/gftd/open-drug-price-negotiation/flagAccessGap.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-flagAccessGap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-recordAction-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'open_jp_mhlw_record_action',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_jp_mhlw_record_action" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-jp-mhlw" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jp_mhlw_record_action" name="recordAction" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_jp_mhlw&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, action_id: actionId, '
                 'bureau: bureau, action_kind: actionKind, related_actor_vid: relatedActorVid, '
                 'issued_at: issuedAt, status: &quot;active&quot;, created_at: string(now()), '
                 'owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, '
                 'actor_id: &quot;sys.bpmn.open-jp-mhlw&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-jp-mhlw.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.jpMhlw.recordAction&quot;" target="action"/><zeebe:input '
                 'source="={vertexId: vertexId}" target="payload"/></zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>',
                 2236,
                 '00-contracts/bpmn/ai/gftd/open-jp-mhlw/recordAction.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-recordAction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-flagPolicyConcern-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'open_jp_mhlw_flag_policy_concern',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_jp_mhlw_flag_policy_concern" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-jp-mhlw" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jp_mhlw_flag_policy_concern" name="flagPolicyConcern" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_jp_mhlw&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, flag_id: flagId, '
                 'action_vid: actionVid, concern_kind: concernKind, reported_at: reportedAt, '
                 'status: &quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-jp-mhlw&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-jp-mhlw.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.jpMhlw.flagPolicyConcern&quot;" '
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
                 2231,
                 '00-contracts/bpmn/ai/gftd/open-jp-mhlw/flagPolicyConcern.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-flagPolicyConcern-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-regulateNarcotics-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'open_jp_mhlw_regulate_narcotics',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_jp_mhlw_regulate_narcotics" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-jp-mhlw" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jp_mhlw_regulate_narcotics" name="regulateNarcotics" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_jp_mhlw&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, action_id: actionId, '
                 'bureau: &quot;longTermCare&quot;, action_kind: &quot;narcoticsControl&quot;, '
                 'related_actor_vid: relatedActorVid, issued_at: issuedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-jp-mhlw&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-jp-mhlw.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.jpMhlw.regulateNarcotics&quot;" '
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
                 '</bpmn:definitions>\n',
                 2293,
                 '00-contracts/bpmn/ai/gftd/open-jp-mhlw/regulateNarcotics.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-regulateNarcotics-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      bpmn_process_id,\n'
         '      version,\n'
         '      xml,\n'
         '      xml_byte_size,\n'
         '      source_path,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      1,\n'
         '      $4,\n'
         '      CAST($5 AS integer),\n'
         '      $6,\n'
         "      'active',\n"
         '      $7,\n'
         '      1,\n'
         '      $8,\n'
         '      $9,\n'
         '      $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-administerInfluenzaVaccine-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'open_jp_mhlw_administer_influenza_vaccine',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_jp_mhlw_administer_influenza_vaccine" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-jp-mhlw" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_jp_mhlw_administer_influenza_vaccine" '
                 'name="administerInfluenzaVaccine" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input source="=&quot;vertex_open_jp_mhlw&quot;" '
                 'target="table"/><zeebe:input source="={vertex_id: vertexId, action_id: actionId, '
                 'bureau: &quot;longTermCare&quot;, action_kind: &quot;influenzaVaccine&quot;, '
                 'related_actor_vid: relatedActorVid, issued_at: issuedAt, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-jp-mhlw&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-jp-mhlw.etzhayyim.com&quot;" target="actor"/><zeebe:input '
                 'source="=&quot;open.jpMhlw.administerInfluenzaVaccine&quot;" '
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
                 '</bpmn:definitions>\n',
                 2331,
                 '00-contracts/bpmn/ai/gftd/open-jp-mhlw/administerInfluenzaVaccine.bpmn',
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-administerInfluenzaVaccine-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-recordRound-v1',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'app.etzhayyim.apps.drugPriceNegotiation.recordRound',
                 'open_drug_price_negotiation_record_round',
                 15000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-recordRound-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-flagAccessGap-v1',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'app.etzhayyim.apps.drugPriceNegotiation.flagAccessGap',
                 'open_drug_price_negotiation_flag_access_gap',
                 30000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'did:web:open-drug-price-negotiation.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-flagAccessGap-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-recordAction-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'app.etzhayyim.apps.jpMhlw.recordAction',
                 'open_jp_mhlw_record_action',
                 15000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-recordAction-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-flagPolicyConcern-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'app.etzhayyim.apps.jpMhlw.flagPolicyConcern',
                 'open_jp_mhlw_flag_policy_concern',
                 30000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-flagPolicyConcern-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-regulateNarcotics-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'app.etzhayyim.apps.jpMhlw.regulateNarcotics',
                 'open_jp_mhlw_regulate_narcotics',
                 15000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-regulateNarcotics-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id,\n'
         '      owner_did,\n'
         '      nsid,\n'
         '      bpmn_process_id,\n'
         '      bpmn_version,\n'
         '      result_timeout_ms,\n'
         '      status,\n'
         '      created_at,\n'
         '      sensitivity_ord,\n'
         '      org_id,\n'
         '      user_id,\n'
         '      actor_id\n'
         '    )\n'
         '    SELECT\n'
         '      $1,\n'
         '      $2,\n'
         '      $3,\n'
         '      $4,\n'
         '      1,\n'
         '      CAST($5 AS integer),\n'
         "      'active',\n"
         '      $6,\n'
         '      1,\n'
         '      $7,\n'
         '      $8,\n'
         '      $9\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-administerInfluenzaVaccine-v1',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'app.etzhayyim.apps.jpMhlw.administerInfluenzaVaccine',
                 'open_jp_mhlw_administer_influenza_vaccine',
                 15000,
                 '2026-04-27T07:40:00Z',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'did:web:open-jp-mhlw.etzhayyim.com',
                 'sys.bpmn.seed.pharma-policy',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-administerInfluenzaVaccine-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-recordRound-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-drug-price-negotiation-flagAccessGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-recordAction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-flagPolicyConcern-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-regulateNarcotics-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.binding/open-jp-mhlw-administerInfluenzaVaccine-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-recordRound-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-drug-price-negotiation-flagAccessGap-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-recordAction-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-flagPolicyConcern-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-regulateNarcotics-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.processDef/open-jp-mhlw-administerInfluenzaVaccine-v1']},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_jp_mhlw', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_open_drug_price_negotiation', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
