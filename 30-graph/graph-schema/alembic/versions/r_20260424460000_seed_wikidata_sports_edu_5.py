"""Captured from Kysely migration 20260424460000_seed_wikidata_sports_edu_5."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260424460000_seed_wikidata_sports_edu_5"
down_revision = 'r_20260424450000_seed_wikidata_sports_nature_10'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-baseballStadium:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:baseballStadium',
                 10000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:baseballStadium',
                 '2026-05-08T00:20:28.076Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-velodromeWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:velodromeWd',
                 1000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:velodromeWd',
                 '2026-05-08T00:20:28.076Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-publicLibrary:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:publicLibrary',
                 60000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:publicLibrary',
                 '2026-05-08T00:20:28.076Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-kindergartenWd:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:kindergartenWd',
                 200000,
                 0.6,
                 'did:web:maps.etzhayyim.com:registry:wikidata:kindergartenWd',
                 '2026-05-08T00:20:28.076Z']},
 {'sql': '\n'
         '      INSERT INTO vertex_maps_coverage_target (\n'
         '        vertex_id, source_did, label, world_total, priority_weight,\n'
         '        ttl_hours, org_id, user_id, actor_id, created_at\n'
         '      ) VALUES (\n'
         "        $1, $2, 'Spot', $3, $4,\n"
         "        168.0, 'anon', 'anon', $5, $6\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:maps.etzhayyim.com/app.etzhayyim.apps.maps.coverageTarget/registry-wikidata-cricketGround:Spot',
                 'did:web:maps.etzhayyim.com:registry:wikidata:cricketGround',
                 15000,
                 0.7,
                 'did:web:maps.etzhayyim.com:registry:wikidata:cricketGround',
                 '2026-05-08T00:20:28.076Z']},
 {'sql': 'FLUSH', 'parameters': []}]

DOWN = []


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
