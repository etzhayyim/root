#!/usr/bin/env node
/**
 * Audit bulk-51 py_primitive node refs and classify each by what kind it
 * COULD become under ADR-2605082000 §2 (mcp_tool / sql_udf / py_ext_udf / llm).
 *
 * For each `kotodama.langgraph_graphs.<actor>:<fn>` reference, read the
 * corresponding Python file and classify the function body:
 *
 *   llm        — calls call_tier_json / anthropic / openai / kotodama.llm
 *   mcp_tool   — calls a `task_*` from `kotodama.<X>_worker_main` (already
 *                a thin wrapper, lift directly to the actor's MCP NSID)
 *   sql_udf    — single SELECT / INSERT, candidate for SQL UDF
 *   identity   — constant return, candidate for com.etzhayyim.tools.const.echo
 *   self_logic — non-trivial inline logic; needs refactor before MCP migration
 *   missing    — function not found in module
 *
 * Output: TSV to stdout, one row per ref. Use this to pick the next batch
 * of migrations and to size the bulk-51 migration entry's complexity.
 */
import { readFileSync, existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const BULK_SQL = path.join(
  REPO_ROOT,
  "30-graph/graph-schema/sql_migrations/20260509150000_topology_bulk_51.up.sql",
);
const PYBASE = path.join(REPO_ROOT, "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs");

const LLM_PATTERNS = [
  /\bcall_tier_json\b/, /\banthropic\b/i, /\bopenai\b/i, /kotodama\.llm\b/,
  /AsyncAnthropic\b/, /AsyncOpenAI\b/,
];
const LLM_TASK_RE = /\btask_generic_llm_chat\b/;
const HEAVY_OTHER_PATTERNS = [
  /\btask_generic_comfyui_call\b/,
  /\btask_generic_db_insert\b/,
  /\btask_generic_db_select\b/,
  /\bhttpx\.AsyncClient\b/, /\baiohttp\.ClientSession\b/,
];
const SQL_PATTERNS = [/\bSELECT\b/i, /\bINSERT INTO\b/i, /\bUPDATE\b/i];
// Only flag identity when the body has zero state interpolation (no
// f-strings touching state, no `state.get(...)` reads in the return value).
const IDENTITY_STATE_DEPS = [/state\.get\b/, /state\[/, /\$\{[^}]*\}/, /f["']/];
// "thin task_* wrapper" — module imports task_<x> from <actor>_worker_main
// AND the body invokes the task without doing other heavy work.
const TASK_INVOKE_RE = /\btask_[a-z_]+\s*\(/;

function refsFromSql() {
  if (!existsSync(BULK_SQL)) {
    throw new Error(`bulk-51 SQL not found at ${BULK_SQL}`);
  }
  const txt = readFileSync(BULK_SQL, "utf8");
  const re = /'(kotodama\.langgraph_graphs\.([a-z_]+)):([a-zA-Z_]+)'/g;
  const out = [];
  let m;
  while ((m = re.exec(txt)) !== null) {
    out.push({ module: m[2], fn: m[3], dotted: `${m[1]}:${m[3]}` });
  }
  // dedup (a few graphs reference the same fn from multiple nodes)
  const seen = new Set();
  return out.filter((x) => {
    const k = `${x.module}:${x.fn}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

function extractFunctionBody(src, fn) {
  // Capture the block after `def fn(` or `async def fn(` until the next
  // top-level `def `/`async def `/`class ` (greedy enough for our purposes).
  const re = new RegExp(
    `(?:^|\\n)(?:async\\s+)?def\\s+${fn}\\s*\\([^)]*\\)[^:]*:\\n([\\s\\S]*?)(?=\\n(?:async\\s+def|def|class)\\s|\\Z)`,
    "m",
  );
  const m = src.match(re);
  return m ? m[1] : null;
}

function classify(body, fileText) {
  if (body == null) return "missing";

  const lines = body
    .trim()
    .split("\n")
    .map((s) => s.trim())
    .filter((s) => s.length > 0 && !s.startsWith("#"));

  const hasLlm = LLM_PATTERNS.some((p) => p.test(body)) || LLM_TASK_RE.test(body);
  const hasHeavyOther = HEAVY_OTHER_PATTERNS.some((p) => p.test(body));
  const hasSql = SQL_PATTERNS.some((p) => p.test(body));
  const hasTaskInvoke = TASK_INVOKE_RE.test(body);
  const hasStateDep = IDENTITY_STATE_DEPS.some((p) => p.test(body));

  // identity: ≤ 3 lines, all `return ...`, NO state interpolation/lookup.
  if (
    lines.length <= 3 &&
    lines.every((l) => /^return\s+/.test(l) || /^pass$/.test(l)) &&
    !hasStateDep
  ) {
    return "identity";
  }

  // llm: calls an LLM AND does no other heavy work.
  if (hasLlm && !hasHeavyOther && !hasSql) return "llm";

  // sql_udf: single SQL pattern, no LLM, no other heavy work.
  if (hasSql && !hasLlm && !hasHeavyOther) return "sql_udf";

  // mcp_tool: invokes a task_* AND no LLM/SQL/heavy mixed in (otherwise
  // it's a multi-step composition that should be a real graph, not 1 node).
  if (hasTaskInvoke && !hasLlm && !hasHeavyOther && !hasSql) return "mcp_tool";

  return "self_logic";
}

function main() {
  const refs = refsFromSql();
  process.stdout.write("class\tmodule\tfn\tnotes\n");
  const tally = {};
  for (const r of refs) {
    const py = path.join(PYBASE, `${r.module}.py`);
    let cls, note = "";
    if (!existsSync(py)) {
      cls = "missing";
      note = `${py} not found`;
    } else {
      const text = readFileSync(py, "utf8");
      const body = extractFunctionBody(text, r.fn);
      cls = classify(body, text);
      if (cls === "missing") note = `def ${r.fn} not found in module`;
    }
    tally[cls] = (tally[cls] || 0) + 1;
    process.stdout.write(`${cls}\t${r.module}\t${r.fn}\t${note}\n`);
  }
  process.stderr.write("\n--- summary ---\n");
  for (const [k, v] of Object.entries(tally).sort((a, b) => b[1] - a[1])) {
    process.stderr.write(`  ${k.padEnd(12)} ${v}\n`);
  }
  process.stderr.write(`  ${"total".padEnd(12)} ${refs.length}\n`);
}

main();
