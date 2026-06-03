"""Captured from Kysely migration 20260507155400_seed_gov_svk_bpmn_mcp_registry."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507155400_seed_gov_svk_bpmn_mcp_registry"
down_revision = 'r_20260507155300_seed_gov_sur_bpmn_mcp_registry'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seedOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_seed_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_seed_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_seed_orgs" name="govSvk seed orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="seed requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Seed"/>\n'
                 '    <bpmn:serviceTask id="Task_Seed" name="seed orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.seedOrgs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/seedOrgs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seedOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-registerDIDs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_register_dids"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_register_dids" name="govSvk register DIDs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="registration requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register DIDs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.registerDIDs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/registerDIDs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-registerDIDs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-followSiteDeps-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_follow_site_deps',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_follow_site_deps"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_follow_site_deps" name="govSvk follow site deps" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="follow requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Follow"/>\n'
                 '    <bpmn:serviceTask id="Task_Follow" name="follow site deps">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.followSiteDeps"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/followSiteDeps.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-followSiteDeps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolveOrgPath-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_resolve_org_path',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_resolve_org_path"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_resolve_org_path" name="govSvk resolve org path" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="resolve requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Resolve"/>\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="resolve org path">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.resolveOrgPath"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/resolveOrgPath.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolveOrgPath-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-listOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_list_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_list_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_list_orgs" name="govSvk list orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="list requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_List"/>\n'
                 '    <bpmn:serviceTask id="Task_List" name="list orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.listOrgs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/listOrgs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-listOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-syncWetUpdates-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_sync_wet_updates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_sync_wet_updates"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_sync_wet_updates" name="govSvk sync wet updates" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sync requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Sync"/>\n'
                 '    <bpmn:serviceTask id="Task_Sync" name="sync wet updates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.syncWetUpdates"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/syncWetUpdates.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-syncWetUpdates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-shinka-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_shinka',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_shinka"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_shinka" name="govSvk shinka" isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="shinka requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Shinka"/>\n'
                 '    <bpmn:serviceTask id="Task_Shinka" name="shinka">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.shinka"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/shinka.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-shinka-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeatTick-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_heartbeat_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_gov_svk_heartbeat_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_heartbeat_tick" name="govSvk heartbeat tick" '
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
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.heartbeatTick"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/heartbeatTick.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeatTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seed-orgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_seed_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_seed_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_seed_orgs" name="govSvk seed orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="seed requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Seed"/>\n'
                 '    <bpmn:serviceTask id="Task_Seed" name="seed orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.seedOrgs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/seedOrgs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seed-orgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-register-dids-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_register_dids',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_register_dids"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_register_dids" name="govSvk register DIDs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="registration requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Register"/>\n'
                 '    <bpmn:serviceTask id="Task_Register" name="register DIDs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.registerDIDs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/registerDIDs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-register-dids-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-follow-site-deps-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_follow_site_deps',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_follow_site_deps"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_follow_site_deps" name="govSvk follow site deps" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="follow requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Follow"/>\n'
                 '    <bpmn:serviceTask id="Task_Follow" name="follow site deps">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.followSiteDeps"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/followSiteDeps.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-follow-site-deps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolve-org-path-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_resolve_org_path',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_resolve_org_path"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_resolve_org_path" name="govSvk resolve org path" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="resolve requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" '
                 'targetRef="Task_Resolve"/>\n'
                 '    <bpmn:serviceTask id="Task_Resolve" name="resolve org path">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.resolveOrgPath"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/resolveOrgPath.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolve-org-path-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-list-orgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_list_orgs',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_list_orgs"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_list_orgs" name="govSvk list orgs" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="list requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_List"/>\n'
                 '    <bpmn:serviceTask id="Task_List" name="list orgs">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.listOrgs"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/listOrgs.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-list-orgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-sync-wet-updates-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_sync_wet_updates',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_gov_svk_sync_wet_updates"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_sync_wet_updates" name="govSvk sync wet updates" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent id="Start" name="sync requested">\n'
                 '      <bpmn:outgoing>Flow_Task</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Sync"/>\n'
                 '    <bpmn:serviceTask id="Task_Sync" name="sync wet updates">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.syncWetUpdates"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/syncWetUpdates.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-sync-wet-updates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeat-tick-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'gov_svk_heartbeat_tick',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_gov_svk_heartbeat_tick"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/govSvk"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="1.0">\n'
                 '  <bpmn:process id="gov_svk_heartbeat_tick" name="govSvk heartbeat tick" '
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
                 '        <zeebe:taskDefinition type="xrpc.com.etzhayyim.govSvk.heartbeatTick"/>\n'
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
                 '00-contracts/bpmn/com/etzhayyim/govSvk/heartbeatTick.bpmn',
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeat-tick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.seedOrgs',
                 'gov_svk_seed_orgs',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.registerDIDs',
                 'gov_svk_register_dids',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 'gov_svk_follow_site_deps',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 'gov_svk_resolve_org_path',
                 60000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.listOrgs',
                 'gov_svk_list_orgs',
                 60000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 'gov_svk_sync_wet_updates',
                 180000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-shinka-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.shinka',
                 'gov_svk_shinka',
                 180000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-shinka-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 'gov_svk_heartbeat_tick',
                 180000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.seedOrgs',
                 'gov_svk_seed_orgs',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.registerDIDs',
                 'gov_svk_register_dids',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 'gov_svk_follow_site_deps',
                 90000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 'gov_svk_resolve_org_path',
                 60000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.listOrgs',
                 'gov_svk_list_orgs',
                 60000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 'gov_svk_sync_wet_updates',
                 180000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1',
                 'did:web:svk-state.etzhayyim.com',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 'gov_svk_heartbeat_tick',
                 180000,
                 '2026-05-07T15:54:00Z',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 'vertex_gov_org,edge_gov_org_site_dependency',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs',
                 'com.etzhayyim.govSvk.seedOrgs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Seed initial Slovakia government organization records into the graph.',
                 '{"properties":{"limit":{"default":50,"maximum":200,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"remaining":{"type":"integer"},"seeded":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.seedOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/seedOrgs.json',
                 '256725b4e5f09062',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs',
                 'com.etzhayyim.govSvk.registerDIDs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Register DIDs for Slovakia government organizations.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"dids":{"items":{"type":"string"},"type":"array"},"ok":{"type":"boolean"},"registered":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.registerDIDs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/registerDIDs.json',
                 'b2e1c977ad73b8c5',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Follow site dependency actors for Slovakia government.',
                 '{"properties":{"limit":{"default":15,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/followSiteDeps.json',
                 'd7070a037290c0e5',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'query',
                 'Resolve a Slovakia government organization path to its graph record.',
                 '{"properties":{"lang":{"type":"string"},"path":{"type":"string"}},"required":["path"],"type":"params"}',
                 '{"properties":{"did":{"type":"string"},"error":{"type":"string"},"name":{"type":"string"},"nameEn":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/resolveOrgPath.json',
                 '813437517a7a7194',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs',
                 'com.etzhayyim.govSvk.listOrgs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'query',
                 'List Slovakia government organization graph records.',
                 '{"properties":{"limit":{"default":50,"maximum":100,"minimum":1,"type":"integer"},"offset":{"default":0,"minimum":0,"type":"integer"},"q":{"type":"string"}},"required":[],"type":"params"}',
                 '{"properties":{"orgs":{"items":{"properties":{"did":{"type":"string"},"name":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"},"type":"array"},"total":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.listOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/listOrgs.json',
                 'a2fc055a4e203341',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Sync recent Slovakia government organization changes to graph.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"checked":{"type":"integer"},"ok":{"type":"boolean"},"posted":{"type":"integer"},"updated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/syncWetUpdates.json',
                 '965896eb383ccb85',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-shinka',
                 'com.etzhayyim.govSvk.shinka',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Post a periodic graph-visible Slovakia government organization update.',
                 '{"properties":{"limit":{"default":1,"maximum":5,"minimum":1,"type":"integer"},"postUpdates":{"default":true,"type":"boolean"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"posted":{"type":"integer"},"touched":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.shinka',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/shinka.json',
                 '3e3c6eba18df5b8d',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-shinka']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Run the Slovakia government actor scheduled maintenance loop through Zeebe.',
                 '{"properties":{"followLimit":{"default":15,"maximum":50,"minimum":1,"type":"integer"},"ingestLimit":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"registerLimit":{"default":10,"maximum":50,"minimum":1,"type":"integer"},"seedLimit":{"default":30,"maximum":100,"minimum":1,"type":"integer"},"shinkaLimit":{"default":1,"maximum":5,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"},"registered":{"type":"integer"},"seeded":{"type":"integer"},"shinkaPosted":{"type":"integer"},"wetUpdated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/heartbeatTick.json',
                 '526f1c91cf8e2ef6',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs',
                 'com.etzhayyim.govSvk.seedOrgs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Seed initial Slovakia government organization records into the graph.',
                 '{"properties":{"limit":{"default":50,"maximum":200,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"ok":{"type":"boolean"},"remaining":{"type":"integer"},"seeded":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.seedOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/seedOrgs.json',
                 '256725b4e5f09062',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs',
                 'com.etzhayyim.govSvk.registerDIDs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Register DIDs for Slovakia government organizations.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"dids":{"items":{"type":"string"},"type":"array"},"ok":{"type":"boolean"},"registered":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.registerDIDs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/registerDIDs.json',
                 'b2e1c977ad73b8c5',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Follow site dependency actors for Slovakia government.',
                 '{"properties":{"limit":{"default":15,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.followSiteDeps',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/followSiteDeps.json',
                 'd7070a037290c0e5',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'query',
                 'Resolve a Slovakia government organization path to its graph record.',
                 '{"properties":{"lang":{"type":"string"},"path":{"type":"string"}},"required":["path"],"type":"params"}',
                 '{"properties":{"did":{"type":"string"},"error":{"type":"string"},"name":{"type":"string"},"nameEn":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.resolveOrgPath',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/resolveOrgPath.json',
                 '813437517a7a7194',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs',
                 'com.etzhayyim.govSvk.listOrgs',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'query',
                 'List Slovakia government organization graph records.',
                 '{"properties":{"limit":{"default":50,"maximum":100,"minimum":1,"type":"integer"},"offset":{"default":0,"minimum":0,"type":"integer"},"q":{"type":"string"}},"required":[],"type":"params"}',
                 '{"properties":{"orgs":{"items":{"properties":{"did":{"type":"string"},"name":{"type":"string"},"website":{"type":"string"}},"required":[],"type":"object"},"type":"array"},"total":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.listOrgs',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/listOrgs.json',
                 'a2fc055a4e203341',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Sync recent Slovakia government organization changes to graph.',
                 '{"properties":{"limit":{"default":10,"maximum":50,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"checked":{"type":"integer"},"ok":{"type":"boolean"},"posted":{"type":"integer"},"updated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.syncWetUpdates',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/syncWetUpdates.json',
                 '965896eb383ccb85',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates']},
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
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 'did:web:svk-state.etzhayyim.com',
                 'svk-state.etzhayyim.com',
                 'procedure',
                 'Run the Slovakia government actor scheduled maintenance loop through Zeebe.',
                 '{"properties":{"followLimit":{"default":15,"maximum":50,"minimum":1,"type":"integer"},"ingestLimit":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"registerLimit":{"default":10,"maximum":50,"minimum":1,"type":"integer"},"seedLimit":{"default":30,"maximum":100,"minimum":1,"type":"integer"},"shinkaLimit":{"default":1,"maximum":5,"minimum":1,"type":"integer"}},"required":[],"type":"object"}',
                 '{"properties":{"followed":{"type":"integer"},"ok":{"type":"boolean"},"registered":{"type":"integer"},"seeded":{"type":"integer"},"shinkaPosted":{"type":"integer"},"wetUpdated":{"type":"integer"}},"required":[],"type":"object"}',
                 'com.etzhayyim.govSvk.heartbeatTick',
                 '00-contracts/lexicons/com/etzhayyim/govSvk/heartbeatTick.json',
                 '526f1c91cf8e2ef6',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'did:web:svk-state.etzhayyim.com',
                 'sys.bpmn.seed.gov-svk',
                 '2026-05-07T15:54:00Z',
                 'at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick']}]

DOWN = [{'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-shinka']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-seedOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-registerDIDs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-followSiteDeps']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-resolveOrgPath']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-listOrgs']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-syncWetUpdates']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:svk-state.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-govSvk-heartbeatTick']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-shinka-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-govSvk-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seedOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-registerDIDs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-followSiteDeps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolveOrgPath-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-listOrgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-syncWetUpdates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-shinka-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeatTick-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-seed-orgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-register-dids-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-follow-site-deps-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-resolve-org-path-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-list-orgs-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-sync-wet-updates-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/gov-svk-heartbeat-tick-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
