import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: B
//
// Generic domain-knowledge RAG spine for llm.etzhayyim.com.
// Facts live in RisingWave vertices and are retrieved by Zeebe Python/LangGraph
// workers. CF Workers must not hard-code domain facts.

const ownerDid = "did:web:llm.etzhayyim.com";
const mediaGamersDid = "did:web:a7m8oocs.etzhayyim.com";
const createdAt = "2026-04-29T14:40:00+09:00";
const pokopiaDocVid =
  "at://did:web:llm.etzhayyim.com/app.etzhayyim.apps.llm.domainKnowledge/pokemon-pokopia-dream-island";
const pokopiaImageUrl =
  "https://www.gamespot.com/a/uploads/scale_super/1639/16394540/4662653-drifloonupdrafts.jpg";

const pokopiaBody = [
  "Pokémon Pokopia / ぽこあポケモンの夢島に行くには、まずフワンテと仲良くなってフワンテのすみかを完成させる。",
  "フワンテの棲家、つまり『あたたかい風の棲家』は初回アンロック条件として扱う。",
  "棲家完成後、ポケモン人形を見つけ、置いた人形を調べるか、人形を持った状態でフワンテに話しかけ、『夢島に行きたい』を選ぶ。",
  "一度フワンテの棲家を完成させた後は、夢島へ行くたびに棲家を作り直す必要はない。",
  "1つの町のフワンテで選べる夢島は1日1種類。同じ日なら同じ夢島へ何度でも戻れる。帰る時はフワンテに話しかける。",
  "GameSpot は、フワンテの棲家についてキャンプファイア3つを横に並べ、ヒトカゲに火をつけてもらう手順として説明している。",
  `参考画像: ${pokopiaImageUrl}`,
].join("\n");

const sources = [
  {
    vid: "at://did:web:llm.etzhayyim.com/app.etzhayyim.apps.llm.knowledgeSource/nintendo-pokopia-dream-island",
    url: "https://en-americas-support.nintendo.com/app/answers/detail/a_id/71382",
    title: "Nintendo Support: How to Visit a Dream Island (Pokémon Pokopia)",
    kind: "official-support",
    confidence: "high",
  },
  {
    vid: "at://did:web:llm.etzhayyim.com/app.etzhayyim.apps.llm.knowledgeSource/gamespot-pokopia-dream-island",
    url: "https://www.gamespot.com/articles/how-dream-islands-work-in-pokemon-pokopia/1100-6538621/",
    title: "GameSpot: How Dream Islands Work in Pokemon Pokopia",
    kind: "guide",
    confidence: "medium",
  },
  {
    vid: "at://did:web:llm.etzhayyim.com/app.etzhayyim.apps.llm.knowledgeSource/gamespot-pokopia-dream-island-image",
    url: pokopiaImageUrl,
    title: "GameSpot image: Drifloon brings you to Dream Island",
    kind: "image",
    confidence: "medium",
  },
];

