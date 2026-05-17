#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 8): the PDS `buildRecordView(obj, ...)` helper
 * must emit `{ uri, cid, value }` where `cid` is derived from `obj.cid`, NOT
 * from `obj.rkey` / `obj.uri` / any other column. A swap here produces
 * silently wrong `cid` values in listRecords/getRecord responses.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

// Only one canonical definition exists; search broadly in case it moves.
const r = spawnSync('rg', [
  '--files-with-matches', '-U',
  'function\\s+buildRecordView\\b',
  '--glob', '*.{ts,tsx,js,mjs}',
  '--glob', '!**/node_modules/**',
  '--glob', '!**/*.test.ts', '--glob', '!**/*.spec.ts',
  '--glob', '!**/_archive/**', '--glob', '!**/_deprecated/**',
  '50-infra', '60-apps', '20-actors', '10-protocol',
], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
const files = (r.stdout || '').split('\n').filter(Boolean);

if (files.length === 0) {
  console.log('lint:repo-record-view-cid-integrity ok (no buildRecordView definitions found)');
  process.exit(0);
}

const offenders = [];
for (const f of files) {
  const text = fs.readFileSync(f, 'utf8');
  // Find `function buildRecordView` body, find the return with `cid:`
  const idx = text.search(/function\s+buildRecordView\b/);
  if (idx < 0) continue;
  const tail = text.slice(idx);
  // Match the first `cid: ...,` or `cid: ...\n` in that function scope
  const cidMatch = tail.match(/\bcid\s*:\s*([^,\n]+?)[,\n]/);
  if (!cidMatch) {
    offenders.push(`${f}: buildRecordView does not return a cid field`);
    continue;
  }
  const expr = cidMatch[1].trim();
  // Accept: obj.cid, cl(obj.cid), row.cid, cl(row.cid), record.cid, cl(record.cid)
  const ok = /\b(obj|row|record)\.cid\b/.test(expr);
  if (!ok) offenders.push(`${f}: cid derived from non-cid expression: ${expr}`);
}

if (offenders.length > 0) {
  console.error('ADR-0007 violation (repo-record-view-cid-integrity):');
  console.error('  `buildRecordView` must set `cid: cl(obj.cid)` (or equivalent). Deriving');
  console.error('  cid from rkey/uri returns silently wrong content identifiers.');
  for (const e of offenders) console.error(`  ${e}`);
  process.exit(1);
}
console.log(`lint:repo-record-view-cid-integrity ok`);
