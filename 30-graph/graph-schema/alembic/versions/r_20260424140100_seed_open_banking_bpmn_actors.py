"""Captured from Kysely migration 20260424140100_seed_open_banking_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424140100_seed_open_banking_bpmn_actors"
down_revision = 'r_20260424140000_vertex_open_banking'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-create-account-v1',
                 'did:web:open-banking.gftd.ai:core',
                 'open_banking_create_account',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_banking_create_account"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-banking"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_banking_create_account" name="口座開設" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Save" name="account 保存">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_banking_account&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:       vertexId,\n'
                 '              owner_did:       ownerDid,\n'
                 '              account_number:  accountNumber,\n'
                 '              account_type:    accountType,\n'
                 '              currency:        currency,\n'
                 '              display_name:    displayName,\n'
                 '              status:          &quot;active&quot;,\n'
                 '              opened_at:       string(now()),\n'
                 '              created_at:      string(now()),\n'
                 '              sensitivity_ord: 2,\n'
                 '              org_id:          ownerDid,\n'
                 '              user_id:         ownerDid,\n'
                 '              actor_id:        &quot;sys.bpmn.open-banking&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit account.open">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-banking.gftd.ai:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openBanking.account.open&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={vertexId: vertexId, accountType: accountType, '
                 'currency: currency}" target="payload"/>\n'
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
                 2722,
                 '00-contracts/bpmn/ai/gftd/open-banking/createAccount.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-banking.gftd.ai:core',
                 'did:web:open-banking.gftd.ai:core',
                 'sys.bpmn.seed.open-banking',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-create-account-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def (vertex_id, owner_did, bpmn_process_id, version, '
         'xml, xml_byte_size, source_path, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         "    SELECT $1, $2, $3, 1, $4, CAST($5 AS integer), $6, 'active', $7, 1, $8, $9, $10\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $11)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-transfer-v1',
                 'did:web:open-banking.gftd.ai:core',
                 'open_banking_transfer',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_open_banking_transfer"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/open-banking"\n'
                 '    exporter="hand-written" exporterVersion="1.0">\n'
                 '  <bpmn:process id="open_banking_transfer" name="振替 (double-entry)" '
                 'isExecutable="true">\n'
                 '    <bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Debit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Debit" name="debit (from)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_banking_ledger_entry&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        string(transactionId) + &quot;:debit&quot;,\n'
                 '              account_vid:      fromAccountDid,\n'
                 '              transaction_id:   transactionId,\n'
                 '              direction:        &quot;debit&quot;,\n'
                 '              amount:           amount,\n'
                 '              currency:         currency,\n'
                 '              counterparty_vid: toAccountDid,\n'
                 '              memo:             memo,\n'
                 '              executed_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  2,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-banking&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_C</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_C" sourceRef="Task_Debit" '
                 'targetRef="Task_Credit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Credit" name="credit (to)">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;vertex_open_banking_ledger_entry&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              vertex_id:        string(transactionId) + &quot;:credit&quot;,\n'
                 '              account_vid:      toAccountDid,\n'
                 '              transaction_id:   transactionId,\n'
                 '              direction:        &quot;credit&quot;,\n'
                 '              amount:           amount,\n'
                 '              currency:         currency,\n'
                 '              counterparty_vid: fromAccountDid,\n'
                 '              memo:             memo,\n'
                 '              executed_at:      string(now()),\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  2,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-banking&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_C</bpmn:incoming><bpmn:outgoing>Flow_E</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_E" sourceRef="Task_Credit" '
                 'targetRef="Task_Edge"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Edge" name="transfer pair edge">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.insert"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;edge_open_banking_transfer_pair&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="={\n'
                 '              edge_id:          transactionId,\n'
                 '              src_vid:          string(transactionId) + &quot;:debit&quot;,\n'
                 '              dst_vid:          string(transactionId) + &quot;:credit&quot;,\n'
                 '              transaction_id:   transactionId,\n'
                 '              created_at:       string(now()),\n'
                 '              owner_did:        callerDid,\n'
                 '              sensitivity_ord:  2,\n'
                 '              org_id:           callerDid,\n'
                 '              user_id:          callerDid,\n'
                 '              actor_id:         &quot;sys.bpmn.open-banking&quot;\n'
                 '          }" target="values"/>\n'
                 '          <zeebe:input source="=&quot;ignore&quot;" target="onConflict"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      '
                 '<bpmn:incoming>Flow_E</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Edge" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="audit transfer.settled">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;did:web:open-banking.gftd.ai:core&quot;" '
                 'target="actor"/>\n'
                 '          <zeebe:input source="=&quot;openBanking.transfer.settled&quot;" '
                 'target="action"/>\n'
                 '          <zeebe:input source="={transactionId: transactionId, amount: amount, '
                 'currency: currency, fromAccountDid: fromAccountDid, toAccountDid: toAccountDid}" '
                 'target="payload"/>\n'
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
                 5476,
                 '00-contracts/bpmn/ai/gftd/open-banking/transfer.bpmn',
                 '2026-04-24T14:30:00Z',
                 'did:web:open-banking.gftd.ai:core',
                 'did:web:open-banking.gftd.ai:core',
                 'sys.bpmn.seed.open-banking',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-transfer-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-createAccount-v1',
                 'did:web:open-banking.gftd.ai:core',
                 'ai.gftd.apps.openBanking.createAccount',
                 'open_banking_create_account',
                 15000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-banking.gftd.ai:core',
                 'did:web:open-banking.gftd.ai:core',
                 'sys.bpmn.seed.open-banking',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-createAccount-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding (vertex_id, owner_did, nsid, '
         'bpmn_process_id, bpmn_version, result_timeout_ms, status, created_at, sensitivity_ord, '
         'org_id, user_id, actor_id)\n'
         "    SELECT $1, $2, $3, $4, 1, CAST($5 AS integer), 'active', $6, 1, $7, $8, $9\n"
         '    WHERE NOT EXISTS (SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $10)\n'
         '  ',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-transfer-v1',
                 'did:web:open-banking.gftd.ai:core',
                 'ai.gftd.apps.openBanking.transfer',
                 'open_banking_transfer',
                 30000,
                 '2026-04-24T14:30:00Z',
                 'did:web:open-banking.gftd.ai:core',
                 'did:web:open-banking.gftd.ai:core',
                 'sys.bpmn.seed.open-banking',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-transfer-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-createAccount-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/open-banking-transfer-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-create-account-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/open-banking-transfer-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
