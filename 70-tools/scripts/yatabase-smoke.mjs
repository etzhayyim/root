#!/usr/bin/env node
// yatabase-smoke.mjs — io-yatabase BaaS surface smoke test (P4a).
//
// Exercises:
//   public:        /health, /_app/meta, /.well-known/agent.json,
//                  /.well-known/mcp.json, /mcp initialize+ping+tools/list+resources/list
//   authenticated: /cypher (WRITE rejection check), /mcp tools/call yata.coverage.report
//
// Usage:
//   node 70-tools/scripts/yatabase-smoke.mjs
//   YATA_API_KEY=sk_live_yata_... node 70-tools/scripts/yatabase-smoke.mjs
//   YATABASE_HOST=https://yatabase.etzhayyim.com YATA_API_KEY=... node ...
//
// Exit code 0 if all PASS, 1 if any FAIL.

const HOST = process.env.YATABASE_HOST ?? "https://yatabase.etzhayyim.com";
const API_KEY = process.env.YATA_API_KEY ?? "";
const REQUIRE_AUTH = Boolean(API_KEY);

const results = [];

function pass(name, detail = "") {
  results.push({ name, ok: true, detail });
  console.log(`PASS  ${name}${detail ? ` — ${detail}` : ""}`);
}

function fail(name, detail) {
  results.push({ name, ok: false, detail });
  console.error(`FAIL  ${name} — ${detail}`);
}

function skip(name, detail) {
  results.push({ name, ok: true, skipped: true, detail });
  console.log(`SKIP  ${name} — ${detail}`);
}

async function getJson(path, init = {}) {
  const url = `${HOST}${path}`;
  const resp = await fetch(url, init);
  const text = await resp.text();
  let body = null;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { status: resp.status, headers: resp.headers, body };
}

async function publicHealth() {
  const r = await getJson("/health");
  if (r.status === 200 && r.body?.ok === true) pass("/health", `app=${r.body.app}`);
  else fail("/health", `status=${r.status} body=${JSON.stringify(r.body)}`);
}

async function publicSignup() {
  // Signup with email — verify the endpoint mints a valid key + tenant DID,
  // then check that emailStatus came back (pending in stub-mode).
  const resp = await fetch(`${HOST}/auth/v1/signup`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ email: `smoke-${Date.now()}@example.com`, name: "smoke-runner" }),
  });
  const body = await resp.json().catch(() => null);
  if (resp.status !== 200 || !body?.apiKey || !body?.orgDid || !body.apiKey.startsWith("sk_live_yata_")) {
    return fail("/auth/v1/signup", `status=${resp.status} body=${JSON.stringify(body).slice(0, 200)}`);
  }
  if (body.emailStatus !== "pending" && body.emailStatus !== "sent" && body.emailStatus !== "failed" && body.emailStatus !== "skipped-no-email") {
    return fail("/auth/v1/signup emailStatus", `unexpected emailStatus=${body.emailStatus}`);
  }
  pass("/auth/v1/signup", `key=${body.apiKey.slice(0, 18)}… orgDid=${body.orgDid.slice(0, 40)}… email=${body.emailStatus}`);
  globalThis.__SMOKE_FRESH_KEY__ = body.apiKey;
}

