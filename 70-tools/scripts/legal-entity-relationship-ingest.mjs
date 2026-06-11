#!/usr/bin/env node
/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  SUPERSEDED — DO NOT RUN ON THE RELIGIOUS-CORP SUBSTRATE              ║
 * ║                                                                       ║
 * ║  Status: pre-religious-corp commercial-fund era artifact (writes to   ║
 * ║          edge_legal_entity_* graph edges on RisingWave-bound PG,      ║
 * ║          neither of which is part of the current substrate per        ║
 * ║          ADR-2605262130 + ADR-2605172000).                            ║
 * ║                                                                       ║
 * ║  Superseded by: ADR-2605263800 — corp ownership-graph attestation     ║
 * ║                 lexicon `com.etzhayyim.corp.ownershipEdge` (CC0 1.0   ║
 * ║                 GLEIF L2 + CC-BY-SA 4.0 OpenCorporates open-data)     ║
 * ║                                                                       ║
 * ║  Why superseded (religious-corp substrate-fit):                       ║
 * ║    - CorpOwnershipSensor Protocol (kotodama.organism.sensors.corp.* ║
 * ║      corp_ownership_sensor) consumes GLEIF L2 / EU UBO registers /    ║
 * ║      OpenCorporates open-data via IPFS-pinned subdataset              ║
 * ║    - com.etzhayyim.corp.ownershipEdge Lexicon record canonical        ║
 * ║      (NOT PG `edge_legal_entity_owns` / `edge_legal_entity_trades_with`)║
 * ║    - `ownershipKind` enum: {ubo, direct-shareholder, parent-subsidiary,║
 * ║      control-relationship, officer} (NOT the legacy mode argument)    ║
 * ║    - Tier-B OpenCorporates open-data fork carries `-tierB-` infix on  ║
 * ║      derivative training artifacts; OpenCorporates paid-API tier is   ║
 * ║      CONSTITUTIONALLY PROHIBITED per Charter Rider §2(e)              ║
 * ║                                                                       ║
 * ║  Operator action:                                                     ║
 * ║    - For new ingestion: use `e7m-dataset pull gleif-l2` +             ║
 * ║      `e7m-dataset pull opencorporates-opendata` (W3; Tier-B accept    ║
 * ║      flag required at ~/.etzhayyim/source-acceptance/                 ║
 * ║      opencorporates-opendata.toml — template at                       ║
 * ║      70-tools/e7m-dataset/acceptance-templates/)                      ║
 * ║                                                                       ║
 * ║  Removal scheduled: ADR-2605263800 W4 deliverable (after sensor       ║
 * ║                     parity is verified at W3).                        ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 *
 * Legal-entity relationship ingest -> edge_legal_entity_owns / edge_legal_entity_trades_with.
 *
 * Input: JSONL with one relationship per line.
 *
 * Examples:
 *   node 70-tools/scripts/legal-entity-relationship-ingest.mjs --mode owns --input ownership.jsonl
 *   node 70-tools/scripts/legal-entity-relationship-ingest.mjs --mode trades --input customers.jsonl --dry-run
 *
 * Owns JSONL shape:
 *   {
 *     "srcLei": "5493001KJTIIGC8Y1R12",
 *     "dstLei": "213800D1EI4B9WTWWD28",
 *     "relationship": "subsidiary",
 *     "stakePct": 1.0,
 *     "votingPct": 1.0,
 *     "controlType": "direct",
 *     "effectiveFrom": "2024-01-01",
 *     "sourceUrl": "https://www.sec.gov/...",
 *     "sourceLicense": "public-disclosure",
 *     "confidence": 0.95
 *   }
 *
 * Trades JSONL shape:
 *   {
 *     "srcLei": "....",
 *     "dstLei": "....",
 *     "relationship": "supplier",
 *     "amount": 250000000,
 *     "amountCurrency": "USD",
 *     "periodStart": "2024-01-01",
 *     "periodEnd": "2024-12-31",
 *     "sourceUrl": "https://www.sec.gov/...",
 *     "sourceLicense": "public-disclosure",
 *     "confidence": 0.8
 *   }
 */

import { readFile } from "node:fs/promises";

const { default: pg } = await import("/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js");

const KOTOBA_URL = process.env.KOTOBA_URL ?? "postgresql://root@127.0.0.1:14566/dev?sslmode=disable";
const COLLECTOR_DID = "did:web:legal-entity.etzhayyim.com";

const args = process.argv.slice(2);
const getArg = (k, d = "") => {
  const i = args.indexOf(`--${k}`);
  return i === -1 ? d : args[i + 1] ?? d;
};
const hasFlag = (k) => args.includes(`--${k}`);

const MODE = getArg("mode", "").trim();
const INPUT = getArg("input", "").trim();
const DRY_RUN = hasFlag("dry-run");

if (!["owns", "trades"].includes(MODE) || !INPUT) {
  console.error("usage: node 70-tools/scripts/legal-entity-relationship-ingest.mjs --mode owns|trades --input file.jsonl [--dry-run]");
  process.exit(2);
}

let _pool = null;
async function pool() {
  if (_pool) return _pool;
  _pool = new pg.Pool({ connectionString: KOTOBA_URL, max: 2, statement_timeout: 60000 });
  return _pool;
}

