"""Captured from Kysely migration 20260429200000_seed_open_adnetwork_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429200000_seed_open_adnetwork_bpmn_actors"
down_revision = 'r_20260429200000_add_yukkuri_video_cols'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-publisher-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_register_publisher',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_register_publisher" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_register_publisher" name="registerPublisher" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.registerPublisher", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save publisher">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_publisher&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.publisher/&quot; '
                 '+ publisherId, publisher_id: publisherId, domain: domain, owner_did: ownerDid, '
                 'revenue_share_pct: 70.0, floor_cpm_usd: floorCpmUsd, content_category: '
                 'contentCategory, ad_policy: &quot;standard&quot;, status: &quot;active&quot;, '
                 'created_at: string(now()), sensitivity_ord: 0, org_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.registerPublisher&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, publisherId: publisherId, '
                 'domain: domain}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2707,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/registerPublisher.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-publisher-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-publisher-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.registerPublisher',
                 'open_adnetwork_register_publisher',
                 30000,
                 'vertex_open_adnetwork_publisher',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-publisher-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_publisher',
                 'open_adnetwork_register_publisher',
                 'ai.gftd.apps.openAdnetwork.registerPublisher',
                 'vertex_open_adnetwork_publisher']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-ad-unit-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_record_ad_unit',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_record_ad_unit" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_record_ad_unit" name="recordAdUnit" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.recordAdUnit", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save ad unit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_ad_unit&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.adUnit/&quot; '
                 '+ unitId, unit_id: unitId, publisher_did: publisherDid, unit_type: unitType, '
                 'size: size, placement: placement, floor_cpm_usd: floorCpmUsd, '
                 'active_campaign_count: 0, status: &quot;active&quot;, created_at: string(now()), '
                 'sensitivity_ord: 0, org_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.recordAdUnit&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, unitId: unitId, '
                 'publisherDid: publisherDid, unitType: unitType}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2664,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/recordAdUnit.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-ad-unit-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-ad-unit-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.recordAdUnit',
                 'open_adnetwork_record_ad_unit',
                 30000,
                 'vertex_open_adnetwork_ad_unit',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-ad-unit-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_ad_unit',
                 'open_adnetwork_record_ad_unit',
                 'ai.gftd.apps.openAdnetwork.recordAdUnit',
                 'vertex_open_adnetwork_ad_unit']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-advertiser-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_register_advertiser',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_register_advertiser" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_register_advertiser" '
                 'name="registerAdvertiser" isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.registerAdvertiser", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save advertiser">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_advertiser&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.advertiser/&quot; '
                 '+ advertiserId, advertiser_id: advertiserId, brand_name: brandName, domain: '
                 'domain, industry_category: industryCategory, monthly_budget_usd: '
                 'monthlyBudgetUsd, payment_method: paymentMethod, status: &quot;active&quot;, '
                 'created_at: string(now()), sensitivity_ord: 0, org_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.registerAdvertiser&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, advertiserId: advertiserId, '
                 'brandName: brandName}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2713,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/registerAdvertiser.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-advertiser-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-advertiser-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.registerAdvertiser',
                 'open_adnetwork_register_advertiser',
                 30000,
                 'vertex_open_adnetwork_advertiser',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-advertiser-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_advertiser',
                 'open_adnetwork_register_advertiser',
                 'ai.gftd.apps.openAdnetwork.registerAdvertiser',
                 'vertex_open_adnetwork_advertiser']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-create-campaign-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_create_campaign',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_create_campaign" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_create_campaign" name="createCampaign" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.createCampaign", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save campaign">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_campaign&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.campaign/&quot; '
                 '+ campaignId, campaign_id: campaignId, advertiser_did: advertiserDid, name: '
                 'name, objective: objective, budget_daily_usd: budgetDailyUsd, bid_strategy: '
                 'bidStrategy, bid_floor_usd: bidFloorUsd, targeting_json: targetingJson, '
                 'start_date: startDate, end_date: endDate, status: &quot;draft&quot;, created_at: '
                 'string(now()), sensitivity_ord: 0, org_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.createCampaign&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, campaignId: campaignId, '
                 'advertiserDid: advertiserDid, objective: objective}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2788,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/createCampaign.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-create-campaign-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-create-campaign-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.createCampaign',
                 'open_adnetwork_create_campaign',
                 30000,
                 'vertex_open_adnetwork_campaign',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-create-campaign-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_campaign',
                 'open_adnetwork_create_campaign',
                 'ai.gftd.apps.openAdnetwork.createCampaign',
                 'vertex_open_adnetwork_campaign']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-impression-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_record_impression',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_record_impression" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_record_impression" name="recordImpression" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.recordImpression", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save impression">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_impression&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.impression/&quot; '
                 '+ impId, imp_id: impId, unit_id: unitId, campaign_id: campaignId, cpm_usd: '
                 'cpmUsd, viewable: viewable, user_cohort: userCohort, country_iso2: countryIso2, '
                 'ts_ms: tsMsVal, created_at: string(now()), sensitivity_ord: 0, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.recordImpression&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={impressionId: impressionId, campaignDid: '
                 'campaignDid, publisherDid: publisherDid, cpmUsd: cpmUsd}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2665,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/recordImpression.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-impression-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-impression-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.recordImpression',
                 'open_adnetwork_record_impression',
                 30000,
                 'vertex_open_adnetwork_impression',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-impression-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_impression',
                 'open_adnetwork_record_impression',
                 'ai.gftd.apps.openAdnetwork.recordImpression',
                 'vertex_open_adnetwork_impression']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-conversion-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_record_conversion',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_record_conversion" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_record_conversion" name="recordConversion" '
                 'isExecutable="true">\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.openAdnetwork.recordConversion", "version": 1, '
                 '"resultTimeoutMs": 30000 }\n'
                 '    </bpmn:documentation>\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save conversion">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_adnetwork_conversion&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.conversion/&quot; '
                 '+ convId, conv_id: convId, click_id: clickId, campaign_id: campaignId, '
                 'conv_type: if convType != null then convType else &quot;lead&quot;, '
                 'conv_value_usd: if convValueUsd != null then convValueUsd else 0.0, ts_ms: '
                 'tsMsVal, created_at: string(now()), sensitivity_ord: 0, actor_id: '
                 '&quot;sys.bpmn.open-adnetwork&quot;}" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.recordConversion&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={conversionId: conversionId, campaignDid: '
                 'campaignDid, impressionDid: impressionDid, convType: convType, convValue: '
                 'convValue}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2745,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/recordConversion.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-conversion-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-conversion-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.recordConversion',
                 'open_adnetwork_record_conversion',
                 30000,
                 'vertex_open_adnetwork_conversion',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-conversion-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_conversion',
                 'open_adnetwork_record_conversion',
                 'ai.gftd.apps.openAdnetwork.recordConversion',
                 'vertex_open_adnetwork_conversion']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-compute-publisher-rpm-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_compute_publisher_rpm',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — daily Publisher RPM snapshot.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. generic.db.select   — aggregate impressions + revenue per publisher\n'
                 '                             for the past 24h. Returns rows (all publishers\n'
                 '                             combined; see ADR-2604281900 §Limitations for\n'
                 '                             multi-publisher deferred work).\n'
                 '    2. generic.db.insert   — write a single aggregate revenue_snapshot row\n'
                 '                             (publisher_did = "__all__", date = today).\n'
                 '    3. generic.audit.emit  — OCEL event.\n'
                 '\n'
                 "  Note: SQL windowing uses NOW() - INTERVAL '1 day' (SQL-side expression)\n"
                 '  to avoid FEEL-in-SQL quoting issues (advisor 2026-04-28).\n'
                 '\n'
                 '  Cadence: R/P1D.\n'
                 '  ADR-2604281900. NSID: ai.gftd.apps.openAdnetwork.computePublisherRpm '
                 '(timer-start, no binding needed).\n'
                 '-->\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_compute_publisher_rpm" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_compute_publisher_rpm" '
                 'name="computePublisherRpm" isExecutable="true">\n'
                 '    <bpmn:startEvent id="StartManual" name="manual recompute">\n'
                 '      <bpmn:outgoing>Flow_ManualToSelect</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ManualToSelect" sourceRef="StartManual" '
                 'targetRef="Task_Select"/>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 1 day">\n'
                 '      <bpmn:outgoing>Flow_ToSelect</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P1D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSelect" sourceRef="Start" '
                 'targetRef="Task_Select"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select publisher impression stats '
                 '(24h)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;SELECT au.publisher_did, COUNT(*) AS '
                 'impressions, SUM(i.cpm_usd) / 1000.0 AS total_revenue FROM '
                 'vertex_open_adnetwork_impression i JOIN vertex_open_adnetwork_ad_unit au ON '
                 'au.unit_id = i.unit_id WHERE i.created_at &gt;= (NOW() - INTERVAL &apos;1 '
                 'day&apos;)::varchar GROUP BY au.publisher_did LIMIT 1000&quot;" '
                 'target="query"/>\n'
                 '          <zeebe:output source="=rows" target="publisherStats"/>\n'
                 '          <zeebe:output source="=rowCount" target="publisherCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSelect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToInsert</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToInsert" sourceRef="Task_Select" '
                 'targetRef="Task_Insert"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Insert" name="write aggregate revenue snapshot">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;vertex_open_adnetwork_revenue_snapshot&quot;" target="table"/>\n'
                 '          <zeebe:input source="={vertex_id: '
                 '&quot;at://did:web:open-adnetwork.etzhayyim.com/ai.gftd.apps.openAdnetwork.revenueSnapshot/&quot; '
                 '+ string(today()), snap_id: &quot;rpm-&quot; + string(today()), publisher_did: '
                 '&quot;__all__&quot;, date: string(today()), impressions: if publisherCount &gt; '
                 '0 then sum(publisherStats.impressions) else 0, clicks: 0, conversions: 0, '
                 'total_revenue_usd: if publisherCount &gt; 0 then '
                 'sum(publisherStats.total_revenue) else 0.0, rpm_usd: if publisherCount &gt; 0 '
                 'and sum(publisherStats.impressions) &gt; 0 then '
                 'sum(publisherStats.total_revenue) / sum(publisherStats.impressions) * 1000.0 '
                 'else 0.0, ctr_pct: 0.0, cvr_pct: 0.0, created_at: string(now()), '
                 'sensitivity_ord: 0, actor_id: &quot;sys.bpmn.open-adnetwork&quot;}" '
                 'target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToInsert</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Insert" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit computePublisherRpm">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;open.adnetwork.computePublisherRpm&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={date: string(today()), publisherCount: '
                 'publisherCount}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 5195,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/computePublisherRpm.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-compute-publisher-rpm-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-compute-publisher-rpm-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.computePublisherRpm',
                 'open_adnetwork_compute_publisher_rpm',
                 90000,
                 'vertex_open_adnetwork_revenue_snapshot',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-compute-publisher-rpm-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['vertex_open_adnetwork_revenue_snapshot',
                 'open_adnetwork_compute_publisher_rpm',
                 'ai.gftd.apps.openAdnetwork.computePublisherRpm',
                 'vertex_open_adnetwork_revenue_snapshot']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (\n'
         '      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '      actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, 1,\n'
         "      $4, CAST($5 AS integer), $6, 'active',\n"
         '      $7, 1, $8, $9, $10,\n'
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-fetch-auction-market-delta-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'open_adnetwork_fetch_auction_market_delta',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — weekly IAB benchmark fetch.\n'
                 '\n'
                 '  Pipeline:\n'
                 '    1. generic.http.fetch  — fetch IAB Measurement Benchmark H1 2024\n'
                 '                             (public PDF, used as market CPM reference).\n'
                 '    2. generic.audit.emit  — OCEL event with fetch status.\n'
                 '\n'
                 '  Cadence: R/P7D.\n'
                 '  ADR-2604281900.\n'
                 '-->\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_adnetwork_fetch_auction_market_delta" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-adnetwork" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_adnetwork_fetch_auction_market_delta" '
                 'name="fetchAuctionMarketDelta" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="every 7 days">\n'
                 '      <bpmn:outgoing>Flow_ToFetch</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToFetch" sourceRef="Start" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch IAB benchmark">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.http.fetch"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;https://www.iab.com/wp-content/uploads/2024/09/IABMeasurementBenchmark_H12024.pdf&quot;" '
                 'target="url"/>\n'
                 '          <zeebe:input source="=&quot;GET&quot;" target="method"/>\n'
                 '          <zeebe:output source="=status" target="fetchStatus"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToFetch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAudit</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAudit" sourceRef="Task_Fetch" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit fetchAuctionMarketDelta">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-adnetwork.etzhayyim.com&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input '
                 'source="=&quot;open.adnetwork.fetchAuctionMarketDelta&quot;" target="action"/>\n'
                 '          <zeebe:input source="={timestamp: string(now()), status: '
                 '&quot;fetched&quot;, fetchStatus: fetchStatus}" target="payload"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAudit</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2831,
                 '00-contracts/bpmn/ai/gftd/open-adnetwork/fetchAuctionMarketDelta.bpmn',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-fetch-auction-market-delta-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '      sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         '      CAST($5 AS integer), $6,\n'
         "      'active', $7, 1, $8, $9, $10,\n"
         "      $11, 'anon'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-fetch-auction-market-delta-v1',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'ai.gftd.apps.openAdnetwork.fetchAuctionMarketDelta',
                 'open_adnetwork_fetch_auction_market_delta',
                 90000,
                 '',
                 '2026-04-29T20:00:00+09:00',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'sys.bpmn.seed.open-adnetwork',
                 'did:web:open-adnetwork.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-fetch-auction-market-delta-v1']},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist = $1\n'
         '    WHERE bpmn_process_id = $2\n'
         '      AND nsid = $3\n'
         '      AND (write_table_allowlist IS NULL OR write_table_allowlist <> $4)\n'
         '  ',
  'parameters': ['',
                 'open_adnetwork_fetch_auction_market_delta',
                 'ai.gftd.apps.openAdnetwork.fetchAuctionMarketDelta',
                 '']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-publisher-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-publisher-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-ad-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-ad-unit-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-register-advertiser-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-register-advertiser-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-create-campaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-create-campaign-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-impression-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-impression-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-record-conversion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-record-conversion-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-compute-publisher-rpm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-compute-publisher-rpm-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-adnetwork-fetch-auction-market-delta-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-adnetwork-fetch-auction-market-delta-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
