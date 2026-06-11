#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 2): every CF Worker `fetch` entry must wrap its
 * body in try/catch that returns a structured 5xx JSON on uncaught errors.
 * Otherwise, exceptions escape as opaque CF 1101 platform errors.
 *
 * Heuristic: within the body of `async fetch(request, env, ctx)` (or the
 * default export), require either:
 *   - a `try {` statement, or
 *   - a comment marker `// ADR-0007: handled by <wrapper>` (for workers that
 *     wrap via Hono error middleware + explicit opt-out).
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

const SCOPES = ['50-infra/cloudflare/workers', '60-apps'];

function listEntryFiles() {
  // Files that define a CF Worker via `export default { fetch` or `export default {\n  async fetch`
  const r = spawnSync('rg', [
    '--files-with-matches', '-U',
    'export\\s+default\\s*\\{[\\s\\S]{0,400}?\\bfetch\\s*[:=]',
    '--glob', '*.{ts,tsx,js,mjs}',
    ...SCOPES,
  ], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
  return (r.stdout || '').split('\n').filter(Boolean);
}

const offenders = [];
for (const f of listEntryFiles()) {
  const text = fs.readFileSync(f, 'utf8');
  // Extract the fetch handler body. Very small grammar: find `fetch` after
  // `export default {` and capture matching braces until the first closing.
  const defaultMatch = text.match(/export\s+default\s*\{([\s\S]+)$/);
  if (!defaultMatch) continue;
  const body = defaultMatch[1];
  const fetchIdx = body.search(/\bfetch\s*[:=]\s*(?:async\s+)?(?:function\b[^{]*|\([^)]*\)\s*=>)\s*\{/);
  if (fetchIdx < 0) continue;
  // Find opening brace of fetch body
  const braceIdx = body.indexOf('{', fetchIdx);
  if (braceIdx < 0) continue;
  let depth = 0, end = -1;
  for (let i = braceIdx; i < body.length; i++) {
    const c = body[i];
    if (c === '{') depth++;
    else if (c === '}') { depth--; if (depth === 0) { end = i; break; } }
  }
  if (end < 0) continue;
  const fetchBody = body.slice(braceIdx + 1, end);
  const hasTry = /\btry\s*\{/.test(fetchBody);
  const hasMarker = /ADR-0007:\s*handled by/.test(fetchBody);
  if (!hasTry && !hasMarker) offenders.push(f);
}

if (offenders.length > 0) {
  console.error('ADR-0007 violation (worker-entry-top-level-try):');
  console.error('  `export default { fetch() {...} }` must wrap body in try/catch that returns');
  console.error('  structured 5xx JSON. Otherwise uncaught exceptions become opaque CF 1101.');
  console.error('  Opt-out marker: `// ADR-0007: handled by <wrapper>` in the handler body.');
  for (const f of offenders) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`lint:worker-entry-top-level-try ok`);