async function resolveVertexId(ref) {
  if (ref.vertexId) return ref.vertexId;
  const pgPool = await pool();

  if (ref.lei) {
    const q = await pgPool.query("SELECT vertex_id FROM vertex_legal_entity WHERE lei = $1 LIMIT 1", [ref.lei]);
    if (q.rows[0]?.vertex_id) return q.rows[0].vertex_id;
  }

  if (ref.source && ref.sourceRecordId) {
    const q = await pgPool.query(
      "SELECT vertex_id FROM vertex_legal_entity WHERE source = $1 AND source_record_id = $2 LIMIT 1",
      [ref.source, ref.sourceRecordId],
    );
    if (q.rows[0]?.vertex_id) return q.rows[0].vertex_id;
  }

  if (ref.name && ref.country) {
    const q = await pgPool.query(
      "SELECT vertex_id FROM vertex_legal_entity WHERE lower(name) = lower($1) AND country = $2 LIMIT 1",
      [ref.name, ref.country],
    );
    if (q.rows[0]?.vertex_id) return q.rows[0].vertex_id;
  }

  return null;
}

function parseJsonl(text) {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, idx) => {
      try {
        return JSON.parse(line);
      } catch (err) {
        throw new Error(`invalid JSONL at line ${idx + 1}: ${err.message}`);
      }
    });
}

async function insertRows(table, cols, rows) {
  if (!rows.length) return 0;
  if (DRY_RUN) return rows.length;
  const pgPool = await pool();
  let inserted = 0;
  for (const row of rows) {
    const edgeId = row.edge_id ?? null;
    if (!edgeId) continue;
    const exists = await pgPool.query(
      `SELECT 1 FROM ${table} WHERE edge_id = $1 LIMIT 1`,
      [edgeId],
    );
    if (exists.rowCount) continue;
    const vals = cols.map((c) => row[c] ?? null);
    const placeholders = vals.map((_, i) => `$${i + 1}`).join(",");
    const result = await pgPool.query(
      `INSERT INTO ${table} (${cols.join(",")}) VALUES (${placeholders})`,
      vals,
    );
    inserted += Number(result.rowCount ?? 0);
  }
  return inserted;
}

async function buildOwnsRows(items) {
  const rows = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const srcVid = await resolveVertexId({
      vertexId: item.srcVertexId,
      lei: item.srcLei,
      source: item.srcSource,
      sourceRecordId: item.srcSourceRecordId,
      name: item.srcName,
      country: item.srcCountry,
    });
    const dstVid = await resolveVertexId({
      vertexId: item.dstVertexId,
      lei: item.dstLei,
      source: item.dstSource,
      sourceRecordId: item.dstSourceRecordId,
      name: item.dstName,
      country: item.dstCountry,
    });
    if (!srcVid || !dstVid) continue;

    rows.push({
      edge_id: item.edgeId ?? `owns:${srcVid}:${dstVid}:${i}`,
      src_vid: srcVid,
      dst_vid: dstVid,
      owner_did: COLLECTOR_DID,
      relationship: item.relationship ?? "subsidiary",
      stake_pct: item.stakePct ?? null,
      voting_pct: item.votingPct ?? null,
      control_type: item.controlType ?? null,
      effective_from: item.effectiveFrom ?? null,
      effective_to: item.effectiveTo ?? null,
      source_url: item.sourceUrl ?? null,
      source_license: item.sourceLicense ?? "public-disclosure",
      confidence: item.confidence ?? 0.8,
      linked_at: item.linkedAt ?? new Date().toISOString(),
    });
  }
  return rows;
}

async function buildTradeRows(items) {
  const rows = [];
  for (let i = 0; i < items.length; i++) {
    const item = items[i];
    const srcVid = await resolveVertexId({
      vertexId: item.srcVertexId,
      lei: item.srcLei,
      source: item.srcSource,
      sourceRecordId: item.srcSourceRecordId,
      name: item.srcName,
      country: item.srcCountry,
    });
    const dstVid = await resolveVertexId({
      vertexId: item.dstVertexId,
      lei: item.dstLei,
      source: item.dstSource,
      sourceRecordId: item.dstSourceRecordId,
      name: item.dstName,
      country: item.dstCountry,
    });
    if (!srcVid || !dstVid) continue;

    rows.push({
      edge_id: item.edgeId ?? `trade:${srcVid}:${dstVid}:${i}`,
      src_vid: srcVid,
      dst_vid: dstVid,
      owner_did: COLLECTOR_DID,
      relationship: item.relationship ?? "supplier",
      amount: item.amount ?? null,
      amount_currency: item.amountCurrency ?? null,
      period_start: item.periodStart ?? null,
      period_end: item.periodEnd ?? null,
      source_url: item.sourceUrl ?? null,
      source_license: item.sourceLicense ?? "public-disclosure",
      confidence: item.confidence ?? 0.7,
      linked_at: item.linkedAt ?? new Date().toISOString(),
    });
  }
  return rows;
}

async function main() {
  const text = await readFile(INPUT, "utf8");
  const items = parseJsonl(text);
  const rows = MODE === "owns" ? await buildOwnsRows(items) : await buildTradeRows(items);

  const ownsCols = [
    "edge_id", "src_vid", "dst_vid", "owner_did", "relationship",
    "stake_pct", "voting_pct", "control_type", "effective_from", "effective_to",
    "source_url", "source_license", "confidence", "linked_at",
  ];
  const tradeCols = [
    "edge_id", "src_vid", "dst_vid", "owner_did", "relationship",
    "amount", "amount_currency", "period_start", "period_end",
    "source_url", "source_license", "confidence", "linked_at",
  ];

  const inserted = await insertRows(
    MODE === "owns" ? "edge_legal_entity_owns" : "edge_legal_entity_trades_with",
    MODE === "owns" ? ownsCols : tradeCols,
    rows,
  );

  console.log(JSON.stringify({
    mode: MODE,
    input: INPUT,
    sourceRows: items.length,
    resolvedRows: rows.length,
    inserted,
    dryRun: DRY_RUN,
  }, null, 2));

  if (_pool) await _pool.end();
}

main().catch(async (err) => {
  console.error(err?.stack || String(err));
  if (_pool) await _pool.end();
  process.exit(1);
});
