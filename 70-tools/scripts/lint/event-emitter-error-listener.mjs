#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 4): any `new Pool(...)` / `new pg.Client(...)` /
 * `new EventEmitter(...)` constructed inside CF Worker code must have a
 * `.on('error', ...)` listener in the same file. EventEmitter 'error' events
 * without a listener escape as CF 1101.
 *
 * Scope: worker scopes only.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

const SCOPES = ['50-infra/cloudflare/workers', '60-apps'];
const CTOR_RE = /\bnew\s+(Pool|Client|EventEmitter)\s*\(/g;

function listFiles() {
  const r = spawnSync('rg', [
    '--files-with-matches', 'new\\s+(Pool|Client|EventEmitter)\\s*\\(',
    '--glob', '*.{ts,tsx,js,mjs}',
    '--glob', '!**/node_modules/**', '--glob', '!**/dist/**',
    '--glob', '!**/_deprecated/**', '--glob', '!**/_archive/**',
    '--glob', '!**/*.test.ts', '--glob', '!**/*.spec.ts',
    ...SCOPES,
  ], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
  return (r.stdout || '').split('\n').filter(Boolean).filter(f => /\/worker(s?)\//.test(f) || f.includes('/worker/'));
}

const offenders = [];
for (const f of listFiles()) {
  const text = fs.readFileSync(f, 'utf8');
  const stripped = text.replace(/\/\/.*$/gm, '').replace(/\/\*[\s\S]*?\*\//g, '');
  // Skip files that don't construct the flagged classes (after comment strip)
  if (!/\bnew\s+(Pool|Client|EventEmitter)\s*\(/.test(stripped)) continue;
  // Require that an error listener exists somewhere in the file
  const hasErrorListener = /\.on\s*\(\s*['"]error['"]/.test(stripped);
  if (!hasErrorListener) offenders.push(f);
}

if (offenders.length > 0) {
  console.error('ADR-0007 violation (event-emitter-error-listener):');
  console.error('  Worker files constructing Pool/Client/EventEmitter must attach a');
  console.error("  .on('error', handler) listener. Unhandled 'error' events → CF 1101.");
  for (const f of offenders) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`lint:event-emitter-error-listener ok`);
