#!/usr/bin/env node
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const runtimePath = resolve(__dirname, "schema-rag-runtime.mjs");

function parseArgs(argv) {
  const args = {
    query: "",
    model: process.env.SCHEMA_RAG_LLM_MODEL || "gemma4-runpod",
    url: process.env.SCHEMA_RAG_LLM_URL || process.env.MURAKUMO_CHAT_URL || "https://llm.etzhayyim.com/v1/chat/completions",
    apiKey: process.env.SCHEMA_RAG_LLM_API_KEY || process.env.MURAKUMO_API_KEY || process.env.LITELLM_MASTER_KEY || "",
    creditsDid: process.env.SCHEMA_RAG_CREDITS_DID || process.env.CREDITS_DID || "did:web:llm.etzhayyim.com",
    magatamaVerified: /^(1|true|yes|on)$/i.test(process.env.SCHEMA_RAG_MAGATAMA_VERIFIED || ""),
    topK: 8,
    maxTokens: 700,
    temperature: 0,
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--query" || arg === "-q") args.query = argv[++i] ?? "";
    else if (arg === "--model") args.model = argv[++i] ?? args.model;
    else if (arg === "--url") args.url = argv[++i] ?? args.url;
    else if (arg === "--api-key") args.apiKey = argv[++i] ?? args.apiKey;
    else if (arg === "--credits-did") args.creditsDid = argv[++i] ?? args.creditsDid;
    else if (arg === "--magatama-verified") args.magatamaVerified = true;
    else if (arg === "--top-k" || arg === "-k") args.topK = Number(argv[++i] ?? args.topK);
    else if (arg === "--max-tokens") args.maxTokens = Number(argv[++i] ?? args.maxTokens);
    else if (arg === "--temperature") args.temperature = Number(argv[++i] ?? args.temperature);
    else if (!arg.startsWith("-") && !args.query) args.query = arg;
  }
  return args;
}

function runRuntime(args) {
  const child = spawnSync(process.execPath, [
    runtimePath,
    "--query",
    args.query,
    "--top-k",
    String(args.topK),
  ], { encoding: "utf8" });
  if (child.status !== 0) {
    throw new Error(`schema runtime failed: ${child.stderr || child.stdout}`);
  }
  return JSON.parse(child.stdout);
}

function verifySql(sql) {
  const child = spawnSync(process.execPath, [
    runtimePath,
    "--sql",
    sql,
  ], { encoding: "utf8" });
  if (child.status !== 0) {
    return { ok: false, errors: [`verifier_failed:${child.stderr || child.stdout}`], warnings: [] };
  }
  return JSON.parse(child.stdout).verification;
}

function extractSql(text) {
  const fenced = text.match(/```(?:sql)?\s*([\s\S]*?)```/i);
  if (fenced) return fenced[1].trim().replace(/;$/, "");
  const json = text.match(/\{[\s\S]*\}/);
  if (json) {
    try {
      const parsed = JSON.parse(json[0]);
      if (typeof parsed.sql === "string") return parsed.sql.trim().replace(/;$/, "");
    } catch {
      // fall through
    }
  }
  const select = text.match(/select[\s\S]*?(?:limit\s+\d+)/i);
  return select ? select[0].trim().replace(/;$/, "") : "";
}

function buildMessages(query, params) {
  return [
    {
      role: "system",
      content: [
        "You are a RisingWave SQL generator for GFTD.",
        "Return strict JSON only: {\"sql\":\"...\",\"rationale\":\"...\"}.",
        "Use only tables and columns present in schema_context.",
        "Generate read-only SELECT SQL.",
        "Always include a LIMIT.",
        "Prefer materialized views or views for coverage/count/summary questions.",
      ].join("\n"),
    },
    {
      role: "user",
      content: JSON.stringify({
        task: query,
        schema_rag_params: params,
      }),
    },
  ];
}

async function callLlm(args, params) {
  const headers = { "Content-Type": "application/json" };
  if (args.apiKey) headers.Authorization = `Bearer ${args.apiKey}`;
  if (args.creditsDid) headers["x-credits-did"] = args.creditsDid;
  if (args.magatamaVerified) headers["x-magatama-verified"] = "true";
  const startedAt = Date.now();
  const response = await fetch(args.url, {
    method: "POST",
    headers,
    body: JSON.stringify({
      model: args.model,
      messages: buildMessages(args.query, params),
      temperature: args.temperature,
      max_tokens: args.maxTokens,
      stream: false,
    }),
    signal: AbortSignal.timeout(240_000),
  });
  const raw = await response.text();
  let body = null;
  try {
    body = JSON.parse(raw);
  } catch {
    body = { raw };
  }
  return {
    ok: response.ok,
    status: response.status,
    latencyMs: Date.now() - startedAt,
    body,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (!args.query) {
    console.error("usage: pnpm --dir 30-graph/graph-schema rag:llm -- --query \"...\" [--model gemma4-runpod]");
    process.exit(2);
  }

  const runtime = runRuntime(args);
  const params = runtime.params;
  const llm = await callLlm(args, params);
  const content = typeof llm.body?.choices?.[0]?.message?.content === "string"
    ? llm.body.choices[0].message.content
    : "";
  const sql = extractSql(content);
  const verification = sql ? verifySql(sql) : { ok: false, errors: ["no_sql_extracted"], warnings: [] };

  console.log(JSON.stringify({
    request: {
      url: args.url,
      model: args.model,
      topK: args.topK,
      hasApiKey: Boolean(args.apiKey),
      creditsDid: args.creditsDid,
      magatamaVerified: args.magatamaVerified,
    },
    retrieval: {
      relations: runtime.catalog.relations,
      columns: runtime.catalog.columns,
      topTables: params.schema_context.map((entry) => ({
        table: entry.table,
        kind: entry.kind,
        score: entry.score,
      })),
    },
    llm,
    extractedSql: sql,
    verification,
  }, null, 2));
}

main().catch((err) => {
  console.error(err instanceof Error ? err.stack || err.message : String(err));
  process.exit(1);
});
