"""Captured from Kysely migration 20260424270000_udf_phase_c_dns_gleif_wikidata_steam."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424270000_udf_phase_c_dns_gleif_wikidata_steam"
down_revision = 'r_20260424270000_seed_wikivoyage_10_more_plus_nwis_note'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE FUNCTION dns_resolve(VARCHAR, VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.dns.resolve'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION dns_resolve_json(VARCHAR, VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.dns.resolveJson'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION gleif_lei_lookup(VARCHAR, VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.gleif.lookup'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION wikidata_entity_claims(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.wikidata.entityClaims'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE FUNCTION steam_release_date(VARCHAR)\n'
         '      RETURNS VARCHAR\n'
         "      AS 'com.etzhayyim.apps.steam.releaseDate'\n"
         "      USING LINK 'http://udf-cluster.mitama-udf.svc:8815'\n"
         '  ',
  'parameters': []}]

DOWN = [{'sql': 'DROP FUNCTION IF EXISTS steam_release_date(VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS wikidata_entity_claims(VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS gleif_lei_lookup(VARCHAR, VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS dns_resolve_json(VARCHAR, VARCHAR)', 'parameters': []},
 {'sql': 'DROP FUNCTION IF EXISTS dns_resolve(VARCHAR, VARCHAR)', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
