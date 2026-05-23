"""Captured from Kysely migration 20260428140000_yadoya_chain_did_resolver."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260428140000_yadoya_chain_did_resolver"
down_revision = 'r_20260428140000_vertex_telecom_wlan'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:marriott', '%marriott%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:hilton', '%hilton%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:hyatt', '%hyatt%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:ihg', '%intercontinental%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:ihg', '%holiday inn%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:accor', '%accor%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:accor', '%mercure%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:accor', '%novotel%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:wyndham', '%wyndham%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:choice', '%comfort inn%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:hoshino', '%hoshino%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:hoshino', '%星野%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:prince', '%prince hotel%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:prince', '%プリンス%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:tokyu-stay', '%tokyu stay%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:apa', '%apa hotel%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:apa', '%アパホテル%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:route-inn', '%route inn%']},
 {'sql': '\n'
         '      UPDATE vertex_yadoya_hotel\n'
         '      SET chain_did = $1\n'
         '      WHERE chain_did IS NULL\n'
         '        AND LOWER(name) LIKE $2\n'
         '    ',
  'parameters': ['did:web:hospitality.etzhayyim.com:actor:chain:route-inn', '%ルートイン%']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_yadoya_hotel\n'
         '    SET chain_did = NULL\n'
         "    WHERE chain_did LIKE 'did:web:hospitality.etzhayyim.com:actor:chain:%'\n"
         '  ',
  'parameters': []},
 {'sql': 'FLUSH', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
