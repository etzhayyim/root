#!/usr/bin/env node
/**
 * json-sql-case lint
 *
 * Enforces SQL-facing naming conventions in JSON/JSON-LD:
 * - object keys should be camelCase (no snake_case)
 * - label-like fields should be PascalCase
 *
 * Baseline-based: only new violations fail.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

const UPDATE = process.argv.includes('--update-baseline');
const BASELINE_PATH = '90-docs/rules/json-sql-case-baseline.txt';

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
  '!reports/**',
  '!**/reports/**',
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
  const result = spawnSync('rg', args, { encoding: 'utf8', maxBuffer: 256 * 1024 * 1024 });
  if (result.error) throw result.error;
  if (result.status !== 0) {
    throw new Error(`rg --files failed (code=${result.status}): ${result.stderr?.trim() ?? ''}`);
  }
  const out = result.stdout.trim();
  return out ? out.split('\n').filter(Boolean).sort() : [];
}

function isReservedKey(key) {
  if (JSONLD_RESERVED_KEYS.has(key)) return true;
  if (key.startsWith('@')) return true;
  if (key.startsWith('$')) return true;
  return false;
}

function isPascalCandidate(value) {
  return typeof value === 'string' &&
    /^[A-Za-z]/.test(value) &&
    IDENTIFIERISH_RE.test(value) &&
    !value.includes(':') &&
    !value.includes('/');
}

function collectViolations() {
  const out = [];

  function walk(value, file, jsonPath) {
    if (Array.isArray(value)) {
      value.forEach((item, i) => walk(item, file, `${jsonPath}[${i}]`));
      return;
    }
    if (!value || typeof value !== 'object') return;

    for (const [key, val] of Object.entries(value)) {
      const keyPath = `${jsonPath}.${key}`;
      if (!isReservedKey(key) && SNAKE_CASE_RE.test(key)) {
        out.push(`${file}:${keyPath}:key:${key}`);
      }

      if (LABEL_KEYS.has(key) && isPascalCandidate(val) && !PASCAL_RE.test(val)) {
        out.push(`${file}:${keyPath}:label:${val}`);
      }
      if (LABEL_ARRAY_KEYS.has(key) && Array.isArray(val)) {
        val.forEach((label, i) => {
          if (isPascalCandidate(label) && !PASCAL_RE.test(label)) {
            out.push(`${file}:${keyPath}[${i}]:label:${label}`);
          }
        });
      }

      walk(val, file, keyPath);
    }
  }

  for (const file of listFiles()) {
    if (file.startsWith('reports/') || file.includes('/reports/')) continue;
    const text = fs.readFileSync(file, 'utf8');
    let parsed;
    try {
      parsed = JSON.parse(text);
    } catch {
      // Ignore non-strict JSON files.
      continue;
    }
    walk(parsed, file, '$');
  }

  return [...new Set(out)].sort();
}

const current = collectViolations();

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
const added = current.filter((entry) => !baselineSet.has(entry));

if (added.length > 0) {
  console.error('New JSON/JSON-LD naming violations (SQL convention) detected:');
  for (const entry of added.slice(0, 200)) console.error(`  ${entry}`);
  if (added.length > 200) console.error(`  ...and ${added.length - 200} more`);
  console.error('\nIf intentional, update the allow-list file directly.');
  process.exit(1);
}

console.log(`lint:json-sql ok (current=${current.length}, baseline=${baseline.length})`);
