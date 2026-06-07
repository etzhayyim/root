#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 1): forbid `pg.Pool` inside Cloudflare Workers.
 *
 * In CF Workers, `pg.Pool`'s idle-client 'error' EventEmitter escapes the
 * fetch handler scope and surfaces as opaque CF 1101 platform errors. All
 * Worker code must use `HyperdriveDialect` (single pg.Client) via
 * `@etzhayyim/kotodama-host-sdk/kysely::createKyselyDb`.
 *
 * Scope: CF Worker source trees under 50-infra/cloudflare/workers and
 * 60-apps per-project worker directories.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

const SCOPES = ['50-infra/cloudflare/workers', '60-apps'];
const ALLOWLIST = new Set([
  // Pool usage inside kotodama-host-sdk HyperdriveDialect — it uses pg.Client, not Pool.
]);

function listFiles() {
  const args = ['--files', '--glob', '*.{ts,tsx,js,mjs}'];
  for (const s of SCOPES) args.push(s);
  const r = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
  return (r.stdout || '').split('\n').filter(Boolean).filter(f => /\/worker(s?)\//.test(f) || f.includes('/worker/'));
}

const offenders = [];
for (const f of listFiles()) {
  if (ALLOWLIST.has(f)) continue;
  const text = fs.readFileSync(f, 'utf8');
  // Ignore comment lines: strip // ... and /* ... */
  const stripped = text.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
  if (/\bnew\s+Pool\s*\(/.test(stripped) && /from\s+['"]pg['"]/.test(stripped)) {
    offenders.push(f);
  }
}

if (offenders.length > 0) {
  console.error('ADR-0007 violation (no-pg-pool-in-worker):');
  console.error('  `pg.Pool` inside CF Worker leaks idle-client errors → CF 1101.');
  console.error('  Use `createKyselyDb(env.HYPERDRIVE)` (HyperdriveDialect, single pg.Client) instead.');
  for (const f of offenders) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`lint:no-pg-pool-in-worker ok (scanned ${SCOPES.join(',')})`);
