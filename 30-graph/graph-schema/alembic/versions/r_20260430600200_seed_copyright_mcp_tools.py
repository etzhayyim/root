"""Captured from Kysely migration 20260430600200_seed_copyright_mcp_tools."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260430600200_seed_copyright_mcp_tools"
down_revision = 'r_20260430600100_seed_copyright_bpmn_actors'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-resolve',
                 'com.etzhayyim.apps.copyright.resolve',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'query',
                 'Resolve a work by DOI / ISBN-13 / ISRC / ISWC.',
                 '{"properties":{"doi":{"type":"string"},"isbn13":{"maxLength":13,"minLength":13,"type":"string"},"isrc":{"type":"string"},"iswc":{"type":"string"}},"type":"params"}',
                 '{"properties":{"error":{"type":"string"},"kind":{"type":"string"},"license":{"type":"string"},"rkey":{"type":"string"},"title":{"type":"string"}},"type":"object"}',
                 'com.etzhayyim.apps.copyright.resolve',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/resolve.json',
                 'afa29be8eabb6cea',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-resolve']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-list',
                 'com.etzhayyim.apps.copyright.list',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'query',
                 'List works filtered by kind / registry / license.',
                 '{"properties":{"kind":{"type":"string"},"license":{"type":"string"},"limit":{"default":50,"maximum":200,"minimum":1,"type":"integer"},"offset":{"default":0,"minimum":0,"type":"integer"},"registry":{"type":"string"}},"type":"params"}',
                 '{"properties":{"items":{"items":{"type":"unknown"},"type":"array"},"limit":{"type":"integer"},"offset":{"type":"integer"},"total":{"type":"integer"}},"required":["items","offset","limit","total"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.list',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/list.json',
                 'a944eccae291d84f',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-list']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-coverage',
                 'com.etzhayyim.apps.copyright.coverage',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'query',
                 'Copyright coverage by registry with kind / license / identifier histograms.',
                 '{"properties":{"registry":{"type":"string"}},"type":"params"}',
                 '{"properties":{"berneAutomatic":{"type":"integer"},"byKind":{"type":"unknown"},"byLicense":{"type":"unknown"},"identifiers":{"properties":{"doi":{"type":"integer"},"isbn":{"type":"integer"},"isrc":{"type":"integer"},"iswc":{"type":"integer"}},"type":"object"},"registry":{"type":"string"},"reportedAt":{"format":"datetime","type":"string"},"total":{"type":"integer"}},"required":["registry","total","reportedAt"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.coverage',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/coverage.json',
                 '4748cb9b284c037f',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-coverage']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestCrossref',
                 'com.etzhayyim.apps.copyright.ingestCrossref',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'procedure',
                 'Trigger a Crossref REST API ingest batch into vertex_work. Cursor-based '
                 'pagination, polite pool.',
                 '{"properties":{"fromYear":{"default":2020,"type":"integer"},"maxPages":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"rowsPerPage":{"default":100,"maximum":1000,"minimum":1,"type":"integer"},"sortField":{"default":"indexed","type":"string"},"sortOrder":{"default":"desc","type":"string"}},"type":"object"}',
                 '{"properties":{"error":{"type":"string"},"nextCursor":{"type":"string"},"ok":{"type":"boolean"},"registry":{"type":"string"},"rowsIngested":{"type":"integer"}},"required":["ok","rowsIngested","registry"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.ingestCrossref',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/ingestCrossref.json',
                 '2ba525df5309f082',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestCrossref']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestDatacite',
                 'com.etzhayyim.apps.copyright.ingestDatacite',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'procedure',
                 'Trigger a DataCite REST API ingest batch into vertex_work. Cursor-based '
                 'pagination.',
                 '{"properties":{"fromYear":{"default":2020,"type":"integer"},"maxPages":{"default":5,"maximum":50,"minimum":1,"type":"integer"},"pageSize":{"default":100,"maximum":1000,"minimum":1,"type":"integer"}},"type":"object"}',
                 '{"properties":{"error":{"type":"string"},"nextCursor":{"type":"string"},"ok":{"type":"boolean"},"registry":{"type":"string"},"rowsIngested":{"type":"integer"}},"required":["ok","rowsIngested","registry"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.ingestDatacite',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/ingestDatacite.json',
                 '18ab7d4ff8cb3196',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestDatacite']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-socialCoverageReport',
                 'com.etzhayyim.apps.copyright.socialCoverageReport',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'procedure',
                 'Generate and post a delta-aware copyright coverage social post. Skips if total '
                 'count delta < minDelta.',
                 '{"properties":{"forcePost":{"default":false,"description":"Skip delta check and '
                 'always post","type":"boolean"},"minDelta":{"default":10,"description":"Minimum '
                 'new works since last post to trigger a '
                 'post","minimum":0,"type":"integer"}},"type":"object"}',
                 '{"properties":{"delta":{"type":"integer"},"error":{"type":"string"},"ok":{"type":"boolean"},"postText":{"type":"string"},"posted":{"type":"boolean"},"skipped":{"type":"boolean"},"totalWorks":{"type":"integer"}},"required":["ok","posted","skipped"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.socialCoverageReport',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/socialCoverageReport.json',
                 'f554a2b27076f2aa',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-socialCoverageReport']},
 {'sql': '\n'
         '      INSERT INTO vertex_mcp_tool_def (\n'
         '        vertex_id, nsid, actor_did, actor_host, lexicon_type, description,\n'
         '        input_schema, output_schema, lxm_scope, visibility, version, enabled,\n'
         '        source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,\n'
         '        actor_id, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3, $4, $5,\n'
         '        $6, $7, $8, $9,\n'
         "        'public', 1, TRUE, $10, $11,\n"
         '        $12, 100, $13, $14, $15, $16\n'
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = $17\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-chat',
                 'com.etzhayyim.apps.copyright.chat',
                 'did:web:copyright.etzhayyim.com',
                 'copyright.etzhayyim.com',
                 'procedure',
                 'Chat with the Copyright Registry agent. Ask about works, licenses, DOI/ISBN '
                 'resolution, orphan works detection, and CMO coverage.',
                 '{"properties":{"maxTokens":{"default":600,"type":"integer"},"system":{"description":"Optional '
                 'system '
                 'override","maxLength":2000,"type":"string"},"temperature":{"default":0.3,"type":"number"},"tier":{"description":"LLM '
                 'tier: fast | standard | precise","type":"string"},"user":{"description":"User '
                 'message","maxLength":4000,"type":"string"}},"required":["user"],"type":"object"}',
                 '{"properties":{"content":{"type":"string"},"latencyMs":{"type":"integer"},"model":{"type":"string"}},"required":["content"],"type":"object"}',
                 'com.etzhayyim.apps.copyright.chat',
                 '00-contracts/lexicons/com/etzhayyim/apps/copyright/chat.json',
                 'f954fc0eedfb4076',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'did:web:copyright.etzhayyim.com',
                 'sys.mcp.seed.copyright',
                 '2026-04-30T15:00:00+09:00',
                 'at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-chat']}]

DOWN = [{'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-resolve']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-list']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-coverage']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestCrossref']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-ingestDatacite']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-socialCoverageReport']},
 {'sql': 'DELETE FROM vertex_mcp_tool_def WHERE vertex_id = $1',
  'parameters': ['at://did:web:copyright.etzhayyim.com/com.etzhayyim.mcp.toolDef/etzhayyim-apps-copyright-chat']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
