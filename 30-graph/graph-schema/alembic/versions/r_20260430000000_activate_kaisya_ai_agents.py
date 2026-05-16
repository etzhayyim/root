"""Captured from Kysely migration 20260430000000_activate_kaisya_ai_agents."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430000000_activate_kaisya_ai_agents"
down_revision = 'r_20260429280000_seed_wellbecoming_minimax_sweep_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_ceo_daily_briefing']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_coo_ops_monitor']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_clo_case_sweep']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_eng_deploy_health_check']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_eng_infra_monitor']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_brand_content_briefing']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'active'\n"
         '      WHERE bpmn_process_id = $1\n'
         "        AND status = 'inactive'\n"
         '    ',
  'parameters': ['kaisya_creative_asset_pipeline']}]

DOWN = [{'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_ceo_daily_briefing']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_coo_ops_monitor']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_clo_case_sweep']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_eng_deploy_health_check']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_eng_infra_monitor']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_brand_content_briefing']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_process_def\n'
         "      SET status = 'inactive'\n"
         '      WHERE bpmn_process_id = $1\n'
         '    ',
  'parameters': ['kaisya_creative_asset_pipeline']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
