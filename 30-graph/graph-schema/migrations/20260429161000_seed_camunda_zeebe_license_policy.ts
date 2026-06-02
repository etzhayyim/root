import type { Kysely } from "kysely";
import { sql } from "kysely";

// tier: B
//
// Seed software-compliance knowledge for LLM RAG. This records the current
// Camunda/Zeebe licensing posture used by the BPMN-as-actor runtime.

const ownerDid = "did:web:llm.etzhayyim.com";
const actorDid = "did:web:bpmn.etzhayyim.com";
const createdAt = "2026-04-29T16:10:00+09:00";
const docVid =
  "at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.domainKnowledge/camunda-zeebe-license-policy-20260429";

const body = [
  "Camunda/Zeebe runtime policy as of 2026-04-29: etzhayyim pins the self-managed Zeebe broker to camunda/zeebe:8.5.23 as a short-term Zeebe-only compatibility track.",
  "Do not deploy Camunda Operate, Tasklist, Optimize, or Elasticsearch/OpenSearch under this 8.5 compatibility posture without separate license review.",
  "Camunda 8.6 and later self-managed production usage changes the licensing posture for Zeebe and the broader Camunda 8 stack; production use should require Enterprise/SaaS approval or an approved replacement plan.",
  "Zeebe 8.5 preserves the existing BPMN XML plus zeebe:taskDefinition, zeebe:ioMapping, and pyzeebe worker contract with minimal code churn, but it is past upstream maintenance end and is not a long-term production baseline.",
  "Before applying a live downgrade from 8.6.x to 8.5.x, validate persisted partition data compatibility or recreate pilot broker state. Do not assume Zeebe broker downgrades are safe in-place.",
].join("\n");

const chunks = [
  "etzhayyim pins the self-managed Zeebe broker to camunda/zeebe:8.5.23 as a short-term Zeebe-only compatibility track.",
  "Do not deploy Operate, Tasklist, Optimize, or Elasticsearch/OpenSearch under the 8.5 compatibility posture without separate license review.",
  "Camunda 8.6+ self-managed production usage changes the licensing posture; require Enterprise/SaaS approval or an approved replacement plan.",
  "Zeebe 8.5 keeps existing BPMN zeebe:taskDefinition, zeebe:ioMapping, and pyzeebe worker contracts with minimal code churn, but is past maintenance end.",
  "Before live downgrade from 8.6.x to 8.5.x, validate persisted partition data compatibility or recreate pilot broker state.",
];

const sources = [
  {
    vid: "at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-pricing-self-managed",
    url: "https://camunda.com/pricing/",
    title: "Camunda pricing: Self-Managed Free and Enterprise",
    kind: "vendor-pricing",
    publisher: "Camunda",
    confidence: "high",
  },
  {
    vid: "at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-license-reference",
    url: "https://docs.camunda.io/docs/reference/licenses/",
    title: "Camunda 8 license reference",
    kind: "vendor-license-doc",
    publisher: "Camunda",
    confidence: "high",
  },
  {
    vid: "at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-8-5-release-notes",
    url: "https://docs.camunda.io/docs/8.5/reference/release-notes/850/",
    title: "Camunda 8.5 release notes and maintenance window",
    kind: "vendor-release-notes",
    publisher: "Camunda",
    confidence: "high",
  },
  {
    vid: "at://did:web:llm.etzhayyim.com/com.etzhayyim.apps.llm.knowledgeSource/camunda-2024-license-update",
    url: "https://camunda.com/blog/2024/04/licensing-update-camunda-8-self-managed/",
    title: "Camunda 8 Self-Managed licensing update",
    kind: "vendor-license-blog",
    publisher: "Camunda",
    confidence: "medium",
  },
];

