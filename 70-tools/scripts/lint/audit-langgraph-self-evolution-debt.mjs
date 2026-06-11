#!/usr/bin/env node
/**
 * audit-langgraph-self-evolution-debt
 *
 * Single-number progress meter for ADR-2605082000 self-evolution transform.
 * Counts every `vertex_langgraph_assistant` and `vertex_langgraph_assistant_node`
 * INSERT row by `kind` across all SQL migrations (not just bulk-51) and
 * compares the totals to ADR-aligned targets:
 *
 *   assistant level (ADR-2605082000 §1):
 *     topology   ← preferred (data-driven, resolves at compile time)
 *     py_factory ← legacy, code-island (entire graph defined in Python)
 *
 *   node level (ADR-2605082000 §2):
 *     mcp_tool / sql_udf / py_ext_udf / llm   ← data-resolved (good)
 *     py_primitive                            ← banned for new rows
 *     rust_udf                                ← grandfathered (precompiled UDF)
 *
 * Output: TSV summary to stdout, totals to stderr. Emits no exit-1 (this is
 * a metrics tool, not a gate — see lint-langgraph-py-primitive-ban for the
 * gate). CI can grep stdout to track trends over time.
 *
 * Usage: node 70-tools/scripts/lint/audit-langgraph-self-evolution-debt.mjs
 */
import { spawnSync } from "node:child_process";
import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const SEARCH_ROOTS = [
  path.join(REPO_ROOT, "30-graph/graph-schema/sql_migrations"),
  path.join(REPO_ROOT, "30-graph/graph-schema/migrations"),
];

function listSql() {
  // Only count *.up.sql / *.ts (live state) — *.down.sql are rollback-only
  // and would skew the metric if treated as applied (the same actor row
  // appears in both .up and .down for restore-on-rollback symmetry).
  const args = ["--files", "--glob", "*.sql", "--glob", "!*.down.sql"];
  for (const r of SEARCH_ROOTS) args.push(r);
  const result = spawnSync("rg", args, { encoding: "utf8" });
  if (result.error) throw result.error;
  if ((result.stdout || "").trim() === "") return [];
  return result.stdout.trim().split("\n").filter(Boolean);
}

