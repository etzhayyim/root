#!/usr/bin/env node
/**
 * dead-exports — barrel index.ts の export 宣言で、codebase 内に import 参照が
 * 1つも存在しないシンボルを検出する。
 *
 * 対象: `src/lib/index.ts`, `appview/src/index.ts` 等の barrel ファイル。
 * スコープ:
 *   - package.json に `"private": true` → 自パッケージ内のみ検索
 *   - package.json に `"private": false` or absent → リポジトリ全体を検索
 *     (cross-workspace consumers を含む; `workspace:*` 経由で参照されるケースに対応)
 *
 * exit 0: 参照ゼロエクスポートなし (or --warn-only モード)
 * exit 1: 参照ゼロエクスポートあり (--warn-only なし)
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const WARN_ONLY = process.argv.includes('--warn-only');
const JSON_OUT  = process.argv.includes('--json');

// Repo root = two directories up from 70-tools/scripts/lint/
const REPO_ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../..');

const EXCLUDE_DIRS = [
  'node_modules', '.svelte-kit', 'dist', 'build', '_svelte', '.wrangler',
  '_deprecated', 'coverage', 'playwright-report', 'static', 'public',
];

// ripgrep exclusion globs
const RG_EXCLUDES = EXCLUDE_DIRS.flatMap(d => ['--glob', `!**/${d}/**`]);

/** Run rg and return stdout string (empty string on no-match / error). */
function rg(args) {
  const r = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.error) throw r.error;
  return r.stdout ?? '';
}

/** Find barrel files: files named index.ts inside a lib/ or src/ directory. */
function findBarrelFiles() {
  const out = rg([
    '--files',
    '--glob', '**/lib/index.ts',
    '--glob', '**/appview/src/index.ts',
    ...RG_EXCLUDES,
  ]);
  return out.trim().split('\n').filter(Boolean);
}

/**
 * Parse named re-exports from a barrel file.
 * Handles:
 *   export { default as Foo } from './Foo.svelte'
 *   export { foo, bar }       from './utils'
 *   export type { FooProps }  from './Foo.svelte'   ← included (type imports matter)
 * Skips:
 *   export * from '...'                              ← star exports (unresolvable)
 *   export default ...                               ← default export (not a named re-export)
 */
function parseNamedExports(filePath) {
  const src = fs.readFileSync(filePath, 'utf8');
  const names = new Set();

  // Match { ... } blocks in export statements
  const RE = /^export(?:\s+type)?\s*\{([^}]+)\}/gm;
  let m;
  while ((m = RE.exec(src)) !== null) {
    const block = m[1];
    // Each specifier: "Foo", "default as Foo", "Foo as Bar"
    for (const spec of block.split(',')) {
      const s = spec.trim();
      if (!s) continue;
      // `X as Y` → exported name is Y
      const asMatch = s.match(/\bas\s+(\w+)\s*$/);
      if (asMatch) {
        names.add(asMatch[1]);
      } else {
        // plain name (possibly prefixed by `type`)
        const plain = s.replace(/^type\s+/, '').trim();
        if (/^\w+$/.test(plain) && plain !== 'default') {
          names.add(plain);
        }
      }
    }
  }
  return [...names];
}

/**
 * Resolve the package root and public/private status for a barrel file.
 * Walk up directories until we find a package.json or wrangler.jsonc.
 *
 * Returns { dir, isPublic }:
 *   isPublic = true  → package.json has `"private": false` (or no private field)
 *                      → search entire repo for import references
 *   isPublic = false → package.json has `"private": true`
 *                      → search only within the package directory
 */
function resolvePackageInfo(barrelFile) {
  let dir = path.dirname(barrelFile);
  for (let i = 0; i < 8; i++) {
    const pkgPath = path.join(dir, 'package.json');
    if (fs.existsSync(pkgPath)) {
      let isPublic = false;
      try {
        const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
        // private: true  → internal app package, scope to own dir
        // private: false or absent → published/shared package, scope to repo
        isPublic = pkg.private !== true;
      } catch { /* treat as private on parse error */ }
      return { dir, isPublic };
    }
    if (fs.existsSync(path.join(dir, 'wrangler.jsonc'))) {
      return { dir, isPublic: false };
    }
    const parent = path.dirname(dir);
    if (parent === dir) break;
    dir = parent;
  }
  return { dir: path.dirname(barrelFile), isPublic: false };
}

/**
 * Check if `name` is imported anywhere inside `searchRoot`
 * (excluding EXCLUDE_DIRS and the barrel file itself).
 *
 * We look for `{ name }`, `{ name,`, `, name }`, `, name,`
 * which covers all destructured import patterns.
 *
 * For public packages (private: false), searchRoot = REPO_ROOT so cross-workspace
 * consumers are included. For private packages, searchRoot = own package dir.
 */
function isImportedInWorkspace(name, searchRoot, barrelFile) {
  // Pattern: the name surrounded by { } import-destructure punctuation or whitespace
  const pattern = `[{,]\\s*(?:type\\s+)?${name}\\s*[},]`;

  const out = rg([
    '--files-with-matches',
    '--glob', '*.ts',
    '--glob', '*.svelte',
    ...RG_EXCLUDES,
    pattern,
    searchRoot,
  ]);

  const files = out.trim().split('\n').filter(Boolean);
  // A match only in the barrel file itself = dead
  return files.some(f => path.resolve(f) !== path.resolve(barrelFile));
}

// ── Main ──────────────────────────────────────────────────────────────────────

const barrels = findBarrelFiles();
if (barrels.length === 0) {
  if (!JSON_OUT) console.log('✅ dead-exports: no barrel index.ts files found');
  else console.log(JSON.stringify({ dead: [], total: 0 }));
  process.exit(0);
}

/** @type {{ file: string, name: string }[]} */
const dead = [];

for (const barrel of barrels) {
  const { dir: pkgDir, isPublic } = resolvePackageInfo(barrel);
  // Public packages (private: false) → search entire repo to catch cross-workspace consumers.
  // Private packages (private: true)  → search only own package dir.
  const searchRoot = isPublic ? REPO_ROOT : pkgDir;
  const names = parseNamedExports(barrel);

  for (const name of names) {
    if (!isImportedInWorkspace(name, searchRoot, barrel)) {
      dead.push({ file: barrel, name });
    }
  }
}

if (JSON_OUT) {
  console.log(JSON.stringify({ dead, total: dead.length }, null, 2));
  process.exit(dead.length > 0 && !WARN_ONLY ? 1 : 0);
}

if (dead.length === 0) {
  console.log('✅ dead-exports: no dead barrel exports found');
  process.exit(0);
}

console.log(`\n${WARN_ONLY ? '⚠️ ' : '❌'} dead-exports: ${dead.length} export(s) with zero import references:\n`);
// Group by file
const byFile = new Map();
for (const d of dead) {
  if (!byFile.has(d.file)) byFile.set(d.file, []);
  byFile.get(d.file).push(d.name);
}
for (const [file, names] of byFile) {
  console.log(`  ${file}`);
  for (const n of names) console.log(`    export { ${n} }`);
}
console.log('');

if (WARN_ONLY) {
  process.exit(0);
} else {
  console.log('  → remove the export declaration or add a reference to suppress');
  process.exit(1);
}
