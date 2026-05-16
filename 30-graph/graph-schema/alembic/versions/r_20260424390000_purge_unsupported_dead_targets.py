"""Captured from Kysely migration 20260424390000_purge_unsupported_dead_targets."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424390000_purge_unsupported_dead_targets"
down_revision = 'r_20260424380000_seed_wikipedia_20_more_langs_b'
branch_labels = None
depends_on = None

UP = [{'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:openaddresses']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:osm']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:uk-ch']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:eu-br']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:jp-moj']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:jp-nta']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:us-edgar']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:opencorporates']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:gtfs']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:street_view']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:opensky']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
