#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { globSync } from 'node:fs';
import path from 'node:path';

const APPLY = process.argv.includes('--apply');
const ROOT = process.cwd();

const manifestPaths = globSync('orgs/etzhayyim/com-etzhayyim-*/actor-manifest.jsonld', { cwd: ROOT }).sort();
let scanned = 0;
let touched = 0;

for (const rel of manifestPaths) {
  scanned += 1;
  const abs = path.join(ROOT, rel);
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(abs, 'utf-8'));
  } catch {
    continue;
  }

  const pipelines = Array.isArray(manifest.pipelines) ? manifest.pipelines : [];
  let changed = false;

  for (const pipeline of pipelines) {
    const steps = Array.isArray(pipeline?.steps) ? pipeline.steps : [];
    for (const step of steps) {
      if (step?.id === 'coverageNodes' && step?.fn === 'graph.query') {
        step.args = {
          sql: "MATCH (n) WHERE n.repo = $did RETURN count(n) AS nodeCount, coalesce(max(n._seq), 0) AS latestSeq LIMIT 1",
        };
        changed = true;
      }
      if (step?.id !== 'coverageSnapshot' || step?.fn !== 'graph.write') continue;
      const collection = `com.etzhayyim.apps.${String(manifest.name || '').toLowerCase().replace(/[^a-z0-9]/g, '') || String(manifest.nanoid || '')}.coverageSnapshot`;
      step.args = {
        template: "MERGE (c:ActorCoverageSnapshot {actorDid: $did, bucket: $bucket, actorName: $actorName, nanoid: $nanoid, nodeCount: $nodeCount, latestTs: $latestTs, repo: $did, collection: $collection, status: 'active'})",
        params: {
          bucket: '6h',
          actorName: String(manifest.name || ''),
          nanoid: String(manifest.nanoid || ''),
          nodeCount: '$coverageNodes.rows[0].nodeCount',
          latestTs: 0,
          collection,
        },
      };
      changed = true;
    }
  }

  if (!changed) continue;
  touched += 1;
  if (APPLY) writeFileSync(abs, JSON.stringify(manifest, null, 2) + '\n');
  console.log(`${APPLY ? '[applied]' : '[plan]'} ${rel}`);
}

console.log(`\nscanned=${scanned} ${APPLY ? 'applied' : 'planned'}=${touched}`);
if (!APPLY) console.log('dry-run only. re-run with --apply');
