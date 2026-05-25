"""Captured from Kysely migration 20260508930000_seed_ki_synthesize_langgraph_binding."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260508930000_seed_ki_synthesize_langgraph_binding"
down_revision = 'r_20260508930000_retire_shosha_trade_book_react_zeebe_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_bpmn_lexicon_binding\n'
         '      (vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,\n'
         '       result_timeout_ms, status, created_at, sensitivity_ord,\n'
         '       org_id, user_id, actor_id, routing_target)\n'
         '    SELECT\n'
         '      $1, $2,\n'
         "      'app.etzhayyim.apps.ki.synthesize',\n"
         "      'ki.synthesize.v1',\n"
         '      1,\n'
         '      CAST(120000 AS integer),\n'
         "      'active', $3, 1,\n"
         '      $4, $5, $6,\n'
         "      'langgraph'\n"
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $7\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/ki-synthesize-langgraph-v1',
                 'did:web:bpmn.etzhayyim.com',
                 '2026-05-08T09:30:00Z',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/ki-synthesize-langgraph-v1']}]

DOWN = [{'sql': 'DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = $1',
  'parameters': ['at://did:web:bpmn.etzhayyim.com/app.etzhayyim.apps.bpmn.lexiconBinding/ki-synthesize-langgraph-v1']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
