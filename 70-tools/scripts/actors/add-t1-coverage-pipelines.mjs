#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs';
import { globSync } from 'node:fs';
import path from 'node:path';

const APPLY = process.argv.includes('--apply');
const ROOT = process.cwd();

function sanitizeSegment(name, nanoid) {
  const s = String(name || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  if (s && /^[a-z]/.test(s)) return s;
  const n = String(nanoid || '').toLowerCase().replace(/[^a-z0-9]/g, '');
  return n || 'actor';
}

function hasCoveragePipeline(manifest) {
  const pipelines = Array.isArray(manifest.pipelines) ? manifest.pipelines : [];
  for (const p of pipelines) {
    const trig = p?.trigger;
    if (trig?.type === 'xrpc' && typeof trig.nsid === 'string' && trig.nsid.includes('.coverage.get')) {
      return true;
    }
    const steps = Array.isArray(p?.steps) ? p.steps : [];
    if (steps.some((s) => s?.id === 'coverageSnapshot' || s?.id === 'coverageStats')) {
      return true;
    }
  }
  return false;
}

function buildCoveragePipelines(manifest) {
  const segment = sanitizeSegment(manifest.name, manifest.nanoid);
  const coverageNSID = `com.etzhayyim.apps.${segment}.coverage.get`;
  const collection = `com.etzhayyim.apps.${segment}.coverageSnapshot`;

  const cronPipeline = {
    trigger: { type: 'cron', cron: '0 */6 * * *' },
    steps: [
      {
        id: 'coverageNodes',
        fn: 'graph.query',
        args: {
          sql: "MATCH (n) WHERE n.repo = $did RETURN count(n) AS nodeCount, coalesce(max(n._seq), 0) AS latestSeq LIMIT 1"
        }
      },
      {
        id: 'coverageCollections',
        fn: 'graph.query',
        args: {
          sql: "MATCH (n) WHERE n.repo = $did AND n.collection IS NOT NULL RETURN n.collection AS collection, count(n) AS cnt ORDER BY cnt DESC LIMIT 10"
        }
      },
      {
        id: 'coverageSnapshot',
        fn: 'graph.write',
        args: {
          template: "MERGE (c:ActorCoverageSnapshot {actorDid: $did, bucket: $bucket, actorName: $actorName, nanoid: $nanoid, nodeCount: $nodeCount, latestTs: $latestTs, repo: $did, collection: $collection, status: 'active'})",
          params: {
            bucket: "6h",
            actorName: manifest.name,
            nanoid: manifest.nanoid,
            nodeCount: "$coverageNodes.rows[0].nodeCount",
            latestTs: 0,
            collection
          }
        }
      }
    ]
  };

  const xrpcPipeline = {
    trigger: { type: 'xrpc', nsid: coverageNSID },
    steps: [
      {
        id: 'coverageStats',
        fn: 'graph.query',
        args: {
          sql: "MATCH (c:ActorCoverageSnapshot {actorDid: $did}) RETURN c.nodeCount AS nodeCount, c.latestSeq AS latestSeq, c.topCollections AS topCollections, c._seq AS snapshotSeq LIMIT 1"
        }
      },
      {
        id: 'coverageHealth',
        fn: 'graph.query',
        args: {
          sql: "MATCH (n) WHERE n.repo = $did AND n._seq IS NOT NULL WITH count(n) AS total, sum(CASE WHEN toInteger(n._seq) > (timestamp() - 86400000) THEN 1 ELSE 0 END) AS fresh RETURN total AS totalNodes, fresh AS freshNodes, CASE WHEN total = 0 THEN 0.0 ELSE toFloat(fresh) / toFloat(total) END AS freshnessRate LIMIT 1"
        }
      }
    ]
  };

  return [cronPipeline, xrpcPipeline, coverageNSID];
}

const manifestPaths = globSync('orgs/etzhayyim/com-etzhayyim-*/actor-manifest.jsonld', { cwd: ROOT }).sort();
let scanned = 0;
let t1Count = 0;
let changed = 0;
let already = 0;

for (const rel of manifestPaths) {
  scanned += 1;
  const abs = path.join(ROOT, rel);
  let manifest;
  try {
    manifest = JSON.parse(readFileSync(abs, 'utf-8'));
  } catch (e) {
    console.error(`[skip:parse] ${rel}: ${e.message}`);
    continue;
  }
  if (manifest.executionTier !== 'T1') continue;
  t1Count += 1;

  if (hasCoveragePipeline(manifest)) {
    already += 1;
    continue;
  }

  if (!Array.isArray(manifest.pipelines)) manifest.pipelines = [];
  const [cronPipeline, xrpcPipeline, nsid] = buildCoveragePipelines(manifest);
  manifest.pipelines.push(cronPipeline, xrpcPipeline);

  if (APPLY) {
    writeFileSync(abs, JSON.stringify(manifest, null, 2) + '\n');
  }
  changed += 1;
  console.log(`${APPLY ? '[applied]' : '[plan]'} ${rel} -> ${nsid}`);
}

console.log(`\nscanned=${scanned} t1=${t1Count} already=${already} ${APPLY ? 'applied' : 'to_apply'}=${changed}`);
if (!APPLY) {
  console.log('dry-run only. re-run with --apply');
}
