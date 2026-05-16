"""Captured from Kysely migration 20260429144000_llm_domain_knowledge_rag."""

from __future__ import annotations

from alembic import op

from graph_schema.db import execute_bound_statements


revision = "r_20260429144000_llm_domain_knowledge_rag"
down_revision = 'r_20260429140500_seed_yoro_actor_quality_bpmn'
branch_labels = None
depends_on = None

UP = [{'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_document (\n'
         '      vertex_id       VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      created_date    DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did       VARCHAR,\n'
         '      actor_did       VARCHAR,\n'
         '      domain          VARCHAR,\n'
         '      canonical_work_id VARCHAR,\n'
         '      game_slug       VARCHAR,\n'
         '      title           VARCHAR,\n'
         '      lang            VARCHAR,\n'
         '      body            VARCHAR,\n'
         '      body_hash       VARCHAR,\n'
         '      source_record_uri VARCHAR,\n'
         '      confidence      VARCHAR,\n'
         '      status          VARCHAR,\n'
         '      created_at      VARCHAR,\n'
         '      updated_at      VARCHAR,\n'
         '      org_id          VARCHAR,\n'
         '      user_id         VARCHAR,\n'
         '      actor_id        VARCHAR,\n'
         '      props           VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_chunk (\n'
         '      vertex_id       VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      created_date    DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did       VARCHAR,\n'
         '      document_vid    VARCHAR,\n'
         '      chunk_index     BIGINT,\n'
         '      chunk_text      VARCHAR,\n'
         '      keywords        VARCHAR,\n'
         '      token_count     BIGINT,\n'
         '      lang            VARCHAR,\n'
         '      embedding       VARCHAR,\n'
         '      embedding_norm  REAL,\n'
         '      embedding_model VARCHAR,\n'
         '      embedded_at     VARCHAR,\n'
         '      created_at      VARCHAR,\n'
         '      org_id          VARCHAR,\n'
         '      user_id         VARCHAR,\n'
         '      actor_id        VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_source (\n'
         '      vertex_id       VARCHAR PRIMARY KEY,\n'
         '      _seq            BIGINT,\n'
         '      created_date    DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did       VARCHAR,\n'
         '      url             VARCHAR,\n'
         '      title           VARCHAR,\n'
         '      source_kind     VARCHAR,\n'
         '      publisher       VARCHAR,\n'
         '      confidence      VARCHAR,\n'
         '      retrieved_at    VARCHAR,\n'
         '      created_at      VARCHAR,\n'
         '      org_id          VARCHAR,\n'
         '      user_id         VARCHAR,\n'
         '      actor_id        VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_domain_knowledge_cites (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      _seq            BIGINT,\n'
         '      created_date    DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did       VARCHAR,\n'
         '      relation_kind   VARCHAR,\n'
         '      confidence      REAL,\n'
         '      created_at      VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': '\n'
         '    CREATE TABLE IF NOT EXISTS edge_domain_knowledge_about (\n'
         '      edge_id         VARCHAR PRIMARY KEY,\n'
         '      src_vid         VARCHAR,\n'
         '      dst_vid         VARCHAR,\n'
         '      _seq            BIGINT,\n'
         '      created_date    DATE,\n'
         '      sensitivity_ord BIGINT,\n'
         '      owner_did       VARCHAR,\n'
         '      relation_kind   VARCHAR,\n'
         '      created_at      VARCHAR\n'
         '    )\n'
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_dk_doc_domain_game_lang ON '
         'vertex_domain_knowledge_document (domain, game_slug, lang)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_dk_doc_actor_updated ON vertex_domain_knowledge_document '
         '(actor_did, updated_at)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_dk_chunk_doc ON vertex_domain_knowledge_chunk '
         '(document_vid, chunk_index)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_dk_chunk_lang ON vertex_domain_knowledge_chunk (lang)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_dk_source_url ON vertex_domain_knowledge_source (url)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_dk_cites_src ON edge_domain_knowledge_cites '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_dk_cites_dst ON edge_domain_knowledge_cites '
         '(dst_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_dk_about_src ON edge_domain_knowledge_about '
         '(src_vid)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_edge_dk_about_dst ON edge_domain_knowledge_about '
         '(dst_vid)',
  'parameters': []},
 {'sql': '\n'
         '    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_knowledge_search AS\n'
         '    SELECT\n'
         '      c.vertex_id AS chunk_vid,\n'
         '      c.document_vid,\n'
         '      d.domain,\n'
         '      d.actor_did,\n'
         '      d.canonical_work_id,\n'
         '      d.game_slug,\n'
         '      d.title,\n'
         '      d.lang,\n'
         '      c.chunk_index,\n'
         '      c.chunk_text,\n'
         '      c.keywords,\n'
         '      c.embedding,\n'
         '      c.embedding_norm,\n'
         '      d.confidence,\n'
         '      d.updated_at,\n'
         "      lower(coalesce(d.title, '') || ' ' || coalesce(c.chunk_text, '') || ' ' || "
         "coalesce(c.keywords, '')) AS search_text\n"
         '    FROM vertex_domain_knowledge_chunk c\n'
         '    JOIN vertex_domain_knowledge_document d ON d.vertex_id = c.document_vid\n'
         "    WHERE d.status = 'active'\n"
         '  ',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_mv_dk_search_game_lang ON mv_domain_knowledge_search '
         '(game_slug, lang)',
  'parameters': []},
 {'sql': 'CREATE INDEX IF NOT EXISTS idx_mv_dk_search_domain ON mv_domain_knowledge_search '
         '(domain)',
  'parameters': []},
 {'sql': '\n'
         '    INSERT INTO vertex_domain_knowledge_document (\n'
         '      vertex_id, _seq, created_date, sensitivity_ord, owner_did, actor_did,\n'
         '      domain, canonical_work_id, game_slug, title, lang, body, body_hash,\n'
         '      source_record_uri, confidence, status, created_at, updated_at,\n'
         '      org_id, user_id, actor_id, props\n'
         '    )\n'
         '    VALUES (\n'
         "      $1, 1, DATE '2026-04-29', 1, $2, $3,\n"
         "      'media_gamers', 'game:work:pokemon-pokopia', 'pokemon-pokopia',\n"
         "      'Pokémon Pokopia Dream Island domain knowledge', 'ja', $4,\n"
         "      'sha256:pending', "
         "'at://did:web:a7m8oocs.gftd.ai/ai.gftd.apps.media_gamers.article/3mkmcl7x3bt2b',\n"
         "      'high', 'active', $5, $6,\n"
         "      'anon', 'anon', 'sys.llm.domain-knowledge.seed',\n"
         '      $7\n'
         '    )\n'
         '  ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 'did:web:llm.gftd.ai',
                 'did:web:a7m8oocs.gftd.ai',
                 'Pokémon Pokopia / ぽこあポケモンの夢島に行くには、まずフワンテと仲良くなってフワンテのすみかを完成させる。\n'
                 'フワンテの棲家、つまり『あたたかい風の棲家』は初回アンロック条件として扱う。\n'
                 '棲家完成後、ポケモン人形を見つけ、置いた人形を調べるか、人形を持った状態でフワンテに話しかけ、『夢島に行きたい』を選ぶ。\n'
                 '一度フワンテの棲家を完成させた後は、夢島へ行くたびに棲家を作り直す必要はない。\n'
                 '1つの町のフワンテで選べる夢島は1日1種類。同じ日なら同じ夢島へ何度でも戻れる。帰る時はフワンテに話しかける。\n'
                 'GameSpot は、フワンテの棲家についてキャンプファイア3つを横に並べ、ヒトカゲに火をつけてもらう手順として説明している。\n'
                 '参考画像: '
                 'https://www.gamespot.com/a/uploads/scale_super/1639/16394540/4662653-drifloonupdrafts.jpg',
                 '2026-04-29T14:40:00+09:00',
                 '2026-04-29T14:40:00+09:00',
                 '{"image":"https://www.gamespot.com/a/uploads/scale_super/1639/16394540/4662653-drifloonupdrafts.jpg"}']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-1',
                 1,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 1,
                 '夢島に行くには、まずフワンテと仲良くなってフワンテのすみかを完成させる。あたたかい風の棲家は初回アンロック条件。',
                 28,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-2',
                 2,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 2,
                 '棲家完成後、ポケモン人形を見つけ、置いた人形を調べるか、人形を持った状態でフワンテに話しかけ、『夢島に行きたい』を選ぶ。',
                 30,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-3',
                 3,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 3,
                 '一度フワンテの棲家を完成させた後は、夢島へ行くたびに棲家を作り直す必要はない。',
                 20,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-4',
                 4,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 4,
                 '1つの町のフワンテで選べる夢島は1日1種類。同じ日なら同じ夢島へ何度でも戻れる。帰る時はフワンテに話しかける。',
                 28,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-5',
                 5,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 5,
                 'GameSpot は、フワンテの棲家についてキャンプファイア3つを横に並べ、ヒトカゲに火をつけてもらう手順として説明している。',
                 32,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_chunk (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        document_vid, chunk_index, chunk_text, keywords, token_count, lang,\n'
         '        embedding, embedding_norm, embedding_model, embedded_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, $2, DATE '2026-04-29', 1, $3,\n"
         '        $4, $5, $6,\n'
         "        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',\n"
         "        $7, 'ja',\n"
         "        NULL, NULL, NULL, NULL, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island/chunk-6',
                 6,
                 'did:web:llm.gftd.ai',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 6,
                 'Dream Island の参考画像: '
                 'https://www.gamespot.com/a/uploads/scale_super/1639/16394540/4662653-drifloonupdrafts.jpg',
                 55,
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         "        $3, $4, $5, '', $6,\n"
         "        $7, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/nintendo-pokopia-dream-island',
                 'did:web:llm.gftd.ai',
                 'https://en-americas-support.nintendo.com/app/answers/detail/a_id/71382',
                 'Nintendo Support: How to Visit a Dream Island (Pokémon Pokopia)',
                 'official-support',
                 'high',
                 '2026-04-29T14:40:00+09:00',
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', 0.9, $5\n"
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:nintendo-pokopia-dream-island',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/nintendo-pokopia-dream-island',
                 'did:web:llm.gftd.ai',
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         "        $3, $4, $5, '', $6,\n"
         "        $7, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/gamespot-pokopia-dream-island',
                 'did:web:llm.gftd.ai',
                 'https://www.gamespot.com/articles/how-dream-islands-work-in-pokemon-pokopia/1100-6538621/',
                 'GameSpot: How Dream Islands Work in Pokemon Pokopia',
                 'guide',
                 'medium',
                 '2026-04-29T14:40:00+09:00',
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', 0.9, $5\n"
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:gamespot-pokopia-dream-island',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/gamespot-pokopia-dream-island',
                 'did:web:llm.gftd.ai',
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO vertex_domain_knowledge_source (\n'
         '        vertex_id, _seq, created_date, sensitivity_ord, owner_did,\n'
         '        url, title, source_kind, publisher, confidence, retrieved_at, created_at,\n'
         '        org_id, user_id, actor_id\n'
         '      )\n'
         '      VALUES (\n'
         "        $1, 1, DATE '2026-04-29', 1, $2,\n"
         "        $3, $4, $5, '', $6,\n"
         "        $7, $8, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'\n"
         '      )\n'
         '    ',
  'parameters': ['at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/gamespot-pokopia-dream-island-image',
                 'did:web:llm.gftd.ai',
                 'https://www.gamespot.com/a/uploads/scale_super/1639/16394540/4662653-drifloonupdrafts.jpg',
                 'GameSpot image: Drifloon brings you to Dream Island',
                 'image',
                 'medium',
                 '2026-04-29T14:40:00+09:00',
                 '2026-04-29T14:40:00+09:00']},
 {'sql': '\n'
         '      INSERT INTO edge_domain_knowledge_cites (\n'
         '        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,\n'
         '        owner_did, relation_kind, confidence, created_at\n'
         '      )\n'
         '      VALUES (\n'
         '        $1, $2, $3,\n'
         "        1, DATE '2026-04-29', 1, $4, 'cites', 0.9, $5\n"
         '      )\n'
         '    ',
  'parameters': ['edge:dk-cites:gamespot-pokopia-dream-island-image',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.domainKnowledge/pokemon-pokopia-dream-island',
                 'at://did:web:llm.gftd.ai/ai.gftd.apps.llm.knowledgeSource/gamespot-pokopia-dream-island-image',
                 'did:web:llm.gftd.ai',
                 '2026-04-29T14:40:00+09:00']}]

DOWN = [{'sql': 'DROP INDEX IF EXISTS idx_mv_dk_search_domain', 'parameters': []},
 {'sql': 'DROP INDEX IF EXISTS idx_mv_dk_search_game_lang', 'parameters': []},
 {'sql': 'DROP MATERIALIZED VIEW IF EXISTS mv_domain_knowledge_search', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_domain_knowledge_about', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS edge_domain_knowledge_cites', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_domain_knowledge_source', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_domain_knowledge_chunk', 'parameters': []},
 {'sql': 'DROP TABLE IF EXISTS vertex_domain_knowledge_document', 'parameters': []}]


def upgrade() -> None:
    execute_bound_statements(op.get_bind(), UP)


def downgrade() -> None:
    execute_bound_statements(op.get_bind(), DOWN)
