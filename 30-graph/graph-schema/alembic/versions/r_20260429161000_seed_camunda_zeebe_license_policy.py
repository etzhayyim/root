"""Captured from Kysely migration 20260429161000_seed_camunda_zeebe_license_policy."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429161000_seed_camunda_zeebe_license_policy"
down_revision = 'r_20260429161000_pd_color_process_mining_views'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    INSERT INTO vertex_domain_knowledge_document (\n'
         '      vertex_id, _seq, created_date, sensitivity_ord, owner_did, actor_did,\n'
         '      domain, canonical_work_id, game_slug, title, lang, body, body_hash,\n'
         '      source_record_uri, confidence, status, created_at, updated_at,\n'
         '      org_id, user_id, actor_id, props\n'
         '    )\n'
         '    SELECT\n'
         "      $1, 1, DATE '2026-04-29', 1, $2, $3,\n"
         "      'software_compliance', 'software:camunda-zeebe', '',\n"
         "      'Camunda/Zeebe runtime license policy 2026-04-29', 'ja', $4,\n"
         "      'sha256:pending', 'git:50-infra/vultr/zeebe/zeebe.yaml',\n"
         "      'high', 'active', $5, $6,\n"
         "      'anon', 'anon', 'sys.llm.domain-knowledge.seed.camunda-zeebe-license',\n"
         '      '
         '\'{"runtime":"zeebe","pinnedImage":"camunda/zeebe:8.5.23","posture":"short-term-compatibility-track"}\'\n'
         '    WHERE NOT EXISTS (\n'
         '      SELECT 1 FROM vertex_domain_knowledge_document WHERE vertex_id = $7\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'did:web:llm.etzhayyim.com',
                 'did:web:bpmn.etzhayyim.com',
                 'Camunda/Zeebe runtime policy as of 2026-04-29: etzhayyim pins the self-managed Zeebe '
                 'broker to camunda/zeebe:8.5.23 as a short-term Zeebe-only compatibility track.\n'
                 'Do not deploy Camunda Operate, Tasklist, Optimize, or Elasticsearch/OpenSearch '
                 'under this 8.5 compatibility posture without separate license review.\n'
                 'Camunda 8.6 and later self-managed production usage changes the licensing '
                 'posture for Zeebe and the broader Camunda 8 stack; production use should require '
                 'Enterprise/SaaS approval or an approved replacement plan.\n'
                 'Zeebe 8.5 preserves the existing BPMN XML plus zeebe:taskDefinition, '
                 'zeebe:ioMapping, and pyzeebe worker contract with minimal code churn, but it is '
                 'past upstream maintenance end and is not a long-term production baseline.\n'
                 'Before applying a live downgrade from 8.6.x to 8.5.x, validate persisted '
                 'partition data compatibility or recreate pilot broker state. Do not assume Zeebe '
                 'broker downgrades are safe in-place.',
                 '2026-04-29T16:10:00+09:00',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         '        $3, 1, $4,\n'
         '        '
         "'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',\n"
         "        56, 'ja',\n"
         "        NULL, CAST(NULL AS REAL), NULL, NULL, $5, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-1',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'etzhayyim pins the self-managed Zeebe broker to camunda/zeebe:8.5.23 as a short-term '
                 'Zeebe-only compatibility track.',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-1']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 2, DATE '2026-04-29', 1, $2,\n"
         '        $3, 2, $4,\n'
         '        '
         "'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',\n"
         "        70, 'ja',\n"
         "        NULL, CAST(NULL AS REAL), NULL, NULL, $5, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-2',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'Do not deploy Operate, Tasklist, Optimize, or Elasticsearch/OpenSearch under the '
                 '8.5 compatibility posture without separate license review.',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-2']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 3, DATE '2026-04-29', 1, $2,\n"
         '        $3, 3, $4,\n'
         '        '
         "'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',\n"
         "        70, 'ja',\n"
         "        NULL, CAST(NULL AS REAL), NULL, NULL, $5, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-3',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'Camunda 8.6+ self-managed production usage changes the licensing posture; '
                 'require Enterprise/SaaS approval or an approved replacement plan.',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-3']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 4, DATE '2026-04-29', 1, $2,\n"
         '        $3, 4, $4,\n'
         '        '
         "'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',\n"
         "        76, 'ja',\n"
         "        NULL, CAST(NULL AS REAL), NULL, NULL, $5, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-4',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'Zeebe 8.5 keeps existing BPMN zeebe:taskDefinition, zeebe:ioMapping, and pyzeebe '
                 'worker contracts with minimal code churn, but is past maintenance end.',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-4']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 5, DATE '2026-04-29', 1, $2,\n"
         '        $3, 5, $4,\n'
         '        '
         "'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',\n"
         "        61, 'ja',\n"
         "        NULL, CAST(NULL AS REAL), NULL, NULL, $5, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-5',
                 'did:web:llm.etzhayyim.com',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'Before live downgrade from 8.6.x to 8.5.x, validate persisted partition data '
                 'compatibility or recreate pilot broker state.',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429/chunk-5']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         "        $7, $8, $9, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_source WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-pricing-self-managed',
                 'did:web:llm.etzhayyim.com',
                 'https://camunda.com/pricing/',
                 'Camunda pricing: Self-Managed Free and Enterprise',
                 'vendor-pricing',
                 'Camunda',
                 'high',
                 '2026-04-29T16:10:00+09:00',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-pricing-self-managed']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', CAST(0.9 AS REAL), $5\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_domain_knowledge_cites WHERE edge_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:camunda-zeebe-license:camunda-pricing-self-managed',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-pricing-self-managed',
                 'did:web:llm.etzhayyim.com',
                 '2026-04-29T16:10:00+09:00',
                 'edge:dk-cites:camunda-zeebe-license:camunda-pricing-self-managed']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         "        $7, $8, $9, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_source WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-license-reference',
                 'did:web:llm.etzhayyim.com',
                 'https://docs.camunda.io/docs/reference/licenses/',
                 'Camunda 8 license reference',
                 'vendor-license-doc',
                 'Camunda',
                 'high',
                 '2026-04-29T16:10:00+09:00',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-license-reference']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', CAST(0.9 AS REAL), $5\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_domain_knowledge_cites WHERE edge_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:camunda-zeebe-license:camunda-license-reference',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-license-reference',
                 'did:web:llm.etzhayyim.com',
                 '2026-04-29T16:10:00+09:00',
                 'edge:dk-cites:camunda-zeebe-license:camunda-license-reference']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         "        $7, $8, $9, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_source WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-8-5-release-notes',
                 'did:web:llm.etzhayyim.com',
                 'https://docs.camunda.io/docs/8.5/reference/release-notes/850/',
                 'Camunda 8.5 release notes and maintenance window',
                 'vendor-release-notes',
                 'Camunda',
                 'high',
                 '2026-04-29T16:10:00+09:00',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-8-5-release-notes']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', CAST(0.9 AS REAL), $5\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_domain_knowledge_cites WHERE edge_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:camunda-zeebe-license:camunda-8-5-release-notes',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-8-5-release-notes',
                 'did:web:llm.etzhayyim.com',
                 '2026-04-29T16:10:00+09:00',
                 'edge:dk-cites:camunda-zeebe-license:camunda-8-5-release-notes']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      SELECT\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         '        $3, $4, $5, $6,\n'
         "        $7, $8, $9, 'anon', 'anon',\n"
         "        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM vertex_domain_knowledge_source WHERE vertex_id = $10\n'
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-2024-license-update',
                 'did:web:llm.etzhayyim.com',
                 'https://camunda.com/blog/2024/04/licensing-update-camunda-8-self-managed/',
                 'Camunda 8 Self-Managed licensing update',
                 'vendor-license-blog',
                 'Camunda',
                 'medium',
                 '2026-04-29T16:10:00+09:00',
                 '2026-04-29T16:10:00+09:00',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-2024-license-update']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      SELECT\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', CAST(0.9 AS REAL), $5\n"
         '      WHERE NOT EXISTS (\n'
         '        SELECT 1 FROM edge_domain_knowledge_cites WHERE edge_id = $6\n'
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:camunda-zeebe-license:camunda-2024-license-update',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429',
                 'at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-2024-license-update',
                 'did:web:llm.etzhayyim.com',
                 '2026-04-29T16:10:00+09:00',
                 'edge:dk-cites:camunda-zeebe-license:camunda-2024-license-update']}]

DOWN = [{'sql': 'DELETE FROM edge_domain_knowledge_cites WHERE src_vid = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-pricing-self-managed']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-license-reference']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-8-5-release-notes']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_source WHERE vertex_id = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-2024-license-update']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_chunk WHERE document_vid = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429']},
 {'sql': 'DELETE FROM vertex_domain_knowledge_document WHERE vertex_id = $1',
  'parameters': ['at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429']}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
