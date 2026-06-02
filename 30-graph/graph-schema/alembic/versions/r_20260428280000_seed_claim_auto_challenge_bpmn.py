"""Captured from Kysely migration 20260428280000_seed_claim_auto_challenge_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428280000_seed_claim_auto_challenge_bpmn"
down_revision = 'r_20260428280000_fix_maps_timer_bpmn_start_events'
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
         "      'sys.bpmn.seed.claim_auto_challenge'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $10\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-auto-challenge-v1',
                 'did:web:claim-consumer.etzhayyim.com',
                 'claim_auto_challenge',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  Timer-start BPMN — claim unchallenged sweep (every 1 hour).\n'
                 '  Finds expired unchallenged pending claims → calls claimUnchallenged() '
                 'on-chain\n'
                 '  via the claim-consumer Python Zeebe actor + authz '
                 '/internal/claim-unchallenged-sweep.\n'
                 '  Emits OCEL alarm when Murakumo fraud signal exists but no challenger stepped '
                 'up\n'
                 '  (triple-witness mismatch, ADR-2604261717 Phase 4 / ADR-0046 simplified).\n'
                 '\n'
                 '  NSID: com.etzhayyim.apps.claim.unchallengedSweep\n'
                 '  vertex_id: '
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-auto-challenge-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_claim_auto_challenge"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/claim"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '  <bpmn:process id="claim_auto_challenge" name="claim unchallenged sweep '
                 '(R/PT1H)" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "com.etzhayyim.apps.claim.unchallengedSweep", "version": 1, '
                 '"resultTimeoutMs": 120000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start" name="every 1 hour">\n'
                 '      <bpmn:outgoing>Flow_1</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer">\n'
                 '        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression"\n'
                 '                        '
                 'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">R/PT1H</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start" targetRef="Task_Sweep"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Sweep" name="unchallenged sweep actor">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="claim.unchallenged.sweep"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=5" target="limit"/>\n'
                 '          <zeebe:output source="=result" target="tickResult"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_1</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_2</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_2" sourceRef="Task_Sweep" '
                 'targetRef="Task_Audit"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Audit" name="emit claim.unchallenged.sweep '
                 'OCEL">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.audit.emit"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input '
                 'source="=&quot;com.etzhayyim.apps.claim.unchallenged.sweep&quot;" '
                 'target="eventType"/>\n'
                 '          <zeebe:input source="={ &quot;ok&quot;: tickResult.ok, '
                 '&quot;scanned&quot;: tickResult.scanned, &quot;submitted&quot;: '
                 'tickResult.submitted, &quot;witnessAlarms&quot;: tickResult.witnessAlarms, '
                 '&quot;errors&quot;: tickResult.errors }" target="attributes"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_2</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_3</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_3" sourceRef="Task_Audit" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_3</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3073,
                 '00-contracts/bpmn/com/etzhayyim/claim/claimAutoChallenge.bpmn',
                 '2026-04-28T19:00:00Z',
                 'did:web:claim-consumer.etzhayyim.com',
                 'did:web:claim-consumer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-auto-challenge-v1']},
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
         "      'sys.bpmn.seed.claim_auto_challenge'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $9\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-unchallengedSweep-v1',
                 'did:web:claim-consumer.etzhayyim.com',
                 'com.etzhayyim.apps.claim.unchallengedSweep',
                 'claim_auto_challenge',
                 120000,
                 '2026-04-28T19:00:00Z',
                 'did:web:claim-consumer.etzhayyim.com',
                 'did:web:claim-consumer.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-unchallengedSweep-v1']}]

DOWN = [{'sql': '\n    DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/claim-unchallengedSweep-v1']},
 {'sql': '\n    DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1\n  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/claim-auto-challenge-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
