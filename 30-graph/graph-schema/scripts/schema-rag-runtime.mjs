#!/usr/bin/env node
import { existsSync, readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const databasePath = resolve(repoRoot, "30-graph/graph-schema/src/database.ts");
const defaultArtifactPath = resolve(repoRoot, "80-data/reports/schema-aware-rag/schema-rag-reranker.json");

const DEFAULT_WEIGHTS = [1.5, 1.5, 1.3, 2.0, 1.0, 0.7, -0.1];

function parseArgs(argv) {
  const args = {
    query: "",
    sql: "",
    topK: 12,
    artifactPath: defaultArtifactPath,
    json: true,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--query" || arg === "-q") args.query = argv[++i] ?? "";
    else if (arg === "--sql") args.sql = argv[++i] ?? "";
    else if (arg === "--top-k" || arg === "-k") args.topK = Number(argv[++i] ?? args.topK);
    else if (arg === "--artifact") args.artifactPath = argv[++i] ?? args.artifactPath;
    else if (arg === "--pretty") args.json = false;
    else if (!arg.startsWith("-") && !args.query) args.query = arg;
  }
  return args;
}

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

function dot(weights, xs) {
  let score = 0;
  for (let i = 0; i < weights.length; i += 1) score += weights[i] * xs[i];
  return score;
}

function tableKind(table) {
  if (table.startsWith("vertex_")) return "vertex";
  if (table.startsWith("edge_")) return "edge";
  if (table.startsWith("mv_")) return "materialized_view";
  if (table.startsWith("view_")) return "view";
  if (table.startsWith("dim_")) return "dimension";
  return "table";
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
      columns.push({ name: column[1], type: column[2].replace(/\s+/g, " ") });
    }
    interfaces.set(interfaceName, columns);
  }
  return interfaces;
}

function parseCatalog(text) {
  const interfaces = parseInterfaces(text);
  const tables = [];
  const tableRe = /^\s{2}([a-z0-9_]+): ([A-Za-z0-9]+Row);$/gm;
  for (const match of text.matchAll(tableRe)) {
    const [, table, interfaceName] = match;
    const columns = interfaces.get(interfaceName) ?? [];
    const kind = tableKind(table);
    const tableTokens = splitTokens(table);
    const columnTokens = columns.flatMap((column) => splitTokens(column.name));
    const typeTokens = columns.flatMap((column) => splitTokens(column.type));
    const tokens = unique([kind, ...tableTokens, ...columnTokens, ...typeTokens]);
    tables.push({
      table,
      interfaceName,
      kind,
      columns,
      tokenSet: new Set(tokens),
      tableTokenSet: new Set(tableTokens),
      columnTokenSet: new Set(columnTokens),
      tokens,
      dense: vectorize(tokens),
    });
  }
  return tables;
}

function loadWeights(artifactPath) {
  if (!existsSync(artifactPath)) return { weights: DEFAULT_WEIGHTS, source: "default" };
  const artifact = JSON.parse(readFileSync(artifactPath, "utf8"));
  if (!Array.isArray(artifact?.train?.weights)) return { weights: DEFAULT_WEIGHTS, source: "default" };
  return { weights: artifact.train.weights, source: artifactPath };
}

function prepareQuery(query) {
  const tokens = unique(splitTokens(query));
  return { query, tokens, dense: vectorize(tokens) };
}

function scoreSparse(queryTokens, table) {
  const tableName = table.table.toLowerCase();
  let score = 0;
  for (const token of queryTokens) {
    if (table.tokenSet.has(token)) score += 3;
    if (tableName.includes(token)) score += 1.5;
    if (table.columnTokenSet.has(token)) score += 0.35;
  }
  return score / Math.log2(8 + table.columns.length);
}

function graphBoost(queryTokens, table) {
  let score = 0;
  if (table.kind === "edge" && queryTokens.some((token) => ["relation", "link", "edge", "between", "to"].includes(token))) {
    score += 1.5;
  }
  if ((table.kind === "view" || table.kind === "materialized_view") && queryTokens.some((token) => ["coverage", "count", "summary", "dashboard", "latest"].includes(token))) {
    score += 1.5;
  }
  for (const token of queryTokens) {
    if (table.tableTokenSet.has(token)) score += 0.8;
  }
  return score;
}

function overlapRatio(leftTokens, rightSet) {
  if (leftTokens.length === 0) return 0;
  let hit = 0;
  for (const token of leftTokens) {
    if (rightSet.has(token)) hit += 1;
  }
  return hit / leftTokens.length;
}

function features(preparedQuery, table) {
  const queryTokens = preparedQuery.tokens;
  return [
    cosine(preparedQuery.dense, table.dense),
    scoreSparse(queryTokens, table),
    graphBoost(queryTokens, table),
    overlapRatio(queryTokens, table.tableTokenSet),
    overlapRatio(queryTokens, table.columnTokenSet),
    queryTokens.includes(table.kind) ? 1 : 0,
    Math.log1p(table.columns.length) / 5,
  ];
}

