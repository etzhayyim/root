"""Captured from Kysely migration 20260424510000_rebase_world_total_saturating."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424510000_rebase_world_total_saturating"
down_revision = 'r_20260424500000_seed_wikidata_transport_religious_5'
branch_labels = None
depends_on = None

UP = [{'sql': 'UPDATE vertex_maps_coverage_target SET world_total = $1 WHERE source_did = $2',
  'parameters': [1500, 'did:web:maps.gftd.ai:eonet:volcanoes']},
 {'sql': 'UPDATE vertex_maps_coverage_target SET world_total = $1 WHERE source_did = $2',
  'parameters': [200, 'did:web:maps.gftd.ai:eonet:seaLakeIce']},
 {'sql': 'UPDATE vertex_maps_coverage_target SET world_total = $1 WHERE source_did = $2',
  'parameters': [1500, 'did:web:maps.gftd.ai:eonet:wildfires']},
 {'sql': 'UPDATE vertex_maps_coverage_target SET world_total = $1 WHERE source_did = $2',
  'parameters': [500, 'did:web:maps.gftd.ai:registry:wikidata:museumShip']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
