#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 7): `70-tools/scripts/contract/gen-pds-lexicon-registry.mjs`
 * must produce a collision-free `NSID_*` constant registry. We run the generator
 * in-process (it already `throw`s on 3-way collisions) and additionally verify
 * that the emitted file has no duplicate `export const NSID_*` declarations.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const GEN = '70-tools/scripts/contract/gen-pds-lexicon-registry.mjs';
const OUT = '50-infra/cloudflare/workers/atproto/src/generated/lexicon-registry.gen.ts';

const r = spawnSync(process.execPath, [GEN], { encoding: 'utf8' });
if (r.status !== 0) {
  console.error('lexicon codegen failed:');
  console.error(r.stdout || '');
  console.error(r.stderr || '');
  process.exit(1);
}

if (!fs.existsSync(OUT)) {
  console.error(`generator did not emit expected output: ${OUT}`);
  process.exit(1);
}
const text = fs.readFileSync(OUT, 'utf8');
const seen = new Map();
const dup = [];
const RE = /^export\s+const\s+(NSID_[A-Z0-9_]+)\s*=/gm;
let m;
while ((m = RE.exec(text)) !== null) {
  const name = m[1];
  if (seen.has(name)) dup.push(name);
  else seen.set(name, true);
}

if (dup.length > 0) {
  console.error('ADR-0007 violation (lexicon-const-name-collision):');
  console.error('  duplicate `export const NSID_*` in generated registry:');
  for (const d of [...new Set(dup)]) console.error(`  ${d}`);
  console.error(`  generator: ${GEN}`);
  console.error(`  output:    ${OUT}`);
  process.exit(1);
}
console.log(`lint:lexicon-const-name-collision ok (${seen.size} unique NSID constants)`);
