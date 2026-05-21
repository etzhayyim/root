"""Captured from Kysely migration 20260424440000_purge_dead_wikivoyage."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424440000_purge_dead_wikivoyage"
down_revision = 'r_20260424430000_seed_wikidata_maritime_academic_10'
branch_labels = None
depends_on = None

UP = [{'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:ar']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:cs']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:da']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:fi']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:ja']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:nl']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:no']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:pl']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:ro']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:sk']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:tr']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.etzhayyim.com:wikivoyage:uk']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
