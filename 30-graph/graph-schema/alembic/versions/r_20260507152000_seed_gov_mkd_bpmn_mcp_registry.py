"""Captured from Kysely migration 20260507152000_seed_gov_mkd_bpmn_mcp_registry."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507152000_seed_gov_mkd_bpmn_mcp_registry"
down_revision = 'r_20260507151900_seed_gov_mhl_bpmn_mcp_registry'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seedOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_seed_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_seed_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_seed_orgs" name="govMkd seed orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="seed requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Seed"/>\n'
                 '    <bpmn:serviceTask id="Task_Seed" name="seed orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.seedOrgs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=seeded" target="seeded"/>\n'
                 '          <zeebe:output source="=remaining" target="remaining"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Seed" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="seeded">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1361,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/seedOrgs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seedOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-registerDIDs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_register_dids"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_register_dids" name="govMkd register DIDs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="registration requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register DIDs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.registerDIDs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=registered" target="registered"/>\n'
                 '          <zeebe:output source="=dids" target="dids"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Register" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="registered">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1403,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/registerDIDs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-registerDIDs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-followSiteDeps-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_follow_site_deps',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_follow_site_deps"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_follow_site_deps" name="govMkd follow site deps" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="follow requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Follow"/>\n'
                 '    <bpmn:serviceTask id="Task_Follow" name="follow site deps">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.followSiteDeps"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=followed" target="followed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Follow" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="followed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1344,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/followSiteDeps.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-followSiteDeps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolveOrgPath-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_resolve_org_path',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_resolve_org_path"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_resolve_org_path" name="govMkd resolve org path" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="resolve requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Resolve"/>\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="resolve org path">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.resolveOrgPath"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=did" target="did"/>\n'
                 '          <zeebe:output source="=name" target="name"/>\n'
                 '          <zeebe:output source="=nameEn" target="nameEn"/>\n'
                 '          <zeebe:output source="=website" target="website"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Resolve" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="resolved">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1519,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/resolveOrgPath.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolveOrgPath-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-listOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_list_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_list_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_list_orgs" name="govMkd list orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="list requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_List"/>\n'
                 '    <bpmn:serviceTask id="Task_List" name="list orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.listOrgs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=orgs" target="orgs"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="listed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1298,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/listOrgs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-listOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-syncWetUpdates-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_sync_wet_updates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_sync_wet_updates"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_sync_wet_updates" name="govMkd sync wet updates" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sync requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Sync"/>\n'
                 '    <bpmn:serviceTask id="Task_Sync" name="sync wet updates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.syncWetUpdates"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=checked" target="checked"/>\n'
                 '          <zeebe:output source="=updated" target="updated"/>\n'
                 '          <zeebe:output source="=posted" target="posted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Sync" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="synced">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1452,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/syncWetUpdates.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-syncWetUpdates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-shinka-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_shinka',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_shinka"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_shinka" name="govMkd shinka" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="shinka requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Shinka"/>\n'
                 '    <bpmn:serviceTask id="Task_Shinka" name="shinka">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.shinka"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=posted" target="posted"/>\n'
                 '          <zeebe:output source="=touched" target="touched"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Shinka" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="posted">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1351,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/shinka.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-shinka-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeatTick-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_heartbeat_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_gov_mkd_heartbeat_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_heartbeat_tick" name="govMkd heartbeat tick" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="ManualStart" name="manual dispatch">\n'
                 '      <bpmn:outgoing>Flow_Manual_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start" name="15 minute tick">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_15m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual_Task" sourceRef="ManualStart" '
                 'targetRef="Task_Tick"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Tick"/>\n'
                 '    <bpmn:serviceTask id="Task_Tick" name="heartbeat tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.heartbeatTick"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=seeded" target="seeded"/>\n'
                 '          <zeebe:output source="=registered" target="registered"/>\n'
                 '          <zeebe:output source="=followed" target="followed"/>\n'
                 '          <zeebe:output source="=wetUpdated" target="wetUpdated"/>\n'
                 '          <zeebe:output source="=shinkaPosted" target="shinkaPosted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Manual_Task</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Tick" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2098,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/heartbeatTick.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeatTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seed-orgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_seed_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_seed_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_seed_orgs" name="govMkd seed orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="seed requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Seed"/>\n'
                 '    <bpmn:serviceTask id="Task_Seed" name="seed orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.seedOrgs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=seeded" target="seeded"/>\n'
                 '          <zeebe:output source="=remaining" target="remaining"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Seed" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="seeded">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1361,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/seedOrgs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seed-orgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-register-dids-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_register_dids"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_register_dids" name="govMkd register DIDs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="registration requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register DIDs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.registerDIDs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=registered" target="registered"/>\n'
                 '          <zeebe:output source="=dids" target="dids"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Register" '
                 'targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="registered">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1403,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/registerDIDs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-register-dids-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-follow-site-deps-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_follow_site_deps',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_follow_site_deps"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_follow_site_deps" name="govMkd follow site deps" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="follow requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Follow"/>\n'
                 '    <bpmn:serviceTask id="Task_Follow" name="follow site deps">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.followSiteDeps"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=followed" target="followed"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Follow" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="followed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1344,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/followSiteDeps.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-follow-site-deps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolve-org-path-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_resolve_org_path',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_resolve_org_path"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_resolve_org_path" name="govMkd resolve org path" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="resolve requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Resolve"/>\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="resolve org path">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.resolveOrgPath"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=did" target="did"/>\n'
                 '          <zeebe:output source="=name" target="name"/>\n'
                 '          <zeebe:output source="=nameEn" target="nameEn"/>\n'
                 '          <zeebe:output source="=website" target="website"/>\n'
                 '          <zeebe:output source="=error" target="error"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Resolve" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="resolved">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1519,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/resolveOrgPath.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolve-org-path-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-list-orgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_list_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_list_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_list_orgs" name="govMkd list orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="list requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_List"/>\n'
                 '    <bpmn:serviceTask id="Task_List" name="list orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.listOrgs"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=orgs" target="orgs"/>\n'
                 '          <zeebe:output source="=total" target="total"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="listed">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1298,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/listOrgs.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-list-orgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-sync-wet-updates-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_sync_wet_updates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_mkd_sync_wet_updates"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_sync_wet_updates" name="govMkd sync wet updates" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sync requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Sync"/>\n'
                 '    <bpmn:serviceTask id="Task_Sync" name="sync wet updates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.syncWetUpdates"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=checked" target="checked"/>\n'
                 '          <zeebe:output source="=updated" target="updated"/>\n'
                 '          <zeebe:output source="=posted" target="posted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Sync" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="synced">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1452,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/syncWetUpdates.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-sync-wet-updates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeat-tick-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'gov_mkd_heartbeat_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_gov_mkd_heartbeat_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govMkd"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_mkd_heartbeat_tick" name="govMkd heartbeat tick" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="ManualStart" name="manual dispatch">\n'
                 '      <bpmn:outgoing>Flow_Manual_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:startEvent id="Start" name="15 minute tick">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_15m">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Manual_Task" sourceRef="ManualStart" '
                 'targetRef="Task_Tick"/>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Tick"/>\n'
                 '    <bpmn:serviceTask id="Task_Tick" name="heartbeat tick">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govMkd.heartbeatTick"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=ok" target="ok"/>\n'
                 '          <zeebe:output source="=seeded" target="seeded"/>\n'
                 '          <zeebe:output source="=registered" target="registered"/>\n'
                 '          <zeebe:output source="=followed" target="followed"/>\n'
                 '          <zeebe:output source="=wetUpdated" target="wetUpdated"/>\n'
                 '          <zeebe:output source="=shinkaPosted" target="shinkaPosted"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_Manual_Task</bpmn:incoming>\n'
                 '      <bpmn:incoming>Flow_Task</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Tick" targetRef="End"/>\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_End</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2098,
                 '00-contracts/bpmn/com/etzhayyim/govMkd/heartbeatTick.bpmn',
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeat-tick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.seedOrgs',
                 'gov_mkd_seed_orgs',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.registerDIDs',
                 'gov_mkd_register_dids',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 'gov_mkd_follow_site_deps',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 'gov_mkd_resolve_org_path',
                 60000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.listOrgs',
                 'gov_mkd_list_orgs',
                 60000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 'gov_mkd_sync_wet_updates',
                 180000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-shinka-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.shinka',
                 'gov_mkd_shinka',
                 180000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-shinka-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 'gov_mkd_heartbeat_tick',
                 180000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.seedOrgs',
                 'gov_mkd_seed_orgs',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.registerDIDs',
                 'gov_mkd_register_dids',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 'gov_mkd_follow_site_deps',
                 90000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 'gov_mkd_resolve_org_path',
                 60000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.listOrgs',
                 'gov_mkd_list_orgs',
                 60000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 'gov_mkd_sync_wet_updates',
                 180000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, write_table_allowlist\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, 1,\n'
         "      CAST($5 AS integer), 'active', $6, 1,\n"
         '      $7, $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1',
                 'did:web:mkd-state.etzhayyim.com',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 'gov_mkd_heartbeat_tick',
                 180000,
                 '2026-05-07T15:20:00Z',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs',
                 'com.etzhayyim.govMkd.seedOrgs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Seed initial North Macedonia government organization records into the graph.',
                 '{"properties":{"limit":{"default":50,"maximum":200,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"remaining":{"type":"integer"},"seeded":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.seedOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/seedOrgs.json',
                 '06c7aaf9e60ca873',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs',
                 'com.etzhayyim.govMkd.registerDIDs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Register DIDs for North Macedonia government organizations.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"dids":{"items":{"type":"string"},"type":"array"},"ok":{"type":"boolean"},"registered":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.registerDIDs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/registerDIDs.json',
                 'b0eb81cc31b972ed',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Follow site dependency actors for North Macedonia government.',
                 '{"properties":{"limit":{"default":15,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/followSiteDeps.json',
                 '58659d6d168880ee',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'query',
                 'Resolve a North Macedonia government organization path to its graph record.',
                 '{"properties":{"lang":{"type":"string"},"path":{"type":"string"}},"required":["path"],"type":"params"}',
                 '{"properties":{"did":{"type":"string"},"error":{"type":"string"},"name":{"type":"string"},"nameEn":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/resolveOrgPath.json',
                 '83a9921ccb6a4d16',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs',
                 'com.etzhayyim.govMkd.listOrgs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'query',
                 'List North Macedonia government organization graph records.',
                 '{"properties":{"limit":{"default":50,"maximum":100,"minimum":1,"type":"integer"},"offset":{"default":0,"minimum":0,"type":"integer"},"q":{"type":"string"}},"required":[],"type":"params"}',
                 '{"properties":{"orgs":{"items":{"properties":{"did":{"type":"string"},"name":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"},"type":"array"},"total":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.listOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/listOrgs.json',
                 '383754cbb7949845',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Sync recent North Macedonia government organization changes to graph.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"checked":{"type":"integer"},"ok":{"type":"boolean"},"posted":{"type":"integer"},"updated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/syncWetUpdates.json',
                 'd513a6ccf6952d6d',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-shinka',
                 'com.etzhayyim.govMkd.shinka',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Post a periodic graph-visible North Macedonia government organization update.',
                 '{"properties":{"limit":{"default":1,"maximum":5,"minimum":1,"type":"integer"},"postUpdates":{"default":true,"type":"boolean"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"posted":{"type":"integer"},"touched":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.shinka',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/shinka.json',
                 '2d3a3ea8c5139815',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-shinka']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Run the North Macedonia government actor scheduled maintenance loop through '
                 'Zeebe.',
                 '{"properties":{"followLimit":{"default":15,"maximum":50,"minimum":1,"type":"integer"},"ingestLimit":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"registerLimit":{"default":10,"maximum":50,"minimum":1,"type":"integer"},"seedLimit":{"default":30,"maximum":100,"minimum":1,"type":"integer"},"shinkaLimit":{"default":1,"maximum":5,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"},"registered":{"type":"integer"},"seeded":{"type":"integer"},"shinkaPosted":{"type":"integer"},"wetUpdated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/heartbeatTick.json',
                 '11f4928d00cb1506',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs',
                 'com.etzhayyim.govMkd.seedOrgs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Seed initial North Macedonia government organization records into the graph.',
                 '{"properties":{"limit":{"default":50,"maximum":200,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"remaining":{"type":"integer"},"seeded":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.seedOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/seedOrgs.json',
                 '06c7aaf9e60ca873',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs',
                 'com.etzhayyim.govMkd.registerDIDs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Register DIDs for North Macedonia government organizations.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"dids":{"items":{"type":"string"},"type":"array"},"ok":{"type":"boolean"},"registered":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.registerDIDs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/registerDIDs.json',
                 'b0eb81cc31b972ed',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Follow site dependency actors for North Macedonia government.',
                 '{"properties":{"limit":{"default":15,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.followSiteDeps',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/followSiteDeps.json',
                 '58659d6d168880ee',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'query',
                 'Resolve a North Macedonia government organization path to its graph record.',
                 '{"properties":{"lang":{"type":"string"},"path":{"type":"string"}},"required":["path"],"type":"params"}',
                 '{"properties":{"did":{"type":"string"},"error":{"type":"string"},"name":{"type":"string"},"nameEn":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.resolveOrgPath',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/resolveOrgPath.json',
                 '83a9921ccb6a4d16',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs',
                 'com.etzhayyim.govMkd.listOrgs',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'query',
                 'List North Macedonia government organization graph records.',
                 '{"properties":{"limit":{"default":50,"maximum":100,"minimum":1,"type":"integer"},"offset":{"default":0,"minimum":0,"type":"integer"},"q":{"type":"string"}},"required":[],"type":"params"}',
                 '{"properties":{"orgs":{"items":{"properties":{"did":{"type":"string"},"name":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"},"type":"array"},"total":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.listOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/listOrgs.json',
                 '383754cbb7949845',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Sync recent North Macedonia government organization changes to graph.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"checked":{"type":"integer"},"ok":{"type":"boolean"},"posted":{"type":"integer"},"updated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.syncWetUpdates',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/syncWetUpdates.json',
                 'd513a6ccf6952d6d',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates']},
 {'sql': '\n'
         '    INSERT INTO vertex_mcp_tool_def (\n'
         '      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '      input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '      actor_id, created_at\n'
         '    )\n'
         '    SELECT\n'
         '      $1, $2, $3, $4, $5,\n'
         '      $6, $7, $8, $9,\n'
         "      'public', 1, TRUE, $10, $11, $12, 1,\n"
         '      $13, $14, $15, $16\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 'did:web:mkd-state.etzhayyim.com',
                 'mkd-state.etzhayyim.com',
                 'procedure',
                 'Run the North Macedonia government actor scheduled maintenance loop through '
                 'Zeebe.',
                 '{"properties":{"followLimit":{"default":15,"maximum":50,"minimum":1,"type":"integer"},"ingestLimit":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"registerLimit":{"default":10,"maximum":50,"minimum":1,"type":"integer"},"seedLimit":{"default":30,"maximum":100,"minimum":1,"type":"integer"},"shinkaLimit":{"default":1,"maximum":5,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"},"registered":{"type":"integer"},"seeded":{"type":"integer"},"shinkaPosted":{"type":"integer"},"wetUpdated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govMkd.heartbeatTick',
                 '00-contracts/lexicons/com/etzhayyim/govMkd/heartbeatTick.json',
                 '11f4928d00cb1506',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'did:web:mkd-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-mkd',
                 '2026-05-07T15:20:00Z',
                 'at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick']}]

DOWN = [{'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-shinka']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-seedOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-registerDIDs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-followSiteDeps']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-resolveOrgPath']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-listOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-syncWetUpdates']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:mkd-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govMkd-heartbeatTick']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-shinka-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govMkd-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-shinka-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-seed-orgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-follow-site-deps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-resolve-org-path-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-list-orgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-sync-wet-updates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-mkd-heartbeat-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
