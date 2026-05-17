#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 3): every `*.waitUntil(<promise>)` must hand
 * in a promise that has a terminal `.catch(...)`. Otherwise a background
 * rejection post-response escapes as CF 1101 and can taint the next request
 * on the same isolate.
 *
 * Valid shapes:
 *   ctx.waitUntil(foo().catch(log))
 *   ctx.waitUntil((async () => { try { ... } catch {} })())
 *   ctx.waitUntil(Promise.resolve(...).catch(() => {}))
 *
 * Baseline: uses 90-docs/rules/waituntil-requires-catch-baseline.txt
 * (so existing violations don't break CI immediately; new ones fail).
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const UPDATE = process.argv.includes('--update-baseline');
const BASELINE_PATH = '90-docs/rules/waituntil-requires-catch-baseline.txt';

const SCOPES = ['50-infra', '60-apps', '20-actors'];

function listFiles() {
  const r = spawnSync('rg', [
    '--files-with-matches', '\\.waitUntil\\s*\\(',
    '--glob', '*.{ts,tsx,js,mjs}',
    '--glob', '!**/node_modules/**', '--glob', '!**/dist/**', '--glob', '!**/.wrangler-out/**',
    ...SCOPES,
  ], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
  return (r.stdout || '').split('\n').filter(Boolean);
}

// Find `.waitUntil(` then extract the balanced-paren argument; flag if it has
// no `.catch(` and is not an IIFE with internal try/catch.
function scanFile(file) {
  const text = fs.readFileSync(file, 'utf8');
  const offenders = [];
  const re = /\.waitUntil\s*\(/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    let depth = 1, i = m.index + m[0].length;
    const start = i;
    while (i < text.length && depth > 0) {
      const c = text[i];
      if (c === '(') depth++;
      else if (c === ')') depth--;
      if (depth === 0) break;
      i++;
    }
    const arg = text.slice(start, i);
    const hasCatch = /\.catch\s*\(/.test(arg);
    const isIIFE = /\(\s*async[\s\S]*\}\s*\)\s*\(\s*\)/.test(arg) && /\btry\s*\{/.test(arg);
    if (!hasCatch && !isIIFE) {
      const lineNo = text.slice(0, m.index).split('\n').length;
      offenders.push(`${file}:${lineNo}`);
    }
  }
  return offenders;
}

const current = [];
for (const f of listFiles()) current.push(...scanFile(f));
current.sort();
const currentSet = [...new Set(current)];

if (UPDATE) {
  fs.mkdirSync(path.dirname(BASELINE_PATH), { recursive: true });
  fs.writeFileSync(BASELINE_PATH, currentSet.join('\n') + '\n');
  console.log(`updated baseline: ${BASELINE_PATH} (${currentSet.length} entries)`);
  process.exit(0);
}

const baseline = fs.existsSync(BASELINE_PATH)
  ? fs.readFileSync(BASELINE_PATH, 'utf8').split('\n').filter(Boolean)
  : [];
const baselineSet = new Set(baseline);
const added = currentSet.filter(e => !baselineSet.has(e));

if (added.length > 0) {
  console.error('ADR-0007 violation (waituntil-requires-catch):');
  console.error('  New `*.waitUntil(<promise>)` without terminal `.catch(...)` or');
  console.error('  internal try/catch IIFE. Unhandled rejections → CF 1101.');
  for (const e of added.slice(0, 50)) console.error(`  ${e}`);
  if (added.length > 50) console.error(`  ...and ${added.length - 50} more`);
  console.error('\nIf intentional, run: pnpm lint:waituntil-catch:update');
  process.exit(1);
}
console.log(`lint:waituntil-requires-catch ok (current=${currentSet.length}, baseline=${baseline.length})`);
