#!/usr/bin/env node
/**
 * Yabai baseline ingest — loads 1400+ JSON-LD records from
 * 60-apps/etzhayyim-project-yabai/content/{entity,evidence,risk}/*.jsonld
 * directly into vertex_yabai_{entity,evidence,risk} on RisingWave.
 *
 * Mirrors the direct-PG pattern used by bulk-stream-ingest.mjs (legal-entity).
 *
 * Run:
 *   node 70-tools/scripts/yabai-baseline-ingest.mjs [--dry-run] [--limit N]
 *
 * Pre-req: 20260417120000_vertex_yabai_tables.ts migration applied.
 */
import { readdir, readFile } from "node:fs/promises";
import { join } from "node:path";

const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");

const KOTOBA_URL = process.env.KOTOBA_URL
  ?? "REDACTED_USE_DATABASE_URL_ENV?sslmode=disable";
const REPO_DID = "did:web:yabai.etzhayyim.com";
const CONTENT_DIR = "/Users/junkawasaki/github/etzhayyim-root/60-apps/etzhayyim-project-yabai/content";

const args = process.argv.slice(2);
const DRY_RUN = args.includes("--dry-run");
const LIMIT = Number(args.includes("--limit") ? args[args.indexOf("--limit") + 1] : 0);

const pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 120_000 });

const today = new Date().toISOString().slice(0, 10);
const BATCH = 200;

function atUri(kind, id) {
  return `at://${REPO_DID}/com.etzhayyim.apps.yabai.${kind}/${id}`;
}

async function loadJsonldDir(dir) {
  const files = await readdir(dir);
  const out = [];
  for (const f of files) {
    if (!f.endsWith(".jsonld")) continue;
    const raw = await readFile(join(dir, f), "utf8");
    try { out.push(JSON.parse(raw)); } catch (e) {
      console.warn(`skip bad jsonld ${f}: ${e.message}`);
    }
  }
  return out;
}

async function insertBatch(table, rows, columns) {
  if (rows.length === 0) return 0;
  const placeholders = rows.map((_, i) => {
    const base = i * columns.length;
    return `(${columns.map((_, j) => `$${base + j + 1}`).join(", ")})`;
  }).join(", ");
  const values = rows.flatMap((r) => columns.map((c) => r[c] ?? null));
  const sql = `INSERT INTO ${table} (${columns.join(", ")}) VALUES ${placeholders}`;
  if (DRY_RUN) {
    console.log(`[dry-run] ${table}: ${rows.length} rows`);
    return rows.length;
  }
  await pool.query(sql, values);
  return rows.length;
}

async function ingestEntities() {
  const recs = await loadJsonldDir(join(CONTENT_DIR, "entity"));
  const capped = LIMIT > 0 ? recs.slice(0, LIMIT) : recs;
  console.log(`entity: ${capped.length} records`);
  const cols = ["vertex_id", "_seq", "created_date", "sensitivity_ord", "owner_did",
    "rkey", "repo", "entity_id", "entity_type", "name", "value", "canonical_name",
    "aliases", "source", "created_at", "org_id", "user_id", "actor_id"];
  let n = 0;
  for (let i = 0; i < capped.length; i += BATCH) {
    const rows = capped.slice(i, i + BATCH).map((rec, idx) => ({
      vertex_id: atUri("entity", rec.entityId),
      _seq: 0, created_date: today, sensitivity_ord: 300, owner_did: REPO_DID,
      rkey: rec.entityId, repo: REPO_DID,
      entity_id: rec.entityId,
      entity_type: rec["@type"] === "Organization" ? "Organization"
        : rec["@type"] === "Person" ? "Person" : "Unknown",
      name: rec.canonicalName ?? rec.name ?? "",
      value: rec.canonicalName ?? "",
      canonical_name: rec.canonicalName ?? null,
      aliases: Array.isArray(rec.aliases) ? JSON.stringify(rec.aliases) : null,
      source: rec.source ?? "baseline",
      created_at: rec.createdAt ?? new Date().toISOString(),
      org_id: "anon", user_id: "anon", actor_id: "sys.baseline",
    }));
    n += await insertBatch("vertex_yabai_entity", rows, cols);
  }
  console.log(`entity inserted: ${n}`);
}

