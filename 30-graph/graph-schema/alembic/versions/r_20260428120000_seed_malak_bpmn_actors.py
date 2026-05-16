"""Captured from Kysely migration 20260428120000_seed_malak_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428120000_seed_malak_bpmn_actors"
down_revision = 'r_20260428100100_seed_telecom_npn_bpmn_actors'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-threat-actor-v1',
                 'did:web:malak.gftd.ai',
                 'malak_register_threat_actor',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.registerThreatActor — migrates cmdRegisterThreatActor.\n'
                 '\n'
                 '  Replaces sdk.pds.createRecord("ai.gftd.apps.malak.threatActor") with\n'
                 '  Hyperdrive-direct INSERT into vertex_threat (ADR-0036).\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (name, actorId?, aliases?, nationality?, motivation?,\n'
                 '           ttps?, confidence?, tlp?, description?)\n'
                 '      → scriptTask: derive rkey + vertexId\n'
                 '      → generic.db.insert (vertex_threat)\n'
                 '      → generic.audit.emit\n'
                 '      → End\n'
                 '\n'
                 '  NSID derivation (sync-bpmn-actors.py convention):\n'
                 '    path = 00-contracts/bpmn/ai/gftd/malak/registerThreatActor.bpmn\n'
                 '    NSID = ai.gftd.apps.malak.registerThreatActor\n'
                 '    vid  = '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-threat-actor-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_register_threat_actor"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_register_threat_actor" name="malak '
                 'registerThreatActor" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.registerThreatActor", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToDerive</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDerive" sourceRef="Start" '
                 'targetRef="Task_Derive"/>\n'
                 '\n'
                 '    <!-- Step 1: derive rkey + vertexId.\n'
                 '         actorId is optional — fall back to timestamp-based unique key. -->\n'
                 '    <bpmn:scriptTask id="Task_Derive" name="derive rkey + vertexId">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:script\n'
                 '            expression=\'=if actorId = null or string(actorId) = "" then { rkey: '
                 'string join(["actor-", replace(string(now()), ":", "-")], ""), actorCode: string '
                 'join(["actor-", replace(string(now()), ":", "-")], "") } else { rkey: '
                 "string(actorId), actorCode: string(actorId) }'\n"
                 '            resultVariable="derived"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDerive</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToInsert</bpmn:outgoing>\n'
                 '    </bpmn:scriptTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToInsert" sourceRef="Task_Derive" '
                 'targetRef="Task_Insert"/>\n'
                 '\n'
                 '    <!-- Step 2: INSERT into vertex_threat (Hyperdrive-direct, ADR-0036) -->\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="vertex_threat INSERT">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_threat&quot;" target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '              vertex_id:       string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.threatActor/", '
                 'derived.rkey], ""),\n'
                 '              rkey:            derived.rkey,\n'
                 '              repo:            "did:web:malak.gftd.ai",\n'
                 '              did:             "did:web:malak.gftd.ai",\n'
                 '              code:            derived.actorCode,\n'
                 '              label:           "ThreatActor",\n'
                 '              name:            string(name),\n'
                 '              display_name:    string(name),\n'
                 '              description:     if description = null then "" else '
                 'string(description),\n'
                 '              category:        "actor",\n'
                 '              severity:        if confidence = null then "medium" else (if '
                 'confidence >= 0.8 then "high" else if confidence >= 0.5 then "medium" else '
                 '"low"),\n'
                 '              source:          "malak.bpmn.register",\n'
                 '              sensitivity_ord: 100,\n'
                 '              owner_did:       "did:web:malak.gftd.ai",\n'
                 '              created_date:    substring(string(now()), 1, 10)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="threatInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <!-- Step 3: OCEL audit -->\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit: malak.actor.created">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:malak.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;malak.actor.created&quot;"   '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ actorId: derived.actorCode, name: '
                 'string(name), threatInserted: threatInserted }" target="payload"/>\n'
                 '          <zeebe:output source="=emitted" target="auditEmitted"/>\n'
                 '          <zeebe:output source="=rkey"    target="auditRkey"/>\n'
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
                 5151,
                 '00-contracts/bpmn/ai/gftd/malak/registerThreatActor.bpmn',
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-threat-actor-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-create-threat-org-v1',
                 'did:web:malak.gftd.ai',
                 'malak_create_threat_org',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.createThreatOrg — migrates cmdCreateThreatOrg.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (slug, name, orgType?, country?, description?, tlp?)\n'
                 '      → generic.db.insert (vertex_threat, category="org")\n'
                 '      → generic.audit.emit\n'
                 '      → End\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.createThreatOrg\n'
                 '  vid:  '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-create-threat-org-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_create_threat_org"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_create_threat_org" name="malak createThreatOrg" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.createThreatOrg", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToInsert</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToInsert" sourceRef="Start" '
                 'targetRef="Task_Insert"/>\n'
                 '\n'
                 '    <!-- Step 1: INSERT org into vertex_threat (label=ThreatOrg, category=org) '
                 '-->\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="vertex_threat INSERT (org)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_threat&quot;" target="table"/>\n'
                 "          <zeebe:input source='={\n"
                 '              vertex_id:       string '
                 'join(["at://did:web:malak.gftd.ai/ai.gftd.apps.malak.threatOrg/", string(slug)], '
                 '""),\n'
                 '              rkey:            string(slug),\n'
                 '              repo:            "did:web:malak.gftd.ai",\n'
                 '              did:             "did:web:malak.gftd.ai",\n'
                 '              code:            string join(["org-", string(slug)], ""),\n'
                 '              label:           "ThreatOrg",\n'
                 '              name:            string(name),\n'
                 '              display_name:    string(name),\n'
                 '              description:     if description = null then "" else '
                 'string(description),\n'
                 '              category:        if orgType = null then "cybercrime" else '
                 'string(orgType),\n'
                 '              url:             if country = null then "" else string '
                 'join(["country:", string(country)], ""),\n'
                 '              source:          "malak.bpmn.create-org",\n'
                 '              sensitivity_ord: 100,\n'
                 '              owner_did:       "did:web:malak.gftd.ai",\n'
                 '              created_date:    substring(string(now()), 1, 10)\n'
                 '          }\' target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '          <zeebe:output source="=inserted" target="orgInserted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit: malak.org.created">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:malak.gftd.ai&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;malak.org.created&quot;"     '
                 'target="action"/>\n'
                 '          <zeebe:input source="={ slug: string(slug), name: string(name), '
                 'orgInserted: orgInserted }" target="payload"/>\n'
                 '          <zeebe:output source="=emitted" target="auditEmitted"/>\n'
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
                 3893,
                 '00-contracts/bpmn/ai/gftd/malak/createThreatOrg.bpmn',
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-create-threat-org-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-threat-actors-v1',
                 'did:web:malak.gftd.ai',
                 'malak_list_threat_actors',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.listThreatActors — migrates cmdListThreatActors.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (limit?, offset?)\n'
                 '      → generic.db.select (vertex_threat WHERE repo=malak.gftd.ai ORDER BY '
                 'created_date DESC)\n'
                 '      → End\n'
                 '\n'
                 '  Output: { rows: [...], rowCount: N }  — callers read variables.rows\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.listThreatActors\n'
                 '  vid:  '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-threat-actors-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_list_threat_actors"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_list_threat_actors" name="malak listThreatActors" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.listThreatActors", "version": 1, '
                 '"resultTimeoutMs": 10000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToSelect</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSelect" sourceRef="Start" '
                 'targetRef="Task_Select"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select threat actors">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_threat&quot;"                         target="table"/>\n'
                 '          <zeebe:input source="=&quot;repo = %s AND label = '
                 '%s&quot;"              target="whereExpr"/>\n'
                 '          <zeebe:input source=\'=["did:web:malak.gftd.ai", '
                 '"ThreatActor"]\'          target="whereParams"/>\n'
                 '          <zeebe:input source="=if limit = null then 50 else if limit > 100 then '
                 '100 else limit" target="limit"/>\n'
                 '          <zeebe:input source="=&quot;created_date '
                 'DESC&quot;"                     target="orderBy"/>\n'
                 '          <zeebe:output source="=rows"     target="rows"/>\n'
                 '          <zeebe:output source="=rowCount" target="rowCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSelect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Select" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2425,
                 '00-contracts/bpmn/ai/gftd/malak/listThreatActors.bpmn',
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-threat-actors-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-query-risk-chain-v1',
                 'did:web:malak.gftd.ai',
                 'malak_query_risk_chain',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.queryRiskChain — migrates cmdQueryRiskChain.\n'
                 '\n'
                 '  Query: ThreatActor → CONTROLS_WALLET → WalletAddress → BlockchainActor → '
                 'RiskSignal\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (address, chain?)\n'
                 '      → scriptTask: derive chainNodeId\n'
                 '      → generic.db.select (vertex_blockchain_actor WHERE address=?)\n'
                 '      → generic.db.select (vertex_risk_signal WHERE target_node_id=?)\n'
                 '      → End\n'
                 '\n'
                 '  Output variables: { blockchainRows, riskRows, chainNodeId, address, chain }\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.queryRiskChain\n'
                 '  vid:  '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-query-risk-chain-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_query_risk_chain"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_query_risk_chain" name="malak queryRiskChain" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.queryRiskChain", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToDerive</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToDerive" sourceRef="Start" '
                 'targetRef="Task_Derive"/>\n'
                 '\n'
                 '    <!-- Step 1: derive chainNodeId = "bchain:{chain}:{address}" -->\n'
                 '    <bpmn:scriptTask id="Task_Derive" name="derive chainNodeId">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:script\n'
                 '            expression=\'=string join(["bchain:", if chain = null then "btc" '
                 'else string(chain), ":", string(address)], "")\'\n'
                 '            resultVariable="chainNodeId"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToDerive</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToBlockchain</bpmn:outgoing>\n'
                 '    </bpmn:scriptTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToBlockchain" sourceRef="Task_Derive" '
                 'targetRef="Task_SelectBlockchain"/>\n'
                 '\n'
                 '    <!-- Step 2: BlockchainActor for this address -->\n'
                 '    <bpmn:serviceTask id="Task_SelectBlockchain" name="select blockchain '
                 'actor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_blockchain_actor&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;address = %s&quot;"            '
                 'target="whereExpr"/>\n'
                 '          <zeebe:input source="=[string(address)]"                   '
                 'target="whereParams"/>\n'
                 '          <zeebe:input source="=1"                                   '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=rows"     target="blockchainRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="blockchainCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToBlockchain</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToRisk</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRisk" sourceRef="Task_SelectBlockchain" '
                 'targetRef="Task_SelectRisk"/>\n'
                 '\n'
                 '    <!-- Step 3: RiskSignals targeting this chain node -->\n'
                 '    <bpmn:serviceTask id="Task_SelectRisk" name="select risk signals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_risk_signal&quot;"      '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;target_node_id = %s&quot;"     '
                 'target="whereExpr"/>\n'
                 '          <zeebe:input source="=[chainNodeId]"                       '
                 'target="whereParams"/>\n'
                 '          <zeebe:input source="=20"                                  '
                 'target="limit"/>\n'
                 '          <zeebe:input source="=&quot;detected_at DESC&quot;"        '
                 'target="orderBy"/>\n'
                 '          <zeebe:output source="=rows"     target="riskRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="riskCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRisk</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_SelectRisk" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 4238,
                 '00-contracts/bpmn/ai/gftd/malak/queryRiskChain.bpmn',
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-query-risk-chain-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-threat-graph-v1',
                 'did:web:malak.gftd.ai',
                 'malak_get_threat_graph',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.getThreatGraph — migrates cmdGetThreatGraph.\n'
                 '\n'
                 '  Fetches ThreatActor node + associated RiskSignals.\n'
                 '  Note: WalletAddress correlation is deferred (vertex_malak_wallet_address\n'
                 '  table not yet in schema; will be added in a follow-up migration).\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (actorId)\n'
                 '      → generic.db.select (vertex_threat WHERE code=actorId)\n'
                 '      → generic.db.select (vertex_risk_signal WHERE chain IS NOT NULL LIMIT 20)\n'
                 '      → End\n'
                 '\n'
                 '  Output variables: { actorRows, riskRows }\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.getThreatGraph\n'
                 '  vid:  '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-threat-graph-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_get_threat_graph"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_get_threat_graph" name="malak getThreatGraph" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.getThreatGraph", "version": 1, '
                 '"resultTimeoutMs": 15000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToActor</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToActor" sourceRef="Start" '
                 'targetRef="Task_SelectActor"/>\n'
                 '\n'
                 '    <!-- Step 1: fetch ThreatActor node (code column = actorId) -->\n'
                 '    <bpmn:serviceTask id="Task_SelectActor" name="select threat actor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_threat&quot;"               '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;repo = %s AND code = %s&quot;"     '
                 'target="whereExpr"/>\n'
                 '          <zeebe:input source=\'=["did:web:malak.gftd.ai", string(actorId)]\' '
                 'target="whereParams"/>\n'
                 '          <zeebe:input source="=1"                                        '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=rows"     target="actorRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="actorCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToActor</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToRisk</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToRisk" sourceRef="Task_SelectActor" '
                 'targetRef="Task_SelectRisk"/>\n'
                 '\n'
                 '    <!-- Step 2: fetch recent blockchain RiskSignals (chain IS NOT NULL = '
                 'blockchain signals) -->\n'
                 '    <bpmn:serviceTask id="Task_SelectRisk" name="select blockchain risk '
                 'signals">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_risk_signal&quot;"      '
                 'target="table"/>\n'
                 '          <zeebe:input source="=&quot;chain IS NOT NULL&quot;"        '
                 'target="whereExpr"/>\n'
                 '          <zeebe:input source="=[]"                                   '
                 'target="whereParams"/>\n'
                 '          <zeebe:input source="=20"                                   '
                 'target="limit"/>\n'
                 '          <zeebe:input source="=&quot;detected_at DESC&quot;"         '
                 'target="orderBy"/>\n'
                 '          <zeebe:output source="=rows"     target="riskRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="riskCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToRisk</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_SelectRisk" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3700,
                 '00-contracts/bpmn/ai/gftd/malak/getThreatGraph.bpmn',
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-threat-graph-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerThreatActor-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.registerThreatActor',
                 'malak_register_threat_actor',
                 15000,
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerThreatActor-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-createThreatOrg-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.createThreatOrg',
                 'malak_create_threat_org',
                 15000,
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-createThreatOrg-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listThreatActors-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.listThreatActors',
                 'malak_list_threat_actors',
                 10000,
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listThreatActors-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-queryRiskChain-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.queryRiskChain',
                 'malak_query_risk_chain',
                 15000,
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-queryRiskChain-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getThreatGraph-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.getThreatGraph',
                 'malak_get_threat_graph',
                 15000,
                 '2026-04-28T12:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getThreatGraph-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerThreatActor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-createThreatOrg-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listThreatActors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-queryRiskChain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getThreatGraph-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-threat-actor-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-create-threat-org-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-threat-actors-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-query-risk-chain-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-threat-graph-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
