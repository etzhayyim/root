"""Captured from Kysely migration 20260506330000_seed_malak_remaining_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260506330000_seed_malak_remaining_bpmn"
down_revision = 'r_20260506320000_seed_resource_flow_query_bpmn'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-build-agency-referral-evidence-bundle-v1',
                 'did:web:malak.gftd.ai',
                 'malak_build_agency_referral_evidence_bundle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_build_agency_referral_evidence_bundle" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_build_agency_referral_evidence_bundle" name="malak '
                 'buildAgencyReferralEvidenceBundle" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="buildAgencyReferralEvidenceBundle">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.buildAgencyReferralEvidenceBundle"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1148,
                 '00-contracts/bpmn/ai/gftd/malak/buildAgencyReferralEvidenceBundle.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-build-agency-referral-evidence-bundle-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-agency-referral-package-v1',
                 'did:web:malak.gftd.ai',
                 'malak_export_agency_referral_package',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_export_agency_referral_package" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_export_agency_referral_package" name="malak '
                 'exportAgencyReferralPackage" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="exportAgencyReferralPackage">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.exportAgencyReferralPackage"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1116,
                 '00-contracts/bpmn/ai/gftd/malak/exportAgencyReferralPackage.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-agency-referral-package-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-stix-bundle-v1',
                 'did:web:malak.gftd.ai',
                 'malak_export_stix_bundle',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_export_stix_bundle" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_export_stix_bundle" name="malak exportStixBundle" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="exportStixBundle">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.exportStixBundle"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1059,
                 '00-contracts/bpmn/ai/gftd/malak/exportStixBundle.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-stix-bundle-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-ingest-trap-message-v1',
                 'did:web:malak.gftd.ai',
                 'malak_ingest_trap_message',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_ingest_trap_message" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_ingest_trap_message" name="malak ingestTrapMessage" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="ingestTrapMessage">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.ingestTrapMessage"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1064,
                 '00-contracts/bpmn/ai/gftd/malak/ingestTrapMessage.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-ingest-trap-message-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-drafts-v1',
                 'did:web:malak.gftd.ai',
                 'malak_list_agency_referral_drafts',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_list_agency_referral_drafts" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_list_agency_referral_drafts" name="malak '
                 'listAgencyReferralDrafts" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="listAgencyReferralDrafts">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.listAgencyReferralDrafts"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1101,
                 '00-contracts/bpmn/ai/gftd/malak/listAgencyReferralDrafts.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-drafts-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-exports-v1',
                 'did:web:malak.gftd.ai',
                 'malak_list_agency_referral_exports',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_list_agency_referral_exports" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_list_agency_referral_exports" name="malak '
                 'listAgencyReferralExports" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="listAgencyReferralExports">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.listAgencyReferralExports"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/ai/gftd/malak/listAgencyReferralExports.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-exports-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-wallets-v1',
                 'did:web:malak.gftd.ai',
                 'malak_list_wallets',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_list_wallets" targetNamespace="https://gftd.ai/bpmn/malak" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_list_wallets" name="malak listWallets" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="listWallets">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.listWallets"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1032,
                 '00-contracts/bpmn/ai/gftd/malak/listWallets.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-wallets-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-phishing-trap-inbox-v1',
                 'did:web:malak.gftd.ai',
                 'malak_register_phishing_trap_inbox',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_register_phishing_trap_inbox" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_register_phishing_trap_inbox" name="malak '
                 'registerPhishingTrapInbox" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="registerPhishingTrapInbox">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.registerPhishingTrapInbox"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/ai/gftd/malak/registerPhishingTrapInbox.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-phishing-trap-inbox-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-review-agency-referral-draft-v1',
                 'did:web:malak.gftd.ai',
                 'malak_review_agency_referral_draft',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_malak_review_agency_referral_draft" '
                 'targetNamespace="https://gftd.ai/bpmn/malak" exporter="hand-written" '
                 'exporterVersion="1.0">\n'
                 '  <bpmn:process id="malak_review_agency_referral_draft" name="malak '
                 'reviewAgencyReferralDraft" isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Run"/>\n'
                 '    <bpmn:serviceTask id="Task_Run" name="reviewAgencyReferralDraft">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.malak.reviewAgencyReferralDraft"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Run" targetRef="End"/>\n'
                 '    <bpmn:endEvent '
                 'id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 1106,
                 '00-contracts/bpmn/ai/gftd/malak/reviewAgencyReferralDraft.bpmn',
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-review-agency-referral-draft-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-buildAgencyReferralEvidenceBundle-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.buildAgencyReferralEvidenceBundle',
                 'malak_build_agency_referral_evidence_bundle',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-buildAgencyReferralEvidenceBundle-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportAgencyReferralPackage-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.exportAgencyReferralPackage',
                 'malak_export_agency_referral_package',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportAgencyReferralPackage-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportStixBundle-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.exportStixBundle',
                 'malak_export_stix_bundle',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportStixBundle-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-ingestTrapMessage-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.ingestTrapMessage',
                 'malak_ingest_trap_message',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-ingestTrapMessage-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralDrafts-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.listAgencyReferralDrafts',
                 'malak_list_agency_referral_drafts',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralDrafts-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralExports-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.listAgencyReferralExports',
                 'malak_list_agency_referral_exports',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralExports-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listWallets-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.listWallets',
                 'malak_list_wallets',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listWallets-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerPhishingTrapInbox-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.registerPhishingTrapInbox',
                 'malak_register_phishing_trap_inbox',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerPhishingTrapInbox-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-reviewAgencyReferralDraft-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.reviewAgencyReferralDraft',
                 'malak_review_agency_referral_draft',
                 30000,
                 '2026-05-06T23:30:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak-remaining',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-reviewAgencyReferralDraft-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-buildAgencyReferralEvidenceBundle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportAgencyReferralPackage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-exportStixBundle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-ingestTrapMessage-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralDrafts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listAgencyReferralExports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-listWallets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-registerPhishingTrapInbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-reviewAgencyReferralDraft-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-build-agency-referral-evidence-bundle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-agency-referral-package-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-export-stix-bundle-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-ingest-trap-message-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-drafts-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-agency-referral-exports-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-list-wallets-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-register-phishing-trap-inbox-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-review-agency-referral-draft-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