async function ingestEvidence() {
  const recs = await loadJsonldDir(join(CONTENT_DIR, "evidence"));
  const capped = LIMIT > 0 ? recs.slice(0, LIMIT) : recs;
  console.log(`evidence: ${capped.length} records`);
  const cols = ["vertex_id", "_seq", "created_date", "sensitivity_ord", "owner_did",
    "rkey", "repo", "evidence_id", "entity_id", "category", "confidence", "severity",
    "probability", "source", "source_reliability", "jurisdiction", "summary",
    "description", "verification_id", "occurred_at", "created_at",
    "org_id", "user_id", "actor_id"];
  let n = 0;
  for (let i = 0; i < capped.length; i += BATCH) {
    const rows = capped.slice(i, i + BATCH).map((rec) => ({
      vertex_id: atUri("evidence", rec.evidenceId),
      _seq: 0, created_date: today, sensitivity_ord: 300, owner_did: REPO_DID,
      rkey: rec.evidenceId, repo: REPO_DID,
      evidence_id: rec.evidenceId,
      entity_id: rec.entityId,
      category: rec.category ?? null,
      confidence: rec.confidence ?? null,
      severity: rec.severity ?? null,
      probability: rec.probability ?? null,
      source: rec.source ?? null,
      source_reliability: rec.sourceReliability ?? null,
      jurisdiction: rec.jurisdiction ?? null,
      summary: rec.summary ?? null,
      description: rec.description ?? null,
      verification_id: rec.verificationId ?? null,
      occurred_at: rec.occurredAt ?? null,
      created_at: rec.createdAt ?? rec.occurredAt ?? new Date().toISOString(),
      org_id: "anon", user_id: "anon", actor_id: "sys.baseline",
    }));
    n += await insertBatch("vertex_yabai_evidence", rows, cols);
  }
  console.log(`evidence inserted: ${n}`);
}

async function ingestRisk() {
  const recs = await loadJsonldDir(join(CONTENT_DIR, "risk"));
  const capped = LIMIT > 0 ? recs.slice(0, LIMIT) : recs;
  console.log(`risk: ${capped.length} records`);
  const cols = ["vertex_id", "_seq", "created_date", "sensitivity_ord", "owner_did",
    "rkey", "repo", "entity_id", "entity_type", "risk_score", "well_becoming_score",
    "penalty_score", "info_risk", "level", "scored_at",
    "org_id", "user_id", "actor_id"];
  let n = 0;
  for (let i = 0; i < capped.length; i += BATCH) {
    const rows = capped.slice(i, i + BATCH).map((rec) => {
      const score = Number(rec.yabaiRiskScore ?? 0);
      const level = score >= 95 ? "critical" : score >= 85 ? "high"
        : score >= 70 ? "medium" : score >= 40 ? "low" : "minimal";
      return {
        vertex_id: atUri("risk", rec.entityId),
        _seq: 0, created_date: today, sensitivity_ord: 300, owner_did: REPO_DID,
        rkey: rec.entityId, repo: REPO_DID,
        entity_id: rec.entityId,
        entity_type: "Unknown",
        risk_score: score,
        well_becoming_score: rec.wellBecomingScore ?? null,
        penalty_score: rec.penaltyScore ?? null,
        info_risk: rec.infoRisk ?? null,
        level,
        scored_at: rec.scoredAt ?? new Date().toISOString(),
        org_id: "anon", user_id: "anon", actor_id: "sys.baseline",
      };
    });
    n += await insertBatch("vertex_yabai_risk", rows, cols);
  }
  console.log(`risk inserted: ${n}`);
}

async function main() {
  await ingestEntities();
  await ingestEvidence();
  await ingestRisk();
  await pool.end();
}

main().catch((e) => { console.error(e); process.exit(1); });
