"""Captured from Kysely migration 20260427010000_seed_gov_zaf_official_source_coverage."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260427010000_seed_gov_zaf_official_source_coverage"
down_revision = 'r_20260427006000_gov_form_extraction_results'
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
         "        $5, 'ai.gftd.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-za-official-seed', 'page-wet-wat-gyotaku-ingested',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-national-departments-9cfc7bff4a-10304550',
                 'did:web:zaf-state.gftd.ai',
                 'zaf-national-departments-9cfc7bff4a-10304550',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'country:zaf',
                 'South African Government',
                 'https://www.gov.za/about-government/government-system/national-departments',
                 '2026-04-27T01:00:00Z',
                 '{"countryCode":"ZAF","officialPublisher":"South African '
                 'Government","evidence":{"page":{"rkey":"zaf-national-departments-9cfc7bff4a-10304550","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.page/zaf-national-departments-9cfc7bff4a-10304550","b2Blob":"official-sources/zaf/govza/zaf-national-departments/page.html"},"wet":{"pageRkey":"zaf-national-departments-9cfc7bff4a-10304550","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wetChunk/zaf-national-departments-9cfc7bff4a-10304550"},"wat":{"rkey":"zaf-national-departments-9cfc7bff4a-10304550","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wat/zaf-national-departments-9cfc7bff4a-10304550"},"screenshot":{"rkey":"zaf-national-departments-9cfc7bff4a-10304550","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.screenshot/zaf-national-departments-9cfc7bff4a-10304550","b2Blob":"official-sources/zaf/govza/zaf-national-departments/gyotaku.png","format":"png","fileSize":388467}}}',
                 'at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-national-departments-9cfc7bff4a-10304550']},
 {'sql': '\n'
         '      INSERT INTO vertex_gov_source (\n'
         '        vertex_id, owner_did, rkey, repo, did, collection, status,\n'
         '        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,\n'
         '        "discoveryMethod", "coverageStage", "lastSeenAt", props\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 'ai.gftd.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-za-official-seed', 'page-wet-wat-gyotaku-ingested',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provinces-2aa86b5df1-10305612',
                 'did:web:zaf-state.gftd.ai',
                 'zaf-provinces-2aa86b5df1-10305612',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'country:zaf',
                 'South African Government',
                 'https://www.gov.za/provinces',
                 '2026-04-27T01:00:00Z',
                 '{"countryCode":"ZAF","officialPublisher":"South African '
                 'Government","evidence":{"page":{"rkey":"zaf-provinces-2aa86b5df1-10305612","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.page/zaf-provinces-2aa86b5df1-10305612","b2Blob":"official-sources/zaf/govza/zaf-provinces/page.html"},"wet":{"pageRkey":"zaf-provinces-2aa86b5df1-10305612","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wetChunk/zaf-provinces-2aa86b5df1-10305612"},"wat":{"rkey":"zaf-provinces-2aa86b5df1-10305612","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wat/zaf-provinces-2aa86b5df1-10305612"},"screenshot":{"rkey":"zaf-provinces-2aa86b5df1-10305612","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.screenshot/zaf-provinces-2aa86b5df1-10305612","b2Blob":"official-sources/zaf/govza/zaf-provinces/gyotaku.png","format":"png","fileSize":493001}}}',
                 'at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provinces-2aa86b5df1-10305612']},
 {'sql': '\n'
         '      INSERT INTO vertex_gov_source (\n'
         '        vertex_id, owner_did, rkey, repo, did, collection, status,\n'
         '        "actorDid", "actorPath", "actorName", "sourceType", "sourceUrl", format,\n'
         '        "discoveryMethod", "coverageStage", "lastSeenAt", props\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4,\n'
         "        $5, 'ai.gftd.gov.source', 'active', $6, $7,\n"
         "        $8, 'official-government-page', $9, 'html',\n"
         "        'gov-za-official-seed', 'page-wet-wat-gyotaku-ingested',\n"
         '        $10, $11\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_gov_source WHERE vertex_id = $12\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provincial-government-6eeae56a66-10306648',
                 'did:web:zaf-state.gftd.ai',
                 'zaf-provincial-government-6eeae56a66-10306648',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'did:web:zaf-state.gftd.ai',
                 'country:zaf',
                 'South African Government',
                 'https://www.gov.za/links/provincial-government',
                 '2026-04-27T01:00:00Z',
                 '{"countryCode":"ZAF","officialPublisher":"South African '
                 'Government","evidence":{"page":{"rkey":"zaf-provincial-government-6eeae56a66-10306648","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.page/zaf-provincial-government-6eeae56a66-10306648","b2Blob":"official-sources/zaf/govza/zaf-provincial-government/page.html"},"wet":{"pageRkey":"zaf-provincial-government-6eeae56a66-10306648","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wetChunk/zaf-provincial-government-6eeae56a66-10306648"},"wat":{"rkey":"zaf-provincial-government-6eeae56a66-10306648","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.wat/zaf-provincial-government-6eeae56a66-10306648"},"screenshot":{"rkey":"zaf-provincial-government-6eeae56a66-10306648","vertexId":"at://did:web:zaf-state.gftd.ai/ai.gftd.apps.site.screenshot/zaf-provincial-government-6eeae56a66-10306648","b2Blob":"official-sources/zaf/govza/zaf-provincial-government/gyotaku.png","format":"png","fileSize":549036}}}',
                 'at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provincial-government-6eeae56a66-10306648']}]

DOWN = [{'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-national-departments-9cfc7bff4a-10304550']},
 {'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provinces-2aa86b5df1-10305612']},
 {'sql': 'DELETE FROM vertex_gov_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:zaf-state.gftd.ai/ai.gftd.gov.source/zaf-provincial-government-6eeae56a66-10306648']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