function collectSupersededFromText(text, supersededSet) {
  // UPDATE vertex_langgraph_assistant SET superseded_by = '...' WHERE assistant_id = '<X>'
  const re = /UPDATE\s+vertex_langgraph_assistant\s+SET\s+superseded_by\s*=\s*'[^']+'\s*WHERE\s+assistant_id\s*=\s*'([^']+)'/gi;
  let m;
  while ((m = re.exec(text)) !== null) supersededSet.add(m[1]);
}

// Same-PK upsert tracker: in RisingWave, INSERT into a table with an
// existing PK overwrites silently. The langgraph_builtin_63 seed inserted
// 63 py_factory rows; bulk-51 then re-INSERTed many of those assistant_ids
// as kind=topology (same vertex_id PK → upsert). The earlier py_factory
// row no longer reflects DB state. Detect by recording each assistant_id's
// LAST-SEEN kind across files processed in date-sorted order.
function trackLatestKind(text, latestKind, fileOrder, fileIdx) {
  const reAssist = /INSERT INTO\s+vertex_langgraph_assistant\b[\s\S]*?VALUES\s*\(\s*'([^']+)'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*'([^']+)'\s*,\s*\d+\s*,\s*'(topology|py_factory)'/gi;
  let m;
  while ((m = reAssist.exec(text)) !== null) {
    const assistantId = m[2];
    const kind = m[3];
    latestKind.set(assistantId, kind);
    fileOrder.set(assistantId, fileIdx);
  }
  const reNode = /INSERT INTO\s+vertex_langgraph_assistant_node\b[\s\S]*?VALUES\s*\(\s*'([^':]+):([^']+)'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'([a-z_]+)'/gi;
  let n;
  while ((n = reNode.exec(text)) !== null) {
    const key = `${n[3]}:${n[4]}`;
    const kind = n[5];
    latestKind.set(`node::${key}`, kind);
    fileOrder.set(`node::${key}`, fileIdx);
  }
}

function countInFileAware(text, supersededSet, latestKind, fileOrder, fileIdx) {
  const out = {
    assistant: { topology: 0, py_factory: 0, other: 0 },
    node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0, other: 0 },
    live_assistant: { topology: 0, py_factory: 0 },
    live_node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0 },
    // ADR-2605082000 Phase D: routing-layer code-island axis. Counts
    // conditional_edges in live topology assistants by their dispatch
    // mechanism: 'router' = legacy py_primitive callable, 'field' =
    // data-driven state lookup. The headline node metric ignored these
    // (they live in vertex_langgraph_assistant.config, not _node), so
    // a metric move via mcp_tool migration could mask routing residue.
    router_island: { router: 0, field: 0 },
    live_router_island: { router: 0, field: 0 },
  };
  // Match a topology assistant INSERT and capture (assistant_id, config_json).
  // The bulk-51 / saikin-v2 / ki-v2 / *_canonical_v2 migrations all use the
  // same shape: ('<aid>', N, 0, '<aid>', V, 'topology', NULL, '<config_json>',
  //              '<description>', '<ts>'). The config JSON is a single-quoted
  // string with embedded escaped JSON; capture greedily until ', '<desc>'.
  const reTopologyConfig =
    /VALUES\s*\(\s*'([^']+)'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*'([^']+)'\s*,\s*\d+\s*,\s*'topology'\s*,\s*(?:NULL|'[^']*')\s*,\s*'([\s\S]*?)'\s*,\s*'/g;
  let cm;
  while ((cm = reTopologyConfig.exec(text)) !== null) {
    const aid = cm[2];
    const cfg = cm[3];
    // Live = same-PK upsert winner + not superseded_by-marked.
    const lk = latestKind.get(aid);
    const lo = fileOrder.get(aid);
    const isLive = (lk === "topology") && (lo === fileIdx) && !supersededSet.has(aid);
    // Each conditional_edge entry has either "router" or "field". Count
    // both for visibility (field = data-driven, router = code-island).
    // Match minimal forms to dodge whitespace & escaping variance.
    const routerHits = (cfg.match(/"router"\s*:\s*"/g) || []).length;
    const fieldHits  = (cfg.match(/"field"\s*:\s*"/g)  || []).length;
    out.router_island.router += routerHits;
    out.router_island.field  += fieldHits;
    if (isLive) {
      out.live_router_island.router += routerHits;
      out.live_router_island.field  += fieldHits;
    }
  }
  const reAssist = /VALUES\s*\(\s*'([^']+)'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*'([^']+)'\s*,\s*\d+\s*,\s*'(topology|py_factory)'/i;
  const reNodeKey = /VALUES\s*\(\s*'([^':]+):([^']+)'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*'([^']+)'\s*,\s*'([^']+)'\s*,\s*'(mcp_tool|sql_udf|py_ext_udf|llm|py_primitive|rust_udf)'/i;
  for (const line of text.split("\n")) {
    const isAssistantInsert = /INSERT INTO\s+vertex_langgraph_assistant\b/i.test(line)
      || /'(topology|py_factory)'\s*,\s*(NULL|'kotodama)/.test(line);
    const isNodeInsert = /INSERT INTO\s+vertex_langgraph_assistant_node\b/i.test(line)
      || /'(mcp_tool|sql_udf|py_ext_udf|llm|py_primitive|rust_udf)'/.test(line);

    let isLive = true;
    let assistKey = null;
    let nodeKey = null;
    const ma = line.match(reAssist);
    if (ma) {
      assistKey = ma[2];
      const lk = latestKind.get(assistKey);
      const lo = fileOrder.get(assistKey);
      // not the latest-seen kind for this PK → upserted away
      if (lk && lk !== ma[3]) isLive = false;
      // not the latest file that touched this PK → upserted away
      if (lo !== undefined && lo !== fileIdx) isLive = false;
      if (supersededSet.has(assistKey)) isLive = false;
    }
    const mn = line.match(reNodeKey);
    if (mn) {
      nodeKey = `node::${mn[3]}:${mn[4]}`;
      const lk = latestKind.get(nodeKey);
      const lo = fileOrder.get(nodeKey);
      if (lk && lk !== mn[5]) isLive = false;
      if (lo !== undefined && lo !== fileIdx) isLive = false;
      if (supersededSet.has(mn[3])) isLive = false;
    }

    if (isAssistantInsert && /'topology'/.test(line)) {
      out.assistant.topology += 1;
      if (isLive) out.live_assistant.topology += 1;
    }
    if (isAssistantInsert && /'py_factory'/.test(line)) {
      out.assistant.py_factory += 1;
      if (isLive) out.live_assistant.py_factory += 1;
    }
    if (isNodeInsert) {
      const mark = (k) => {
        out.node[k] += 1;
        if (isLive) out.live_node[k] += 1;
      };
      if (/'mcp_tool'/.test(line))         mark("mcp_tool");
      else if (/'sql_udf'/.test(line))     mark("sql_udf");
      else if (/'py_ext_udf'/.test(line))  mark("py_ext_udf");
      else if (/'llm'/.test(line))         mark("llm");
      else if (/'py_primitive'/.test(line)) mark("py_primitive");
      else if (/'rust_udf'/.test(line))    mark("rust_udf");
    }
  }
  return out;
}


function countInFile(text, supersededSet) {
  const out = {
    assistant: { topology: 0, py_factory: 0, other: 0 },
    node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0, other: 0 },
    live_assistant: { topology: 0, py_factory: 0 },
    live_node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0 },
  };
  // Capture each row's assistant_id so we can skip superseded ones for
  // "live" counts. Both vertex_langgraph_assistant and *_node rows include
  // the assistant_id as the 4th value: ('vertex_id', 0, 0, '<assistant_id>', ...).
  // The assistant table's own VALUES start with `'<assistant_id>'` (since
  // vertex_id == assistant_id) — same regex captures both.
  const ASSIST_ID_RE = /VALUES\s*\(\s*'[^']*'\s*,\s*[0-9]+\s*,\s*[0-9]+\s*,\s*(?:[0-9]+\s*,\s*)?\s*'([^']+)'/i;
  for (const line of text.split("\n")) {
    const isAssistantInsert = /INSERT INTO\s+vertex_langgraph_assistant\b/i.test(line)
      || /'(topology|py_factory)'\s*,\s*(NULL|'kotodama)/.test(line);
    const isNodeInsert = /INSERT INTO\s+vertex_langgraph_assistant_node\b/i.test(line)
      || /'(mcp_tool|sql_udf|py_ext_udf|llm|py_primitive|rust_udf)'/.test(line);

    let live = true;
    const m = line.match(ASSIST_ID_RE);
    if (m && supersededSet.has(m[1])) live = false;

    if (isAssistantInsert && /'topology'/.test(line)) {
      out.assistant.topology += 1;
      if (live) out.live_assistant.topology += 1;
    }
    if (isAssistantInsert && /'py_factory'/.test(line)) {
      out.assistant.py_factory += 1;
      if (live) out.live_assistant.py_factory += 1;
    }
    if (isNodeInsert) {
      const mark = (k) => {
        out.node[k] += 1;
        if (live) out.live_node[k] += 1;
      };
      if (/'mcp_tool'/.test(line))         mark("mcp_tool");
      else if (/'sql_udf'/.test(line))     mark("sql_udf");
      else if (/'py_ext_udf'/.test(line))  mark("py_ext_udf");
      else if (/'llm'/.test(line))         mark("llm");
      else if (/'py_primitive'/.test(line)) mark("py_primitive");
      else if (/'rust_udf'/.test(line))    mark("rust_udf");
    }
  }
  return out;
}

function main() {
  const totals = {
    assistant: { topology: 0, py_factory: 0 },
    node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0 },
    live_assistant: { topology: 0, py_factory: 0 },
    live_node: { mcp_tool: 0, sql_udf: 0, py_ext_udf: 0, llm: 0, py_primitive: 0, rust_udf: 0 },
    router_island: { router: 0, field: 0 },
    live_router_island: { router: 0, field: 0 },
  };
  // Two-pass: first collect all superseded assistant_ids + same-PK upsert
  // history (latest-seen kind wins, file order = filename sort = apply order
  // since migrations are date-prefixed), then count.
  const superseded = new Set();
  const latestKind = new Map();
  const fileOrder = new Map();
  // Sort files by basename so date-prefixed migrations apply chronologically.
  const files = listSql().sort((a, b) =>
    path.basename(a).localeCompare(path.basename(b)));
  for (let i = 0; i < files.length; i += 1) {
    const txt = readFileSync(files[i], "utf8");
    collectSupersededFromText(txt, superseded);
    trackLatestKind(txt, latestKind, fileOrder, i);
  }
  // A row is "live" if it is the latest-seen kind for its (assistant_id) or
  // (assistant_id:node_id), AND its assistant is not superseded_by-marked.
  for (let i = 0; i < files.length; i += 1) {
    const txt = readFileSync(files[i], "utf8");
    const c = countInFileAware(txt, superseded, latestKind, fileOrder, i);
    for (const k of Object.keys(totals.assistant))      totals.assistant[k]      += c.assistant[k];
    for (const k of Object.keys(totals.node))           totals.node[k]           += c.node[k];
    for (const k of Object.keys(totals.live_assistant)) totals.live_assistant[k] += c.live_assistant[k];
    for (const k of Object.keys(totals.live_node))      totals.live_node[k]      += c.live_node[k];
    for (const k of Object.keys(totals.router_island))      totals.router_island[k]      += c.router_island[k];
    for (const k of Object.keys(totals.live_router_island)) totals.live_router_island[k] += c.live_router_island[k];
  }

  // TSV
  process.stdout.write("level\tkind\tcount\tcategory\n");
  process.stdout.write(`assistant\ttopology\t${totals.assistant.topology}\tdata\n`);
  process.stdout.write(`assistant\tpy_factory\t${totals.assistant.py_factory}\tcode-island\n`);
  process.stdout.write(`node\tmcp_tool\t${totals.node.mcp_tool}\tdata\n`);
  process.stdout.write(`node\tsql_udf\t${totals.node.sql_udf}\tdata\n`);
  process.stdout.write(`node\tpy_ext_udf\t${totals.node.py_ext_udf}\tdata\n`);
  process.stdout.write(`node\tllm\t${totals.node.llm}\tdata\n`);
  process.stdout.write(`node\tpy_primitive\t${totals.node.py_primitive}\tcode-island\n`);
  process.stdout.write(`node\trust_udf\t${totals.node.rust_udf}\tprecompiled\n`);
  process.stdout.write(`route\trouter\t${totals.router_island.router}\tcode-island\n`);
  process.stdout.write(`route\tfield\t${totals.router_island.field}\tdata\n`);

  const nodeData = totals.node.mcp_tool + totals.node.sql_udf + totals.node.py_ext_udf + totals.node.llm;
  const nodeCode = totals.node.py_primitive;
  const nodeTotal = nodeData + nodeCode + totals.node.rust_udf;
  const nodeShare = nodeTotal > 0 ? ((nodeData / nodeTotal) * 100).toFixed(1) : "n/a";

  const assistTotal = totals.assistant.topology + totals.assistant.py_factory;
  const assistShare = assistTotal > 0
    ? ((totals.assistant.topology / assistTotal) * 100).toFixed(1)
    : "n/a";

  // Live-only metric: same calculation but excluding rows whose
  // assistant_id has been superseded by a later v2 assistant.
  const lvNodeData = totals.live_node.mcp_tool + totals.live_node.sql_udf
    + totals.live_node.py_ext_udf + totals.live_node.llm;
  const lvNodeCode = totals.live_node.py_primitive;
  const lvNodeTotal = lvNodeData + lvNodeCode + totals.live_node.rust_udf;
  const lvNodeShare = lvNodeTotal > 0 ? ((lvNodeData / lvNodeTotal) * 100).toFixed(1) : "n/a";
  const lvAssistTotal = totals.live_assistant.topology + totals.live_assistant.py_factory;
  const lvAssistShare = lvAssistTotal > 0
    ? ((totals.live_assistant.topology / lvAssistTotal) * 100).toFixed(1)
    : "n/a";

  process.stderr.write("\n--- self-evolution debt summary (all rows) ---\n");
  process.stderr.write(`assistant data-share:  ${assistShare}%  (${totals.assistant.topology} / ${assistTotal})\n`);
  process.stderr.write(`node      data-share:  ${nodeShare}%  (${nodeData} / ${nodeTotal})\n`);
  process.stderr.write(`node      code-island: ${nodeCode}\n`);
  process.stderr.write(`assistant code-island: ${totals.assistant.py_factory}\n`);

  process.stderr.write("\n--- live-only (excluding superseded_by-marked v1 rows) ---\n");
  process.stderr.write(`assistant data-share (live):  ${lvAssistShare}%  (${totals.live_assistant.topology} / ${lvAssistTotal})\n`);
  process.stderr.write(`node      data-share (live):  ${lvNodeShare}%  (${lvNodeData} / ${lvNodeTotal})\n`);
  process.stderr.write(`node      code-island (live): ${lvNodeCode}\n`);
  process.stderr.write(`assistant code-island (live): ${totals.live_assistant.py_factory}\n`);
  // Routing-layer code-island axis (ADR-2605082000 Phase D).
  const routeTotal = totals.router_island.router + totals.router_island.field;
  const routeShare = routeTotal > 0
    ? ((totals.router_island.field / routeTotal) * 100).toFixed(1)
    : "n/a";
  const lvRouteTotal = totals.live_router_island.router + totals.live_router_island.field;
  const lvRouteShare = lvRouteTotal > 0
    ? ((totals.live_router_island.field / lvRouteTotal) * 100).toFixed(1)
    : "n/a";
  process.stderr.write(
    `route     data-share:  ${routeShare}%  (${totals.router_island.field} field / ${routeTotal} total)\n`,
  );
  process.stderr.write(
    `route     code-island: ${totals.router_island.router}  (legacy py_primitive routers)\n`,
  );
  process.stderr.write(
    `route     data-share (live):  ${lvRouteShare}%  (${totals.live_router_island.field} field / ${lvRouteTotal} total)\n`,
  );
  process.stderr.write(
    `route     code-island (live): ${totals.live_router_island.router}\n`,
  );

  process.stderr.write("\nADR-2605082000 target: data-share 100% / code-island 0 (incl. router)\n");
}

main();