function rankTables(tables, query, weights, topK) {
  const preparedQuery = prepareQuery(query);
  const rows = [];
  for (const table of tables) {
    const row = {
      table: table.table,
      kind: table.kind,
      score: dot(weights, features(preparedQuery, table)),
      columns: table.columns,
    };
    let inserted = false;
    for (let i = 0; i < rows.length; i += 1) {
      if (row.score > rows[i].score) {
        rows.splice(i, 0, row);
        inserted = true;
        break;
      }
    }
    if (!inserted && rows.length < topK) rows.push(row);
    if (rows.length > topK) rows.pop();
  }
  return rows;
}

function relationHints(tableName, tablesByName) {
  const hints = [];
  const domain = tableName
    .replace(/^(vertex|edge|mv|view|dim)_/, "")
    .split("_")
    .slice(0, 3);
  for (const [name, table] of tablesByName) {
    if (name === tableName) continue;
    if (hints.length >= 8) break;
    const overlap = domain.filter((part) => table.tableTokenSet.has(part)).length;
    if (overlap > 0) hints.push({ table: name, kind: table.kind, overlap });
  }
  return hints.sort((a, b) => b.overlap - a.overlap);
}

function buildParams(query, ranked, tablesByName) {
  return {
    query,
    schema_context: ranked.map((row) => ({
      table: row.table,
      kind: row.kind,
      score: Number(row.score.toFixed(6)),
      columns: row.columns.slice(0, 24),
      relation_hints: relationHints(row.table, tablesByName),
    })),
    sql_policy: {
      read_only: true,
      require_limit: true,
      prefer_views_or_materialized_views_for_rollups: true,
      reject_unknown_tables: true,
      reject_unknown_columns: true,
    },
  };
}

function parseSqlRefs(sql) {
  const tables = [];
  const aliases = new Map();
  for (const match of sql.matchAll(/\b(from|join)\s+([a-z0-9_]+)(?:\s+(?:as\s+)?([a-z][a-z0-9_]*))?/gi)) {
    const table = match[2];
    const alias = match[3] && !["where", "join", "left", "right", "inner", "outer", "on", "group", "order", "limit"].includes(match[3].toLowerCase())
      ? match[3]
      : table;
    tables.push(table);
    aliases.set(alias, table);
    aliases.set(table, table);
  }
  const qualifiedColumns = [];
  for (const match of sql.matchAll(/\b([a-z][a-z0-9_]*)\.([a-z][a-z0-9_]*)\b/gi)) {
    qualifiedColumns.push({ qualifier: match[1], column: match[2] });
  }
  return { tables: unique(tables), aliases, qualifiedColumns };
}

function verifySql(sql, tablesByName) {
  const errors = [];
  const warnings = [];
  const lowered = sql.toLowerCase();
  if (!lowered.trim().startsWith("select")) errors.push("non_select_sql");
  if (/\b(drop|delete|update|insert|alter|create|truncate|copy)\b/i.test(sql)) errors.push("write_or_ddl_sql");
  if (!/\blimit\s+\d+\b/i.test(sql)) errors.push("missing_limit");
  const refs = parseSqlRefs(sql);
  for (const tableName of refs.tables) {
    if (!tablesByName.has(tableName)) errors.push(`unknown_table:${tableName}`);
  }
  for (const ref of refs.qualifiedColumns) {
    const tableName = refs.aliases.get(ref.qualifier);
    if (!tableName || !tablesByName.has(tableName)) {
      errors.push(`unknown_qualifier:${ref.qualifier}`);
      continue;
    }
    const table = tablesByName.get(tableName);
    if (!table.columns.some((column) => column.name === ref.column)) {
      errors.push(`unknown_column:${ref.qualifier}.${ref.column}`);
    }
  }
  if (refs.tables.length > 3) warnings.push("multi_table_query_requires_explain_budget_gate");
  if (refs.tables.some((tableName) => tableName.startsWith("vertex_")) && !/\bwhere\b/i.test(sql)) {
    warnings.push("base_vertex_scan_without_where");
  }
  return { ok: errors.length === 0, errors, warnings, refs: { tables: refs.tables } };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.query && !args.sql) {
    console.error("usage: pnpm --dir 30-graph/graph-schema rag:retrieve -- --query \"...\" [--sql \"SELECT ... LIMIT 20\"]");
    process.exit(2);
  }

  const source = readFileSync(databasePath, "utf8");
  const tables = parseCatalog(source);
  const tablesByName = new Map(tables.map((table) => [table.table, table]));
  const loaded = loadWeights(args.artifactPath);
  const ranked = args.query ? rankTables(tables, args.query, loaded.weights, args.topK) : [];
  const params = args.query ? buildParams(args.query, ranked, tablesByName) : null;
  const verification = args.sql ? verifySql(args.sql, tablesByName) : null;

  const result = {
    catalog: {
      source: databasePath,
      relations: tables.length,
      columns: tables.reduce((sum, table) => sum + table.columns.length, 0),
    },
    reranker: {
      weightsSource: loaded.source,
      weights: loaded.weights,
    },
    params,
    verification,
  };

  if (args.json) console.log(JSON.stringify(result, null, 2));
  else {
    for (const row of ranked) console.log(`${row.score.toFixed(3)}\t${row.kind}\t${row.table}`);
    if (verification) console.log(JSON.stringify(verification, null, 2));
  }
}

main();
