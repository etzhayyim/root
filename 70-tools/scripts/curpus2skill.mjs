#!/usr/bin/env node
/**
 * curpus2skill / corpus2skill
 *
 * Extracts evidence edges from public corpus tables to canonical ESCO skills
 * in vertex_skill. The extractor is deliberately conservative: it emits
 * edge_corpus_skill_evidence rows, not new vertex_skill rows.
 *
 * Usage:
 *   node 70-tools/scripts/curpus2skill.mjs --list-sources
 *   node 70-tools/scripts/curpus2skill.mjs --source legal-corpus --limit 100 --dry-run
 *   node 70-tools/scripts/curpus2skill.mjs --source houbun-article --min-score 0.82
 */
import { createHash } from "node:crypto";

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const OWNER_DID = "did:web:recruit.etzhayyim.com";
const EXTRACTOR_VERSION = "curpus2skill-v0.1.0";
const SOURCE = "curpus2skill";

const args = process.argv.slice(2);
const hasFlag = (k) => args.includes(`--${k}`);
const getArg = (k, d) => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1] ?? d;
};

const DRY_RUN = hasFlag("dry-run");
const SOURCE_ID = getArg("source", "legal-corpus");
const LIMIT = Number.parseInt(getArg("limit", "100"), 10);
const SKILL_LIMIT = Number.parseInt(getArg("skill-limit", "20000"), 10);
const TOP_K = Number.parseInt(getArg("top-k", "5"), 10);
const MIN_SCORE = Number.parseFloat(getArg("min-score", "0.9"));

const SOURCE_QUERIES = {
  "legal-corpus": {
    table: "vertex_legal_corpus_document",
    actorDid: "did:web:legal-corpus.etzhayyim.com",
    licenseColumn: "source_id",
    sql: `
      SELECT
        vertex_id,
        'vertex_legal_corpus_document' AS corpus_table,
        title,
        COALESCE(body_text, '') AS body,
        COALESCE(topic_tags_csv, '') AS tags,
        COALESCE(owner_did, 'did:web:legal-corpus.etzhayyim.com') AS owner_did,
        COALESCE(source_id, 'unknown') AS source_license
      FROM vertex_legal_corpus_document
      WHERE body_text IS NOT NULL
        AND body_text NOT LIKE 'signal:v1:%'
      LIMIT $1
    `,
  },
  "houbun-article": {
    table: "vertex_houbun_article",
    actorDid: "did:web:houbun.etzhayyim.com",
    licenseColumn: "source_url",
    sql: `
      SELECT
        vertex_id,
        'vertex_houbun_article' AS corpus_table,
        title,
        COALESCE(text, '') AS body,
        COALESCE(article_no, '') AS tags,
        COALESCE(owner_did, 'did:web:houbun.etzhayyim.com') AS owner_did,
        COALESCE(source_url, 'unknown') AS source_license
      FROM vertex_houbun_article
      WHERE text IS NOT NULL
        AND text NOT LIKE 'signal:v1:%'
      LIMIT $1
    `,
  },
  "domain-knowledge": {
    table: "vertex_domain_knowledge_chunk",
    actorDid: "did:web:llm.etzhayyim.com",
    licenseColumn: "keywords",
    sql: `
      SELECT
        c.vertex_id,
        'vertex_domain_knowledge_chunk' AS corpus_table,
        d.title,
        COALESCE(c.chunk_text, '') AS body,
        COALESCE(c.keywords, '') AS tags,
        COALESCE(d.owner_did, 'did:web:llm.etzhayyim.com') AS owner_did,
        COALESCE(c.keywords, 'unknown') AS source_license
      FROM vertex_domain_knowledge_chunk c
      LEFT JOIN vertex_domain_knowledge_document d ON d.vertex_id = c.document_vid
      WHERE c.chunk_text IS NOT NULL
        AND c.chunk_text NOT LIKE 'signal:v1:%'
      LIMIT $1
    `,
  },
};

if (hasFlag("help") || hasFlag("h")) {
  printHelp();
  process.exit(0);
}

if (hasFlag("list-sources")) {
  for (const [id, source] of Object.entries(SOURCE_QUERIES)) {
    console.log(`${id}\t${source.table}\t${source.actorDid}`);
  }
  process.exit(0);
}

if (!SOURCE_QUERIES[SOURCE_ID]) {
  console.error(`error: unknown --source ${SOURCE_ID}`);
  console.error(`known sources: ${Object.keys(SOURCE_QUERIES).join(", ")}`);
  process.exit(2);
}

function printHelp() {
  console.log(`Usage:
  node 70-tools/scripts/curpus2skill.mjs --list-sources
  node 70-tools/scripts/curpus2skill.mjs --source legal-corpus --limit 100 --dry-run

Options:
  --source       ${Object.keys(SOURCE_QUERIES).join(" | ")}
  --limit        corpus document limit (default: 100)
  --skill-limit  canonical skill load limit (default: 20000)
  --top-k        max skill matches per document (default: 5)
  --min-score    conservative threshold (default: 0.78)
  --dry-run      print JSON summary and do not write RisingWave
`);
}

