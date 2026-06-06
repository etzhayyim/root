#!/usr/bin/env node
/**
 * YORO actor quality backfill driver.
 *
 * Finds low-quality YORO actor profiles and starts
 * com.etzhayyim.apps.yoro.actorQualityEnrich through the public PDS XRPC route.
 *
 * Defaults are intentionally conservative:
 *   node 70-tools/scripts/yoro/actor-quality-backfill.mjs
 *
 * Live run:
 *   DATABASE_URL='postgres://root@host:4566/dev?sslmode=disable' \
 *     node 70-tools/scripts/yoro/actor-quality-backfill.mjs --live --limit=10 --sleep-ms=1000
 */

const NSID = "com.etzhayyim.apps.yoro.actorQualityEnrich";
const DEFAULT_PDS_URL = "https://atproto.etzhayyim.com";
const DEFAULT_SOURCE_HINT = `yoro actor quality backfill ${new Date().toISOString().slice(0, 10)}`;

function parseArgs(argv) {
  const out = {
    limit: 10,
    sleepMs: 1000,
    concurrency: 1,
    live: false,
    includePostless: false,
    allowUnsharded: false,
    actorDid: "",
    handle: "",
    hashPrefix: "",
    sourceHint: DEFAULT_SOURCE_HINT,
    pdsUrl: process.env.PDS_URL ?? DEFAULT_PDS_URL,
  };

  for (const arg of argv) {
    if (arg === "--live") out.live = true;
    else if (arg === "--dry-run") out.live = false;
    else if (arg === "--include-postless") out.includePostless = true;
    else if (arg === "--allow-unsharded") out.allowUnsharded = true;
    else if (arg.startsWith("--actor-did=")) out.actorDid = arg.slice("--actor-did=".length).trim();
    else if (arg.startsWith("--handle=")) out.handle = arg.slice("--handle=".length).trim();
    else if (arg.startsWith("--limit=")) out.limit = parsePositiveInt(arg, "--limit=");
    else if (arg.startsWith("--sleep-ms=")) out.sleepMs = parseNonNegativeInt(arg, "--sleep-ms=");
    else if (arg.startsWith("--concurrency=")) out.concurrency = parsePositiveInt(arg, "--concurrency=");
    else if (arg.startsWith("--hash-prefix=")) out.hashPrefix = arg.slice("--hash-prefix=".length).trim().toLowerCase();
    else if (arg.startsWith("--source-hint=")) out.sourceHint = arg.slice("--source-hint=".length).trim();
    else if (arg.startsWith("--pds-url=")) out.pdsUrl = arg.slice("--pds-url=".length).replace(/\/+$/, "");
    else if (arg === "--help" || arg === "-h") usage(0);
    else throw new Error(`Unknown argument: ${arg}`);
  }

  if (!/^[0-9a-f]*$/.test(out.hashPrefix)) {
    throw new Error("--hash-prefix must be lowercase hex, for example --hash-prefix=0a");
  }
  if (out.hashPrefix.length > 8) {
    throw new Error("--hash-prefix is capped at 8 hex chars");
  }
  if (out.limit > 100 && !out.hashPrefix && !out.allowUnsharded) {
    throw new Error("Refusing unsharded run with --limit > 100. Add --hash-prefix=HEX or --allow-unsharded.");
  }
  if (out.concurrency > 4 && !out.allowUnsharded) {
    throw new Error("Refusing --concurrency > 4 without --allow-unsharded.");
  }
  if (!out.sourceHint) {
    throw new Error("--source-hint cannot be empty");
  }
  if (!out.pdsUrl) {
    throw new Error("--pds-url cannot be empty");
  }
  if (out.handle && !out.actorDid) {
    throw new Error("--handle requires --actor-did");
  }

  return out;
}

function parsePositiveInt(arg, prefix) {
  const value = Number.parseInt(arg.slice(prefix.length), 10);
  if (!Number.isSafeInteger(value) || value <= 0) throw new Error(`${prefix.slice(0, -1)} must be a positive integer`);
  return value;
}

function parseNonNegativeInt(arg, prefix) {
  const value = Number.parseInt(arg.slice(prefix.length), 10);
  if (!Number.isSafeInteger(value) || value < 0) throw new Error(`${prefix.slice(0, -1)} must be a non-negative integer`);
  return value;
}

function usage(code) {
  console.log(`Usage:
  node 70-tools/scripts/yoro/actor-quality-backfill.mjs [options]

Options:
  --live                    Start real enrichment. Default sends dryRun=true.
  --limit=N                 Candidate count. Default: 10.
  --sleep-ms=N              Delay after each XRPC call per worker. Default: 1000.
  --concurrency=N           Parallel XRPC workers. Default: 1. Capped unless --allow-unsharded.
  --actor-did=DID           Run one exact actor instead of querying candidates.
  --handle=HANDLE           Optional handle for --actor-did. Defaults to actor DID.
  --hash-prefix=HEX         Shard by md5(actor id) prefix.
  --include-postless        Also target profiles without app.bsky.feed.post records.
  --source-hint=TEXT        Provenance text passed to the BPMN workflow.
  --pds-url=URL             PDS base URL. Default: ${DEFAULT_PDS_URL}.
  --allow-unsharded         Permit larger/unsharded runs after operator review.
`);
  process.exit(code);
}

const opts = parseArgs(process.argv.slice(2));
const databaseUrl = process.env.DATABASE_URL ?? process.env.KOTOBA_URL ?? process.env.KOTOBA_URL;
if (!databaseUrl) {
  throw new Error("Set DATABASE_URL, KOTOBA_URL, or KOTOBA_URL for RisingWave.");
}

