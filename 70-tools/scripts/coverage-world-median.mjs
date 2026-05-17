#!/usr/bin/env node
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const out = {
    samples: 7,
    intervalSec: 5,
    org: '',
    pds: '',
    strict: false,
    since: '',
    worldData: '',
    outFile: '',
  };
  for (let i = 2; i < argv.length; i++) {
    const a = argv[i];
    const next = argv[i + 1];
    if (a === '--samples' && next) {
      out.samples = Math.max(1, Number(next) || 7);
      i++;
    } else if (a === '--interval' && next) {
      out.intervalSec = Math.max(0, Number(next) || 5);
      i++;
    } else if (a === '--org' && next) {
      out.org = next;
      i++;
    } else if (a === '--pds' && next) {
      out.pds = next;
      i++;
    } else if (a === '--since' && next) {
      out.since = next;
      i++;
    } else if (a === '--world-data' && next) {
      out.worldData = next;
      i++;
    } else if (a === '--out' && next) {
      out.outFile = next;
      i++;
    } else if (a === '--strict') {
      out.strict = true;
    } else if (a === '--help' || a === '-h') {
      printUsage();
      process.exit(0);
    }
  }
  return out;
}

function printUsage() {
  console.log(`coverage-world-median.mjs

Usage:
  node scripts/coverage-world-median.mjs [options]

Options:
  --samples <n>      Number of samples (default: 7)
  --interval <sec>   Seconds between samples (default: 5)
  --org <id>         Pass through to gftd coverage --org
  --pds <url>        Pass through to gftd coverage --pds
  --since <window>   Pass through to gftd coverage --since
  --world-data <f>   Pass through to gftd coverage --world-data
  --strict           Pass through to gftd coverage --strict
  --out <file>       Output JSON report path (default: reports/world-coverage-samples-<ts>.json)
`);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function toNum(v) {
  return typeof v === 'number' && Number.isFinite(v) ? v : null;
}

function median(values) {
  const arr = values.filter((v) => typeof v === 'number' && Number.isFinite(v)).slice().sort((a, b) => a - b);
  if (arr.length === 0) return null;
  const mid = Math.floor(arr.length / 2);
  if (arr.length % 2 === 0) return (arr[mid - 1] + arr[mid]) / 2;
  return arr[mid];
}

function pickNearestSample(samples, target) {
  if (!samples.length || target == null) return null;
  let best = null;
  for (const s of samples) {
    if (!s.summary || toNum(s.summary.worldCoverageOverall) == null) continue;
    const d = Math.abs(s.summary.worldCoverageOverall - target);
    if (!best || d < best.delta) best = { sample: s, delta: d };
  }
  return best ? best.sample : null;
}

function buildCoverageArgs(opts) {
  const args = ['run', '.', 'coverage', '-json'];
  if (opts.org) args.push('--org', opts.org);
  if (opts.pds) args.push('--pds', opts.pds);
  if (opts.since) args.push('--since', opts.since);
  if (opts.worldData) args.push('--world-data', opts.worldData);
  if (opts.strict) args.push('--strict');
  return args;
}

async function main() {
  const opts = parseArgs(process.argv);
  const repoRoot = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
  const gftdDir = path.join(repoRoot, 'packages', 'cmd', 'gftd');

  const stamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\..+/, 'Z');
  const outFile = opts.outFile || path.join(repoRoot, 'reports', `world-coverage-samples-${stamp}.json`);
  fs.mkdirSync(path.dirname(outFile), { recursive: true });

  const samples = [];
  const commandArgs = buildCoverageArgs(opts);

  console.error(`Sampling gftd coverage ${opts.samples}x (interval=${opts.intervalSec}s)`);
  for (let i = 0; i < opts.samples; i++) {
    const startedAt = new Date().toISOString();
    const res = spawnSync('go', commandArgs, {
      cwd: gftdDir,
      encoding: 'utf8',
      timeout: 120000,
      maxBuffer: 20 * 1024 * 1024,
    });

    let parsed = null;
    let parseError = '';
    if (res.stdout) {
      try {
        parsed = JSON.parse(res.stdout);
      } catch (e) {
        parseError = String(e);
      }
    }

    const sample = {
      index: i + 1,
      startedAt,
      exitCode: res.status,
      signal: res.signal || '',
      parseError,
      stderr: (res.stderr || '').trim(),
      summary: parsed?.summary || null,
      evaluatedAt: parsed?.evaluatedAt || '',
    };
    samples.push(sample);

    const rec = sample.summary?.totalRecords;
    const wc = sample.summary?.worldCoverageOverall;
    console.error(`#${sample.index} exit=${sample.exitCode} records=${rec ?? 'n/a'} world=${wc ?? 'n/a'}`);

    if (i < opts.samples - 1 && opts.intervalSec > 0) {
      await sleep(opts.intervalSec * 1000);
    }
  }

  const ok = samples.filter((s) => s.exitCode === 0 && s.summary);
  if (ok.length === 0) {
    const report = { generatedAt: new Date().toISOString(), options: opts, samples, error: 'no successful coverage samples' };
    fs.writeFileSync(outFile, JSON.stringify(report, null, 2));
    console.error(`No successful samples. Report: ${outFile}`);
    process.exit(1);
  }

  const med = {
    totalApps: median(ok.map((s) => toNum(s.summary.totalApps))),
    totalDIDs: median(ok.map((s) => toNum(s.summary.totalDIDs))),
    totalRecords: median(ok.map((s) => toNum(s.summary.totalRecords))),
    totalProfiles: median(ok.map((s) => toNum(s.summary.totalProfiles))),
    worldCoverageDid: median(ok.map((s) => toNum(s.summary.worldCoverageDid))),
    worldCoverageRecord: median(ok.map((s) => toNum(s.summary.worldCoverageRecord))),
    worldCoverageOverall: median(ok.map((s) => toNum(s.summary.worldCoverageOverall))),
  };

  const representative = pickNearestSample(ok, med.worldCoverageOverall);

  const report = {
    generatedAt: new Date().toISOString(),
    options: opts,
    command: ['go', ...commandArgs].join(' '),
    successfulSamples: ok.length,
    medianSummary: med,
    representativeSample: representative
      ? {
          index: representative.index,
          evaluatedAt: representative.evaluatedAt,
          summary: representative.summary,
        }
      : null,
    samples,
  };

  fs.writeFileSync(outFile, JSON.stringify(report, null, 2));

  console.log(JSON.stringify({
    outFile,
    successfulSamples: ok.length,
    medianSummary: med,
    representativeIndex: representative?.index || null,
  }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
