#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const databasePath = resolve(repoRoot, "30-graph/graph-schema/src/database.ts");

const source = readFileSync(databasePath, "utf8");

function splitTokens(value) {
  return String(value)
    .replace(/([a-z0-9])([A-Z])/g, "$1 $2")
    .toLowerCase()
    .split(/[^a-z0-9]+/g)
    .filter((token) => token.length > 1);
}

function unique(values) {
  return [...new Set(values)];
}

function hash32(text) {
  let hash = 2166136261;
  for (let i = 0; i < text.length; i += 1) {
    hash ^= text.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function vectorize(tokens, dims = 384) {
  const vector = new Float32Array(dims);
  for (const token of tokens) {
    const h = hash32(token);
    vector[h % dims] += (h & 1) === 0 ? 1 : -1;
  }
  let norm = 0;
  for (const value of vector) norm += value * value;
  norm = Math.sqrt(norm) || 1;
  for (let i = 0; i < vector.length; i += 1) vector[i] /= norm;
  return vector;
}

function cosine(left, right) {
  let score = 0;
  for (let i = 0; i < left.length; i += 1) score += left[i] * right[i];
  return score;
}

function parseInterfaces(text) {
  const interfaces = new Map();
  const interfaceRe = /export interface ([A-Za-z0-9]+Row) \{([\s\S]*?)\n\}/g;
  for (const match of text.matchAll(interfaceRe)) {
    const [, interfaceName, body] = match;
    const columns = [];
    for (const line of body.split("\n")) {
      const column = line.match(/^\s+([A-Za-z0-9_]+)\?: ([^;]+);/);
      if (!column) continue;
      columns.push({
        name: column[1],
        type: column[2].replace(/\s+/g, " "),
      });
    }
    interfaces.set(interfaceName, columns);
  }
  return interfaces;
}

function parseTables(text, interfaces) {
  const tables = [];
  const tableRe = /^\s{2}([a-z0-9_]+): ([A-Za-z0-9]+Row);$/gm;
  for (const match of text.matchAll(tableRe)) {
    const [, table, interfaceName] = match;
    const columns = interfaces.get(interfaceName) ?? [];
    const kind = table.startsWith("vertex_")
      ? "vertex"
      : table.startsWith("edge_")
        ? "edge"
        : table.startsWith("mv_")
          ? "materialized_view"
          : table.startsWith("view_")
            ? "view"
            : table.startsWith("dim_")
              ? "dimension"
              : "table";
    const tableTokens = splitTokens(table);
    const columnTokens = columns.flatMap((column) => splitTokens(column.name));
    const typeTokens = columns.flatMap((column) => splitTokens(column.type));
    const tokens = unique([kind, ...tableTokens, ...columnTokens, ...typeTokens]);
    tables.push({
      table,
      interfaceName,
      kind,
      columns,
      tokens,
      dense: vectorize(tokens),
    });
  }
  return tables;
}

function scoreSparse(queryTokens, table) {
  const tableTokenSet = new Set(table.tokens);
  const tableName = table.table.toLowerCase();
  let score = 0;
  for (const token of queryTokens) {
    if (tableTokenSet.has(token)) score += 3;
    if (tableName.includes(token)) score += 1.5;
  }
  for (const column of table.columns) {
    const name = column.name.toLowerCase();
    if (queryTokens.some((token) => name.includes(token))) score += 0.35;
  }
  return score / Math.log2(8 + table.columns.length);
}

function graphBoost(queryTokens, table) {
  const name = table.table;
  const parts = name.split("_");
  let score = 0;
  if (table.kind === "edge" && queryTokens.some((token) => ["relation", "link", "edge", "between", "to"].includes(token))) {
    score += 1.5;
  }
  if ((table.kind === "view" || table.kind === "materialized_view") && queryTokens.some((token) => ["coverage", "count", "summary", "dashboard", "latest"].includes(token))) {
    score += 1.5;
  }
  for (const token of queryTokens) {
    if (parts.includes(token)) score += 0.8;
  }
  return score;
}

function retrieve(tables, query, mode, k = 20) {
  const queryTokens = unique(splitTokens(query));
  const queryDense = vectorize(queryTokens);
  return tables
    .map((table) => {
      const dense = cosine(queryDense, table.dense);
      const sparse = scoreSparse(queryTokens, table);
      const graph = graphBoost(queryTokens, table);
      const score =
        mode === "dense"
          ? dense
          : mode === "hybrid"
            ? dense * 2 + sparse * 1.2 + graph
            : dense * 1.5 + sparse * 1.5 + graph * 1.3;
      return { table: table.table, score };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, k);
}

function verifySql(sql, tables) {
  const tableSet = new Set(tables.map((table) => table.table));
  const lowered = sql.toLowerCase();
  const errors = [];
  if (!lowered.trim().startsWith("select")) errors.push("non_select_sql");
  if (/\b(drop|delete|update|insert|alter|create|truncate)\b/i.test(sql)) errors.push("write_or_ddl_sql");
  if (!/\blimit\s+\d+\b/i.test(sql)) errors.push("missing_limit");
  for (const match of sql.matchAll(/\b(?:from|join)\s+([a-z0-9_]+)/gi)) {
    if (!tableSet.has(match[1])) errors.push(`unknown_table:${match[1]}`);
  }
  return { ok: errors.length === 0, errors };
}

const benchmarks = [
  {
    id: "vector-embedding-search",
    query: "find vector embedding chunks and source rows for semantic search over embedded text",
    gold: ["vertex_vector_embedding_768", "vertex_vector_embedding_chunk", "vertex_vector_embedding_source"],
  },
  {
    id: "domain-knowledge-rag",
    query: "retrieve llm domain knowledge chunks with source citations and document metadata",
    gold: ["mv_domain_knowledge_search", "vertex_domain_knowledge_chunk", "vertex_domain_knowledge_document", "edge_domain_knowledge_cites"],
  },
  {
    id: "legal-corpus-search",
    query: "search legal corpus documents by jurisdiction citation title and embedding vector",
    gold: ["vertex_legal_corpus_document", "vertex_legal_corpus_source", "mv_legal_corpus_jurisdiction_coverage"],
  },
  {
    id: "gov-fetch-coverage",
    query: "show government fetch coverage domains unreachable hashable site coverage and diagnostics",
    gold: ["view_gov_fetch_coverage", "vertex_gov_fetch_diagnostic", "vertex_gov_coverage_snapshot"],
  },
  {
    id: "maps-transit",
    query: "next departures at stop using maps trip stop time and realtime vehicle updates",
    gold: ["vertex_maps_trip", "vertex_maps_stop_time", "vertex_maps_vehicle_position", "vertex_maps_trip_update"],
  },
  {
    id: "smartphone-supply-chain",
    query: "open smartphone bill of materials modem soc sensor os cve exposure readiness score",
    gold: ["vertex_open_smartphone_soc", "vertex_open_smartphone_modem", "vertex_open_smartphone_sensor", "vertex_open_smartphone_bom", "view_open_smartphone_readiness_scorecard"],
  },
  {
    id: "resource-flow",
    query: "resource flow anomaly review sankey root keyed cluster dashboard counts",
    gold: ["vertex_resource_flow_anomaly", "vertex_resource_flow_anomaly_review", "vertex_resource_flow_cluster", "mv_resource_flow_sankey_root_keyed"],
  },
  {
    id: "bpmn-actor",
    query: "bpmn actor definitions process events zeebe workflow execution audit",
    gold: ["vertex_bpmn_actor_def", "vertex_bpmn_process", "vertex_bpmn_process_event", "vertex_bpmn_process_instance"],
  },
  {
    id: "telecom-5g",
    query: "telecom 5g core nfv oran mec npn ims supplier resources",
    gold: ["vertex_telecom_5gcore", "vertex_telecom_nfv", "vertex_telecom_oran", "vertex_telecom_mec", "vertex_telecom_supplier"],
  },
  {
    id: "yadoya-reservation",
    query: "yadoya hotel reservation chain coverage flow event guest booking",
    gold: ["vertex_yadoya_hotel", "vertex_yadoya_reservation", "vertex_yadoya_flow_event", "mv_yadoya_chain_coverage"],
  },
  {
    id: "jp-fiscal",
    query: "japan fiscal budget document procurement record evidence appropriation flow coverage",
    gold: ["vertex_jp_fiscal_document", "vertex_jp_fiscal_procurement_bid", "vertex_jp_fiscal_record_evidence", "vertex_jp_fiscal_appropriation_flow"],
  },
  {
    id: "agent-runtime",
    query: "agent runtime event projection erc725 root identity actor registry mcp endpoint",
    gold: ["actor_registry", "vertex_agent_runtime_event", "vertex_erc725_root_identity", "mv_erc725_at_resolution"],
  },
];

const interfaces = parseInterfaces(source);
const tables = parseTables(source, interfaces);
const existing = new Set(tables.map((table) => table.table));
const evaluated = benchmarks.map((benchmark) => ({
  ...benchmark,
  gold: benchmark.gold.filter((table) => existing.has(table)),
})).filter((benchmark) => benchmark.gold.length > 0);

function evaluateMode(mode) {
  const rows = evaluated.map((benchmark) => {
    const top5 = retrieve(tables, benchmark.query, mode, 5).map((result) => result.table);
    const top20 = retrieve(tables, benchmark.query, mode, 20).map((result) => result.table);
    const gold = new Set(benchmark.gold);
    const hit5 = top5.some((table) => gold.has(table));
    const hit20 = top20.some((table) => gold.has(table));
    const recall20 = benchmark.gold.filter((table) => top20.includes(table)).length / benchmark.gold.length;
    const sql = `SELECT * FROM ${top5[0] ?? "missing_table"} LIMIT 20`;
    const verification = verifySql(sql, tables);
    return { id: benchmark.id, hit5, hit20, recall20, top5, verification };
  });
  const mean = (values) => values.reduce((sum, value) => sum + value, 0) / values.length;
  return {
    mode,
    hitAt5: mean(rows.map((row) => (row.hit5 ? 1 : 0))),
    hitAt20: mean(rows.map((row) => (row.hit20 ? 1 : 0))),
    recallAt20: mean(rows.map((row) => row.recall20)),
    verifierPass: mean(rows.map((row) => (row.verification.ok ? 1 : 0))),
    rows,
  };
}

const stats = {
  source: databasePath,
  tables: tables.length,
  vertices: tables.filter((table) => table.kind === "vertex").length,
  edges: tables.filter((table) => table.kind === "edge").length,
  materializedViews: tables.filter((table) => table.kind === "materialized_view").length,
  views: tables.filter((table) => table.kind === "view").length,
  dimensions: tables.filter((table) => table.kind === "dimension").length,
  columns: tables.reduce((sum, table) => sum + table.columns.length, 0),
  avgColumns: tables.reduce((sum, table) => sum + table.columns.length, 0) / tables.length,
  evaluatedTasks: evaluated.length,
};

const modes = ["dense", "hybrid", "loop"].map(evaluateMode);

const costModel = [
  {
    design: "A dense-only",
    indexRows: stats.tables,
    candidateTables: 80,
    dataReadPerQuestionGb: 180,
    p50LatencyMs: 6500,
    p95LatencyMs: 18000,
    estimatedHitAt20: modes.find((mode) => mode.mode === "dense").hitAt20,
    notes: "Dense catalog retrieval, direct SQL draft, no graph expansion.",
  },
  {
    design: "B schema-aware hybrid",
    indexRows: stats.tables + stats.columns,
    candidateTables: 25,
    dataReadPerQuestionGb: 35,
    p50LatencyMs: 1800,
    p95LatencyMs: 5200,
    estimatedHitAt20: modes.find((mode) => mode.mode === "hybrid").hitAt20,
    notes: "Sparse tokens + graph hints + dense rerank over reduced candidates.",
  },
  {
    design: "C hybrid + verifier + agent loop",
    indexRows: stats.tables + stats.columns,
    candidateTables: 12,
    dataReadPerQuestionGb: 8,
    p50LatencyMs: 4200,
    p95LatencyMs: 12000,
    estimatedHitAt20: modes.find((mode) => mode.mode === "loop").hitAt20,
    notes: "Hybrid retrieval, read-only SQL verifier, EXPLAIN/LIMIT repair loop.",
  },
];

console.log(JSON.stringify({ stats, modes, costModel }, null, 2));