let _pool = null;
async function pool() {
  if (_pool) return _pool;
  const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 120000 });
  return _pool;
}

function stableId(prefix, parts) {
  const digest = createHash("sha256").update(parts.join("\u001f")).digest("hex").slice(0, 24);
  return `${prefix}:${digest}`;
}

function normalize(text) {
  return String(text ?? "")
    .toLowerCase()
    .normalize("NFKC")
    .replace(/[^\p{Letter}\p{Number}+#.]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function tokenize(text) {
  return normalize(text)
    .split(" ")
    .filter((t) => t.length >= 2 && !STOPWORDS.has(t));
}

const STOPWORDS = new Set([
  "and", "or", "the", "for", "with", "from", "that", "this", "into", "are",
  "was", "were", "have", "has", "not", "する", "こと", "ため", "及び", "また",
]);

const GENERIC_SKILL_LABELS = new Set([
  "assume responsibility",
  "communication",
  "delegate responsibilities",
  "manage data",
  "manage financial and material resources",
  "product comprehension",
  "provide membership service",
]);

function parseAltLabels(value) {
  if (!value) return [];
  try {
    const parsed = JSON.parse(value);
    return Array.isArray(parsed) ? parsed.filter(Boolean).map(String) : [];
  } catch {
    return String(value).split(/\n|;/).map((s) => s.trim()).filter(Boolean);
  }
}

function compileSkill(row) {
  const labels = [row.name, row.label, ...parseAltLabels(row.alt_labels)]
    .filter(Boolean)
    .map(String);
  const normalizedLabels = [...new Set(labels.map(normalize).filter((s) => s.length >= 3))];
  const tokenSets = normalizedLabels.map((label) => tokenize(label));
  return {
    skillId: row.vertex_id,
    name: row.name || row.label || row.vertex_id,
    sourceLicense: row.source_license || null,
    labels: normalizedLabels,
    tokenSets,
  };
}

function labelIsUsable(label) {
  const tokens = tokenize(label);
  if (GENERIC_SKILL_LABELS.has(label)) return false;
  if (tokens.length < 2) return false;
  if (label.length < 14) return false;
  if (/^(manage|provide|perform|carry out|execute|use|apply|follow)\s/.test(label) && tokens.length < 4) {
    return false;
  }
  return true;
}

function evidenceSnippet(_rawText, normalizedText, label) {
  const idx = normalizedText.indexOf(label);
  if (idx === -1) {
    const first = label.split(" ")[0];
    const rawIdx = normalizedText.indexOf(first);
    return {
      text: normalizedText.slice(Math.max(0, rawIdx - 80), rawIdx === -1 ? 220 : rawIdx + 220),
      start: rawIdx === -1 ? 0 : rawIdx,
      end: rawIdx === -1 ? 0 : rawIdx + first.length,
    };
  }
  return {
    text: normalizedText.slice(Math.max(0, idx - 80), idx + label.length + 180),
    start: idx,
    end: idx + label.length,
  };
}

function scoreSkill(docText, normalizedDoc, skill) {
  if (GENERIC_SKILL_LABELS.has(normalize(skill.name))) return null;
  let best = null;
  for (let i = 0; i < skill.labels.length; i += 1) {
    const label = skill.labels[i];
    if (!labelIsUsable(label)) continue;
    if (normalizedDoc.includes(label)) {
      const score = Math.min(0.99, 0.9 + Math.min(0.09, label.length / 180));
      best = { score, matchKind: "exact_label", label };
      continue;
    }
    const tokens = skill.tokenSets[i] ?? [];
    if (tokens.length < 4) continue;
    const matched = tokens.filter((t) => normalizedDoc.includes(t)).length;
    const ratio = matched / tokens.length;
    if (ratio >= 1) {
      const score = 0.82 + Math.min(0.07, tokens.length / 100);
      if (!best || score > best.score) best = { score, matchKind: "token_overlap", label };
    }
  }
  if (!best || best.score < MIN_SCORE) return null;
  return { ...best, evidence: evidenceSnippet(docText, normalizedDoc, best.label) };
}

async function loadSkills(client) {
  const { rows } = await client.query(`
    SELECT vertex_id, label, name, alt_labels, source_license
    FROM vertex_skill
    WHERE COALESCE(name, label, '') <> ''
    LIMIT ${SKILL_LIMIT}
  `);
  return rows.map(compileSkill);
}

async function loadCorpus(client, source) {
  const { rows } = await client.query(source.sql.replaceAll("$1", String(LIMIT)));
  return rows;
}

function matchDocument(doc, skills) {
  const rawText = [doc.title, doc.tags, doc.body].filter(Boolean).join("\n");
  const normalizedDoc = normalize(rawText);
  const matches = [];
  for (const skill of skills) {
    const scored = scoreSkill(rawText, normalizedDoc, skill);
    if (scored) {
      matches.push({
        corpusVertexId: doc.vertex_id,
        corpusTable: doc.corpus_table,
        skillId: skill.skillId,
        skillName: skill.name,
        score: Number(scored.score.toFixed(4)),
        matchKind: scored.matchKind,
        evidenceText: scored.evidence.text.slice(0, 900),
        evidenceStart: scored.evidence.start,
        evidenceEnd: scored.evidence.end,
        sourceActorDid: doc.owner_did || SOURCE_QUERIES[SOURCE_ID].actorDid,
        sourceLicense: doc.source_license || null,
      });
    }
  }
  return matches.sort((a, b) => b.score - a.score).slice(0, TOP_K);
}

async function insertRun(client, run) {
  await client.query(`
    INSERT INTO vertex_corpus_skill_extraction_run (
      vertex_id, sensitivity_ord, owner_did, rkey, repo, label, source_table,
      source_actor_did, extractor_version, model_id, params_json, corpus_limit,
      skill_limit, min_score, matched_documents, emitted_edges, status,
      started_at, finished_at
    )
    SELECT
      $1,
      $2::BIGINT,
      $3,
      $4,
      $5,
      $6,
      $7,
      $8,
      $9,
      $10,
      $11,
      $12::BIGINT,
      $13::BIGINT,
      $14::DOUBLE PRECISION,
      $15::BIGINT,
      $16::BIGINT,
      $17,
      $18,
      $19
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_corpus_skill_extraction_run WHERE vertex_id = $1
    )
  `, [
    run.vertexId, 1, OWNER_DID, run.rkey, OWNER_DID, run.label, run.sourceTable,
    run.sourceActorDid, EXTRACTOR_VERSION, "lexical-v0", JSON.stringify(run.params),
    LIMIT, SKILL_LIMIT, MIN_SCORE, run.matchedDocuments, run.emittedEdges,
    run.status, run.startedAt, run.finishedAt,
  ]);
}

async function insertEvidence(client, runId, edge) {
  const edgeId = stableId("edge:corpus-skill", [
    edge.corpusTable,
    edge.corpusVertexId,
    edge.skillId,
    edge.matchKind,
  ]);
  await client.query(`
    INSERT INTO edge_corpus_skill_evidence (
      edge_id, corpus_vertex_id, corpus_table, skill_id, extraction_run_id,
      source_actor_did, match_kind, score, evidence_text, evidence_start,
      evidence_end, source, source_license, ingested_at, props
    )
    SELECT
      $1,
      $2,
      $3,
      $4,
      $5,
      $6,
      $7,
      $8::DOUBLE PRECISION,
      $9,
      $10::BIGINT,
      $11::BIGINT,
      $12,
      $13,
      $14,
      $15
    WHERE NOT EXISTS (
      SELECT 1 FROM edge_corpus_skill_evidence WHERE edge_id = $1
    )
  `, [
    edgeId, edge.corpusVertexId, edge.corpusTable, edge.skillId, runId,
    edge.sourceActorDid, edge.matchKind, edge.score, edge.evidenceText,
    edge.evidenceStart, edge.evidenceEnd, SOURCE, edge.sourceLicense,
    new Date().toISOString(), JSON.stringify({ skillName: edge.skillName }),
  ]);
}

async function main() {
  const source = SOURCE_QUERIES[SOURCE_ID];
  const client = await (await pool()).connect();
  const startedAt = new Date().toISOString();
  try {
    const [skills, docs] = await Promise.all([
      loadSkills(client),
      loadCorpus(client, source),
    ]);
    const edges = docs.flatMap((doc) => matchDocument(doc, skills));
    const runId = stableId("run:curpus2skill", [
      SOURCE_ID,
      startedAt,
      String(LIMIT),
      String(SKILL_LIMIT),
      String(MIN_SCORE),
    ]);
    const run = {
      vertexId: runId,
      rkey: runId.replace(/[^a-zA-Z0-9-]/g, "-").slice(0, 63),
      label: `curpus2skill ${SOURCE_ID} ${startedAt}`,
      sourceTable: source.table,
      sourceActorDid: source.actorDid,
      params: { source: SOURCE_ID, topK: TOP_K, dryRun: DRY_RUN },
      matchedDocuments: new Set(edges.map((e) => e.corpusVertexId)).size,
      emittedEdges: edges.length,
      status: DRY_RUN ? "dry_run" : "completed",
      startedAt,
      finishedAt: new Date().toISOString(),
    };

    if (!DRY_RUN) {
      await insertRun(client, run);
      for (const edge of edges) await insertEvidence(client, run.vertexId, edge);
    }

    console.log(JSON.stringify({
      dryRun: DRY_RUN,
      runId: run.vertexId,
      source: SOURCE_ID,
      sourceTable: source.table,
      documentsScanned: docs.length,
      skillsLoaded: skills.length,
      matchedDocuments: run.matchedDocuments,
      emittedEdges: run.emittedEdges,
      sample: edges.slice(0, 10),
    }, null, 2));
  } finally {
    client.release();
    if (_pool) await _pool.end();
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
