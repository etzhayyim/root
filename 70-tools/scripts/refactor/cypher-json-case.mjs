#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const DRY_RUN = process.argv.includes('--dry-run');

const EXCLUDE_GLOBS = [
  '!.git',
  '!**/node_modules/**',
  '!**/.next/**',
  '!**/.svelte-kit/**',
  '!**/dist/**',
  '!**/build/**',
  '!**/coverage/**',
  '!**/.turbo/**',
  '!**/gen/**',
  '!**/generated/**',
  '!**/*.min.*',
  '!**/*.map',
  '!**/pnpm-lock.yaml',
  '!**/package-lock.json',
  '!**/bun.lock*',
];

const JSONLD_RESERVED_KEYS = new Set([
  '@base',
  '@container',
  '@context',
  '@direction',
  '@graph',
  '@id',
  '@import',
  '@included',
  '@index',
  '@json',
  '@language',
  '@list',
  '@nest',
  '@none',
  '@prefix',
  '@propagate',
  '@protected',
  '@reverse',
  '@set',
  '@type',
  '@value',
  '@version',
  '@vocab',
]);

const LABEL_KEYS = new Set([
  'label',
  'nodeLabel',
  'sourceLabel',
  'targetLabel',
  'fromLabel',
  'toLabel',
  'entityLabel',
]);

const LABEL_ARRAY_KEYS = new Set(['labels', 'nodeLabels']);

const SNAKE_CASE_RE = /^[a-z][a-z0-9]*(?:_[a-z0-9]+)+$/;
const PASCAL_RE = /^[A-Z][A-Za-z0-9]*$/;
const IDENTIFIERISH_RE = /^[A-Za-z0-9_-]+$/;

function listFiles() {
  const args = ['--files', '--hidden'];
  for (const glob of EXCLUDE_GLOBS) args.push('--glob', glob);
  args.push('--glob', '*.json', '--glob', '*.jsonld');
  const r = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  if (r.error) throw r.error;
  if (r.status !== 0) {
    throw new Error(`rg --files failed: ${r.stderr?.trim() ?? ''}`);
  }
  const out = r.stdout.trim();
  return out ? out.split('\n').filter(Boolean).sort() : [];
}

function toCamel(key) {
  return key.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
}

function toPascal(value) {
  return value
    .split(/[_\-\s]+/)
    .filter(Boolean)
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join('');
}

function shouldKeepKey(key) {
  if (JSONLD_RESERVED_KEYS.has(key)) return true;
  if (key.startsWith('@')) return true;
  if (key.startsWith('$')) return true;
  return false;
}

function maybePascalizeLabel(value) {
  if (typeof value !== 'string') return value;
  if (!IDENTIFIERISH_RE.test(value)) return value;
  if (value.includes(':') || value.includes('/')) return value;
  if (PASCAL_RE.test(value)) return value;
  return toPascal(value);
}

function transform(value, jsonPath = '$') {
  if (Array.isArray(value)) {
    return value.map((v, i) => transform(v, `${jsonPath}[${i}]`));
  }
  if (!value || typeof value !== 'object') return value;

  const out = {};
  for (const [origKey, origVal] of Object.entries(value)) {
    let key = origKey;
    if (!shouldKeepKey(origKey) && SNAKE_CASE_RE.test(origKey)) {
      key = toCamel(origKey);
    }

    const nextPath = `${jsonPath}.${key}`;
    let nextVal = transform(origVal, nextPath);

    if (LABEL_KEYS.has(key)) {
      nextVal = maybePascalizeLabel(nextVal);
    } else if (LABEL_ARRAY_KEYS.has(key) && Array.isArray(nextVal)) {
      nextVal = nextVal.map((v) => maybePascalizeLabel(v));
    }

    if (Object.prototype.hasOwnProperty.call(out, key) && JSON.stringify(out[key]) !== JSON.stringify(nextVal)) {
      throw new Error(`key collision at ${nextPath}`);
    }
    out[key] = nextVal;
  }
  return out;
}

let changed = 0;
let skipped = 0;
let parseErr = 0;

for (const rel of listFiles()) {
  const abs = path.resolve(rel);
  const src = fs.readFileSync(abs, 'utf8');
  let parsed;
  try {
    parsed = JSON.parse(src);
  } catch {
    parseErr += 1;
    skipped += 1;
    continue;
  }

  let next;
  try {
    next = transform(parsed);
  } catch {
    skipped += 1;
    continue;
  }

  const out = `${JSON.stringify(next, null, 2)}\n`;
  if (out !== src) {
    changed += 1;
    if (!DRY_RUN) fs.writeFileSync(abs, out, 'utf8');
  }
}

console.log(JSON.stringify({ dryRun: DRY_RUN, changed, skipped, parseErr }, null, 2));
