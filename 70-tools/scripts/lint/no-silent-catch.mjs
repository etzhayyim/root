#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const UPDATE = process.argv.includes('--update-baseline');
const BASELINE_PATH = '90-docs/rules/silent-catch-baseline.txt';

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
  '!**/.etzhayyim-deploy/**',
  '!**/_app/immutable/**',
  '!**/static-ui/**',
  '!**/playwright-report/**',
  '!**/project.inlang/cache/**',
  '!**/dist-desktop-test/**',
  '!**/*.min.*',
  '!**/*.map',
  '!pnpm-lock.yaml',
  '!docs/**',
  '!**/*.d.ts',
  '!**/_svelte/**',
  '!**/static/assets/**',
  '!40-engine/kami-engine/kami-engine-sdk/src/lib/genko/genko-embed.ts',
];

// Pattern A: Promise catch with no error parameter
const CATCH_NO_ERR_RE = /\.catch\(\s*(?:async\s*)?\(\s*\)\s*=>/g;
// Pattern B: empty catch block
const EMPTY_CATCH_RE = /catch\s*(?:\([^)]*\))?\s*\{\s*\}/g;

function listFiles() {
  const args = ['--files', '--hidden', '--glob', '*.{ts,tsx,js,mjs,cjs,svelte,sh}'];
  for (const glob of EXCLUDE_GLOBS) args.push('--glob', glob);

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

function collectEntries() {
  const entries = [];

  for (const file of listFiles()) {
    const text = fs.readFileSync(file, 'utf8');
    const lines = text.split('\n');

    for (const line of lines) {
      CATCH_NO_ERR_RE.lastIndex = 0;
      let m;
      while ((m = CATCH_NO_ERR_RE.exec(line)) !== null) {
        entries.push(`${file}:catch-no-err-param:${line.trim()}`);
      }

      EMPTY_CATCH_RE.lastIndex = 0;
      while ((m = EMPTY_CATCH_RE.exec(line)) !== null) {
        entries.push(`${file}:empty-catch-block:${line.trim()}`);
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
  console.error('New silent catch patterns detected:');
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error('\nIf intentional, run: pnpm lint:silent-catch:update');
  process.exit(1);
}

console.log(`lint:silent-catch ok (current=${current.length}, baseline=${baseline.length})`);
