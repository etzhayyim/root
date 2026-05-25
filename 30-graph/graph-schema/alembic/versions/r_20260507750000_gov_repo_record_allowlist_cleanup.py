"""Captured from Kysely migration 20260507750000_gov_repo_record_allowlist_cleanup."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260507750000_gov_repo_record_allowlist_cleanup"
down_revision = 'r_20260507740000_seed_graph_sos_intel_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = REPLACE(write_table_allowlist, ',vertex_repo_record', "
         "'')\n"
         "    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "      AND write_table_allowlist LIKE '%,vertex_repo_record%'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = REPLACE(write_table_allowlist, 'vertex_repo_record,', "
         "'')\n"
         "    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "      AND write_table_allowlist LIKE '%vertex_repo_record,%'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         "    SET write_table_allowlist = ''\n"
         "    WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "      AND write_table_allowlist = 'vertex_repo_record'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist =\n'
         '        CASE\n'
         "          WHEN COALESCE(write_table_allowlist, '') = '' THEN $1\n"
         "          ELSE write_table_allowlist || ',' || $2\n"
         '        END\n'
         "      WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "        AND COALESCE(write_table_allowlist, '') NOT LIKE $3\n"
         '    ',
  'parameters': ['vertex_gov_org', 'vertex_gov_org', '%vertex_gov_org%']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist =\n'
         '        CASE\n'
         "          WHEN COALESCE(write_table_allowlist, '') = '' THEN $1\n"
         "          ELSE write_table_allowlist || ',' || $2\n"
         '        END\n'
         "      WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "        AND COALESCE(write_table_allowlist, '') NOT LIKE $3\n"
         '    ',
  'parameters': ['vertex_gov_actor_manifest',
                 'vertex_gov_actor_manifest',
                 '%vertex_gov_actor_manifest%']},
 {'sql': '\n'
         '      UPDATE vertex_bpmn_lexicon_binding\n'
         '      SET write_table_allowlist =\n'
         '        CASE\n'
         "          WHEN COALESCE(write_table_allowlist, '') = '' THEN $1\n"
         "          ELSE write_table_allowlist || ',' || $2\n"
         '        END\n'
         "      WHERE (actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%')\n"
         "        AND COALESCE(write_table_allowlist, '') NOT LIKE $3\n"
         '    ',
  'parameters': ['edge_gov_org_site_dependency',
                 'edge_gov_org_site_dependency',
                 '%edge_gov_org_site_dependency%']}]

DOWN = [{'sql': '\n'
         '    UPDATE vertex_bpmn_lexicon_binding\n'
         '    SET write_table_allowlist =\n'
         '      CASE\n'
         "        WHEN write_table_allowlist LIKE '%vertex_repo_record%' THEN "
         'write_table_allowlist\n'
         "        ELSE write_table_allowlist || ',vertex_repo_record'\n"
         '      END\n'
         "    WHERE actor_id LIKE 'gov-%' OR nsid LIKE 'app.etzhayyim.gov%'\n"
         '  ',
  'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
