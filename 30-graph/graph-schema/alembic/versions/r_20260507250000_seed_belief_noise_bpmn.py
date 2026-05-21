"""Captured from Kysely migration 20260507250000_seed_belief_noise_bpmn."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507250000_seed_belief_noise_bpmn"
down_revision = 'r_20260507240000_vertex_belief_noise'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_process_def\n'
         '      (vertex_id, bpmn_process_id, version, xml,\n'
         '       sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         '      $1,\n'
         "      'wellbecoming_belief_noise_inject',\n"
         "      1, '',\n"
         "      1, '', '', 'sys.bpmn.wellbecoming'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = $2\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-noise-inject-v1',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-noise-inject-v1']},
 {'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, nsid, bpmn_process_id,\n'
         '       sensitivity_ord, org_id, user_id, actor_id)\n'
         '    SELECT\n'
         '      $1,\n'
         "      'ai.gftd.apps.wellbecoming.beliefNoiseInject',\n"
         "      'wellbecoming_belief_noise_inject',\n"
         "      1, '', '', 'sys.bpmn.wellbecoming'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $2\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-noise-inject-v1',
                 'at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-noise-inject-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.lexiconBinding/wellbecoming-belief-noise-inject-v1']},
 {'sql': 'DELETE FROM vertex_bpmn_process_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/ai.gftd.apps.bpmn.processDef/wellbecoming-belief-noise-inject-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
