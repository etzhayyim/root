"""Captured from Kysely migration 20260430170000_seed_chart_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430170000_seed_chart_bpmn"
down_revision = 'r_20260430160000_vertex_game_chart'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, $3, 1,\n'
         '           $4, CAST($5 AS integer),\n'
         '           $6,\n'
         '           $7, $8, 1,\n'
         '           $9, $10, $11\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-fetch-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'media_gamers_chart_fetch',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  media-gamers.chartFetch\n'
                 '\n'
                 '  Weekly game chart ingestion + LLM analysis pipeline.\n'
                 '  Timer R/P7D fires every Monday → fetch top-20 from SteamSpy + RAWG →\n'
                 '  persist vertex_game_chart_snapshot → LLM analyze → social post.\n'
                 '\n'
                 '  Task types (pymagatama primitives/media_gamers_chart.py):\n'
                 '    mediaGamers.chart.fetchAndPersist  — HTTP fetch + title matching + DB '
                 'insert\n'
                 '    mediaGamers.chart.analyze          — LLM trend analysis + social post\n'
                 '\n'
                 '  Input variables (timer-start, no explicit input):\n'
                 '    none — weekStart computed inside fetchAndPersist\n'
                 '\n'
                 '  Output variables produced by fetchAndPersist:\n'
                 '    weekStart    — ISO date string (Monday of this week)\n'
                 '    source       — primary source used ("steamspy_top2w")\n'
                 '    snapshotCount — rows inserted into vertex_game_chart_snapshot\n'
                 '\n'
                 '  Output variables produced by analyze:\n'
                 '    analysisUri  — vertex_id of vertex_game_chart_analysis row\n'
                 '    socialText   — Japanese post text (≤300 chars)\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'
                 '    id="Definitions_media_gamers_chart_fetch"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/media-gamers"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="media_gamers_chart_fetch" name="media gamers chart fetch" '
                 'isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Timer" name="weekly chart fetch timer">\n'
                 '      <bpmn:outgoing>Flow_ToFetch</bpmn:outgoing>\n'
                 '      <bpmn:timerEventDefinition id="Timer_7d">\n'
                 '        <bpmn:timeCycle '
                 'xsi:type="bpmn:tFormalExpression">R/P7D</bpmn:timeCycle>\n'
                 '      </bpmn:timerEventDefinition>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToFetch" sourceRef="Start_Timer" '
                 'targetRef="Task_Fetch"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Fetch" name="fetch and persist chart snapshots">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.chart.fetchAndPersist"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:output source="=weekStart"     target="weekStart"/>\n'
                 '          <zeebe:output source="=source"        target="source"/>\n'
                 '          <zeebe:output source="=snapshotCount" target="snapshotCount"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToFetch</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToAnalyze</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAnalyze" sourceRef="Task_Fetch" '
                 'targetRef="Task_Analyze"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Analyze" name="LLM analyze and post">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.chart.analyze"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=weekStart" target="weekStart"/>\n'
                 '          <zeebe:input source="=source"    target="source"/>\n'
                 '          <zeebe:output source="=analysisUri"  target="analysisUri"/>\n'
                 '          <zeebe:output source="=socialText"   target="socialText"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAnalyze</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Analyze" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="chart analysis complete"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 3366,
                 '00-contracts/bpmn/com/etzhayyim/media-gamers/chartFetch.bpmn',
                 'active',
                 '2026-04-30T16:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.media-gamers-chart',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-fetch-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '       source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT $1, $2, $3, 1,\n'
         '           $4, CAST($5 AS integer),\n'
         '           $6,\n'
         '           $7, $8, 1,\n'
         '           $9, $10, $11\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $12\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-analyze-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'media_gamers_chart_analyze',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<!--\n'
                 '  media-gamers.chartAnalyze\n'
                 '\n'
                 '  On-demand chart analysis triggered via XRPC\n'
                 '  com.etzhayyim.apps.media_gamers.analyzeChart.\n'
                 '\n'
                 '  Useful for back-filling historical weeks or re-analyzing after new\n'
                 '  vertex_game_title data arrives.\n'
                 '\n'
                 '  Input variables (from BPMN lexicon binding → XRPC body):\n'
                 '    weekStart  — ISO date string e.g. "2026-04-27" (Monday)\n'
                 '    source     — "steamspy_top2w" | "rawg_top" | "steam_jp_topsellers"\n'
                 '\n'
                 '  Output variables:\n'
                 '    analysisUri — vertex_id of vertex_game_chart_analysis row\n'
                 '    socialText  — Japanese post text\n'
                 '-->\n'
                 '<bpmn:definitions\n'
                 '    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"\n'
                 '    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"\n'
                 '    id="Definitions_media_gamers_chart_analyze"\n'
                 '    targetNamespace="https://etzhayyim.com/bpmn/media-gamers"\n'
                 '    exporter="hand-written"\n'
                 '    exporterVersion="2.0">\n'
                 '\n'
                 '  <bpmn:process id="media_gamers_chart_analyze" name="media gamers chart '
                 'analyze" isExecutable="true">\n'
                 '\n'
                 '    <bpmn:startEvent id="Start_Manual" name="analyze chart requested">\n'
                 '      <bpmn:outgoing>Flow_ToAnalyze</bpmn:outgoing>\n'
                 '    </bpmn:startEvent>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToAnalyze" sourceRef="Start_Manual" '
                 'targetRef="Task_Analyze"/>\n'
                 '\n'
                 '    <bpmn:serviceTask id="Task_Analyze" name="LLM analyze chart and post">\n'
                 '      <bpmn:extensionElements>\n'
                 '        <zeebe:taskDefinition type="mediaGamers.chart.analyze"/>\n'
                 '        <zeebe:ioMapping>\n'
                 '          <zeebe:input source="=string(weekStart)" target="weekStart"/>\n'
                 '          <zeebe:input source="=string(source)"    target="source"/>\n'
                 '          <zeebe:output source="=analysisUri"  target="analysisUri"/>\n'
                 '          <zeebe:output source="=socialText"   target="socialText"/>\n'
                 '        </zeebe:ioMapping>\n'
                 '      </bpmn:extensionElements>\n'
                 '      <bpmn:incoming>Flow_ToAnalyze</bpmn:incoming>\n'
                 '      <bpmn:outgoing>Flow_ToEnd</bpmn:outgoing>\n'
                 '    </bpmn:serviceTask>\n'
                 '    <bpmn:sequenceFlow id="Flow_ToEnd" sourceRef="Task_Analyze" '
                 'targetRef="End"/>\n'
                 '\n'
                 '    <bpmn:endEvent id="End" name="analysis complete"/>\n'
                 '\n'
                 '  </bpmn:process>\n'
                 '</bpmn:definitions>\n',
                 2066,
                 '00-contracts/bpmn/com/etzhayyim/media-gamers/chartAnalyze.bpmn',
                 'active',
                 '2026-04-30T16:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.media-gamers-chart',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-analyze-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version, result_timeout_ms,\n'
         '       write_table_allowlist, status, created_at, sensitivity_ord, org_id, user_id, '
         'actor_id)\n'
         '    SELECT $1, $2,\n'
         '           $3, $4,\n'
         '           1, CAST($5 AS integer), NULL,\n'
         '           $6, $7, 1,\n'
         '           $8, $9, $10\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $11\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-media-gamers-analyzeChart-v1',
                 'did:web:bpmn.etzhayyim.com',
                 'com.etzhayyim.apps.media_gamers.analyzeChart',
                 'media_gamers_chart_analyze',
                 180000,
                 'active',
                 '2026-04-30T16:00:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'sys.bpmn.seed.media-gamers-chart',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-media-gamers-analyzeChart-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/etzhayyim-apps-media-gamers-analyzeChart-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-analyze-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/media-gamers-chart-fetch-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
