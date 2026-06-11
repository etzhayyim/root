#!/usr/bin/env node
/**
 * gen-bulk51-mcp-migration-draft.mjs
 *
 * For each `mcp_tool` candidate in the bulk-51 audit, emit a draft migration
 * artifact that an operator can review and apply:
 *
 *   - vertex_mcp_tool_def INSERT row     (SQL fragment)
 *   - vertex_langgraph_assistant + node  (SQL fragments for v2)
 *   - _DEFAULT_ACTORS entry              (Python tuple for mcp_dispatch)
 *   - lexicon JSON stub                  (00-contracts/lexicons/...)
 *
 * The generator is intentionally NOT auto-apply: it writes a `.draft.*` file
 * per actor so the operator can edit (input/output schema, descriptions,
 * input_keys) before committing. Each artifact is repeatable / idempotent —
 * re-running the script overwrites the drafts.
 *
 * Inputs:
 *   - 30-graph/.../sql_migrations/20260509150000_topology_bulk_51.up.sql
 *   - 40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs/<actor>.py
 *
 * Outputs (under _working/transform-drafts/bulk51/):
 *   - <actor>.lexicon.<method>.draft.json
 *   - <actor>.migration.draft.sql
 *   - <actor>.dispatch_entry.draft.py.txt
 *   - INDEX.tsv (one row per generated artifact)
 *
 * Usage:
 *   node 70-tools/scripts/codegen/gen-bulk51-mcp-migration-draft.mjs [actor]
 *
 * If `actor` is supplied, only that one is generated; otherwise all
 * mcp_tool candidates are processed.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const BULK_SQL = path.join(
  REPO_ROOT,
  "30-graph/graph-schema/sql_migrations/20260509150000_topology_bulk_51.up.sql",
);
const PYBASE = path.join(REPO_ROOT, "40-engine/kotoba/crates/kotoba-kotodama/py/src/kotodama/langgraph_graphs");
const OUTBASE = path.join(REPO_ROOT, "_working/transform-drafts/bulk51");

const SNAKE = /(?<!^)(?=[A-Z])/g;
function camelToSnake(s) { return s.replace(SNAKE, "_").toLowerCase(); }
function snakeToCamel(s) { return s.replace(/_([a-z])/g, (_, c) => c.toUpperCase()); }

// Skip already-migrated assistants — these have v2 rows / pin flip migrations.
const ALREADY_MIGRATED = new Set([
  "saikin_cycle",
  "ki_cycle",
  "adsk_ingest_dataset",
]);

// Sibling assistants that share a task primitive module map to a single
// canonical actor. Naming: the actor maps to a real Worker hostname
// (<actor>.etzhayyim.com) so it's intentionally short. Method NSIDs include the
// distinguishing prefix that was originally part of the assistant_id.
const ACTOR_GROUPS = {
  // kotodama.primitives.aria_signal:task_aria_*  →  com.etzhayyim.apps.aria.*
  aria: {
    matches: /^aria_/,
    method_template: (assistantId) => assistantId.replace(/^aria_/, ""),
    module: "kotodama.primitives.aria_signal",
    fn_template: "task_aria_{snake}",
  },
  // kotodama.primitives.shosha:task_shosha_*  →  com.etzhayyim.apps.shosha.*
  shosha: {
    matches: /^shosha_/,
    method_template: (assistantId) => assistantId.replace(/^shosha_/, ""),
    module: "kotodama.primitives.shosha",
    fn_template: "task_shosha_{snake}",
  },
  // kotodama.primitives.isbn:task_isbn_*  →  com.etzhayyim.apps.isbn.*
  isbn: {
    matches: /^isbn_/,
    method_template: (assistantId) => assistantId.replace(/^isbn_/, ""),
    module: "kotodama.primitives.isbn",
    fn_template: "task_isbn_{snake}",
  },
  // kotodama.primitives.wellbecoming_*  →  com.etzhayyim.apps.wellbecoming.*
  // (per-sub-module variation; resolver still finds it because module is set)
  wellbecoming: {
    matches: /^wellbecoming_/,
    method_template: (assistantId) => assistantId.replace(/^wellbecoming_/, ""),
    // Module varies per assistant; left null so per-actor analysis fills in.
    module: null,
    fn_template: null,
  },
};

function groupForAssistant(assistantId) {
  for (const [actor, grp] of Object.entries(ACTOR_GROUPS)) {
    if (grp.matches.test(assistantId)) return { actor, ...grp };
  }
  return null;
}

function refsFromBulk() {
  const txt = readFileSync(BULK_SQL, "utf8");
  // Extract assistant_id + node bindings.
  const assistRe = /VALUES\s*\(\s*'([a-z0-9_]+)'\s*,[^)]*?'topology'[^)]*?'(\{[^']+\})'/g;
  const nodeRe = /VALUES\s*\(\s*'([a-z0-9_]+):([a-z0-9_]+)'\s*,[^)]*?'([a-z0-9_]+)'\s*,\s*'([a-z0-9_]+)'\s*,\s*'py_primitive'\s*,\s*'(kotodama\.langgraph_graphs\.([a-z_]+)):([a-zA-Z_]+)'/g;
  const assistants = {};
  let m;
  while ((m = assistRe.exec(txt)) !== null) {
    try {
      const spec = JSON.parse(m[2]);
      assistants[m[1]] = spec;
    } catch { /* skip */ }
  }
  const nodes = [];
  while ((m = nodeRe.exec(txt)) !== null) {
    const [, , , assistantId, nodeId, , module, fn] = m;
    nodes.push({ assistantId, nodeId, module, fn });
  }
  return { assistants, nodes };
}