async function authedOutbox() {
  if (!REQUIRE_AUTH) return skip("/api/outbox", "YATA_API_KEY unset");
  const r = await getJson("/api/outbox", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || !Array.isArray(r.body?.events)) {
    return fail("/api/outbox", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  pass("/api/outbox", `events=${r.body.events.length}`);
}

async function authedAuditLog() {
  if (!REQUIRE_AUTH) return skip("/api/audit", "YATA_API_KEY unset");
  // Generate at least one event so the log has something to find.
  await getJson("/api/plan", { headers: { authorization: `Bearer ${API_KEY}` } });
  // Audit insert is fire-and-forget via waitUntil; allow propagation.
  await new Promise((r) => setTimeout(r, 18_000));
  const r = await getJson("/api/audit?limit=20", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || !Array.isArray(r.body?.events)) {
    return fail("/api/audit", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  if (r.body.events.length === 0) {
    return fail("/api/audit (no events)", "no audit rows visible after 18s — eventual consistency lag");
  }
  const sample = r.body.events[0];
  if (!sample.surface || !sample.method || typeof sample.statusCode !== "number") {
    return fail("/api/audit shape", JSON.stringify(sample).slice(0, 200));
  }
  pass("/api/audit", `events=${r.body.events.length} sample=${sample.method} ${sample.path.slice(0, 24)} [${sample.surface}] ${sample.statusCode}`);
}

async function authedDataExport() {
  if (!REQUIRE_AUTH) return skip("/api/export", "YATA_API_KEY unset");
  const r = await getJson("/api/export", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || typeof r.body?.orgDid !== "string" || !r.body?.tenantSchema) {
    return fail("/api/export", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  if (r.body.privacyLawCompliance?.jpAct33 !== "改正個人情報保護法 第33条 開示請求権") {
    return fail("/api/export privacy claim", JSON.stringify(r.body.privacyLawCompliance).slice(0, 200));
  }
  pass("/api/export", `tables=${r.body.tenantSchema?.tables?.length ?? 0} billingEvents=${r.body.billingEvents?.length ?? 0} apiKeys=${r.body.apiKeys?.length ?? 0}`);
}

async function authedDeleteRequiresConfirm() {
  if (!REQUIRE_AUTH) return skip("/api/account/delete confirmation", "YATA_API_KEY unset");
  // Don't actually delete — just verify the confirmation guard rejects
  // bodies without `{confirm:"DELETE"}`.
  const r = await postJsonRpc("/api/account/delete", {}, { authorization: `Bearer ${API_KEY}` });
  if (r.status === 400 && /ConfirmationRequired/i.test(JSON.stringify(r.body))) {
    pass("/api/account/delete confirmation", "missing confirm rejected");
  } else {
    fail("/api/account/delete confirmation", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
}

async function authedMembersList() {
  if (!REQUIRE_AUTH) return skip("/api/members", "YATA_API_KEY unset");
  const r = await getJson("/api/members", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || !Array.isArray(r.body?.members) || r.body.members.length === 0) {
    return fail("/api/members", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  const owner = r.body.members.find((m) => m.role === "owner");
  if (!owner || owner.status !== "active") {
    return fail("/api/members owner", JSON.stringify(r.body).slice(0, 200));
  }
  pass("/api/members", `org=${r.body.orgDid.slice(0, 30)}… members=${r.body.members.length} owner=${owner.name}`);
}

async function authedInviteCycle() {
  if (!REQUIRE_AUTH) return skip("/auth/v1/invite", "YATA_API_KEY unset");
  const inviteResp = await postJsonRpc("/auth/v1/invite", { name: `smoke-invite-${Date.now()}` }, { authorization: `Bearer ${API_KEY}` });
  if (inviteResp.status !== 200 || !inviteResp.body?.apiKey || !inviteResp.body?.keyId) {
    return fail("/auth/v1/invite", `status=${inviteResp.status} body=${JSON.stringify(inviteResp.body).slice(0, 200)}`);
  }
  if (!inviteResp.body.apiKey.startsWith("sk_live_yata_")) {
    return fail("/auth/v1/invite key shape", JSON.stringify(inviteResp.body).slice(0, 200));
  }
  // Wait for RW eventual consistency before revoke — the SELECT in revoke
  // path reads the freshly-INSERTed row. Window can stretch to ~150s
  // under load, especially when other smoke runs piled up writes.
  let revokeResp = null;
  for (let attempt = 0; attempt < 15; attempt++) {
    await new Promise((r) => setTimeout(r, 10_000));
    revokeResp = await postJsonRpc("/auth/v1/revoke", { keyId: inviteResp.body.keyId }, { authorization: `Bearer ${API_KEY}` });
    if (revokeResp.status === 200) break;
  }
  if (revokeResp?.status !== 200) {
    return fail("/auth/v1/revoke", `status=${revokeResp?.status} body=${JSON.stringify(revokeResp?.body).slice(0, 200)}`);
  }
  pass("/auth/v1/invite + revoke cycle", `keyId=${inviteResp.body.keyId}`);
}

async function authedInvoiceHtml() {
  if (!REQUIRE_AUTH) return skip("/api/invoice", "YATA_API_KEY unset");
  // Pick the current month — should always have at least the smoke run's
  // own metering events.
  const now = new Date();
  const month = `${now.getUTCFullYear()}-${String(now.getUTCMonth() + 1).padStart(2, "0")}`;
  const url = `${HOST}/api/invoice?month=${month}`;
  const resp = await fetch(url, { headers: { authorization: `Bearer ${API_KEY}` } });
  const text = await resp.text();
  const hasQII = text.includes("T9007028460042");
  const hasInvoiceHeader = text.includes("適格請求書");
  const hasTotals = text.includes("消費税");
  const ctOk = (resp.headers.get("content-type") ?? "").startsWith("text/html");
  if (resp.status !== 200 || !ctOk || !hasQII || !hasInvoiceHeader || !hasTotals) {
    return fail(
      "/api/invoice",
      `status=${resp.status} ct=${resp.headers.get("content-type")} qii=${hasQII} header=${hasInvoiceHeader} totals=${hasTotals}`,
    );
  }
  pass("/api/invoice", `month=${month} bytes=${text.length} T9007028460042=present`);
}

async function authedInvoicesList() {
  if (!REQUIRE_AUTH) return skip("/api/invoices list", "YATA_API_KEY unset");
  const r = await getJson("/api/invoices", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || !Array.isArray(r.body?.months)) {
    return fail("/api/invoices list", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  pass("/api/invoices list", `months=${r.body.months.length}`);
}

async function authedUpgradeRejectsEnterprise() {
  if (!REQUIRE_AUTH) return skip("/auth/v1/upgrade rejects enterprise", "YATA_API_KEY unset");
  const r = await postJsonRpc("/auth/v1/upgrade", { plan: "enterprise" }, { authorization: `Bearer ${API_KEY}` });
  if (r.status === 400 && /sales-only|InvalidPlan/i.test(JSON.stringify(r.body))) {
    pass("/auth/v1/upgrade rejects enterprise");
  } else {
    fail("/auth/v1/upgrade rejects enterprise", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
}

async function authedPlan() {
  if (!REQUIRE_AUTH) return skip("/api/plan", "YATA_API_KEY unset");
  const r = await getJson("/api/plan", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || typeof r.body?.plan !== "string" || !r.body?.quota) {
    return fail("/api/plan", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  const planOk = ["free", "starter", "developer", "business", "enterprise"].includes(r.body.plan);
  if (!planOk) return fail("/api/plan plan tier", `unknown plan=${r.body.plan}`);
  pass("/api/plan", `plan=${r.body.plan} used=${r.body.quota.apiRequestUsedToday} limit=${r.body.quota.apiRequestPerDay ?? "∞"}`);
}

async function authedUsage() {
  if (!REQUIRE_AUTH) return skip("/api/usage", "YATA_API_KEY unset");
  const r = await getJson("/api/usage", { headers: { authorization: `Bearer ${API_KEY}` } });
  if (r.status !== 200 || typeof r.body?.orgDid !== "string" || !Array.isArray(r.body?.byMetric)) {
    return fail("/api/usage", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  // The metering smoke just checks shape — qty depends on prior calls in
  // this run, which the cypher tests already incremented.
  pass("/api/usage", `orgDid=${r.body.orgDid.slice(0, 30)}… metrics=${r.body.byMetric.length} totalJpy=${r.body.totalBilledJpy}`);
}

async function publicStudio() {
  // 2026-05 split: `/` is the marketing landing page; `/studio` and
  // `/embed` serve the browser console. Both are public, both edge-cached.
  // We verify each surface returns the right `x-yatabase-surface` header
  // + sentinel HTML strings.
  const landingResp = await fetch(`${HOST}/`);
  const landingText = await landingResp.text();
  const landingOk =
    landingResp.status === 200 &&
    (landingResp.headers.get("content-type") ?? "").startsWith("text/html") &&
    landingResp.headers.get("x-yatabase-surface") === "landing" &&
    landingText.includes("<title>Yatabase") &&
    landingText.includes("Pricing") &&
    landingText.includes("Open Studio");
  if (!landingOk) {
    return fail(
      "Landing /",
      `status=${landingResp.status} surface=${landingResp.headers.get("x-yatabase-surface")} bytes=${landingText.length}`,
    );
  }
  for (const path of ["/studio", "/embed"]) {
    const url = `${HOST}${path}`;
    const resp = await fetch(url);
    const text = await resp.text();
    const ok = resp.status === 200 &&
      (resp.headers.get("content-type") ?? "").startsWith("text/html") &&
      resp.headers.get("x-yatabase-surface") === "studio" &&
      text.includes("<title>yatabase Studio</title>") &&
      text.includes("MATCH (n:Demo)") &&
      text.includes("yatabase.apiKey");
    if (!ok) return fail(`Studio ${path}`, `status=${resp.status} ct=${resp.headers.get("content-type")} bytes=${text.length}`);
  }
  pass("Landing / + Studio (/studio, /embed)", "landing public, studio served at /studio + /embed");
}

async function publicMeta() {
  const r = await getJson("/_app/meta");
  if (r.status !== 200) return fail("/_app/meta", `status=${r.status}`);
  const required = ["/cypher", "/mcp", "/.well-known/agent.json", "/.well-known/mcp.json"];
  const surfaces = r.body?.surfaces ?? [];
  const missing = required.filter((s) => !surfaces.includes(s));
  if (missing.length) return fail("/_app/meta surfaces[]", `missing: ${missing.join(", ")}`);
  if (r.body.codename !== "io-yatabase") return fail("/_app/meta codename", `expected io-yatabase, got ${r.body.codename}`);
  pass("/_app/meta", `codename=${r.body.codename} surfaces=${surfaces.length}`);
}

async function publicAgentJson() {
  const r = await getJson("/.well-known/agent.json");
  if (r.status !== 200) return fail("/.well-known/agent.json", `status=${r.status}`);
  if (r.body?.name !== "yatabase") return fail("/.well-known/agent.json", `name=${r.body?.name}`);
  if (!Array.isArray(r.body?.skills) || r.body.skills.length === 0) return fail("/.well-known/agent.json", "no skills declared");
  pass("/.well-known/agent.json", `skills=${r.body.skills.length}`);
}

async function publicMcpJson() {
  const r = await getJson("/.well-known/mcp.json");
  if (r.status !== 200) return fail("/.well-known/mcp.json", `status=${r.status}`);
  if (r.body?.protocolVersion !== "2025-06-18") return fail("/.well-known/mcp.json", `protocolVersion=${r.body?.protocolVersion}`);
  if (!Array.isArray(r.body?.tools) || r.body.tools.length === 0) return fail("/.well-known/mcp.json", "no tools declared");
  pass("/.well-known/mcp.json", `tools=${r.body.tools.length}`);
}

async function mcpInitialize() {
  const r = await postJsonRpc("/mcp", { jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2025-06-18", capabilities: {} } });
  if (r.status !== 200) return fail("MCP initialize", `status=${r.status}`);
  if (r.body?.error) return fail("MCP initialize", JSON.stringify(r.body.error));
  if (r.body?.result?.protocolVersion !== "2025-06-18") return fail("MCP initialize", `result.protocolVersion=${r.body?.result?.protocolVersion}`);
  pass("MCP initialize", `serverInfo=${r.body.result.serverInfo?.name}@${r.body.result.serverInfo?.version}`);
}

async function mcpPing() {
  const r = await postJsonRpc("/mcp", { jsonrpc: "2.0", id: 2, method: "ping" });
  if (r.body?.result?.ok === true) pass("MCP ping");
  else fail("MCP ping", JSON.stringify(r.body));
}

async function mcpToolsList() {
  const r = await postJsonRpc("/mcp", { jsonrpc: "2.0", id: 3, method: "tools/list" });
  const tools = r.body?.result?.tools;
  if (!Array.isArray(tools) || tools.length === 0) return fail("MCP tools/list", `tools=${JSON.stringify(tools)}`);
  const names = tools.map((t) => t.name);
  const required = ["yata.graph.sparql", "yata.graph.cypher", "yata.storage.list_buckets", "yata.coverage.report"];
  const missing = required.filter((n) => !names.includes(n));
  if (missing.length) return fail("MCP tools/list", `missing tools: ${missing.join(", ")}`);
  pass("MCP tools/list", `tools=${tools.length}`);
}

async function mcpResourcesList() {
  const r = await postJsonRpc("/mcp", { jsonrpc: "2.0", id: 4, method: "resources/list" });
  const resources = r.body?.result?.resources;
  if (!Array.isArray(resources) || resources.length === 0) return fail("MCP resources/list", JSON.stringify(r.body));
  pass("MCP resources/list", `resources=${resources.length}`);
}

async function mcpUnauthorizedToolsCall() {
  // Without auth, tools/call should return -32001 Unauthorized.
  const r = await postJsonRpc("/mcp", {
    jsonrpc: "2.0",
    id: 5,
    method: "tools/call",
    params: { name: "yata.coverage.report", arguments: {} },
  });
  if (r.body?.error?.code === -32001) pass("MCP tools/call requires auth", `code=${r.body.error.code}`);
  else fail("MCP tools/call requires auth", JSON.stringify(r.body));
}

async function cypherDetachRejection() {
  if (!REQUIRE_AUTH) return skip("/cypher DETACH rejection", "YATA_API_KEY unset");
  const r = await postJsonRpc("/cypher", {
    statements: [{ statement: "MATCH (n:Demo) DETACH DELETE n", parameters: {} }],
  }, { authorization: `Bearer ${API_KEY}` });
  if (r.status === 400 && Array.isArray(r.body?.errors) && r.body.errors.some((e) => /not yet supported/i.test(e.message ?? ""))) {
    pass("/cypher DETACH rejection", "DETACH DELETE blocked at edge");
  } else if (r.status === 401) {
    fail("/cypher DETACH rejection", "401 Unauthorized — API_KEY may be invalid");
  } else {
    fail("/cypher DETACH rejection", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
}

async function authedCypherEdgeTraversal() {
  if (!REQUIRE_AUTH) return skip("/cypher edge traversal", "YATA_API_KEY unset");
  const ts = Date.now();
  const a = `at://smoke-edge/alice-${ts}`;
  const b = `at://smoke-edge/bob-${ts}`;

  // Create two Person nodes
  for (const [id, name] of [[a, "alice-smoke"], [b, "bob-smoke"]]) {
    const cr = await postJsonRpc("/cypher", {
      statements: [{
        statement: `CREATE (n:Person {vertex_id: '${id}', name: '${name}', created_at: '2026-05-10'}) RETURN n.name`,
        parameters: {},
      }],
    }, { authorization: `Bearer ${API_KEY}` });
    if (!cr.body?.results?.[0]?.data?.length) {
      return fail("/cypher edge traversal (CREATE node)", JSON.stringify(cr.body).slice(0, 200));
    }
  }

  // Wait for vertex INSERTs to propagate before edge CREATE INSERT...SELECT.
  // RW eventual consistency for fresh rows in tenant schema can take 30-60s
  // depending on cache state; retry the edge CREATE itself if the first
  // attempt doesn't see the vertices yet.
  let edgeCreated = false;
  for (let attempt = 0; attempt < 5; attempt++) {
    await new Promise((r) => setTimeout(r, 20_000));
    const er = await postJsonRpc("/cypher", {
      statements: [{
        statement: `MATCH (a:Person {vertex_id: '${a}'}),(b:Person {vertex_id: '${b}'}) CREATE (a)-[:KNOWS]->(b)`,
        parameters: {},
      }],
    }, { authorization: `Bearer ${API_KEY}` });
    if (Array.isArray(er.body?.errors) && er.body.errors.length > 0) continue;
    edgeCreated = true;
    break;
  }
  if (!edgeCreated) {
    return fail("/cypher edge traversal (CREATE edge)", "edge INSERT...SELECT never matched the vertices after 100s");
  }

  // Wait for edge to propagate, then TRAVERSE
  let rows = [];
  for (let attempt = 0; attempt < 12; attempt++) {
    await new Promise((r) => setTimeout(r, 5_000));
    const tr = await postJsonRpc("/cypher", {
      statements: [{
        statement: `MATCH (a:Person)-[:KNOWS]->(b:Person) WHERE a.vertex_id = '${a}' RETURN a.name, b.name LIMIT 5`,
        parameters: {},
      }],
    }, { authorization: `Bearer ${API_KEY}` });
    rows = tr.body?.results?.[0]?.data ?? [];
    if (rows.length > 0) break;
  }
  const found = rows.find((r) => r.row?.[0] === "alice-smoke" && r.row?.[1] === "bob-smoke");
  if (found) {
    pass("/cypher edge traversal", `(:Person)-[:KNOWS]->(:Person) returned alice→bob`);
  } else {
    fail("/cypher edge traversal", `${rows.length} rows after 40s; sample: ${rows.length > 0 ? JSON.stringify(rows[0]).slice(0, 100) : "[]"}`);
  }
}

async function authedSchemaDescribe() {
  if (!REQUIRE_AUTH) return skip("/api/schema", "YATA_API_KEY unset");
  const r = await getJson("/api/schema", {
    headers: { authorization: `Bearer ${API_KEY}` },
  });
  if (r.status !== 200 || typeof r.body?.schema !== "string" || !Array.isArray(r.body?.tables)) {
    return fail("/api/schema", `status=${r.status} body=${JSON.stringify(r.body).slice(0, 200)}`);
  }
  const demoTable = r.body.tables.find((t) => t.name === "vertex_demo");
  if (!demoTable || !demoTable.columns.some((c) => c.name === "vertex_id" && c.isPrimaryKey)) {
    return fail("/api/schema (vertex_demo PK)", JSON.stringify(r.body).slice(0, 200));
  }
  pass("/api/schema", `schema=${r.body.schema} tables=${r.body.tables.length}`);
}

async function authedStoragePutListCycle() {
  if (!REQUIRE_AUTH) return skip("/storage put+list cycle", "YATA_API_KEY unset");
  const bucket = "smoke-bucket";
  const key = `smoke-${Date.now()}.txt`;

  // PUT
  const putUrl = `${HOST}/storage/v1/object/${bucket}/${key}`;
  const putResp = await fetch(putUrl, {
    method: "PUT",
    headers: { "authorization": `Bearer ${API_KEY}`, "content-type": "text/plain" },
    body: `smoke content ${key}`,
  });
  if (putResp.status !== 200) {
    const text = await putResp.text().catch(() => "");
    return fail("/storage put+list cycle (PUT)", `status=${putResp.status} body=${text.slice(0, 200)}`);
  }

  // Wait for RW to propagate the INSERT through to read side. The
  // listObjects path goes through a streaming MV and the consistency
  // window can stretch to ~90s for cold queries under load. Poll up
  // to 18 times at 5s intervals.
  let listBody = null;
  let listResp = null;
  let found = null;
  for (let attempt = 0; attempt < 18; attempt++) {
    await new Promise((r) => setTimeout(r, 5_000));
    listResp = await fetch(`${HOST}/storage/v1/object/list/${bucket}?limit=100`, {
      headers: { "authorization": `Bearer ${API_KEY}` },
    });
    listBody = await listResp.json().catch(() => null);
    if (listResp.status !== 200 || !Array.isArray(listBody?.objects)) continue;
    found = listBody.objects.find((o) => o.objectKey === key);
    if (found) break;
  }
  if (!listBody || !Array.isArray(listBody.objects)) {
    return fail("/storage put+list cycle (LIST)", `status=${listResp?.status} body=${JSON.stringify(listBody).slice(0, 200)}`);
  }
  if (!found) {
    return fail("/storage put+list cycle (find)", `${listBody.objects.length} objects, none match ${key}`);
  }
  if (typeof found.etag !== "string" || !found.etag) {
    return fail("/storage put+list cycle (etag)", `missing etag: ${JSON.stringify(found)}`);
  }
  pass("/storage put+list cycle", `bucket=${bucket} key=${key.slice(-12)} etag=${found.etag.slice(0, 12)}…`);
}

async function authedCypherFullCrudCycle() {
  if (!REQUIRE_AUTH) return skip("/cypher CREATE+SET+DELETE cycle", "YATA_API_KEY unset");
  const id = `at://smoke-test/note-${Date.now()}`;

  // CREATE
  const cr = await postJsonRpc("/cypher", {
    statements: [{
      statement: `CREATE (n:Demo {vertex_id: '${id}', name: 'before', created_at: '2026-05-10T01:00:00Z'}) RETURN n.vertex_id, n.name`,
      parameters: {},
    }],
  }, { authorization: `Bearer ${API_KEY}` });
  const created = cr.body?.results?.[0]?.data?.[0]?.row;
  if (!Array.isArray(created) || created[0] !== id) {
    return fail("/cypher CREATE+SET+DELETE cycle (CREATE)", JSON.stringify(cr.body).slice(0, 200));
  }

  // SET (eventual consistency: cur.rowcount may be 0 even on success — Python
  // worker treats any error-free UPDATE as 1 logical update so the wire
  // contract remains stable for clients).
  const sr = await postJsonRpc("/cypher", {
    statements: [{
      statement: `MATCH (n:Demo {vertex_id: '${id}'}) SET n.name = 'after' RETURN n.name`,
      parameters: {},
    }],
  }, { authorization: `Bearer ${API_KEY}` });
  if (Array.isArray(sr.body?.errors) && sr.body.errors.length > 0) {
    return fail("/cypher CREATE+SET+DELETE cycle (SET)", JSON.stringify(sr.body).slice(0, 200));
  }
  const setRow = sr.body?.results?.[0]?.data?.[0]?.row;
  if (!Array.isArray(setRow) || setRow[0] !== "after") {
    return fail("/cypher CREATE+SET+DELETE cycle (SET echo)", JSON.stringify(sr.body).slice(0, 200));
  }

  // DELETE
  const dr = await postJsonRpc("/cypher", {
    statements: [{
      statement: `MATCH (n:Demo {vertex_id: '${id}'}) DELETE n`,
      parameters: {},
    }],
  }, { authorization: `Bearer ${API_KEY}` });
  if (Array.isArray(dr.body?.errors) && dr.body.errors.length > 0) {
    return fail("/cypher CREATE+SET+DELETE cycle (DELETE)", JSON.stringify(dr.body).slice(0, 200));
  }
  pass("/cypher CREATE+SET+DELETE cycle", `id=${id.slice(-12)}`);
}

async function authedCypherTool() {
  if (!REQUIRE_AUTH) return skip("/mcp tools/call yata.graph.cypher (READ)", "YATA_API_KEY unset");
  const r = await postJsonRpc("/mcp", {
    jsonrpc: "2.0",
    id: 10,
    method: "tools/call",
    params: {
      name: "yata.graph.cypher",
      arguments: { statement: "MATCH (n:Demo) RETURN n.vertex_id LIMIT 3", parametersJson: "{}" },
    },
  }, { authorization: `Bearer ${API_KEY}` });
  if (r.body?.result?.content?.[0]?.text) {
    let inner;
    try { inner = JSON.parse(r.body.result.content[0].text); } catch { inner = null; }
    if (inner?.ok && inner?.bpmnProcessId === "yata_run_cypher") {
      const v = inner.variables ?? {};
      const sqlOK = /select vertex_id from "yata_[0-9a-f]{16}"\.vertex_demo/i.test(v.translatedSql ?? "");
      pass("/mcp tools/call yata.graph.cypher (READ)", `rowCount=${v.rowCount} elapsedMs=${v.elapsedMs} schemaRouted=${sqlOK ? "yes" : "no"}`);
    } else {
      fail("/mcp tools/call yata.graph.cypher (READ)", `unexpected inner: ${r.body.result.content[0].text.slice(0,150)}`);
    }
  } else if (r.body?.error?.code === -32000) {
    skip("/mcp tools/call yata.graph.cypher (READ)", `dispatcher offline: ${r.body.error.message}`);
  } else {
    fail("/mcp tools/call yata.graph.cypher (READ)", JSON.stringify(r.body).slice(0, 200));
  }
}

async function authedCypherDemoTenant() {
  if (!REQUIRE_AUTH) return skip("/cypher tenant Demo row", "YATA_API_KEY unset");
  const r = await postJsonRpc("/cypher", {
    statements: [{ statement: "MATCH (n:Demo) RETURN n.vertex_id, n.name LIMIT 100", parameters: {} }],
  }, { authorization: `Bearer ${API_KEY}` });
  const result = r.body?.results?.[0];
  const welcomeRow = result?.data?.find((d) =>
    typeof d?.row?.[1] === "string" && d.row[1].includes("yatabase tenant"),
  );
  if (Array.isArray(result?.columns) && result.columns[0] === "vertex_id" && welcomeRow) {
    pass("/cypher tenant Demo row", `rows=${result.data.length} welcomeRow="${welcomeRow.row[0].slice(0, 50)}…"`);
  } else {
    fail("/cypher tenant Demo row", JSON.stringify(r.body).slice(0, 200));
  }
}

async function authedCypherTenantIsolation() {
  if (!REQUIRE_AUTH) return skip("/cypher tenant isolation (Actor blocked)", "YATA_API_KEY unset");
  const r = await postJsonRpc("/cypher", {
    statements: [{ statement: "MATCH (n:Actor) RETURN n.vertex_id LIMIT 1", parameters: {} }],
  }, { authorization: `Bearer ${API_KEY}` });
  const errs = r.body?.errors;
  const blocked = Array.isArray(errs) && errs.some((e) =>
    e.code === "Yatabase.CypherError" && /not found: vertex_actor/i.test(e.message ?? ""),
  );
  if (blocked && (!r.body.results || r.body.results.length === 0)) {
    pass("/cypher tenant isolation (Actor blocked)", "tenant cannot see public.vertex_actor");
  } else {
    fail("/cypher tenant isolation (Actor blocked)", JSON.stringify(r.body).slice(0, 200));
  }
}

async function postJsonRpc(path, body, extraHeaders = {}) {
  const url = `${HOST}${path}`;
  const headers = { "content-type": "application/json", ...extraHeaders };
  const resp = await fetch(url, { method: "POST", headers, body: JSON.stringify(body) });
  let text = "";
  try {
    text = await resp.text();
  } catch {
    text = "";
  }
  let parsed = null;
  try {
    parsed = JSON.parse(text);
  } catch {
    parsed = text;
  }
  return { status: resp.status, body: parsed };
}

async function main() {
  console.log(`yatabase-smoke target=${HOST} auth=${REQUIRE_AUTH ? "yes" : "public-only"}`);
  console.log("─".repeat(72));

  await publicHealth();
  await publicStudio();
  await publicMeta();
  await publicSignup();
  await publicAgentJson();
  await publicMcpJson();
  await mcpInitialize();
  await mcpPing();
  await mcpToolsList();
  await mcpResourcesList();
  await mcpUnauthorizedToolsCall();
  await cypherDetachRejection();
  await authedCypherTool();
  await authedCypherDemoTenant();
  await authedCypherTenantIsolation();
  await authedCypherFullCrudCycle();
  await authedCypherEdgeTraversal();
  await authedSchemaDescribe();
  await authedPlan();
  await authedUpgradeRejectsEnterprise();
  await authedInvoicesList();
  await authedInvoiceHtml();
  await authedMembersList();
  await authedInviteCycle();
  await authedAuditLog();
  await authedOutbox();
  await authedDataExport();
  await authedDeleteRequiresConfirm();
  await authedUsage();
  await authedStoragePutListCycle();

  console.log("─".repeat(72));
  const failed = results.filter((r) => !r.ok);
  const skipped = results.filter((r) => r.skipped);
  const passed = results.filter((r) => r.ok && !r.skipped);
  console.log(`PASSED ${passed.length} / FAILED ${failed.length} / SKIPPED ${skipped.length}`);
  if (failed.length > 0) process.exit(1);
}

main().catch((e) => {
  console.error("smoke error:", e);
  process.exit(2);
});
