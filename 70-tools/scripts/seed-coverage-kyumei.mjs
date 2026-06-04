#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const out = {
    // Prioritize global corporate + government actors by default.
    domains: ['sovereign', 'cofog', 'treaty', 'isic', 'telecom', 'society6'],
    org: 'admin',
    pds: '',
    samples: 5,
    interval: 2,
    skipSeed: false,
    settleSeconds: 45,
    afterRetries: 3,
    minAfterRatio: 0.85,
    kyumeiTimeoutMs: 420000,
    tag: '',
    since: '',
    sinceWindowHours: 720,
    worldData: '',
    freezeWorldData: true,
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const n = argv[i + 1];
    if (a === '--domains' && n) {
      out.domains = n.split(',').map((s) => s.trim()).filter(Boolean);
      i++;
    } else if (a === '--org' && n) {
      out.org = n;
      i++;
    } else if (a === '--pds' && n) {
      out.pds = n;
      i++;
    } else if (a === '--samples' && n) {
      out.samples = Math.max(1, Number(n) || 5);
      i++;
    } else if (a === '--interval' && n) {
      out.interval = Math.max(0, Number(n) || 2);
      i++;
    } else if (a === '--skip-seed') {
      out.skipSeed = true;
    } else if (a === '--settle-seconds' && n) {
      out.settleSeconds = Math.max(0, Number(n) || 45);
      i++;
    } else if (a === '--after-retries' && n) {
      out.afterRetries = Math.max(1, Number(n) || 3);
      i++;
    } else if (a === '--min-after-ratio' && n) {
      out.minAfterRatio = Math.min(1, Math.max(0, Number(n) || 0.85));
      i++;
    } else if (a === '--kyumei-timeout-ms' && n) {
      out.kyumeiTimeoutMs = Math.max(60000, Number(n) || 420000);
      i++;
    } else if (a === '--tag' && n) {
      out.tag = String(n).trim();
      i++;
    } else if (a === '--since' && n) {
      out.since = String(n).trim();
      i++;
    } else if (a === '--since-window-hours' && n) {
      out.sinceWindowHours = Math.max(1, Number(n) || 720);
      i++;
    } else if (a === '--world-data' && n) {
      out.worldData = String(n).trim();
      i++;
    } else if (a === '--no-freeze-world-data') {
      out.freezeWorldData = false;
    } else if (a === '--help' || a === '-h') {
      console.log('Usage: node scripts/seed-coverage-kyumei.mjs [--domains a,b,c] [--org admin] [--pds URL] [--samples 5] [--interval 2] [--skip-seed] [--settle-seconds 45] [--after-retries 3] [--min-after-ratio 0.85] [--kyumei-timeout-ms 420000] [--tag run1] [--since RFC3339] [--since-window-hours 720] [--world-data /path/world.json] [--no-freeze-world-data]');
      process.exit(0);
    }
  }
  return out;
}

function run(cmd, args, opts = {}) {
  const res = spawnSync(cmd, args, {
    cwd: opts.cwd,
    encoding: 'utf8',
    stdio: opts.capture ? ['ignore', 'pipe', 'pipe'] : 'inherit',
    timeout: opts.timeout ?? 180000,
    maxBuffer: 20 * 1024 * 1024,
  });
  if (res.status !== 0) {
    const msg = `${cmd} ${args.join(' ')} failed (${res.status})`;
    if (opts.capture) {
      throw new Error(`${msg}\n${res.stderr || ''}`.trim());
    }
    throw new Error(msg);
  }
  return res;
}

function readJSON(file) {
  return JSON.parse(fs.readFileSync(file, 'utf8'));
}

function sumLiveRecords(obj) {
  return Object.values(obj || {}).reduce((a, b) => a + (Number(b) || 0), 0);
}

function projectDirForDomain(repoRoot, domain) {
  const candidate = path.join(repoRoot, 'projects', `etzhayyim-project-${domain}`);
  return fs.existsSync(candidate) ? candidate : path.join(repoRoot, 'projects');
}

