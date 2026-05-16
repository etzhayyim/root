"""Captured from Kysely migration 20260428180000_seed_malak_get_dashboard_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428180000_seed_malak_get_dashboard_bpmn"
down_revision = 'r_20260428170000_seed_hospitality_chain_profiles'
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-dashboard-v1',
                 'did:web:malak.gftd.ai',
                 'malak_get_dashboard',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  malak.getDashboard — migrates cmdGetDashboard.\n'
                 '\n'
                 '  Reads mv_malak_dashboard_counts (4-row streaming MV) and pivots\n'
                 '  into a typed dashboard object.  No wallet TODOs remain — the MV\n'
                 '  now includes walletAddresses + threatOrgs after migration\n'
                 '  20260428170000_mv_malak_dashboard_counts_v2.\n'
                 '\n'
                 '  Flow:\n'
                 '    Start (no inputs)\n'
                 '      → generic.db.select (mv_malak_dashboard_counts — all 4 metric rows)\n'
                 '      → scriptTask: pivot rows[] into dashboard object\n'
                 '      → End\n'
                 '\n'
                 '  Output variable: dashboard { threatActors, walletAddresses, btcRiskSignals, '
                 'threatOrgs }\n'
                 '\n'
                 '  NSID: ai.gftd.apps.malak.getDashboard\n'
                 '  vid:  '
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-dashboard-v1\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_malak_get_dashboard"\n'
                 '    targetNamespace="https://gftd.ai/bpmn/malak"\n'
                 '    exporter="hand-written" exporterVersion="2.0">\n'
                 '  <bpmn:process id="malak_get_dashboard" name="malak getDashboard" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:documentation>\n'
                 '      { "nsid": "ai.gftd.apps.malak.getDashboard", "version": 1, '
                 '"resultTimeoutMs": 10000 }\n'
                 '    </bpmn:documentation>\n'
                 '\n'
                 '    <bpmn:startEvent id="Start">\n'
                 '      <bpmn:outgoing>Flow_ToSelect</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToSelect" sourceRef="Start" '
                 'targetRef="Task_Select"/>\n'
                 '\n'
                 '    <!-- Step 1: read all rows from the 4-metric dashboard MV -->\n'
                 '    <bpmn:serviceTask id="Task_Select" name="select mv_malak_dashboard_counts">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="generic.db.select"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=&quot;mv_malak_dashboard_counts&quot;" '
                 'target="table"/>\n'
                 '          <zeebe:input source="=10"                                    '
                 'target="limit"/>\n'
                 '          <zeebe:output source="=rows"     target="mvRows"/>\n'
                 '          <zeebe:output source="=rowCount" target="mvCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToSelect</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToPivot</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToPivot" sourceRef="Task_Select" '
                 'targetRef="Task_Pivot"/>\n'
                 '\n'
                 '    <!-- Step 2: pivot metric rows into a typed dashboard context -->\n'
                 '    <bpmn:scriptTask id="Task_Pivot" name="pivot metrics into dashboard">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:script\n'
                 "            expression='={\n"
                 '              threatActors:    if (mvRows[metric = "threatActors"])[1] = null '
                 'then 0 else (mvRows[metric = "threatActors"])[1].cnt,\n'
                 '              walletAddresses: if (mvRows[metric = "walletAddresses"])[1] = null '
                 'then 0 else (mvRows[metric = "walletAddresses"])[1].cnt,\n'
                 '              btcRiskSignals:  if (mvRows[metric = "btcRiskSignals"])[1] = null '
                 'then 0 else (mvRows[metric = "btcRiskSignals"])[1].cnt,\n'
                 '              threatOrgs:      if (mvRows[metric = "threatOrgs"])[1] = null then '
                 '0 else (mvRows[metric = "threatOrgs"])[1].cnt\n'
                 "            }'\n"
                 '            resultVariable="dashboard"/>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToPivot</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:scriptTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Pivot" targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="done">\n'
                 '      <bpmn:incoming>Flow_ToEnd</bpmn:incoming>\n'
                 '    </bpmn:endEvent>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3471,
                 '00-contracts/bpmn/ai/gftd/malak/getDashboard.bpmn',
                 '2026-04-28T18:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-dashboard-v1']},
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
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getDashboard-v1',
                 'did:web:malak.gftd.ai',
                 'ai.gftd.apps.malak.getDashboard',
                 'malak_get_dashboard',
                 10000,
                 '2026-04-28T18:00:00Z',
                 'did:web:malak.gftd.ai',
                 'did:web:malak.gftd.ai',
                 'sys.bpmn.seed.malak',
                 'at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getDashboard-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.binding/malak-getDashboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.gftd.ai/ai.gftd.apps.bpmn.processDef/malak-get-dashboard-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
