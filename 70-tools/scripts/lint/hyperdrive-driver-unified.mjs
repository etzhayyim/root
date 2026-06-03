#!/usr/bin/env node
/**
 * ADR-0007 enforcement (rule 6): Hyperdrive → Kysely wiring must go through
 * the canonical `createKyselyDb` factory exported by
 * `@etzhayyim/magatama-host-sdk/kysely`. Local `createHyperdriveDb` factories in
 * worker code are allowed ONLY if they delegate to `createKyselyDb` (proved
 * by their body importing/calling it). Anything else drifts the driver
 * layer and re-introduces pg.Pool.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';

const SCOPES = ['50-infra', '60-apps'];
const SDK_PATH = '20-actors/magatama/sdk/magatama-host-sdk/src/kysely.ts';

function listFiles() {
  const r = spawnSync('rg', [
    '--files-with-matches',
    'export\\s+(function|const)\\s+create(Hyperdrive|Kysely)Db',
    '--glob', '*.{ts,tsx,js,mjs}',
    '--glob', '!**/node_modules/**',
    ...SCOPES,
  ], { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 });
  if (r.status !== 0 && r.status !== 1) throw new Error(`rg failed: ${r.stderr}`);
  return (r.stdout || '').split('\n').filter(Boolean);
}

const offenders = [];
for (const f of listFiles()) {
  if (f.endsWith(SDK_PATH)) continue; // canonical
  const text = fs.readFileSync(f, 'utf8');
  const declaresLocalFactory = /export\s+(function|const)\s+create(Hyperdrive|Kysely)Db\b/.test(text);
  if (!declaresLocalFactory) continue;
  // Allow only if it imports `createKyselyDb` from the SDK and calls it within the factory body.
  const importsSdk = /from\s+['"]@etzhayyim\/magatama-host-sdk\/kysely['"]/.test(text) || /from\s+['"]@etzhayyim\/magatama-host-sdk['"]/.test(text);
  const delegates = /createKyselyDb\s*\(/.test(text);
  if (!(importsSdk && delegates)) offenders.push(f);
}

if (offenders.length > 0) {
  console.error('ADR-0007 violation (hyperdrive-driver-unified):');
  console.error('  Local `createHyperdriveDb` / `createKyselyDb` factories must delegate to');
  console.error('  `@etzhayyim/magatama-host-sdk/kysely::createKyselyDb` (HyperdriveDialect, single pg.Client).');
  for (const f of offenders) console.error(`  ${f}`);
  process.exit(1);
}
console.log(`lint:hyperdrive-driver-unified ok`);