function buildCoverageMedianArgs(repoRoot, opts, outPath, fixedSince, worldDataPath) {
  const args = [
    path.join(repoRoot, 'scripts', 'coverage-world-median.mjs'),
    '--samples', String(opts.samples),
    '--interval', String(opts.interval),
    '--org', opts.org,
    '--out', outPath,
  ];
  if (opts.pds) args.push('--pds', opts.pds);
  if (fixedSince) args.push('--since', fixedSince);
  if (worldDataPath) args.push('--world-data', worldDataPath);
  return args;
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function coverageMedianTimeoutMs(opts) {
  // Worst-case per sample can approach 120s in coverage-world-median.
  // Add headroom for process startup and JSON write.
  return Math.max(300000, opts.samples * 130000 + 30000);
}

function seedTimeoutMs(opts) {
  // Large domain sets can take significantly longer due network + projection lag.
  return Math.max(900000, opts.domains.length * 120000);
}

function normalizeSince(opts) {
  if (opts.since) return opts.since;
  const t = new Date(Date.now() - opts.sinceWindowHours * 60 * 60 * 1000);
  return t.toISOString();
}

function generateWorldDataSnapshot(repoRoot, outPath) {
  const src = path.join(repoRoot, 'packages', 'cmd', 'etzhayyim', 'world_coverage.go');
  const raw = fs.readFileSync(src, 'utf8');
  const start = raw.indexOf('var worldDomains = []worldDomain{');
  if (start < 0) {
    throw new Error('worldDomains block not found in world_coverage.go');
  }
  const end = raw.indexOf('\n}\n\n// ── PDS live query types', start);
  const block = raw.slice(start, end > start ? end : raw.length);
  const entryMatches = block.match(/\{[^{}]*Domain:\s*"[^"]+"[^{}]*\},/g) || [];
  const entries = [];
  for (const rec of entryMatches) {
    const domain = rec.match(/Domain:\s*"([^"]+)"/)?.[1];
    const app = rec.match(/App:\s*"([^"]+)"/)?.[1];
    const worldTotalRaw = rec.match(/WorldTotal:\s*([0-9_]+)/)?.[1];
    const unit = rec.match(/Unit:\s*"([^"]+)"/)?.[1];
    const source = rec.match(/Source:\s*"([^"]+)"/)?.[1];
    const didLabel = rec.match(/DIDLabel:\s*"([^"]+)"/)?.[1];
    const recordLabel = rec.match(/RecordLabel:\s*"([^"]+)"/)?.[1];
    if (!domain || !app || !worldTotalRaw || !unit || !source || !didLabel) continue;
    const altRaw = rec.match(/AltPrefixes:\s*\[]string\{([^}]*)\}/)?.[1] || '';
    const altPrefixes = [...altRaw.matchAll(/"([^"]+)"/g)].map((m) => m[1]);
    const row = {
      domain,
      app,
      ...(altPrefixes.length > 0 ? { altPrefixes } : {}),
      worldTotal: Number(worldTotalRaw.replaceAll('_', '')),
      unit,
      source,
      didLabel,
      ...(recordLabel ? { recordLabel } : {}),
    };
    entries.push(row);
  }
  if (entries.length === 0) {
    throw new Error('failed to parse world domains from world_coverage.go');
  }
  fs.mkdirSync(path.dirname(outPath), { recursive: true });
  fs.writeFileSync(outPath, JSON.stringify(entries, null, 2));
  return outPath;
}

