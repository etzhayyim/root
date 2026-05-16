"""Captured from Kysely migration 20260507450000_seed_business_manager_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507450000_seed_business_manager_bpmn"
down_revision = 'r_20260507441000_vertex_edge_bunken'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-health-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_health',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_health" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="health"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.health" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 706,
                 '00-contracts/bpmn/ai/gftd/business-manager/health.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-health-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.health',
                 'business_manager_health',
                 30000,
                 '',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-health-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-describe-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_describe',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_describe" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="describe"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.describe" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 712,
                 '00-contracts/bpmn/ai/gftd/business-manager/describe.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-describe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-describe-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.describe',
                 'business_manager_describe',
                 30000,
                 '',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-describe-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-wave-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_wave',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_wave" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="wave"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.wave" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 700,
                 '00-contracts/bpmn/ai/gftd/business-manager/wave.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-wave-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-wave-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.wave',
                 'business_manager_wave',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-wave-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-echo-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_echo',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_echo" isExecutable="true"><bpmn:startEvent id="start" '
                 '/><bpmn:serviceTask id="task" '
                 'name="echo"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.echo" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 700,
                 '00-contracts/bpmn/ai/gftd/business-manager/echo.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-echo-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-echo-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.echo',
                 'business_manager_echo',
                 30000,
                 '',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-echo-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-journal-entry-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_create_journal_entry',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_create_journal_entry" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="createJournalEntry"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.createJournalEntry" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 744,
                 '00-contracts/bpmn/ai/gftd/business-manager/createJournalEntry.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-journal-entry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-journal-entry-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.createJournalEntry',
                 'business_manager_create_journal_entry',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-journal-entry-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-invoice-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_create_invoice',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_create_invoice" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="createInvoice"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.createInvoice" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 728,
                 '00-contracts/bpmn/ai/gftd/business-manager/createInvoice.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-invoice-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-invoice-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.createInvoice',
                 'business_manager_create_invoice',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-invoice-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-record-payment-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_record_payment',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_record_payment" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="recordPayment"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.recordPayment" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 728,
                 '00-contracts/bpmn/ai/gftd/business-manager/recordPayment.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-record-payment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-record-payment-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.recordPayment',
                 'business_manager_record_payment',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-record-payment-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-register-employee-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_register_employee',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_register_employee" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="registerEmployee"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.registerEmployee" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 737,
                 '00-contracts/bpmn/ai/gftd/business-manager/registerEmployee.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-register-employee-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-register-employee-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.registerEmployee',
                 'business_manager_register_employee',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-register-employee-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-purchase-order-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_create_purchase_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_create_purchase_order" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="createPurchaseOrder"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.createPurchaseOrder" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 747,
                 '00-contracts/bpmn/ai/gftd/business-manager/createPurchaseOrder.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-purchase-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-purchase-order-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.createPurchaseOrder',
                 'business_manager_create_purchase_order',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-purchase-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-approve-purchase-order-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_approve_purchase_order',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_approve_purchase_order" '
                 'isExecutable="true"><bpmn:startEvent id="start" /><bpmn:serviceTask id="task" '
                 'name="approvePurchaseOrder"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.approvePurchaseOrder" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 750,
                 '00-contracts/bpmn/ai/gftd/business-manager/approvePurchaseOrder.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-approve-purchase-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-approve-purchase-order-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.approvePurchaseOrder',
                 'business_manager_approve_purchase_order',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-approve-purchase-order-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-allocate-budget-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_allocate_budget',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_allocate_budget" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="allocateBudget"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.allocateBudget" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 731,
                 '00-contracts/bpmn/ai/gftd/business-manager/allocateBudget.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-allocate-budget-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-allocate-budget-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.allocateBudget',
                 'business_manager_allocate_budget',
                 30000,
                 'vertex_business_manager_journal_entry,vertex_business_manager_invoice,vertex_business_manager_payment,vertex_business_manager_employee,vertex_business_manager_purchase_order,vertex_business_manager_budget_allocation,edge_business_manager_invoice_payment',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-allocate-budget-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord,\n'
         '        org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, 1,\n'
         "        $4, CAST($5 AS integer), $6, 'active',\n"
         '        $7, 100, $8, $9, $10,\n'
         "        $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-coverage-stats-v1',
                 'did:web:business-manager.gftd.ai',
                 'business_manager_coverage_stats',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'targetNamespace="https://gftd.ai/bpmn/business-manager"><bpmn:process '
                 'id="business_manager_coverage_stats" isExecutable="true"><bpmn:startEvent '
                 'id="start" /><bpmn:serviceTask id="task" '
                 'name="coverageStats"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="xrpc.ai.gftd.apps.businessManager.coverageStats" '
                 '/></bpmn:extensionElements></bpmn:serviceTask><bpmn:endEvent id="end" '
                 '/><bpmn:sequenceFlow id="flow_start_task" sourceRef="start" targetRef="task" '
                 '/><bpmn:sequenceFlow id="flow_task_end" sourceRef="task" targetRef="end" '
                 '/></bpmn:process></bpmn:definitions>\n',
                 728,
                 '00-contracts/bpmn/ai/gftd/business-manager/coverageStats.bpmn',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-coverage-stats-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        $5, $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-coverage-stats-v1',
                 'did:web:business-manager.gftd.ai',
                 'ai.gftd.apps.businessManager.coverageStats',
                 'business_manager_coverage_stats',
                 30000,
                 '',
                 '2026-05-07T02:05:00Z',
                 'did:web:business-manager.gftd.ai',
                 'did:web:business-manager.gftd.ai',
                 'sys.bpmn.seed.business-manager',
                 'did:web:business-manager.gftd.ai',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-coverage-stats-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-health-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-describe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-describe-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-wave-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-wave-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-echo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-echo-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-journal-entry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-journal-entry-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-invoice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-invoice-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-record-payment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-record-payment-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-register-employee-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-register-employee-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-create-purchase-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-create-purchase-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-approve-purchase-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-approve-purchase-order-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-allocate-budget-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-allocate-budget-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/business-manager-coverage-stats-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/business-manager-coverage-stats-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
