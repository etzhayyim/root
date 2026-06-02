"""Captured from Kysely migration 20260430211100_seed_kami_ketsu_gorilla_bpmn_actors."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430211100_seed_kami_ketsu_gorilla_bpmn_actors"
down_revision = 'r_20260430211000_vertex_kami_ketsu_gorilla_score'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-submit-score-v1',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'kami_ketsu_gorilla_submit_score',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_ketsu_gorilla_submit_score" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiKetsuGorilla"><bpmn:process '
                 'id="kami_ketsu_gorilla_submit_score" name="kamiKetsuGorilla submitScore" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.kami.ketsuGorilla.submitScore", "version": 1, "resultTimeoutMs": '
                 '30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="submit score"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiKetsuGorilla.submitScore"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1065,
                 '00-contracts/bpmn/com/etzhayyim/kamiKetsuGorilla/submitScore.bpmn',
                 '2026-04-30T21:11:00+09:00',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'sys.bpmn.seed.kami-ketsu-gorilla',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-submit-score-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-submitScore-v1',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'com.etzhayyim.apps.kami.ketsuGorilla.submitScore',
                 'kami_ketsu_gorilla_submit_score',
                 30000,
                 'vertex_atrecord_kami_ketsu_gorilla_score',
                 '2026-04-30T21:11:00+09:00',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'sys.bpmn.seed.kami-ketsu-gorilla',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-submitScore-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_process_def (\n'
         '        vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,\n'
         '        source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id,\n'
         '        actor_did, org_did\n'
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
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-get-leaderboard-v1',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'kami_ketsu_gorilla_get_leaderboard',
                 '<?xml version="1.0" encoding="UTF-8"?>\n'
                 '<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" '
                 'xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" '
                 'id="Definitions_kami_ketsu_gorilla_get_leaderboard" '
                 'targetNamespace="https://etzhayyim.com/bpmn/kamiKetsuGorilla"><bpmn:process '
                 'id="kami_ketsu_gorilla_get_leaderboard" name="kamiKetsuGorilla getLeaderboard" '
                 'isExecutable="true"><bpmn:documentation>{ "nsid": '
                 '"com.etzhayyim.apps.kami.ketsuGorilla.getLeaderboard", "version": 1, '
                 '"resultTimeoutMs": 30000 }</bpmn:documentation><bpmn:startEvent '
                 'id="Start"><bpmn:outgoing>F1</bpmn:outgoing></bpmn:startEvent><bpmn:sequenceFlow '
                 'id="F1" sourceRef="Start" targetRef="Task"/><bpmn:serviceTask id="Task" '
                 'name="get leaderboard"><bpmn:extensionElements><zeebe:taskDefinition '
                 'type="kamiKetsuGorilla.getLeaderboard"/></bpmn:extensionElements><bpmn:incoming>F1</bpmn:incoming><bpmn:outgoing>F2</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow '
                 'id="F2" sourceRef="Task" targetRef="End"/><bpmn:endEvent '
                 'id="End"><bpmn:incoming>F2</bpmn:incoming></bpmn:endEvent></bpmn:process></bpmn:definitions>\n',
                 1083,
                 '00-contracts/bpmn/com/etzhayyim/kamiKetsuGorilla/getLeaderboard.bpmn',
                 '2026-04-30T21:11:00+09:00',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'sys.bpmn.seed.kami-ketsu-gorilla',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-get-leaderboard-v1']},
 {'sql': '\n'
         '      INSERT INTO vertex_bpmn_lexicon_binding (\n'
         '        vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '        result_timeout_ms, write_table_allowlist, status, created_at,\n'
         '        sensitivity_ord, org_id, user_id, actor_id, actor_did, org_did\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, 1,\n'
         "        CAST($5 AS integer), $6, 'active', $7,\n"
         "        100, $8, $9, $10, $11, 'anon'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-getLeaderboard-v1',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'com.etzhayyim.apps.kami.ketsuGorilla.getLeaderboard',
                 'kami_ketsu_gorilla_get_leaderboard',
                 30000,
                 '',
                 '2026-04-30T21:11:00+09:00',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'sys.bpmn.seed.kami-ketsu-gorilla',
                 'did:web:k3t5g0r1.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-getLeaderboard-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-submitScore-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-submit-score-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/kami-ketsu-gorilla-getLeaderboard-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/kami-ketsu-gorilla-get-leaderboard-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