const chunks = [
  "夢島に行くには、まずフワンテと仲良くなってフワンテのすみかを完成させる。あたたかい風の棲家は初回アンロック条件。",
  "棲家完成後、ポケモン人形を見つけ、置いた人形を調べるか、人形を持った状態でフワンテに話しかけ、『夢島に行きたい』を選ぶ。",
  "一度フワンテの棲家を完成させた後は、夢島へ行くたびに棲家を作り直す必要はない。",
  "1つの町のフワンテで選べる夢島は1日1種類。同じ日なら同じ夢島へ何度でも戻れる。帰る時はフワンテに話しかける。",
  "GameSpot は、フワンテの棲家についてキャンプファイア3つを横に並べ、ヒトカゲに火をつけてもらう手順として説明している。",
  `Dream Island の参考画像: ${pokopiaImageUrl}`,
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_document (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      actor_did       VARCHAR,
      domain          VARCHAR,
      canonical_work_id VARCHAR,
      game_slug       VARCHAR,
      title           VARCHAR,
      lang            VARCHAR,
      body            VARCHAR,
      body_hash       VARCHAR,
      source_record_uri VARCHAR,
      confidence      VARCHAR,
      status          VARCHAR,
      created_at      VARCHAR,
      updated_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR,
      props           VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_chunk (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      document_vid    VARCHAR,
      chunk_index     BIGINT,
      chunk_text      VARCHAR,
      keywords        VARCHAR,
      token_count     BIGINT,
      lang            VARCHAR,
      embedding       VARCHAR,
      embedding_norm  REAL,
      embedding_model VARCHAR,
      embedded_at     VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS vertex_domain_knowledge_source (
      vertex_id       VARCHAR PRIMARY KEY,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      url             VARCHAR,
      title           VARCHAR,
      source_kind     VARCHAR,
      publisher       VARCHAR,
      confidence      VARCHAR,
      retrieved_at    VARCHAR,
      created_at      VARCHAR,
      org_id          VARCHAR,
      user_id         VARCHAR,
      actor_id        VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_domain_knowledge_cites (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      relation_kind   VARCHAR,
      confidence      REAL,
      created_at      VARCHAR
    )
  `.execute(db);

  await sql`
    CREATE TABLE IF NOT EXISTS edge_domain_knowledge_about (
      edge_id         VARCHAR PRIMARY KEY,
      src_vid         VARCHAR,
      dst_vid         VARCHAR,
      _seq            BIGINT,
      created_date    DATE,
      sensitivity_ord BIGINT,
      owner_did       VARCHAR,
      relation_kind   VARCHAR,
      created_at      VARCHAR
    )
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_dk_doc_domain_game_lang ON vertex_domain_knowledge_document (domain, game_slug, lang)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dk_doc_actor_updated ON vertex_domain_knowledge_document (actor_did, updated_at)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dk_chunk_doc ON vertex_domain_knowledge_chunk (document_vid, chunk_index)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dk_chunk_lang ON vertex_domain_knowledge_chunk (lang)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_dk_source_url ON vertex_domain_knowledge_source (url)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dk_cites_src ON edge_domain_knowledge_cites (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dk_cites_dst ON edge_domain_knowledge_cites (dst_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dk_about_src ON edge_domain_knowledge_about (src_vid)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_edge_dk_about_dst ON edge_domain_knowledge_about (dst_vid)`.execute(db);

  await sql`
    CREATE MATERIALIZED VIEW IF NOT EXISTS mv_domain_knowledge_search AS
    SELECT
      c.vertex_id AS chunk_vid,
      c.document_vid,
      d.domain,
      d.actor_did,
      d.canonical_work_id,
      d.game_slug,
      d.title,
      d.lang,
      c.chunk_index,
      c.chunk_text,
      c.keywords,
      c.embedding,
      c.embedding_norm,
      d.confidence,
      d.updated_at,
      lower(coalesce(d.title, '') || ' ' || coalesce(c.chunk_text, '') || ' ' || coalesce(c.keywords, '')) AS search_text
    FROM vertex_domain_knowledge_chunk c
    JOIN vertex_domain_knowledge_document d ON d.vertex_id = c.document_vid
    WHERE d.status = 'active'
  `.execute(db);

  await sql`CREATE INDEX IF NOT EXISTS idx_mv_dk_search_game_lang ON mv_domain_knowledge_search (game_slug, lang)`.execute(db);
  await sql`CREATE INDEX IF NOT EXISTS idx_mv_dk_search_domain ON mv_domain_knowledge_search (domain)`.execute(db);

  await sql`
    INSERT INTO vertex_domain_knowledge_document (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did, actor_did,
      domain, canonical_work_id, game_slug, title, lang, body, body_hash,
      source_record_uri, confidence, status, created_at, updated_at,
      org_id, user_id, actor_id, props
    )
    VALUES (
      ${pokopiaDocVid}, 1, DATE '2026-04-29', 1, ${ownerDid}, ${mediaGamersDid},
      'media_gamers', 'game:work:pokemon-pokopia', 'pokemon-pokopia',
      'Pokémon Pokopia Dream Island domain knowledge', 'ja', ${pokopiaBody},
      'sha256:pending', 'at://did:web:a7m8oocs.etzhayyim.com/app.etzhayyim.apps.media_gamers.article/3mkmcl7x3bt2b',
      'high', 'active', ${createdAt}, ${createdAt},
      'anon', 'anon', 'sys.llm.domain-knowledge.seed',
      ${JSON.stringify({ image: pokopiaImageUrl })}
    )
  `.execute(db);

  for (const [i, chunk] of chunks.entries()) {
    await sql`
      INSERT INTO vertex_domain_knowledge_chunk (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        document_vid, chunk_index, chunk_text, keywords, token_count, lang,
        embedding, embedding_norm, embedding_model, embedded_at, created_at,
        org_id, user_id, actor_id
      )
      VALUES (
        ${`${pokopiaDocVid}/chunk-${i + 1}`}, ${i + 1}, DATE '2026-04-29', 1, ${ownerDid},
        ${pokopiaDocVid}, ${i + 1}, ${chunk},
        'pokemon-pokopia,ぽこあポケモン,夢島,フワンテ,あたたかい風の棲家,ポケモン人形',
        ${Math.ceil(chunk.length / 2)}, 'ja',
        NULL, NULL, NULL, NULL, ${createdAt}, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'
      )
    `.execute(db);
  }

  for (const source of sources) {
    await sql`
      INSERT INTO vertex_domain_knowledge_source (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        url, title, source_kind, publisher, confidence, retrieved_at, created_at,
        org_id, user_id, actor_id
      )
      VALUES (
        ${source.vid}, 1, DATE '2026-04-29', 1, ${ownerDid},
        ${source.url}, ${source.title}, ${source.kind}, '', ${source.confidence},
        ${createdAt}, ${createdAt}, 'anon', 'anon', 'sys.llm.domain-knowledge.seed'
      )
    `.execute(db);

    await sql`
      INSERT INTO edge_domain_knowledge_cites (
        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,
        owner_did, relation_kind, confidence, created_at
      )
      VALUES (
        ${`edge:dk-cites:${source.vid.split("/").pop()}`}, ${pokopiaDocVid}, ${source.vid},
        1, DATE '2026-04-29', 1, ${ownerDid}, 'cites', 0.9, ${createdAt}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DROP INDEX IF EXISTS idx_mv_dk_search_domain`.execute(db);
  await sql`DROP INDEX IF EXISTS idx_mv_dk_search_game_lang`.execute(db);
  await sql`DROP MATERIALIZED VIEW IF EXISTS mv_domain_knowledge_search`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_domain_knowledge_about`.execute(db);
  await sql`DROP TABLE IF EXISTS edge_domain_knowledge_cites`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_knowledge_source`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_knowledge_chunk`.execute(db);
  await sql`DROP TABLE IF EXISTS vertex_domain_knowledge_document`.execute(db);
}
