#!/usr/bin/env node
/**
 * ts-camelcase lint — enforce camelCase identifiers in TS/TSX files.
 *
 * Detects snake_case identifiers in variable/function/property declarations.
 * Exception: snake_case is allowed only in SQL syntax lines.
 *
 * Uses baseline approach: new violations fail CI, existing ones are tracked.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const UPDATE = process.argv.includes('--update-baseline');
const BASELINE_PATH = 'rules/ts-camelcase-baseline.txt';

const EXCLUDE_GLOBS = [
  '!.git',
  '!**/node_modules/**',
  '!**/.svelte-kit/**',
  '!**/dist/**',
  '!**/build/**',
  '!**/coverage/**',
  '!**/out/**',
  '!**/.out/**',
  '!**/.wrangler-out/**',
  '!**/_app/immutable/**',
  '!**/static-ui/**',
  '!**/playwright-report/**',
  '!**/project.inlang/cache/**',
  '!**/dist-desktop-test/**',
  '!**/*.min.*',
  '!**/*.map',
  '!**/*.d.ts',
  '!**/*.gen.ts',
  '!**/*.gen.tsx',
  '!pnpm-lock.yaml',
  '!docs/**',
  '!**/pkg/**',
  '!**/perf/**',
  '!**/scripts/**',
  '!**/test/**',
  '!**/tests/**',
  // Infra TS: snake_case allowed (external protocol compat: Nomad, Iceberg Avro, daemon heartbeat, R2 SQL, promoted columns)
  '!infra/cloudflare/workers/murakumo/**',
  '!infra/cloudflare/workers/kagami/**',
  '!infra/cloudflare/workers/atproto/**',
  '!infra/cloudflare/instance/**',
  // Graph packages: Iceberg/Avro/promoted column schema fields are snake_case by spec
  '!packages/graph/**',
  // KAMI engine: Rust WASM FFI bindings use snake_case
  '!packages/engine/kami-engine/**',
  // Deploy cache (generated, not source)
  '!**/.etzhayyim-deploy/**',
];

/**
 * Regex to match snake_case identifiers in TS declarations.
 * Captures: const foo_bar, let foo_bar, var foo_bar, function foo_bar,
 *           property: foo_bar, foo_bar:, foo_bar =
 * Must contain at least one underscore surrounded by lowercase letters/digits.
 */
const SNAKE_CASE_DECL_RE =
  /(?:(?:const|let|var|function|type|interface|enum)\s+|(?:^|\s|,\s*|{\s*))([a-z][a-z0-9]*(?:_[a-z0-9]+)+)\s*(?:[=:;,)\]}]|$)/gm;

/**
 * Identifiers explicitly allowed as SQL column/schema fields.
 * These names are snake_case by design for R2 SQL / table schemas.
 */
const ALLOW_IDENTIFIERS = new Set([
  'record_type',
  'vertex_id',
  'owner_did',
  'app_id',
  'val',
  'org_id',
  'user_id',
  'actor_id',
  'ivf_cluster_id',
  'edge_id',
  'edge_label',
  'src_vid',
  'dst_vid',
  'src_label',
  'dst_label',
  'cluster_id',
  'vector_label',
  // RLS + promoted columns (used in app record literals per CLAUDE.md §RLS)
  'created_at',
  'updated_at',
  'sensitivity_ord',
  'owner_hash',
  'project_id',
  'last_heartbeat',
  'display_name',
  'deploy_at',
  'vertex_type',
  'embedding_norm',
]);

/** File paths exempt from this lint (generated code, external type defs). */
const ALLOW_PATHS_SUFFIXES = [
  '.gen.ts',
  '.gen.tsx',
  '.generated.ts',
  '.generated.tsx',
  'nsid-registry.ts',
  'service-generated.ts',
];

/** Lines containing these patterns are skipped (SQL queries, config objects). */
const SKIP_LINE_PATTERNS = [
  /^\s*\/\//,         // single-line comments
  /^\s*\*/,           // block comment lines
  /^\s*\* /,          // TSDoc lines
  /\bSELECT\b/i,      // SQL
  /\bINSERT\b/i,      // SQL
  /\bUPDATE\b/i,      // SQL
  /\bDELETE\b/i,      // SQL
  /\bFROM\b/i,        // SQL
  /\bWHERE\b/i,       // SQL
  /\bJOIN\b/i,        // SQL
  /\bGROUP\s+BY\b/i,  // SQL
  /\bORDER\s+BY\b/i,  // SQL
  /\bLIMIT\b/i,       // SQL
  /\bWITH\b/i,        // SQL CTE
  /\bRETURNING\b/i,   // SQL
  /\bCREATE\s+TABLE\b/i,
  /\bALTER\s+TABLE\b/i,
  /\bDROP\s+TABLE\b/i,
  /\bON\s+CONFLICT\b/i,
];

