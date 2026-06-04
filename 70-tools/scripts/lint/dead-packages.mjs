#!/usr/bin/env node
/**
 * dead-packages — package.json の dependencies / devDependencies のうち、
 * ソースファイル内に import / require 参照が1つも存在しないパッケージを検出する。
 *
 * スコープ: 各 package.json と同じディレクトリ以下のソースファイル。
 * 対象外:
 *   - pnpm workspace protocol (`workspace:*`) のパッケージ
 *   - @types/* パッケージ (TS 型のみ、import なし)
 *   - bin ツール (wrangler, vite, tsc 等: devDeps で実行するもの)
 *   - peer dependencies
 *
 * exit 0: 未使用パッケージなし (or --warn-only)
 * exit 1: 未使用パッケージあり (--warn-only なし)
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const WARN_ONLY  = process.argv.includes('--warn-only');
const JSON_OUT   = process.argv.includes('--json');
const ONLY_PROD  = process.argv.includes('--prod'); // devDeps を除外

// These packages are never imported in source but are legitimately used via
// CLI / config / peer resolution. Exclude from dead-package detection.
const KNOWN_TOOLCHAIN = new Set([
  // build/deploy toolchain
  'wrangler', 'vite', 'typescript', 'esbuild', 'rollup', 'parcel', 'webpack',
  'nx', 'turbo', 'lefthook', 'husky',
  // test runners
  'vitest', 'jest', '@jest/core', 'playwright', '@playwright/test', 'mocha',
  // svelte / framework build deps
  '@sveltejs/kit', '@sveltejs/adapter-cloudflare', '@sveltejs/adapter-static',
  '@sveltejs/adapter-auto', 'svelte', 'svelte-check',
  // Tailwind toolchain
  'tailwindcss', 'autoprefixer', 'postcss', 'prettier', 'eslint',
  '@tailwindcss/vite',
  // type stubs (not imported, but tsconfig needs them)
  '@cloudflare/workers-types',
  // pnpm special
  'pnpm',
]);

const EXCLUDE_DIRS = [
  'node_modules', '.svelte-kit', 'dist', 'build', '_svelte', '.wrangler',
  '_deprecated', 'coverage', 'static', 'public', '.git',
];
const RG_EXCLUDES = EXCLUDE_DIRS.flatMap(d => ['--glob', `!**/${d}/**`]);

function rg(args) {
  const r = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.error) throw r.error;
  return r.stdout ?? '';
}

/** Find package.json files (one level inside 60-apps and major workspace dirs). */
function findPackageJsons() {
  // We want package.json in actual workspaces, not root or nested node_modules.
  // Use rg to list all package.json files, then filter.
  const out = rg([
    '--files',
    '--glob', '**/package.json',
    ...RG_EXCLUDES,
    '--glob', '!**/wasm/**/_svelte/**',
  ]);
  return out.trim().split('\n').filter(Boolean);
}

/**
 * Return all direct dep names from a package.json.
 * Excludes workspace:*, @types/*, peerDependencies, and KNOWN_TOOLCHAIN.
 */
function getDeps(pkgPath) {
  let pkg;
  try {
    pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf8'));
  } catch {
    return [];
  }

  const all = {
    ...(ONLY_PROD ? {} : (pkg.devDependencies ?? {})),
    ...(pkg.dependencies ?? {}),
  };

  return Object.entries(all)
    .filter(([name, ver]) => {
      if (String(ver).startsWith('workspace:')) return false; // local workspace pkg
      if (name.startsWith('@types/')) return false;           // type-only
      if (KNOWN_TOOLCHAIN.has(name)) return false;            // CLI toolchain
      return true;
    })
    .map(([name]) => name);
}

/**
 * Escape a package name for use in a regex.
 * e.g. "@etzhayyim/wproto" → `@etzhayyim\/wproto`
 */
function escapeForRegex(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

/**
 * Check whether `pkgName` is referenced in `dir`'s source files.
 * Matches: import ... from 'pkgName', require('pkgName'),
 *          import 'pkgName', from "pkgName/..."
 */
function isUsedInDir(pkgName, dir) {
  const esc = escapeForRegex(pkgName);
  // Match: from 'pkg', from "pkg", require('pkg'), import 'pkg'
  const pattern = `(?:from|require|import)\\s+['"](${esc}(?:/[^'"]*)?)['"']`;

  const out = rg([
    '--quiet',
    '--glob', '*.ts',
    '--glob', '*.svelte',
    '--glob', '*.js',
    '--glob', '*.mjs',
    '--glob', '*.cjs',
    ...RG_EXCLUDES,
    pattern,
    dir,
  ]);
  return out.trim().length > 0;
}

// ── Main ──────────────────────────────────────────────────────────────────────

const pkgFiles = findPackageJsons();

/** @type {{ pkgJson: string, package: string }[]} */
const dead = [];

for (const pkgJson of pkgFiles) {
  const dir  = path.dirname(pkgJson);
  const deps = getDeps(pkgJson);

  for (const dep of deps) {
    if (!isUsedInDir(dep, dir)) {
      dead.push({ pkgJson, package: dep });
    }
  }
}

if (JSON_OUT) {
  console.log(JSON.stringify({ dead, total: dead.length }, null, 2));
  process.exit(dead.length > 0 && !WARN_ONLY ? 1 : 0);
}

if (dead.length === 0) {
  console.log('✅ dead-packages: no unused npm packages found');
  process.exit(0);
}

console.log(`\n${WARN_ONLY ? '⚠️ ' : '❌'} dead-packages: ${dead.length} package(s) with no import references:\n`);
const byFile = new Map();
for (const d of dead) {
  if (!byFile.has(d.pkgJson)) byFile.set(d.pkgJson, []);
  byFile.get(d.pkgJson).push(d.package);
}
for (const [file, pkgs] of byFile) {
  console.log(`  ${file}`);
  for (const p of pkgs) console.log(`    "${p}"`);
}
console.log('');

if (WARN_ONLY) {
  process.exit(0);
} else {
  console.log('  → remove from package.json or add an import to suppress');
  process.exit(1);
}
