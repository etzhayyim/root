import pg from "pg";

const connectionString = process.env.DATABASE_URL;
if (!connectionString) {
  console.error("DATABASE_URL is required");
  process.exit(2);
}

const timeoutMs = Number(process.env.GOV_ZAF_VERIFY_TIMEOUT_MS || 15000);
const owner = "did:web:zaf-state.etzhayyim.com";
const rkeys = [
  "zaf-national-departments-9cfc7bff4a-10304550",
  "zaf-provinces-2aa86b5df1-10305612",
  "zaf-provincial-government-6eeae56a66-10306648",
];

const collections = {
  page: {
    table: "vertex_page",
    nsid: "ai.gftd.apps.site.page",
    columns: "rkey, url, domain, title, status_code, content_type",
  },
  wet: {
    table: "vertex_wet_chunk",
    nsid: "ai.gftd.apps.site.wetChunk",
    columns: "page_rkey, url, domain, title, chunk_index, total_chunks",
    keyColumn: "page_rkey",
  },
  wat: {
    table: "vertex_wat",
    nsid: "ai.gftd.apps.site.wat",
    columns: "rkey",
  },
  screenshot: {
    table: "vertex_screenshot",
    nsid: "ai.gftd.apps.site.screenshot",
    columns: 'rkey, blob_ref, "format", file_size',
  },
};

const client = new pg.Client({
  connectionString,
  connectionTimeoutMillis: timeoutMs,
  query_timeout: timeoutMs,
  statement_timeout: timeoutMs,
});

function vertexId(nsid, rkey) {
  return `at://${owner}/${nsid}/${rkey}`;
}

async function verifyCollection(name, spec) {
  const rows = [];
  const errors = [];

  for (const rkey of rkeys) {
    const id = vertexId(spec.nsid, rkey);
    try {
      const keyColumn = spec.keyColumn || "vertex_id";
      const keyValue = keyColumn === "vertex_id" ? id : rkey;
      const result = await client.query(
        `select ${spec.columns} from ${spec.table} where ${keyColumn}=$1 limit 1`,
        [keyValue],
      );
      rows.push({ rkey, ok: result.rowCount === 1, row: result.rows[0] ?? null });
    } catch (error) {
      errors.push({ rkey, error: String(error.message || error) });
    }
  }

  return {
    ok: rows.length === rkeys.length && rows.every((row) => row.ok) && errors.length === 0,
    expected: rkeys.length,
    found: rows.filter((row) => row.ok).length,
    rows,
    errors,
  };
}

async function verifyOrgSeeds() {
  try {
    const result = await client.query(
      `
        select org_tier, count(*)::int as count
        from vertex_gov_org
        where owner_did=$1
        group by org_tier
        order by org_tier
      `,
      [owner],
    );
    const counts = Object.fromEntries(result.rows.map((row) => [row.org_tier, row.count]));
    const ok = counts.agency === 11 && counts.ministry === 33 && counts.state === 9;
    return { ok, expected: { agency: 11, ministry: 33, state: 9 }, counts };
  } catch (error) {
    return { ok: false, error: String(error.message || error) };
  }
}

async function verifyGovSources() {
  const rows = [];
  const errors = [];

  for (const rkey of rkeys) {
    const id = vertexId("ai.gftd.gov.source", rkey);
    try {
      const result = await client.query(
        `
          select rkey, "sourceUrl", "sourceType", "coverageStage", props
          from vertex_gov_source
          where vertex_id=$1
          limit 1
        `,
        [id],
      );
      rows.push({ rkey, ok: result.rowCount === 1, row: result.rows[0] ?? null });
    } catch (error) {
      errors.push({ rkey, error: String(error.message || error) });
    }
  }

  return {
    ok: rows.length === rkeys.length && rows.every((row) => row.ok) && errors.length === 0,
    expected: rkeys.length,
    found: rows.filter((row) => row.ok).length,
    rows,
    errors,
  };
}

try {
  await client.connect();
  const checks = {};
  for (const [name, spec] of Object.entries(collections)) {
    checks[name] = await verifyCollection(name, spec);
  }
  checks.govSources = await verifyGovSources();
  checks.orgSeeds = await verifyOrgSeeds();

  const ok = Object.values(checks).every((check) => check.ok);
  console.log(JSON.stringify({ ok, deleteAllowed: ok, owner, rkeys, checks }, null, 2));
  process.exitCode = ok ? 0 : 1;
} finally {
  await client.end().catch(() => {});
}
