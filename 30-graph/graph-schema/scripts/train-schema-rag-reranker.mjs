#!/usr/bin/env node
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(__dirname, "../../..");
const databasePath = resolve(repoRoot, "30-graph/graph-schema/src/database.ts");
const artifactDir = resolve(repoRoot, "80-data/reports/schema-aware-rag");
const artifactPath = resolve(artifactDir, "schema-rag-reranker.json");

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
      columns.push({ name: column[1], type: column[2].replace(/\s+/g, " ") });
    }
    interfaces.set(interfaceName, columns);
  }
  return interfaces;
}

function tableKind(table) {
  if (table.startsWith("vertex_")) return "vertex";
  if (table.startsWith("edge_")) return "edge";
  if (table.startsWith("mv_")) return "materialized_view";
  if (table.startsWith("view_")) return "view";
  if (table.startsWith("dim_")) return "dimension";
  return "table";
}

function parseTables(text, interfaces) {
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

function prepareQuery(query) {
  const tokens = unique(splitTokens(query));
  return { query, tokens, dense: vectorize(tokens) };
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

function dot(weights, xs) {
  let score = 0;
  for (let i = 0; i < weights.length; i += 1) score += weights[i] * xs[i];
  return score;
}

function makeQueries(table) {
  const tableWords = table.tokens.filter((token) => !["vertex", "edge", "view", "materialized", "table"].includes(token));
  const columns = table.columns.slice(0, 8).flatMap((column) => splitTokens(column.name));
  const core = unique([...tableWords.slice(0, 8), ...columns.slice(0, 8)]).join(" ");
  const action =
    table.kind === "edge"
      ? "find relation links between"
      : table.kind === "view" || table.kind === "materialized_view"
        ? "show latest coverage summary for"
        : "retrieve rows and columns for";
  return [
    `${action} ${core}`,
    `${table.kind} ${core}`,
  ];
}

function seededNegative(tables, seed, avoidTable) {
  let idx = hash32(`${seed}:neg`) % tables.length;
  for (let i = 0; i < tables.length; i += 1) {
    const candidate = tables[(idx + i) % tables.length];
    if (candidate.table !== avoidTable) return candidate;
  }
  throw new Error("no negative candidate");
}

function rank(tables, preparedQuery, scorer, k = 20) {
  const top = [];
  for (const table of tables) {
    const row = { table: table.table, score: scorer(preparedQuery, table) };
    let inserted = false;
    for (let i = 0; i < top.length; i += 1) {
      if (row.score > top[i].score) {
        top.splice(i, 0, row);
        inserted = true;
        break;
      }
    }
    if (!inserted && top.length < k) top.push(row);
    if (top.length > k) top.pop();
  }
  return top.map((row) => row.table);
}

function metric(rows, k) {
  return rows.reduce((sum, row) => sum + (row.rank > 0 && row.rank <= k ? 1 : 0), 0) / rows.length;
}

function evaluate(tables, examples, scorer) {
  const rows = examples.map((example) => {
    const top = rank(tables, example.preparedQuery, scorer, 20);
    const idx = top.indexOf(example.gold);
    return { rank: idx < 0 ? Infinity : idx + 1 };
  });
  return {
    examples: rows.length,
    hitAt1: metric(rows, 1),
    hitAt5: metric(rows, 5),
    hitAt20: metric(rows, 20),
    mrr20: rows.reduce((sum, row) => sum + (row.rank <= 20 ? 1 / row.rank : 0), 0) / rows.length,
  };
}

const interfaces = parseInterfaces(source);
const tables = parseTables(source, interfaces);
const examples = tables.flatMap((table) => makeQueries(table).map((query) => ({
  query,
  preparedQuery: prepareQuery(query),
  gold: table.table,
})));

const train = [];
const test = [];
for (const example of examples) {
  const bucket = hash32(example.gold + "\n" + example.query) % 10;
  if (bucket < 7) train.push(example);
  else test.push(example);
}

const benchTest = test.filter((example) => hash32(example.gold) % 5 === 0).slice(0, 500);

const weights = [1.5, 1.5, 1.3, 2.0, 1.0, 0.7, -0.1];
const learningRate = 0.08;
const epochs = 6;
let updates = 0;

for (let epoch = 0; epoch < epochs; epoch += 1) {
  for (const example of train) {
    const positive = tables.find((table) => table.table === example.gold);
    const negative = seededNegative(tables, `${epoch}:${example.gold}:${example.query}`, example.gold);
    const posFeatures = features(example.preparedQuery, positive);
    const negFeatures = features(example.preparedQuery, negative);
    const margin = dot(weights, posFeatures) - dot(weights, negFeatures);
    if (margin < 1) {
      for (let i = 0; i < weights.length; i += 1) {
        weights[i] += learningRate * (posFeatures[i] - negFeatures[i]);
      }
      updates += 1;
    }
  }
}

const denseScorer = (preparedQuery, table) => features(preparedQuery, table)[0];
const heuristicScorer = (preparedQuery, table) => {
  const xs = features(preparedQuery, table);
  return xs[0] * 2 + xs[1] * 1.2 + xs[2];
};
const trainedScorer = (preparedQuery, table) => dot(weights, features(preparedQuery, table));

const result = {
  source: databasePath,
  trainedAt: new Date().toISOString(),
  catalog: {
    tables: tables.length,
    columns: tables.reduce((sum, table) => sum + table.columns.length, 0),
  },
  train: {
    examples: train.length,
    epochs,
    updates,
    model: "linear pairwise schema reranker",
    featureNames: [
      "dense_cosine",
      "sparse_schema_score",
      "graph_boost",
      "table_token_overlap",
      "column_token_overlap",
      "kind_match",
      "column_count_penalty",
    ],
    weights,
  },
  bench: {
    testExamplesTotal: test.length,
    testExamplesBenchSample: benchTest.length,
    denseOnly: evaluate(tables, benchTest, denseScorer),
    heuristicHybrid: evaluate(tables, benchTest, heuristicScorer),
    trainedHybrid: evaluate(tables, benchTest, trainedScorer),
  },
};

mkdirSync(artifactDir, { recursive: true });
writeFileSync(artifactPath, JSON.stringify(result, null, 2));
console.log(JSON.stringify({ ...result, artifactPath }, null, 2));