export async function up(db: Kysely<unknown>): Promise<void> {
  await sql`
    INSERT INTO vertex_domain_knowledge_document (
      vertex_id, _seq, created_date, sensitivity_ord, owner_did, actor_did,
      domain, canonical_work_id, game_slug, title, lang, body, body_hash,
      source_record_uri, confidence, status, created_at, updated_at,
      org_id, user_id, actor_id, props
    )
    SELECT
      ${docVid}, 1, DATE '2026-04-29', 1, ${ownerDid}, ${actorDid},
      'software_compliance', 'software:camunda-zeebe', '',
      'Camunda/Zeebe runtime license policy 2026-04-29', 'ja', ${body},
      'sha256:pending', 'git:50-infra/vultr/zeebe/zeebe.yaml',
      'high', 'active', ${createdAt}, ${createdAt},
      'anon', 'anon', 'sys.llm.domain-knowledge.seed.camunda-zeebe-license',
      '{"runtime":"zeebe","pinnedImage":"camunda/zeebe:8.5.23","posture":"short-term-compatibility-track"}'
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_domain_knowledge_document WHERE vertex_id = ${docVid}
    )
  `.execute(db);

  for (const [i, chunk] of chunks.entries()) {
    const chunkVid = `${docVid}/chunk-${i + 1}`;
    const seq = sql.raw(String(i + 1));
    const tokenCount = sql.raw(String(Math.ceil(chunk.length / 2)));
    await sql`
      INSERT INTO vertex_domain_knowledge_chunk (
        vertex_id, _seq, created_date, sensitivity_ord, owner_did,
        document_vid, chunk_index, chunk_text, keywords, token_count, lang,
        embedding, embedding_norm, embedding_model, embedded_at, created_at,
        org_id, user_id, actor_id
      )
      SELECT
        ${chunkVid}, ${seq}, DATE '2026-04-29', 1, ${ownerDid},
        ${docVid}, ${seq}, ${chunk},
        'camunda,zeebe,license,8.5,8.6,enterprise,self-managed,operate,tasklist,pyzeebe',
        ${tokenCount}, 'ja',
        NULL, CAST(NULL AS REAL), NULL, NULL, ${createdAt}, 'anon', 'anon',
        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_domain_knowledge_chunk WHERE vertex_id = ${chunkVid}
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
      SELECT
        ${source.vid}, 1, DATE '2026-04-29', 1, ${ownerDid},
        ${source.url}, ${source.title}, ${source.kind}, ${source.publisher},
        ${source.confidence}, ${createdAt}, ${createdAt}, 'anon', 'anon',
        'sys.llm.domain-knowledge.seed.camunda-zeebe-license'
      WHERE NOT EXISTS (
        SELECT 1 FROM vertex_domain_knowledge_source WHERE vertex_id = ${source.vid}
      )
    `.execute(db);

    const edgeId = `edge:dk-cites:camunda-zeebe-license:${source.vid.split("/").pop()}`;
    await sql`
      INSERT INTO edge_domain_knowledge_cites (
        edge_id, src_vid, dst_vid, _seq, created_date, sensitivity_ord,
        owner_did, relation_kind, confidence, created_at
      )
      SELECT
        ${edgeId}, ${docVid}, ${source.vid},
        1, DATE '2026-04-29', 1, ${ownerDid}, 'cites', CAST(0.9 AS REAL), ${createdAt}
      WHERE NOT EXISTS (
        SELECT 1 FROM edge_domain_knowledge_cites WHERE edge_id = ${edgeId}
      )
    `.execute(db);
  }
}

export async function down(db: Kysely<unknown>): Promise<void> {
  await sql`DELETE FROM edge_domain_knowledge_cites WHERE src_vid = ${docVid}`.execute(db);
  for (const source of sources) {
    await sql`DELETE FROM vertex_domain_knowledge_source WHERE vertex_id = ${source.vid}`.execute(db);
  }
  await sql`DELETE FROM vertex_domain_knowledge_chunk WHERE document_vid = ${docVid}`.execute(db);
  await sql`DELETE FROM vertex_domain_knowledge_document WHERE vertex_id = ${docVid}`.execute(db);
}
