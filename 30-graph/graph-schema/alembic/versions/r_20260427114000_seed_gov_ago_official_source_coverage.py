"""Captured from Kysely migration 20260427114000_seed_gov_ago_official_source_coverage."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427114000_seed_gov_ago_official_source_coverage"
down_revision = 'r_20260427113000_seed_gov_ago_bpmn_mcp_registry'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_gov_source (\n'
         '        vertex_id, owner_did, rkey, repo, did, collection, status,\n'
         '        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,\n'
         '        "discoveryMethod", "coverageStage", "lastSeenAt", props\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 'com.etzhayyim.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-ago-official-seed', 'pending-page-wet-wat-gyotaku',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-ministro-8c8c8b4d31-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'ago-ministro-8c8c8b4d31-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'country:ago',
                 'Angolan Government',
                 'https://governo.gov.ao/ministro',
                 '2026-04-27T11:40:00Z',
                 '{"countryCode":"AGO","officialPublisher":"Angolan '
                 'Government","evidence":{"page":{"rkey":"ago-ministro-8c8c8b4d31-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.page/ago-ministro-8c8c8b4d31-11400000","b2Blob":"official-sources/ago/governo/ago-ministro/page.html"},"wet":{"pageRkey":"ago-ministro-8c8c8b4d31-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wetChunk/ago-ministro-8c8c8b4d31-11400000"},"wat":{"rkey":"ago-ministro-8c8c8b4d31-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wat/ago-ministro-8c8c8b4d31-11400000"},"screenshot":{"rkey":"ago-ministro-8c8c8b4d31-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.screenshot/ago-ministro-8c8c8b4d31-11400000","b2Blob":"official-sources/ago/governo/ago-ministro/gyotaku.png","format":"png","fileSize":0}}}',
                 'at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-ministro-8c8c8b4d31-11400000']},
 {'sql': '\n'
         '      INSERT INTO vertex_gov_source (\n'
         '        vertex_id, owner_did, rkey, repo, did, collection, status,\n'
         '        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,\n'
         '        "discoveryMethod", "coverageStage", "lastSeenAt", props\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 'com.etzhayyim.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-ago-official-seed', 'pending-page-wet-wat-gyotaku',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-governador-e495bf67e7-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'ago-governador-e495bf67e7-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'country:ago',
                 'Angolan Government',
                 'https://governo.gov.ao/governador',
                 '2026-04-27T11:40:00Z',
                 '{"countryCode":"AGO","officialPublisher":"Angolan '
                 'Government","evidence":{"page":{"rkey":"ago-governador-e495bf67e7-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.page/ago-governador-e495bf67e7-11400000","b2Blob":"official-sources/ago/governo/ago-governador/page.html"},"wet":{"pageRkey":"ago-governador-e495bf67e7-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wetChunk/ago-governador-e495bf67e7-11400000"},"wat":{"rkey":"ago-governador-e495bf67e7-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wat/ago-governador-e495bf67e7-11400000"},"screenshot":{"rkey":"ago-governador-e495bf67e7-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.screenshot/ago-governador-e495bf67e7-11400000","b2Blob":"official-sources/ago/governo/ago-governador/gyotaku.png","format":"png","fileSize":0}}}',
                 'at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-governador-e495bf67e7-11400000']},
 {'sql': '\n'
         '      INSERT INTO vertex_gov_source (\n'
         '        vertex_id, owner_did, rkey, repo, did, collection, status,\n'
         '        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,\n'
         '        "discoveryMethod", "coverageStage", "lastSeenAt", props\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 'com.etzhayyim.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-ago-official-seed', 'pending-page-wet-wat-gyotaku',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-provincias-36779ddfea-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'ago-provincias-36779ddfea-11400000',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'did:web:ago-state.etzhayyim.com',
                 'country:ago',
                 'Angolan Government',
                 'https://governo.gov.ao/angola/provincias',
                 '2026-04-27T11:40:00Z',
                 '{"countryCode":"AGO","officialPublisher":"Angolan '
                 'Government","evidence":{"page":{"rkey":"ago-provincias-36779ddfea-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.page/ago-provincias-36779ddfea-11400000","b2Blob":"official-sources/ago/governo/ago-provincias/page.html"},"wet":{"pageRkey":"ago-provincias-36779ddfea-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wetChunk/ago-provincias-36779ddfea-11400000"},"wat":{"rkey":"ago-provincias-36779ddfea-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.wat/ago-provincias-36779ddfea-11400000"},"screenshot":{"rkey":"ago-provincias-36779ddfea-11400000","vertexId":"at://did:web:ago-state.etzhayyim.com/com.etzhayyim.apps.site.screenshot/ago-provincias-36779ddfea-11400000","b2Blob":"official-sources/ago/governo/ago-provincias/gyotaku.png","format":"png","fileSize":0}}}',
                 'at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-provincias-36779ddfea-11400000']}]

DOWN = [{'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-ministro-8c8c8b4d31-11400000']},
 {'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-governador-e495bf67e7-11400000']},
 {'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:ago-state.etzhayyim.com/com.etzhayyim.gov.source/ago-provincias-36779ddfea-11400000']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
