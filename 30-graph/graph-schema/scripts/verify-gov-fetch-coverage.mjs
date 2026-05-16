import pg from "pg";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error("DATABASE_URL is required");
  process.exit(2);
}

const timeoutMs = Number(process.env.GOV_FETCH_COVERAGE_TIMEOUT_MS || 15000);
const domains = (process.env.GOV_FETCH_COVERAGE_DOMAINS || "")
  .split(",")
  .map((value) => value.trim())
  .filter(Boolean);

const client = new pg.Client({
  connectionString,
  connectionTimeoutMillis: timeoutMs,
  query_timeout: timeoutMs,
  statement_timeout: timeoutMs,
});

function pct(numerator, denominator) {
  if (!denominator) return 0;
  return Math.round((Number(numerator) * 10000) / Number(denominator)) / 100;
}

function rowMetrics(row) {
  const withWebsite = Number(row.with_website || 0);
  const fetchChecked = Number(row.fetch_checked || 0);
  const reachable = Number(row.reachable || 0);
  const hashable = Number(row.hashable || 0);
  const hashed = Number(row.hashed || 0);
  return {
    domainCode: row.domain_code,
    total: Number(row.total || 0),
    withWebsite,
    fetchChecked,
    reachable,
    hashable,
    hashed,
    unreachable: Number(row.unreachable || 0),
    unchecked: Math.max(0, withWebsite - fetchChecked),
    hashCoveragePct: pct(hashed, withWebsite),
    reachabilityCoveragePct: pct(reachable, fetchChecked),
    hashableSiteCoveragePct: pct(hashed, hashable),
  };
}

async function fetchSummary() {
  const params = [];
  let domainFilter = "";
  if (domains.length > 0) {
    params.push(domains);
    domainFilter = "where domain_code = any($1)";
  }

  const result = await client.query(
    `
      select
        domain_code,
        total,
        with_website,
        fetch_checked,
        reachable,
        hashable,
        hashed,
        unreachable
      from view_gov_fetch_coverage
      ${domainFilter}
      order by unreachable desc, domain_code
    `,
    params,
  );
  return result.rows.map(rowMetrics);
}

async function fetchStatusBreakdown() {
  const params = [];
  let domainFilter = "";
  if (domains.length > 0) {
    params.push(domains);
    domainFilter = "and domain_code = any($1)";
  }

  const result = await client.query(
    `
      select
        coalesce(nullif(last_fetch_status, ''), 'unchecked') as status,
        count(*)::int as count
      from vertex_gov_org
      where coalesce(website, '') <> ''
      ${domainFilter}
      group by status
      order by count desc, status
    `,
    params,
  );
  return result.rows.map((row) => ({
    status: row.status,
    count: Number(row.count || 0),
  }));
}

async function fetchExamples() {
  const params = [];
  let domainFilter = "";
  if (domains.length > 0) {
    params.push(domains);
    domainFilter = "and domain_code = any($1)";
  }

  const result = await client.query(
    `
      select
        domain_code,
        owner_did,
        name_en,
        website,
        last_fetch_status,
        left(coalesce(last_fetch_error, ''), 240) as last_fetch_error,
        last_fetch_checked_at
      from vertex_gov_org
      where coalesce(website, '') <> ''
        and coalesce(last_fetch_checked_at, '') <> ''
        and coalesce(last_content_hash, '') = ''
        and coalesce(last_fetch_status, '') not in ('direct_ok', 'proxy_ok', 'wet_chunk')
      ${domainFilter}
      order by last_fetch_checked_at desc, domain_code, name_en
      limit 25
    `,
    params,
  );
  return result.rows;
}

try {
  await client.connect();
  const byDomain = await fetchSummary();
  const totals = byDomain.reduce(
    (acc, row) => {
      acc.total += row.total;
      acc.withWebsite += row.withWebsite;
      acc.fetchChecked += row.fetchChecked;
      acc.reachable += row.reachable;
      acc.hashable += row.hashable;
      acc.hashed += row.hashed;
      acc.unreachable += row.unreachable;
      acc.unchecked += row.unchecked;
      return acc;
    },
    { total: 0, withWebsite: 0, fetchChecked: 0, reachable: 0, hashable: 0, hashed: 0, unreachable: 0, unchecked: 0 },
  );

  const output = {
    ok: true,
    domains: domains.length > 0 ? domains : null,
    totals: {
      ...totals,
      hashCoveragePct: pct(totals.hashed, totals.withWebsite),
      reachabilityCoveragePct: pct(totals.reachable, totals.fetchChecked),
      hashableSiteCoveragePct: pct(totals.hashed, totals.hashable),
    },
    byDomain,
    statusBreakdown: await fetchStatusBreakdown(),
    examples: await fetchExamples(),
  };
  console.log(JSON.stringify(output, null, 2));
} finally {
  await client.end().catch(() => {});
}