const { default: pg } = await import(
  "/Users/junkawasaki/github/etzhayyim-root/30-graph/graph-schema/node_modules/pg/lib/index.js"
);

const pool = new pg.Pool({
  connectionString: databaseUrl,
  max: Math.min(Math.max(opts.concurrency, 1), 4),
  statement_timeout: 120_000,
});

function buildCandidateQuery() {
  const params = [];
  const where = [
    "COALESCE(NULLIF(did, ''), NULLIF(repo, ''), NULLIF(actor_did, '')) IS NOT NULL",
    "(NULLIF(display_name, '') IS NULL OR NULLIF(description, '') IS NULL)",
  ];

  if (opts.hashPrefix) {
    params.push(opts.hashPrefix);
    where.push(
      `substr(md5(COALESCE(NULLIF(handle, ''), NULLIF(did, ''), NULLIF(repo, ''), NULLIF(actor_did, ''))), 1, ${opts.hashPrefix.length}) = $${params.length}`
    );
  }

  if (opts.includePostless) {
    where[1] = `(${where[1]} OR NOT EXISTS (
      SELECT 1
      FROM vertex_repo_record r
      WHERE r.repo = COALESCE(NULLIF(vertex_profile.did, ''), NULLIF(vertex_profile.repo, ''), NULLIF(vertex_profile.actor_did, ''))
        AND r.collection = 'app.bsky.feed.post'
      LIMIT 1
    ))`;
  }

  const sql = `
    SELECT
      COALESCE(NULLIF(did, ''), NULLIF(repo, ''), NULLIF(actor_did, '')) AS actor_did,
      COALESCE(NULLIF(handle, ''), NULLIF(did, ''), NULLIF(repo, ''), NULLIF(actor_did, '')) AS handle,
      display_name,
      description,
      created_at
    FROM vertex_profile
    WHERE ${where.join("\n      AND ")}
    ORDER BY COALESCE(created_at, '') DESC
    LIMIT ${opts.limit}
  `;
  return { sql, params };
}

async function fetchCandidates() {
  if (opts.actorDid) {
    return [{
      actorDid: opts.actorDid,
      handle: opts.handle || opts.actorDid,
      hasDisplayName: null,
      hasDescription: null,
      createdAt: null,
    }];
  }

  const { sql, params } = buildCandidateQuery();
  const result = await pool.query(sql, params);
  const seen = new Set();
  return result.rows
    .map((row) => ({
      actorDid: row.actor_did,
      handle: row.handle || row.actor_did,
      hasDisplayName: Boolean(row.display_name),
      hasDescription: Boolean(row.description),
      createdAt: row.created_at,
    }))
    .filter((row) => {
      if (!row.actorDid || seen.has(row.actorDid)) return false;
      seen.add(row.actorDid);
      return true;
    });
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function startWorkflow(candidate) {
  const body = {
    actorDid: candidate.actorDid,
    handle: candidate.handle,
    sourceHint: opts.sourceHint,
    dryRun: !opts.live,
  };
  const startedAt = Date.now();
  const response = await fetch(`${opts.pdsUrl}/xrpc/${NSID}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  const text = await response.text();
  let parsed = null;
  try {
    parsed = text ? JSON.parse(text) : null;
  } catch {
    parsed = { raw: text.slice(0, 500) };
  }
  return {
    actorDid: candidate.actorDid,
    handle: candidate.handle,
    dryRun: !opts.live,
    status: response.status,
    ok: response.ok,
    elapsedMs: Date.now() - startedAt,
    instanceKey: parsed?.instanceKey,
    asyncStarted: parsed?.asyncStarted,
    error: response.ok ? undefined : parsed,
  };
}

async function runPool(candidates) {
  let index = 0;
  let failures = 0;

  async function worker(workerId) {
    while (index < candidates.length) {
      const candidate = candidates[index++];
      try {
        const result = await startWorkflow(candidate);
        if (!result.ok) failures += 1;
        console.log(JSON.stringify({ event: "workflow", workerId, ...result }));
      } catch (error) {
        failures += 1;
        console.log(JSON.stringify({
          event: "workflow",
          workerId,
          actorDid: candidate.actorDid,
          handle: candidate.handle,
          dryRun: !opts.live,
          ok: false,
          error: error instanceof Error ? error.message : String(error),
        }));
      }
      if (opts.sleepMs > 0) await sleep(opts.sleepMs);
    }
  }

  await Promise.all(Array.from({ length: opts.concurrency }, (_, i) => worker(i + 1)));
  return failures;
}

try {
  console.log(JSON.stringify({
    event: "start",
    nsid: NSID,
    live: opts.live,
    dryRun: !opts.live,
    limit: opts.limit,
    sleepMs: opts.sleepMs,
    concurrency: opts.concurrency,
    hashPrefix: opts.hashPrefix || null,
    includePostless: opts.includePostless,
    pdsUrl: opts.pdsUrl,
  }));

  const candidates = await fetchCandidates();
  console.log(JSON.stringify({ event: "candidates", count: candidates.length }));
  for (const candidate of candidates) {
    console.log(JSON.stringify({ event: "candidate", ...candidate }));
  }

  const failures = await runPool(candidates);
  console.log(JSON.stringify({ event: "done", count: candidates.length, failures }));
  process.exitCode = failures === 0 ? 0 : 1;
} finally {
  await pool.end();
}
