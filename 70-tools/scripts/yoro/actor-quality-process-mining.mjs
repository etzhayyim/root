#!/usr/bin/env node
/**
 * Process mining snapshot for the YORO actor-quality enrichment rollout.
 *
 * This intentionally avoids full-table counts across actor-scale relations.
 * It samples bounded recent PDS events and bounded recent repo records, then
 * reconstructs observable cases from profile/seed-post artifacts.
 */

const DEFAULT_DATABASE_URL = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;
const NSID = "com.etzhayyim.apps.yoro.actorQualityEnrich";

function parseArgs(argv) {
  const out = {
    sinceHours: 12,
    limit: 500,
    json: false,
  };

  for (const arg of argv) {
    if (arg === "--json") out.json = true;
    else if (arg.startsWith("--since-hours=")) out.sinceHours = parsePositiveNumber(arg, "--since-hours=");
    else if (arg.startsWith("--limit=")) out.limit = parsePositiveInt(arg, "--limit=");
    else if (arg === "--help" || arg === "-h") usage(0);
    else throw new Error(`Unknown argument: ${arg}`);
  }

  if (out.limit > 5000) {
    throw new Error("--limit is capped at 5000 to avoid accidental actor-scale scans");
  }
  return out;
}

function parsePositiveNumber(arg, prefix) {
  const value = Number.parseFloat(arg.slice(prefix.length));
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${prefix.slice(0, -1)} must be positive`);
  return value;
}

function parsePositiveInt(arg, prefix) {
  const value = Number.parseInt(arg.slice(prefix.length), 10);
  if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`${prefix.slice(0, -1)} must be a positive integer`);
  return value;
}

function usage(code) {
  console.log(`Usage:
  DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \\
    node 70-tools/scripts/yoro/actor-quality-process-mining.mjs [options]

Options:
  --since-hours=N   Lookback window for PDS/BPMN/OCEL counters. Default: 12.
  --limit=N         Bounded recent repo-record sample size. Default: 500.
  --json            Emit machine-readable JSON.
`);
  process.exit(code);
}

const opts = parseArgs(process.argv.slice(2));
if (!DEFAULT_DATABASE_URL) {
  throw new Error("Set DATABASE_URL, KOTOBA_URL, or KOTOBA_URL for RisingWave.");
}

const { default: pg } = await import(
  "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
);

const pool = new pg.Pool({
  connectionString: DEFAULT_DATABASE_URL,
  max: 2,
  statement_timeout: 60_000,
});

function firstSourceHint(valueJson) {
  if (!valueJson) return "";
  const match = String(valueJson).match(/Source:\s*([^"\\]+)/);
  return match?.[1]?.trim() ?? "";
}

function isoFloorFromHours(hours) {
  return new Date(Date.now() - hours * 60 * 60 * 1000).toISOString();
}

function stats(values) {
  const nums = values.filter((value) => Number.isFinite(value)).sort((a, b) => a - b);
  if (nums.length === 0) return { count: 0, min: null, p50: null, p95: null, max: null, avg: null };
  const pick = (q) => nums[Math.min(nums.length - 1, Math.floor((nums.length - 1) * q))];
  return {
    count: nums.length,
    min: nums[0],
    p50: pick(0.5),
    p95: pick(0.95),
    max: nums[nums.length - 1],
    avg: Math.round((nums.reduce((sum, value) => sum + value, 0) / nums.length) * 10) / 10,
  };
}

async function queryOne(sql, params = []) {
  const result = await pool.query(sql, params);
  return result.rows;
}

try {
  const sinceIso = isoFloorFromHours(opts.sinceHours);

  const [pdsRows, bpmnRows, seedRows, profileRows] = await Promise.all([
    queryOne(
      `SELECT event_ts, outcome, wall_time_ms, cpu_time_ms, cf_colo
       FROM vertex_pds_tail_event
       WHERE event_ts >= now() - ($1::varchar || ' hours')::interval
         AND (nsid = $2 OR request_url LIKE '%actorQualityEnrich%')
       ORDER BY event_ts ASC
       LIMIT 5000`,
      [String(opts.sinceHours), NSID]
    ),
    queryOne(
      `SELECT 'bpmn_instance' AS source, count(*) AS n
         FROM vertex_bpmn_instance
        WHERE started_at >= $1
          AND (process_id LIKE '%actorQuality%' OR variables_json LIKE '%actorQuality%')
       UNION ALL
       SELECT 'bpmn_activity' AS source, count(*) AS n
         FROM vertex_bpmn_activity_event
        WHERE occurred_at >= $1
          AND (activity_id LIKE '%actorQuality%' OR payload_json LIKE '%actorQuality%')
       UNION ALL
       SELECT 'bpmn_signal' AS source, count(*) AS n
         FROM vertex_bpmn_signal_log
        WHERE occurred_at >= $1
          AND (payload_json LIKE '%actorQuality%' OR message_name LIKE '%actorQuality%')
       UNION ALL
       SELECT 'ocel_event' AS source, count(*) AS n
         FROM vertex_ocel_event
        WHERE timestamp >= $1
          AND (activity LIKE '%actorQuality%' OR props LIKE '%actorQuality%' OR text LIKE '%actorQuality%')`,
      [sinceIso]
    ),
    queryOne(
      `SELECT repo, rkey, indexed_at, value_json
       FROM vertex_repo_record
       WHERE collection = 'app.bsky.feed.post'
         AND rkey LIKE 'murakumo-quality-seed-%'
       ORDER BY indexed_at DESC
       LIMIT ${opts.limit}`
    ),
    queryOne(
      `SELECT repo, rkey, indexed_at, value_json
       FROM vertex_repo_record
       WHERE collection = 'app.bsky.actor.profile'
         AND rkey = 'self'
       ORDER BY indexed_at DESC
       LIMIT ${opts.limit}`
    ),
  ]);

  const seedCases = seedRows.map((row) => ({
    actorDid: row.repo,
    seedRkey: row.rkey,
    seedIndexedAt: row.indexed_at,
    sourceHint: firstSourceHint(row.value_json),
  }));
  const profileByActor = new Map(
    profileRows.map((row) => [row.repo, {
      profileIndexedAt: row.indexed_at,
      sourceHint: firstSourceHint(row.value_json),
      hasDisplayName: String(row.value_json ?? "").includes("displayName"),
      hasDescription: String(row.value_json ?? "").includes("description"),
    }])
  );

  const reconstructedCases = seedCases
    .map((seed) => ({ ...seed, ...(profileByActor.get(seed.actorDid) ?? {}) }))
    .filter((row) => row.sourceHint || row.profileIndexedAt);

  const bySourceHint = new Map();
  for (const row of reconstructedCases) {
    const key = row.sourceHint || "unknown";
    const group = bySourceHint.get(key) ?? {
      sourceHint: key,
      cases: 0,
      withProfile: 0,
      withSeedPost: 0,
      firstIndexedAt: row.seedIndexedAt,
      lastIndexedAt: row.seedIndexedAt,
    };
    group.cases += 1;
    if (row.profileIndexedAt) group.withProfile += 1;
    if (row.seedRkey) group.withSeedPost += 1;
    if (!group.firstIndexedAt || row.seedIndexedAt < group.firstIndexedAt) group.firstIndexedAt = row.seedIndexedAt;
    if (!group.lastIndexedAt || row.seedIndexedAt > group.lastIndexedAt) group.lastIndexedAt = row.seedIndexedAt;
    bySourceHint.set(key, group);
  }

  const pdsByOutcome = new Map();
  for (const row of pdsRows) {
    const key = row.outcome || "unknown";
    pdsByOutcome.set(key, (pdsByOutcome.get(key) ?? 0) + 1);
  }

  const summary = {
    generatedAt: new Date().toISOString(),
    nsid: NSID,
    sinceHours: opts.sinceHours,
    observableEventModel: [
      "candidate.selected",
      "xrpc.workflow.start.accepted",
      "bpmn.actorQuality.task.started",
      "bpmn.actorQuality.task.completed",
      "repo.profile.self.written",
      "repo.seedPost.written",
      "appview.profile.visible",
    ],
    pds: {
      count: pdsRows.length,
      byOutcome: Object.fromEntries(pdsByOutcome),
      wallTimeMs: stats(pdsRows.map((row) => row.wall_time_ms)),
      firstSeen: pdsRows[0]?.event_ts ?? null,
      lastSeen: pdsRows[pdsRows.length - 1]?.event_ts ?? null,
    },
    instrumentation: Object.fromEntries(bpmnRows.map((row) => [row.source, Number(row.n)])),
    artifacts: {
      reconstructedCases: reconstructedCases.length,
      sourceHints: Array.from(bySourceHint.values()).sort((a, b) => String(b.lastIndexedAt).localeCompare(String(a.lastIndexedAt))),
      samples: reconstructedCases.slice(0, 20),
    },
  };

  if (opts.json) {
    console.log(JSON.stringify(summary, null, 2));
  } else {
    console.log(`# YORO actorQuality Process Mining Snapshot

- generatedAt: ${summary.generatedAt}
- nsid: ${summary.nsid}
- PDS accepted events: ${summary.pds.count}
- PDS outcomes: ${JSON.stringify(summary.pds.byOutcome)}
- PDS wall time ms: ${JSON.stringify(summary.pds.wallTimeMs)}
- BPMN/OCEL instrumentation: ${JSON.stringify(summary.instrumentation)}
- reconstructed artifact cases: ${summary.artifacts.reconstructedCases}

## Source Hints
${summary.artifacts.sourceHints.map((row) => `- ${row.sourceHint}: cases=${row.cases}, profile=${row.withProfile}, seedPost=${row.withSeedPost}, window=${row.firstIndexedAt}..${row.lastIndexedAt}`).join("\n")}

## Samples
${summary.artifacts.samples.map((row) => `- ${row.actorDid}: seed=${row.seedIndexedAt}, profile=${row.profileIndexedAt ?? "missing"}, source=${row.sourceHint || "unknown"}`).join("\n")}
`);
  }
} finally {
  await pool.end();
}
