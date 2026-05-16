"""Captured from Kysely migration 20260424480000_purge_phase51_dead_qids."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424480000_purge_phase51_dead_qids"
down_revision = 'r_20260424470000_seed_wikipedia_10_langs_c'
branch_labels = None
depends_on = None

UP = [{'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:wikidata:parliamentBldg']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:wikidata:aquariumWd']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:wikidata:prisonWd']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:wikidata:boardingSchool']},
 {'sql': 'DELETE FROM vertex_maps_coverage_target WHERE source_did = $1',
  'parameters': ['did:web:maps.gftd.ai:registry:wikidata:gurdwara']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