function listFiles() {
  const args = ['--files', '--hidden'];
  for (const glob of EXCLUDE_GLOBS) args.push('--glob', glob);
  args.push('--glob', '*.{ts,tsx}');

  const result = spawnSync('rg', args, {
    encoding: 'utf8',
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ''}`);
  }

  const out = result.stdout.trim();
  return out ? out.split('\n').filter(Boolean) : [];
}

/**
 * Check whether a file path should be skipped entirely.
 * @param filePath - relative file path
 */
function isAllowedPath(filePath) {
  if (ALLOW_PATHS_SUFFIXES.some((suffix) => filePath.endsWith(suffix))) return true;
  if (filePath.endsWith('.d.ts')) return true;
  if (filePath.includes('/pkg/')) return true;
  if (filePath.includes('/perf/')) return true;
  if (filePath.includes('/scripts/')) return true;
  if (filePath.includes('/test/')) return true;
  if (filePath.includes('/tests/')) return true;
  return false;
}

/**
 * Check whether a line should be skipped (comments, SQL/SQL).
 * @param line - source line text
 */
function isSkippedLine(line) {
  return SKIP_LINE_PATTERNS.some((re) => re.test(line));
}

/**
 * Collect 1-based line numbers that belong to SQL-like template literals.
 * This allows snake_case in multiline SQL column lists as well.
 *
 * Heuristic:
 * - Find all backtick template literals: `...`
 * - If the literal body contains SQL keywords, mark the full line span as SQL.
 */
function collectSqlTemplateLines(text) {
  const sqlLines = new Set();
  const templateRe = /`[\s\S]*?`/g;
  const sqlKeywordRe = /\b(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE|JOIN|GROUP\s+BY|ORDER\s+BY|LIMIT|WITH|RETURNING|CREATE\s+TABLE|ALTER\s+TABLE|DROP\s+TABLE|ON\s+CONFLICT)\b/i;

  let m;
  while ((m = templateRe.exec(text)) !== null) {
    const chunk = m[0];
    if (!sqlKeywordRe.test(chunk)) continue;

    const startIndex = m.index;
    const endIndex = m.index + chunk.length;
    const startLine = text.slice(0, startIndex).split('\n').length;
    const endLine = text.slice(0, endIndex).split('\n').length;
    for (let ln = startLine; ln <= endLine; ln++) sqlLines.add(ln);
  }
  return sqlLines;
}

function collectEntries() {
  const entries = [];

  for (const file of listFiles()) {
    if (isAllowedPath(file)) continue;

    const text = fs.readFileSync(file, 'utf8');
    const lines = text.split('\n');
    const sqlTemplateLines = collectSqlTemplateLines(text);

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      if (sqlTemplateLines.has(i + 1)) continue;
      if (isSkippedLine(line)) continue;

      SNAKE_CASE_DECL_RE.lastIndex = 0;
      let m;
      while ((m = SNAKE_CASE_DECL_RE.exec(line)) !== null) {
        const ident = m[1];
        if (ALLOW_IDENTIFIERS.has(ident)) continue;
        // Skip SCREAMING_SNAKE_CASE (constants) — only flag lowercase snake_case
        if (/^[A-Z]/.test(ident)) continue;
        entries.push(`${file}:${i + 1}:${ident}`);
      }
    }
  }

  return [...new Set(entries)].sort();
}

const current = collectEntries();

if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, `${current.join('\n')}\n`);
  console.log(`updated baseline: ${BASELINE_PATH} (${current.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, 'utf8').split('\n').filter(Boolean)
  : [];
const baselineSet = new Set(baseline);

const added = current.filter((e) => !baselineSet.has(e));
if (added.length > 0) {
  console.error('New snake_case identifiers detected in TS (should be camelCase):');
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error('\nIf intentional, update the allow-list file directly.');
  process.exit(1);
}

console.log(`lint:ts-camel ok (current=${current.length}, baseline=${baseline.length})`);