async function main() {
  const opts = parseArgs(process.argv);
  const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
  const etzhayyimDir = path.join(repoRoot, 'packages', 'cmd', 'etzhayyim');
  const reportsDir = path.join(repoRoot, 'reports');
  fs.mkdirSync(reportsDir, { recursive: true });

  const startedAt = new Date().toISOString();
  const tagSuffix = opts.tag ? `-${opts.tag}` : '';
  const beforePath = path.join(reportsDir, `world-coverage-before-seed${tagSuffix}.json`);
  const afterPath = path.join(reportsDir, `world-coverage-after-seed${tagSuffix}.json`);
  const fixedSince = normalizeSince(opts);
  const snapshotWorldDataPath = path.join(reportsDir, `world-domains-snapshot${tagSuffix || '-fixed'}.json`);
  const worldDataPath = opts.worldData
    ? path.resolve(repoRoot, opts.worldData)
    : (opts.freezeWorldData ? snapshotWorldDataPath : '');
  if (opts.freezeWorldData && !opts.worldData) {
    generateWorldDataSnapshot(repoRoot, worldDataPath);
  }

  console.error('1) Coverage baseline median');
  run('node', buildCoverageMedianArgs(repoRoot, opts, beforePath, fixedSince, worldDataPath), {
    cwd: repoRoot,
    timeout: coverageMedianTimeoutMs(opts),
  });
  const before = readJSON(beforePath);

  if (!opts.skipSeed) {
    console.error('2) Seed batch');
    const seedArgs = ['run', '.', 'seed', '-app', opts.domains.join(',')];
    if (opts.pds) seedArgs.push('--pds', opts.pds);
    run('go', seedArgs, { cwd: etzhayyimDir, timeout: seedTimeoutMs(opts) });
  }

  console.error('3) Coverage after median');
  const beforeMedianRecords = Number(before?.medianSummary?.totalRecords || 0);
  let after = null;
  let afterAttempt = 0;
  const afterThreshold = Math.floor(beforeMedianRecords * opts.minAfterRatio);
  while (afterAttempt < opts.afterRetries) {
    afterAttempt += 1;
    if (afterAttempt > 1) {
      console.error(`Retrying after-coverage (${afterAttempt}/${opts.afterRetries})`);
    }
    run('node', buildCoverageMedianArgs(repoRoot, opts, afterPath, fixedSince, worldDataPath), {
      cwd: repoRoot,
      timeout: coverageMedianTimeoutMs(opts),
    });
    after = readJSON(afterPath);
    const afterMedianRecords = Number(after?.medianSummary?.totalRecords || 0);
    if (afterMedianRecords >= afterThreshold) break;
    if (afterAttempt < opts.afterRetries) {
      console.error(
        `after totalRecords too low (${afterMedianRecords} < ${afterThreshold}); waiting ${opts.settleSeconds}s for projection settle`,
      );
      await sleep(opts.settleSeconds * 1000);
    }
  }

  console.error('4) Kyumei per domain');
  const kyumei = [];
  for (const d of opts.domains) {
    const out = path.join(reportsDir, `kyumei-domain-${d}${tagSuffix}.json`);
    const args = [
      'run', '.', 'apps', 'kyumei-koji',
      '-domain', d,
      '-json',
      '-dir', projectDirForDomain(repoRoot, d),
      '-fast',
      '-max-subdids', '24',
      '-timeout', '8',
    ];
    if (opts.pds) args.push('--pds', opts.pds);
    try {
      const res = run('go', args, { cwd: etzhayyimDir, capture: true, timeout: opts.kyumeiTimeoutMs });
      fs.writeFileSync(out, res.stdout || '{}');
      const j = JSON.parse(res.stdout || '{}');
      kyumei.push({
        domain: d,
        nanoid: j.nanoid || '',
        readiness: j.readiness_grade || '',
        score: j.readiness_score ?? null,
        liveRecords: sumLiveRecords(j.live_record_counts || {}),
        collections: Object.keys(j.live_record_counts || {}).length,
      });
    } catch (e) {
      kyumei.push({ domain: d, error: String(e.message || e) });
    }
  }

  const b = before.medianSummary || {};
  const a = after.medianSummary || {};
  const summary = {
    generatedAt: new Date().toISOString(),
    startedAt,
    options: opts,
    fixedSince,
    worldDataPath,
    afterAttempt,
    beforeMedian: b,
    afterMedian: a,
    delta: {
      totalRecords: (a.totalRecords ?? 0) - (b.totalRecords ?? 0),
      worldCoverageRecord: (a.worldCoverageRecord ?? 0) - (b.worldCoverageRecord ?? 0),
      worldCoverageOverall: (a.worldCoverageOverall ?? 0) - (b.worldCoverageOverall ?? 0),
    },
    kyumei,
  };

  const summaryPath = path.join(reportsDir, `seed-coverage-kyumei-summary${tagSuffix}.json`);
  fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

  console.log(JSON.stringify({
    summaryPath,
    beforePath,
    afterPath,
    delta: summary.delta,
    kyumeiCount: kyumei.length,
  }, null, 2));
}

main();