// Inspect a single langgraph_graphs/<actor>.py function body.
function analyzeNode(actor, fn) {
  const py = path.join(PYBASE, `${actor}.py`);
  if (!existsSync(py)) return null;
  const text = readFileSync(py, "utf8");
  // Function body capture.
  const re = new RegExp(
    `(?:^|\\n)(?:async\\s+)?def\\s+${fn}\\s*\\([^)]*\\)[^:]*:\\n([\\s\\S]*?)(?=\\n(?:async\\s+def|def|class)\\s|\\Z)`,
    "m",
  );
  const m = text.match(re);
  if (!m) return null;
  const body = m[1];

  // Find `from <module> import task_<name>` inside function body.
  const importRe = /from\s+(kotodama\.[a-z0-9_.]+)\s+import\s+([a-zA-Z_]+(?:\s*,\s*[a-zA-Z_]+)*)/g;
  const imports = [];
  let im;
  while ((im = importRe.exec(body)) !== null) {
    const mod = im[1];
    const names = im[2].split(/\s*,\s*/).filter((s) => s.startsWith("task_"));
    for (const n of names) imports.push({ module: mod, fn: n });
  }

  // Find state.get("key", ...) calls — input_keys candidates.
  const stateRe = /state\.get\(\s*["']([a-zA-Z_]+)["']/g;
  const stateKeys = new Set();
  let sm;
  while ((sm = stateRe.exec(body)) !== null) stateKeys.add(sm[1]);

  return {
    body,
    imports,
    stateKeys: Array.from(stateKeys).sort(),
  };
}

function deriveMethod(actor, fn) {
  // Strip leading underscore + `_node` suffix common in langgraph_graphs.
  let m = fn.replace(/^_+/, "").replace(/_node$/, "");
  return snakeToCamel(m);
}

function makeArtifacts(actor, byNode, assistantSpec) {
  // Synthesize lexicon, dispatch entry, and SQL.
  const methods = byNode.map((n) => ({
    nodeId: n.nodeId,
    method: deriveMethod(actor, n.fn),
    fn: n.fn,
    analysis: n.analysis,
  }));

  // Pick module + fn_template heuristically: most common task import.
  const taskCounts = {};
  for (const n of byNode) {
    if (!n.analysis) continue;
    for (const im of n.analysis.imports) {
      const key = `${im.module}::${im.fn}`;
      taskCounts[key] = (taskCounts[key] || 0) + 1;
    }
  }
  const sortedTasks = Object.entries(taskCounts).sort((a, b) => b[1] - a[1]);
  const dominantImport = sortedTasks[0]?.[0];

  // Default convention: module = kotodama.{actor}_worker_main, fn = task_{snake}
  const defaultModule = `kotodama.${actor}_worker_main`;
  const defaultFnFor = (m) => `task_${camelToSnake(m)}`;

  // If dominant task is in a different module OR has unusual prefix, emit override.
  let dispatchEntry;
  if (!dominantImport) {
    dispatchEntry = {
      actor,
      methods: methods.map((m) => m.method),
      _todo: "no task import detected — operator must wire manually",
    };
  } else {
    const [domModule, domFn] = dominantImport.split("::");
    if (domModule === defaultModule && domFn === defaultFnFor(methods[0].method)) {
      dispatchEntry = { actor, methods: methods.map((m) => m.method) };
    } else {
      // Try to derive fn_template from the dominant.
      // E.g. task_adsk_dataset_ingest_all + method datasetIngestAll →
      //   "task_adsk_{snake}" (snake = "dataset_ingest_all").
      const m0 = methods[0];
      const expectedSuffix = `_${camelToSnake(m0.method)}`;
      let fnTemplate = "task_{snake}";
      if (domFn.endsWith(expectedSuffix)) {
        const prefix = domFn.slice(0, domFn.length - expectedSuffix.length);
        fnTemplate = `${prefix}_{snake}`;
      } else {
        fnTemplate = `__TODO_review_${domFn}__`;
      }
      dispatchEntry = {
        actor,
        methods: methods.map((m) => m.method),
        module: domModule,
        fn_template: fnTemplate,
      };
    }
  }

  // Lexicon stubs (one per method).
  const lexicons = methods.map((m) => ({
    path: `00-contracts/lexicons/com/etzhayyim/apps/${actor}/${m.method}.json`,
    json: {
      lexicon: 1,
      id: `com.etzhayyim.apps.${actor}.${m.method}`,
      defs: {
        main: {
          type: "procedure",
          description: `[STUB — operator: fill from ${actor}.py::${m.fn}]`,
          input: {
            encoding: "application/json",
            schema: {
              type: "object",
              properties: Object.fromEntries(
                (m.analysis?.stateKeys || []).map((k) => [
                  k, { type: "string", description: `[stub — refine type]` },
                ]),
              ),
            },
          },
          output: {
            encoding: "application/json",
            schema: {
              type: "object",
              description: "[STUB — operator: fill]",
              properties: { error: { type: "string" } },
            },
          },
        },
      },
    },
  }));

  // SQL: mcp_tool_def + assistant + nodes (v2).
  const v2 = `${actor}.v2`;
  let sql = `-- DRAFT — bulk-51 actor ${actor} → mcp_tool migration\n`;
  sql += `-- Re-run the generator (gen-bulk51-mcp-migration-draft.mjs) to refresh.\n\n`;
  for (const m of methods) {
    const slug = `etzhayyim-apps-${actor}-${m.method}`;
    sql += `INSERT INTO vertex_mcp_tool_def\n`;
    sql += `  (vertex_id, _seq, sensitivity_ord, nsid, actor_did, actor_host, lexicon_type,\n`;
    sql += `   description, input_schema, output_schema, visibility, version, enabled,\n`;
    sql += `   source_path, org_id, user_id, actor_id, created_at)\n`;
    sql += `VALUES\n`;
    sql += `  ('at://did:web:${actor}.etzhayyim.com/com.etzhayyim.mcp.toolDef/${slug}',\n`;
    sql += `   0, 0, 'com.etzhayyim.apps.${actor}.${m.method}',\n`;
    sql += `   'did:web:${actor}.etzhayyim.com', '${actor}.etzhayyim.com', 'procedure',\n`;
    sql += `   '[STUB — fill from lexicon]',\n`;
    sql += `   '{"type":"object"}', '{"type":"object"}',\n`;
    sql += `   'public', 1, TRUE,\n`;
    sql += `   '00-contracts/lexicons/com/etzhayyim/apps/${actor}/${m.method}.json',\n`;
    sql += `   'anon', 'anon', '', '2026-05-09T00:00:00Z');\n\n`;
  }

  // Build assistant spec: copy from existing topology, just adjust state_keys
  // to include the per-method `<method>Out` result keys.
  const stateKeys = (assistantSpec?.state_keys || [])
    .concat(methods.map((m) => `${m.method}Out`));
  const newSpec = { ...assistantSpec, state_keys: stateKeys };
  sql += `INSERT INTO vertex_langgraph_assistant\n`;
  sql += `  (vertex_id, _seq, sensitivity_ord, assistant_id, version, kind,\n`;
  sql += `   factory_path, spec, description, created_at,\n`;
  sql += `   checkpointer_mode, authored_by)\n`;
  sql += `VALUES (\n`;
  sql += `  '${v2}', 0, 0, '${v2}', 2, 'topology', NULL,\n`;
  sql += `  '${JSON.stringify(newSpec).replace(/'/g, "''")}',\n`;
  sql += `  '${actor} (topology v2, mcp_tool nodes)',\n`;
  sql += `  '2026-05-09T00:00:00Z', 'rw_vertex', 'did:web:agent.${actor}.etzhayyim.com'\n`;
  sql += `);\n\n`;

  sql += `INSERT INTO vertex_langgraph_assistant_node\n`;
  sql += `  (vertex_id, _seq, sensitivity_ord, assistant_id, node_id, kind, ref, config, created_at)\n`;
  sql += `VALUES\n`;
  const nodeRows = methods.map((m) => {
    const config = JSON.stringify({
      input_keys: m.analysis?.stateKeys || [],
      result_key: `${m.method}Out`,
      args: { name: `com.etzhayyim.apps.${actor}.${m.method}` },
    });
    return `  ('${v2}:${m.nodeId}', 0, 0, '${v2}', '${m.nodeId}',\n` +
           `   'mcp_tool', 'mcp://com.etzhayyim.apps.${actor}.${m.method}',\n` +
           `   '${config.replace(/'/g, "''")}',\n` +
           `   '2026-05-09T00:00:00Z')`;
  });
  sql += nodeRows.join(",\n") + ";\n\n";

  sql += `UPDATE vertex_langgraph_assistant SET superseded_by = '${v2}'\n`;
  sql += ` WHERE assistant_id = '${actor}';\n\n`;
  sql += `FLUSH;\n`;

  return { lexicons, dispatchEntry, sql };
}

function main() {
  const arg = process.argv[2];
  const { assistants, nodes } = refsFromBulk();

  // Group nodes by assistant_id.
  const byAssistant = {};
  for (const n of nodes) {
    if (!byAssistant[n.assistantId]) byAssistant[n.assistantId] = [];
    byAssistant[n.assistantId].push(n);
  }

  if (!existsSync(OUTBASE)) mkdirSync(OUTBASE, { recursive: true });

  const indexLines = ["assistant_id\tcanonical_actor\tmethods\tlexicons\tdispatch_override\tnotes"];
  let count = 0;
  for (const [actor, ns] of Object.entries(byAssistant)) {
    if (arg && actor !== arg) continue;
    if (ALREADY_MIGRATED.has(actor)) continue;

    // Analyze each node's body
    const annotated = ns.map((n) => ({ ...n, analysis: analyzeNode(n.module, n.fn) }));
    const missing = annotated.filter((n) => n.analysis === null).length;
    if (missing === annotated.length) {
      indexLines.push(`${actor}\t-\t-\t-\tNO_PY_FILE`);
      continue;
    }

    const spec = assistants[actor];
    const { lexicons, dispatchEntry, sql } = makeArtifacts(actor, annotated, spec);

    // Write lexicons
    for (const lex of lexicons) {
      const lexPath = path.join(OUTBASE, `${actor}.lexicon.${path.basename(lex.path)}.draft.json`);
      writeFileSync(lexPath, JSON.stringify(lex.json, null, 2) + "\n");
    }
    // Write SQL
    writeFileSync(path.join(OUTBASE, `${actor}.migration.draft.sql`), sql);
    // Write dispatch entry
    const dispatchTxt = `# Add to mcp_dispatch._DEFAULT_ACTORS\n${JSON.stringify(dispatchEntry, null, 2)}\n`;
    writeFileSync(path.join(OUTBASE, `${actor}.dispatch_entry.draft.py.txt`), dispatchTxt);

    let override;
    if (dispatchEntry._todo) {
      override = "NO_TASK_IMPORT";
    } else if (dispatchEntry.module) {
      override = `${dispatchEntry.module}|${dispatchEntry.fn_template}`;
    } else {
      override = "default";
    }
    const grp = groupForAssistant(actor);
    const canonicalActor = grp ? grp.actor : actor;
    indexLines.push(
      `${actor}\t${canonicalActor}\t${lexicons.length}\t${lexicons.map((l) => path.basename(l.path)).join(",")}\t${override}\t${dispatchEntry._todo || "ok"}`,
    );
    count += 1;
  }

  writeFileSync(path.join(OUTBASE, "INDEX.tsv"), indexLines.join("\n") + "\n");
  process.stderr.write(`generated drafts for ${count} actors → ${OUTBASE}\n`);
}

main();
