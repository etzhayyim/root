"""Captured from Kysely migration 20260425172000_seed_pharma_supply_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260425172000_seed_pharma_supply_bpmn_actors"
down_revision = 'r_20260425172000_medical_coverage_ingest_targets'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-register-product-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'open_pharma_supply_register_product',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_pharma_supply_register_product" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-pharma-supply" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_pharma_supply_register_product" name="registerProduct" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_pharma_supply&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, product_id: productId, atc_code: atcCode, '
                 'ndc_code: ndcCode, ema_product_number: emaProductNumber, manufacturer_lei: '
                 'manufacturerLei, api_origin_iso3: apiOriginIso3, dosage_form: dosageForm, '
                 'registered_at: registeredAt, status: &quot;active&quot;, created_at: '
                 'string(now()), owner_did: callerDid, sensitivity_ord: 1, org_id: callerDid, '
                 'user_id: callerDid, actor_id: &quot;sys.bpmn.open-pharma-supply&quot;}" '
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
                 'source="=&quot;did:web:open-pharma-supply.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.pharmaSupply.registerProduct&quot;" '
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
                 2391,
                 '00-contracts/bpmn/ai/gftd/open-pharma-supply/registerProduct.bpmn',
                 '2026-04-25T17:20:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.pharma-supply',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-register-product-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-shortage-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'open_pharma_supply_flag_shortage',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                 'id="Definitions_open_pharma_supply_flag_shortage" '
                 'targetNamespace="https://etzhayyim.com/bpmn/open-pharma-supply" '
                 'exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_pharma_supply_flag_shortage" name="flagShortage" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '    <bpmn:serviceTask id="Task_Save" name="save">\n'
                 '      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping><zeebe:input '
                 'source="=&quot;vertex_open_pharma_supply&quot;" target="table"/><zeebe:input '
                 'source="={vertex_id: vertexId, shortage_id: shortageId, product_vid: productVid, '
                 'reporter: reporter, root_cause: rootCause, critical_mineral_vid: '
                 'criticalMineralVid, supply_chain_finance_vid: supplyChainFinanceVid, '
                 'estimated_restore_date: estimatedRestoreDate, flagged_at: flaggedAt, '
                 'severity_tier: if rootCause = &quot;api_shortage&quot; or rootCause = '
                 '&quot;mfg_disruption&quot; then &quot;high&quot; else if rootCause = '
                 '&quot;recall&quot; then &quot;critical&quot; else &quot;moderate&quot;, status: '
                 '&quot;active&quot;, created_at: string(now()), owner_did: callerDid, '
                 'sensitivity_ord: 1, org_id: callerDid, user_id: callerDid, actor_id: '
                 '&quot;sys.bpmn.open-pharma-supply&quot;}" target="values"/><zeebe:input '
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
                 'source="=&quot;did:web:open-pharma-supply.etzhayyim.com&quot;" '
                 'target="actor"/><zeebe:input '
                 'source="=&quot;open.pharmaSupply.flagShortage&quot;" '
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
                 2623,
                 '00-contracts/bpmn/ai/gftd/open-pharma-supply/flagShortage.bpmn',
                 '2026-04-25T17:20:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.pharma-supply',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-shortage-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-registerProduct-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'ai.gftd.apps.pharmaSupply.registerProduct',
                 'open_pharma_supply_register_product',
                 15000,
                 '2026-04-25T17:20:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.pharma-supply',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-registerProduct-v1']},
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagShortage-v1',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'ai.gftd.apps.pharmaSupply.flagShortage',
                 'open_pharma_supply_flag_shortage',
                 15000,
                 '2026-04-25T17:20:00Z',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'did:web:open-pharma-supply.etzhayyim.com:ops',
                 'sys.bpmn.seed.pharma-supply',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagShortage-v1']}]

DOWN = [{'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-registerProduct-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_lexicon_binding\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.binding/open-pharma-supply-flagShortage-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-register-product-v1']},
 {'sql': '\n      DELETE FROM vertex_bpmn_process_def\n      WHERE vertex_id = $1\n    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/open-pharma-supply-flag-shortage-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
