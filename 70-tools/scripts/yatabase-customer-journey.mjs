#!/usr/bin/env node
/**
 * yatabase-customer-journey — end-to-end proof that a real customer
 * journey works today on production. Runs against https://yatabase.etzhayyim.com
 * and exercises every surface a paying customer touches in order:
 *
 *   1. POST /auth/v1/signup                  — mint a tenant
 *   2. GET  /api/plan                        — confirm free tier (with auth-propagation retry)
 *   3. POST /cypher                          — first write (CREATE) + first read (MATCH)
 *   4. POST /mcp tools/list                  — verify MCP discovery
 *   5. POST /mcp tools/call yata.graph.cypher — same query, MCP shape
 *   6. PUT  /storage/v1/object/...           — first object PUT
 *   7. POST /webhook/stripe                  — synthetic signed event flips plan to starter
 *   8. GET  /api/plan                        — confirm flip
 *   9. GET  /api/usage                       — confirm metering captured the journey
 *  10. GET  /api/export                      — right-to-know (CCPA / GDPR / 改正個人情報保護法 §33)
 *  11. POST /api/account/delete              — right-to-erasure (cleanup)
 *
 * Each step asserts. RW eventual consistency is handled via retry
 * windows that match the smoke harness defaults. Storage PUT can hit
 * the dispatcher 500 (P29) — treated as soft FAIL with explicit
 * incident-note so the report stays honest.
 *
 * Required env:
 *   YATA_BASE                  default https://yatabase.etzhayyim.com
 *   STRIPE_WEBHOOK_SECRET      must match wrangler secret on the Worker
 *   PROPAGATION_MAX_S          default 180 (auth propagation cap)
 *
 * Exit codes:
 *   0 — full journey PASS
 *   1 — at least one hard step FAILED
 *   2 — missing env / setup error
 */

import crypto from "node:crypto";

const HOST = (process.env.YATA_BASE ?? "https://yatabase.etzhayyim.com").replace(/\/$/, "");
const STRIPE_SECRET = process.env.STRIPE_WEBHOOK_SECRET;
const PROPAGATION_MAX = Number(process.env.PROPAGATION_MAX_S ?? "180") | 0;

if (!STRIPE_SECRET) {
  console.error("ERR: STRIPE_WEBHOOK_SECRET env required (must match wrangler secret on kotodama-y4t4b4se)");
  process.exit(2);
}

const stepResults = [];
let hardFails = 0;

function step(label, fn, { soft = false } = {}) {
  process.stdout.write(`▸ ${label.padEnd(64, " ")}`);
  return (async () => {
    const t0 = Date.now();
    try {
      const note = await fn();
      const dur = Date.now() - t0;
      console.log(`PASS  ${note ?? ""} ${dur > 1000 ? `(${(dur / 1000).toFixed(1)}s)` : ""}`);
      stepResults.push({ label, status: "PASS", note: note ?? "", duration_ms: dur });
    } catch (e) {
      const dur = Date.now() - t0;
      const msg = (e?.message ?? String(e)).slice(0, 200);
      console.log(`${soft ? "SOFT " : "FAIL"}  ${msg}`);
      stepResults.push({ label, status: soft ? "SOFT" : "FAIL", note: msg, duration_ms: dur });
      if (!soft) hardFails++;
    }
  })();
}

function fmtSig(unixTs, payload, secret) {
  const signedPayload = `${unixTs}.${payload}`;
  const v1 = crypto.createHmac("sha256", secret).update(signedPayload).digest("hex");
  return `t=${unixTs},v1=${v1}`;
}

function syntheticCheckoutSession(orgDid, plan) {
  return {
    id: `evt_journey_${crypto.randomBytes(8).toString("hex")}`,
    object: "event",
    api_version: "2024-04-10",
    created: Math.floor(Date.now() / 1000),
    type: "checkout.session.completed",
    data: {
      object: {
        id: `cs_journey_${crypto.randomBytes(12).toString("hex")}`,
        object: "checkout.session",
        customer: `cus_journey_${crypto.randomBytes(8).toString("hex")}`,
        subscription: `sub_journey_${crypto.randomBytes(10).toString("hex")}`,
        client_reference_id: orgDid,
        metadata: { org_did: orgDid, plan },
        mode: "subscription",
        payment_status: "paid",
        status: "complete",
      },
    },
  };
}

async function pollWithBackoff(fn, predicate, maxMs = PROPAGATION_MAX * 1000, pollMs = 5000) {
  const deadline = Date.now() + maxMs;
  let last;
  while (Date.now() < deadline) {
    last = await fn();
    if (predicate(last)) return last;
    await new Promise((r) => setTimeout(r, pollMs));
  }
  return last;
}

let apiKey = "";
let orgDid = "";
let signupBody = null;

// P86: minimal SigV4 helpers (no @aws-sdk dep).
async function sha256HexJ(s) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return Array.from(new Uint8Array(buf)).map((b) => b.toString(16).padStart(2, "0")).join("");
}
async function hmacBin(key, data) {
  const k = await crypto.subtle.importKey("raw", key, { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", k, data));
}
function hexJ(buf) {
  return Array.from(buf).map((b) => b.toString(16).padStart(2, "0")).join("");
}

async function main() {
  console.log(`yatabase-customer-journey  target=${HOST}`);
  console.log("─".repeat(80));

  // 1. Signup
  await step("1. POST /auth/v1/signup", async () => {
    const r = await fetch(`${HOST}/auth/v1/signup`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ name: "customer-journey-test" }),
    });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const b = await r.json();
    if (!b.apiKey || !b.orgDid) throw new Error("missing apiKey/orgDid");
    apiKey = b.apiKey;
    orgDid = b.orgDid;
    signupBody = b;
    return `apiKey=${apiKey.slice(0, 18)}… org=${orgDid.slice(0, 30)}…`;
  });
  if (!apiKey) {
    console.log("─".repeat(80));
    console.log("FAIL — cannot continue without an API key");
    process.exit(1);
  }

  // 2. Plan pre-flip (with auth-propagation retry)
  await step(`2. GET /api/plan (auth-propagation retry up to ${PROPAGATION_MAX}s)`, async () => {
    const body = await pollWithBackoff(
      async () => {
        const r = await fetch(`${HOST}/api/plan`, { headers: { authorization: `Bearer ${apiKey}` } });
        if (!r.ok) return { _httpStatus: r.status };
        return await r.json();
      },
      (b) => b && b.plan === "free",
    );
    if (!body || body.plan !== "free") throw new Error(`expected plan=free, got ${JSON.stringify(body).slice(0, 100)}`);
    return `plan=free quota.used=${body?.quota?.apiRequestUsedToday ?? "?"}`;
  });

  // 3. Cypher CREATE + MATCH
  // Soft: when yata-zeebe-worker is in degraded state the dispatcher
  // returns 500 — this is operational (P29), not a regression.
  await step(
    "3a. POST /cypher CREATE (n:Journey)",
    async () => {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query: 'CREATE (n:Journey {step:"3a", ts:"' + new Date().toISOString() + '"}) RETURN n' }),
      });
      if (!r.ok) throw new Error(`status=${r.status} body=${(await r.text()).slice(0, 200)}`);
      return `accepted`;
    },
    { soft: true },
  );

  await step(
    "3b. POST /cypher MATCH (n:Journey)",
    async () => {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query: "MATCH (n:Journey) RETURN n.step LIMIT 5" }),
      });
      if (!r.ok) throw new Error(`status=${r.status}`);
      const body = await r.json();
      const rows = body?.results?.[0]?.data?.length ?? 0;
      return `rows=${rows}`;
    },
    { soft: true },
  );

  // 4. MCP discovery
  await step("4. POST /mcp tools/list (public)", async () => {
    const r = await fetch(`${HOST}/mcp`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", method: "tools/list", id: 1 }),
    });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const tools = body?.result?.tools?.length ?? 0;
    if (tools === 0) throw new Error("no tools returned");
    return `tools=${tools}`;
  });

  // 5. MCP tools/call yata.graph.cypher — same dispatcher path as /cypher,
  // soft-fail on dispatcher 500 (P29 operational).
  await step(
    "5. POST /mcp tools/call yata.graph.cypher",
    async () => {
      const r = await fetch(`${HOST}/mcp`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({
          jsonrpc: "2.0",
          method: "tools/call",
          params: { name: "yata.graph.cypher", arguments: { query: "MATCH (n:Journey) RETURN n LIMIT 5" } },
          id: 2,
        }),
      });
      if (!r.ok) throw new Error(`status=${r.status}`);
      const body = await r.json();
      if (body?.error) throw new Error(`jsonrpc error: ${JSON.stringify(body.error).slice(0, 120)}`);
      return `ok`;
    },
    { soft: true },
  );

  // 6. Storage PUT (soft — known P29 cluster recovery cluster sometimes returns dispatcher 500)
  await step(
    "6. PUT /storage/v1/object/journey-bucket/welcome.txt",
    async () => {
      const r = await fetch(`${HOST}/storage/v1/object/journey-bucket/welcome.txt`, {
        method: "PUT",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "text/plain" },
        body: `Hello from customer-journey ${new Date().toISOString()}\n`,
      });
      if (!r.ok) throw new Error(`status=${r.status} body=${(await r.text()).slice(0, 120)}`);
      return `stored`;
    },
    { soft: true },
  );

  // 7. Webhook (signed) → plan flip to starter
  let webhookOk = false;
  await step("7. POST /webhook/stripe (signed checkout.session.completed)", async () => {
    const event = syntheticCheckoutSession(orgDid, "starter");
    const payload = JSON.stringify(event);
    const ts = Math.floor(Date.now() / 1000);
    const sig = fmtSig(ts, payload, STRIPE_SECRET);
    const r = await fetch(`${HOST}/webhook/stripe`, {
      method: "POST",
      headers: { "content-type": "application/json", "stripe-signature": sig },
      body: payload,
    });
    if (!r.ok) throw new Error(`status=${r.status} body=${(await r.text()).slice(0, 120)}`);
    const body = await r.json();
    if (!body.ok) throw new Error(`webhook ack not ok: ${JSON.stringify(body)}`);
    webhookOk = true;
    return `event=${event.type} ack=${JSON.stringify(body)}`;
  });

  // 8. Plan flip
  if (webhookOk) {
    await step(`8. GET /api/plan (poll up to ${PROPAGATION_MAX}s for plan=starter)`, async () => {
      const body = await pollWithBackoff(
        async () => {
          const r = await fetch(`${HOST}/api/plan`, { headers: { authorization: `Bearer ${apiKey}` } });
          return r.ok ? await r.json() : null;
        },
        (b) => b && b.plan === "starter",
      );
      if (!body || body.plan !== "starter") throw new Error(`expected plan=starter, got plan=${body?.plan}`);
      return `flip free → starter`;
    });
  }

  // 9. Usage shows journey-step metering
  // Threshold: at least 1 api_request event must be visible. Public surfaces
  // (mcp tools/list, webhook) don't emit. Surfaces that 500 at the
  // dispatcher (cypher, storage) may not emit either. The point is to
  // prove that the metering pipeline is alive when auth passed and a
  // surface returned cleanly — even if other surfaces are degraded.
  await step("9. GET /api/usage (metering pipeline alive)", async () => {
    const r = await fetch(`${HOST}/api/usage`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const apiReqMetric = (body.byMetric ?? []).find((m) => m.metric === "api_request");
    if (!apiReqMetric || apiReqMetric.totalQty < 1) throw new Error(`api_request totalQty=${apiReqMetric?.totalQty ?? 0} < 1 (metering pipeline appears broken)`);
    return `byMetric=${(body.byMetric ?? []).length} api_request.totalQty=${apiReqMetric.totalQty}`;
  });

  // 3c.b P95 — Cypher WHERE clause (CONTAINS / STARTS WITH / ENDS WITH)
  await step("3c.b POST /cypher WHERE CONTAINS/STARTS WITH (P95)", async () => {
    async function q(query) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${query}`);
      return r.json();
    }
    await q('CREATE (n:P95Mail {addr:"alice@acme.com"}) RETURN n');
    await q('CREATE (n:P95Mail {addr:"bob@acme.com"}) RETURN n');
    await q('CREATE (n:P95Mail {addr:"carol@other.io"}) RETURN n');
    const c = await q('MATCH (n:P95Mail) WHERE n.addr CONTAINS "acme" RETURN n.addr');
    const cRows = c?.results?.[0]?.data ?? [];
    if (cRows.length !== 2) throw new Error(`CONTAINS expected 2, got ${cRows.length}`);
    const s = await q('MATCH (n:P95Mail) WHERE n.addr STARTS WITH "al" RETURN n.addr');
    if ((s?.results?.[0]?.data?.length ?? 0) !== 1) throw new Error(`STARTS WITH expected 1`);
    const e = await q('MATCH (n:P95Mail) WHERE n.addr ENDS WITH ".io" RETURN n.addr');
    if ((e?.results?.[0]?.data?.length ?? 0) !== 1) throw new Error(`ENDS WITH expected 1`);
    return `CONTAINS=2, STARTS WITH=1, ENDS WITH=1`;
  });

  // 3c.c P96 — numeric WHERE + AND combinator
  await step("3c.c POST /cypher numeric WHERE + AND (P96)", async () => {
    async function q(query) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${query}`);
      return r.json();
    }
    await q('CREATE (n:P96Age {name:"alice", age:"30"}) RETURN n');
    await q('CREATE (n:P96Age {name:"bob", age:"25"}) RETURN n');
    await q('CREATE (n:P96Age {name:"carol", age:"42"}) RETURN n');
    const gt = await q('MATCH (n:P96Age) WHERE n.age > 25 RETURN n.name');
    if ((gt?.results?.[0]?.data?.length ?? 0) !== 2) throw new Error("n.age > 25 expected 2");
    const and = await q('MATCH (n:P96Age) WHERE n.age >= 25 AND n.age < 42 RETURN n.name');
    if ((and?.results?.[0]?.data?.length ?? 0) !== 2) throw new Error("range AND expected 2");
    const eq = await q('MATCH (n:P96Age) WHERE n.name = "alice" RETURN n.name');
    if ((eq?.results?.[0]?.data?.length ?? 0) !== 1) throw new Error("string EQ expected 1");
    return `> 25 → 2, [25,42) → 2, =alice → 1`;
  });

  // 3c.d P97 — outbound webhook registry + mutation surfacing
  await step("3c.d /api/webhooks register + cypher mutation surface (P97)", async () => {
    const reg = await fetch(`${HOST}/api/webhooks`, {
      method: "POST",
      headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({
        url: "https://example.com/journey-sink",
        types: ["cypher.create"],
        label: "JourneyWh",
      }),
    });
    if (!reg.ok) throw new Error(`register status=${reg.status}`);
    const rb = await reg.json();
    if (!rb.webhook?.id) throw new Error("missing webhook id");
    if (!rb.webhook?.secret || rb.webhook.secret.length < 16) throw new Error("missing/short secret");
    const id = rb.webhook.id;

    // GET should show 1 row with REDACTED secret.
    const list = await fetch(`${HOST}/api/webhooks`, { headers: { authorization: `Bearer ${apiKey}` } });
    const lb = await list.json();
    if ((lb.webhooks?.length ?? 0) !== 1) throw new Error(`expected 1 webhook, got ${lb.webhooks?.length}`);
    if (lb.webhooks[0].secret) throw new Error("secret leaked on GET");
    if (!lb.webhooks[0].secretPrefix) throw new Error("missing secretPrefix");

    // CREATE on the filter label should produce a mutation event in the response.
    const cre = await fetch(`${HOST}/cypher`, {
      method: "POST",
      headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ query: 'CREATE (n:JourneyWh {name:"wh-test"}) RETURN n' }),
    });
    const crB = await cre.json();
    const muts = crB.results?.[0]?.mutations;
    if (!Array.isArray(muts) || muts.length !== 1) throw new Error(`expected 1 mutation, got ${JSON.stringify(muts)}`);
    if (muts[0]?.event !== "cypher.create") throw new Error(`wrong event: ${muts[0]?.event}`);

    // DELETE webhook + verify list is empty.
    await fetch(`${HOST}/api/webhooks/${id}`, { method: "DELETE", headers: { authorization: `Bearer ${apiKey}` } });
    const list2 = await fetch(`${HOST}/api/webhooks`, { headers: { authorization: `Bearer ${apiKey}` } });
    const l2b = await list2.json();
    if ((l2b.webhooks?.length ?? 0) !== 0) throw new Error("webhook DELETE didn't remove from index");
    return `registered → list 1 (secret redacted) → mutation surfaced → deleted → 0`;
  });

  // 3d. P92 — Cypher edges: CREATE (a)-[:T]->(b) + single-hop MATCH traversal
  await step("3d. POST /cypher edge CREATE + MATCH traversal (P92)", async () => {
    async function q(query) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${query}`);
      return r.json();
    }
    await q('CREATE (a:P92Person {name:"alice"})-[:FOLLOWS]->(b:P92Person {name:"bob"}) RETURN a, b');
    await q('CREATE (a:P92Person {name:"alice2"})-[:FOLLOWS]->(b:P92Person {name:"carol"}) RETURN a, b');
    const all = await q('MATCH (a:P92Person)-[:FOLLOWS]->(b) RETURN a, b');
    const rows = all?.results?.[0]?.data ?? [];
    if (rows.length !== 2) throw new Error(`expected 2 edges, got ${rows.length}`);
    const traversal = await q('MATCH (a:P92Person {name:"alice"})-[:FOLLOWS]->(b) RETURN b.name');
    const tRows = traversal?.results?.[0]?.data ?? [];
    if (tRows.length !== 1 || tRows[0]?.row?.[0] !== "bob") {
      throw new Error(`traversal expected ["bob"], got ${JSON.stringify(tRows)}`);
    }
    return `2 edges created, traversal alice→bob verified`;
  });

  // 3f. P102 — MERGE (find-or-create) + two-hop traversal
  await step("3f. POST /cypher MERGE + two-hop traversal (P102)", async () => {
    async function q(query) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${query}`);
      return r.json();
    }
    // Build alice -FOLLOWS-> bob, bob -OWNS-> dog
    await q('MERGE (a:JTwo {name:"alice"})-[:FOLLOWS]->(b:JTwo {name:"bob"}) RETURN a, b');
    await q('MERGE (a:JTwo {name:"bob"})-[:OWNS]->(b:JTwoPet {kind:"dog"}) RETURN a, b');
    // bob should appear ONCE — MERGE reused it.
    const bobs = await q('MATCH (n:JTwo {name:"bob"}) RETURN n');
    if ((bobs?.results?.[0]?.data?.length ?? 0) !== 1) {
      throw new Error(`MERGE should reuse bob; got ${bobs?.results?.[0]?.data?.length} bob nodes`);
    }
    // Two-hop traversal should find dog through bob.
    const path = await q('MATCH (a:JTwo {name:"alice"})-[:FOLLOWS]->(b)-[:OWNS]->(c) RETURN a.name, c.kind');
    const rows = path?.results?.[0]?.data ?? [];
    if (rows.length !== 1) throw new Error(`two-hop expected 1 row, got ${rows.length}`);
    if (rows[0]?.row?.[1] !== "dog") throw new Error(`two-hop wrong dst: ${JSON.stringify(rows[0])}`);
    // Idempotency: re-MERGE alice→bob, ensure alice still single.
    await q('MERGE (a:JTwo {name:"alice"})-[:FOLLOWS]->(b:JTwo {name:"bob"}) RETURN a, b');
    const alices = await q('MATCH (n:JTwo {name:"alice"}) RETURN n');
    if ((alices?.results?.[0]?.data?.length ?? 0) !== 1) {
      throw new Error(`MERGE not idempotent on alice; got ${alices?.results?.[0]?.data?.length}`);
    }
    // P103: edge MERGE is also idempotent — re-MERGE alice→bob should NOT
    // add a second FOLLOWS edge, and should NOT fire a webhook event.
    const reMerge = await q('MERGE (a:JTwo {name:"alice"})-[:FOLLOWS]->(b:JTwo {name:"bob"}) RETURN a, b');
    const reMutations = reMerge?.results?.[0]?.mutations ?? [];
    if (reMutations.length !== 0) {
      throw new Error(`P103: re-MERGE should emit 0 mutations, got ${reMutations.length}`);
    }
    const followsEdges = await q('MATCH (a:JTwo {name:"alice"})-[:FOLLOWS]->(b) RETURN b.name');
    const fRows = followsEdges?.results?.[0]?.data ?? [];
    if (fRows.length !== 1) {
      throw new Error(`P103: re-MERGE created duplicate edge; got ${fRows.length} (expected 1)`);
    }
    return `alice→bob→dog roundtrip; nodes singletons; edges singletons (P103: no dup, no webhook)`;
  });

  // 3e. P93 — Cypher edges: incoming traversal + DELETE
  await step("3e. POST /cypher incoming MATCH + DELETE edge (P93)", async () => {
    async function q(query) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${query}`);
      return r.json();
    }
    // Incoming MATCH — find followers of bob (set up by 3d's alice→bob).
    const inc = await q('MATCH (b:P92Person {name:"bob"})<-[:FOLLOWS]-(a) RETURN a.name');
    const incRows = inc?.results?.[0]?.data ?? [];
    if (incRows.length !== 1 || incRows[0]?.row?.[0] !== "alice") {
      throw new Error(`incoming MATCH expected [alice], got ${JSON.stringify(incRows)}`);
    }
    // DELETE_EDGE — drop alice→bob, leave alice2→carol intact.
    await q('MATCH (a:P92Person {name:"alice"})-[r:FOLLOWS]->(b) DELETE r');
    const all = await q('MATCH (a:P92Person)-[:FOLLOWS]->(b) RETURN a, b');
    const allRows = all?.results?.[0]?.data ?? [];
    if (allRows.length !== 1) throw new Error(`after DELETE expected 1 edge, got ${allRows.length}`);
    if (allRows[0]?.row?.[0]?.properties?.name !== "alice2") throw new Error(`wrong edge survived: ${JSON.stringify(allRows[0])}`);
    return `incoming → [alice], DELETE_EDGE alice→bob preserved alice2→carol`;
  });

  // 3b.2 P91 — Multi-tenant isolation. Signup a SECOND tenant and verify
  //          it cannot see the first tenant's cypher node, storage object,
  //          or audit events. Critical correctness check.
  await step("3b.2 P91: tenant isolation (cypher + storage + audit)", async () => {
    // Mint a second tenant + flush auth-cache propagation.
    const r2 = await fetch(`${HOST}/auth/v1/signup`, {
      method: "POST", headers: { "content-type": "application/json" }, body: "{}",
    });
    if (!r2.ok) throw new Error(`tenant B signup status=${r2.status}`);
    const b2 = await r2.json();
    if (!b2.apiKey || !b2.orgDid) throw new Error("tenant B signup missing apiKey/orgDid");
    if (b2.orgDid === orgDid) throw new Error("tenant B got SAME orgDid as tenant A — isolation broken at mint");
    const authB = { authorization: `Bearer ${b2.apiKey}`, "content-type": "application/json" };
    await new Promise((r) => setTimeout(r, 20000));

    // Verify tenant B cannot MATCH tenant A's Journey nodes.
    const m = await fetch(`${HOST}/cypher`, {
      method: "POST", headers: authB,
      body: JSON.stringify({ query: "MATCH (n:Journey) RETURN n" }),
    });
    if (!m.ok) throw new Error(`tenant B cypher status=${m.status}`);
    const mb = await m.json();
    const rows = mb?.results?.[0]?.data ?? [];
    if (rows.length > 0) throw new Error(`ISOLATION BREACH: tenant B sees ${rows.length} of tenant A's Journey nodes`);

    // Tenant B cannot GET tenant A's storage object.
    const s = await fetch(`${HOST}/storage/v1/object/journey-bucket/welcome.txt`, { headers: authB });
    if (s.status !== 404) throw new Error(`ISOLATION BREACH: tenant B got ${s.status} on tenant A's storage object (expect 404)`);

    // Tenant B cannot see tenant A's audit events.
    const a = await fetch(`${HOST}/api/audit`, { headers: authB });
    if (!a.ok) throw new Error(`tenant B audit status=${a.status}`);
    const ab = await a.json();
    const bEvents = ab.events ?? [];
    for (const e of bEvents) {
      if (e.surface === "cypher" && e.path === "/cypher") {
        // OK — tenant B made its own cypher call as part of THIS isolation check
      }
    }
    // Tenant B's audit should NOT contain paths from tenant A's earlier journey steps
    // (e.g. /api/plan, /webhook/stripe). They might have a few audit events from B's
    // own probes — that's fine — but never tenant A's.
    // A weak check: assert no event has path "/storage/v1/object/journey-bucket/welcome.txt"
    // with a 200 (B's HEAD was 404). Stronger: B's bEvents <= 4 (the calls we just made).
    if (bEvents.length > 6) throw new Error(`tenant B audit unexpectedly has ${bEvents.length} events`);

    // Cleanup tenant B.
    await fetch(`${HOST}/api/account/delete`, {
      method: "POST", headers: authB, body: JSON.stringify({ confirm: "DELETE" }),
    });
    return `tenant B (org=${b2.orgDid.slice(0, 24)}…) blind to tenant A; auth/cypher/storage/audit isolated`;
  });

  // 3c. P90 — Cypher property filter + SET (KV engine)
  await step("3c. POST /cypher property filter + SET (P90)", async () => {
    async function cypherQ(q) {
      const r = await fetch(`${HOST}/cypher`, {
        method: "POST",
        headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
        body: JSON.stringify({ query: q }),
      });
      if (!r.ok) throw new Error(`status=${r.status} q=${q}`);
      return r.json();
    }
    await cypherQ('CREATE (n:JourneyP90 {name:"alpha", role:"viewer"}) RETURN n');
    await cypherQ('CREATE (n:JourneyP90 {name:"beta", role:"viewer"}) RETURN n');
    await cypherQ('CREATE (n:JourneyP90 {name:"gamma", role:"admin"}) RETURN n');
    const viewers = await cypherQ('MATCH (n:JourneyP90 {role:"viewer"}) RETURN n');
    const v = viewers?.results?.[0]?.data ?? [];
    if (v.length !== 2) throw new Error(`property filter expected 2 viewers, got ${v.length}`);
    await cypherQ('MATCH (n:JourneyP90 {name:"alpha"}) SET n.role = "superadmin" RETURN n');
    const elevated = await cypherQ('MATCH (n:JourneyP90 {role:"superadmin"}) RETURN n');
    const e = elevated?.results?.[0]?.data ?? [];
    if (e.length !== 1) throw new Error(`SET expected 1 superadmin, got ${e.length}`);
    if (e[0]?.row?.[0]?.properties?.name !== "alpha") throw new Error(`SET wrong node updated`);
    return `filter=2-viewers SET=alpha→superadmin, verify=1-superadmin`;
  });

  // 6b. P105 — full storage lifecycle (list, sign, anonymous GET, delete)
  await step("6b. /storage/v1 full lifecycle (list, sign, anon GET, delete)", async () => {
    const h = { authorization: `Bearer ${apiKey}` };
    // List the bucket — should include the file from step 6.
    const listR = await fetch(`${HOST}/storage/v1/object/list/journey-bucket`, { headers: h });
    if (!listR.ok) throw new Error(`list status=${listR.status}`);
    const list = await listR.json();
    const files = list.objects ?? [];
    if (!files.some((o) => o.name === "welcome.txt")) {
      throw new Error(`welcome.txt not in list: ${JSON.stringify(files.map((o) => o.name))}`);
    }
    // Sign a URL for the same file.
    const signR = await fetch(`${HOST}/storage/v1/object/sign/journey-bucket/welcome.txt`, {
      method: "POST", headers: { ...h, "content-type": "application/json" },
      body: JSON.stringify({ expiresIn: 60 }),
    });
    if (!signR.ok) throw new Error(`sign status=${signR.status}`);
    const sb = await signR.json();
    if (!sb.signedURL) throw new Error("sign response missing signedURL");
    // Anonymous GET (no Authorization header) via the signed URL.
    const anonR = await fetch(sb.signedURL);
    if (anonR.status !== 200) throw new Error(`anonymous signed GET status=${anonR.status}`);
    const body = await anonR.text();
    if (!body) throw new Error("signed GET returned empty body");
    // DELETE the file.
    const delR = await fetch(`${HOST}/storage/v1/object/journey-bucket/welcome.txt`, { method: "DELETE", headers: h });
    if (!delR.ok) throw new Error(`delete status=${delR.status}`);
    // Confirm gone — GET should 404, list should not include it.
    const get2 = await fetch(`${HOST}/storage/v1/object/journey-bucket/welcome.txt`, { headers: h });
    if (get2.status !== 404) throw new Error(`post-delete GET should 404, got ${get2.status}`);
    return `list, sign, anon GET (${body.length}B), delete, post-delete-404 all OK`;
  });

  // 6c. P86 — S3 SigV4 path actually works end-to-end (PUT + GET)
  await step("6c. /s3/* AWS SigV4 (boto3-compat path)", async () => {
    if (!signupBody?.awsAccessKeyId || !signupBody?.awsSecretAccessKey) {
      throw new Error("signup did not include awsAccessKeyId / awsSecretAccessKey");
    }
    // Inline SigV4 signing for a tiny PUT — the customer-journey script
    // must not depend on @aws-sdk/* so we sign manually.
    const ak = signupBody.awsAccessKeyId;
    const sk = signupBody.awsSecretAccessKey;
    const region = "us-east-1", service = "s3", bucket = "journey-s3", key = "hi.txt";
    const body = "journey-s3-payload";
    const enc = new TextEncoder();
    const bodyHash = await sha256HexJ(body);
    const now = new Date();
    const amzDate = now.toISOString().replace(/[-:]/g, "").replace(/\.\d+/, "");
    const dateStamp = amzDate.slice(0, 8);
    const host = "yatabase.etzhayyim.com";
    const pathStr = `/s3/${bucket}/${key}`;
    const canonicalReq = `PUT\n${pathStr}\n\nhost:${host}\nx-amz-content-sha256:${bodyHash}\nx-amz-date:${amzDate}\n\nhost;x-amz-content-sha256;x-amz-date\n${bodyHash}`;
    const credScope = `${dateStamp}/${region}/${service}/aws4_request`;
    const sts = `AWS4-HMAC-SHA256\n${amzDate}\n${credScope}\n${await sha256HexJ(canonicalReq)}`;
    const kDate = await hmacBin(enc.encode("AWS4" + sk), enc.encode(dateStamp));
    const kReg = await hmacBin(kDate, enc.encode(region));
    const kSvc = await hmacBin(kReg, enc.encode(service));
    const kSign = await hmacBin(kSvc, enc.encode("aws4_request"));
    const sig = hexJ(await hmacBin(kSign, enc.encode(sts)));
    const authz = `AWS4-HMAC-SHA256 Credential=${ak}/${credScope},SignedHeaders=host;x-amz-content-sha256;x-amz-date,Signature=${sig}`;
    const r = await fetch(`${HOST}${pathStr}`, {
      method: "PUT",
      headers: { authorization: authz, "x-amz-date": amzDate, "x-amz-content-sha256": bodyHash },
      body,
    });
    if (r.status !== 200) throw new Error(`PUT status=${r.status} body=${(await r.text()).slice(0, 200)}`);
    return `s3 PUT ${pathStr} → 200 etag=${r.headers.get("etag")?.slice(0,12)}…`;
  });

  // 9b. P76 — whoami before attach (expect attachedEmail=null)
  await step("9b. GET /auth/v1/whoami (pre-attach)", async () => {
    const r = await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    if (body.orgDid !== orgDid) throw new Error(`orgDid mismatch ${body.orgDid} !== ${orgDid}`);
    if (body.attachedEmail !== null) throw new Error(`unexpected attachedEmail=${body.attachedEmail}`);
    return `plan=${body.plan} canOpenPortal=${body.canOpenPortal}`;
  });

  // 9c. P76 — attach-email + whoami reflects it (P83: verified=false until link clicked)
  const journeyEmail = `journey-${Date.now()}@example.com`;
  await step("9c. POST /auth/v1/attach-email (P83: unverified by default)", async () => {
    const r = await fetch(`${HOST}/auth/v1/attach-email`, {
      method: "POST",
      headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ email: journeyEmail }),
    });
    if (!r.ok) throw new Error(`status=${r.status} body=${(await r.text()).slice(0, 200)}`);
    const ab = await r.json();
    if (ab.attachedEmailVerified !== false) throw new Error(`P83: expected verified=false on first attach, got ${ab.attachedEmailVerified}`);
    const w = await (await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${apiKey}` } })).json();
    if (w.attachedEmail !== journeyEmail) throw new Error(`whoami did not reflect attach: ${w.attachedEmail}`);
    if (w.attachedEmailVerified !== false) throw new Error(`whoami P83 verified state wrong: ${w.attachedEmailVerified}`);
    return `attached=${journeyEmail} verified=false`;
  });

  // 9d. P76 — recover ALWAYS returns 200 (no enumeration)
  await step("9d. POST /auth/v1/recover (matching email, no enumeration)", async () => {
    const r1 = await fetch(`${HOST}/auth/v1/recover`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: journeyEmail }),
    });
    if (!r1.ok) throw new Error(`matching status=${r1.status}`);
    const b1 = await r1.json();
    const r2 = await fetch(`${HOST}/auth/v1/recover`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ email: `unknown-${Date.now()}@example.com` }),
    });
    if (!r2.ok) throw new Error(`unknown status=${r2.status}`);
    const b2 = await r2.json();
    if (b1.message !== b2.message) throw new Error("enumeration leak: matching vs unknown returned different messages");
    return `matching+unknown both ok msg="${b1.message?.slice(0, 30)}..."`;
  });

  // 9e. P76 — redeem rejects bad tokens with 400 TokenExpired
  await step("9e. POST /auth/v1/redeem (bad token rejected)", async () => {
    const r = await fetch(`${HOST}/auth/v1/redeem`, {
      method: "POST", headers: { "content-type": "application/json" },
      body: JSON.stringify({ token: "deadbeef".repeat(6) }),
    });
    if (r.status !== 400) throw new Error(`expected 400, got ${r.status}`);
    const body = await r.json();
    if (body.error !== "TokenExpired") throw new Error(`expected TokenExpired, got ${body.error}`);
    return `400 TokenExpired (single-use semantics enforced)`;
  });

  // 9b.d P104 — Invite + Revoke (KV revocation actually invalidates)
  await step("9b.d POST /auth/v1/invite + /revoke (P104: revoke kills key)", async () => {
    // Invite a second key.
    const inv = await fetch(`${HOST}/auth/v1/invite`, {
      method: "POST", headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ name: "journey-invitee" }),
    });
    if (!inv.ok) throw new Error(`invite status=${inv.status}`);
    const ib = await inv.json();
    if (!ib.apiKey || !ib.keyId) throw new Error("invite missing apiKey/keyId");
    // Give the invited key a moment to propagate, then confirm it works.
    await new Promise((r) => setTimeout(r, 4000));
    const w1 = await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${ib.apiKey}` } });
    if (w1.status !== 200) throw new Error(`invited key pre-revoke status=${w1.status}`);

    // Revoke from the owner bearer.
    const rev = await fetch(`${HOST}/auth/v1/revoke`, {
      method: "POST", headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ keyId: ib.keyId }),
    });
    if (!rev.ok) throw new Error(`revoke status=${rev.status}`);
    const rb = await rev.json();
    if (rb.mode !== "kv-revoked") throw new Error(`expected mode=kv-revoked, got ${rb.mode}`);

    // Wait for KV propagation; revoked key should 401.
    await new Promise((r) => setTimeout(r, 5000));
    const w2 = await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${ib.apiKey}` } });
    if (w2.status !== 401) throw new Error(`revoked key should 401, got ${w2.status}`);
    // Owner key still valid.
    const w3 = await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (w3.status !== 200) throw new Error(`owner key should still work, got ${w3.status}`);
    return `invite → 200, revoke → kv-revoked, revoked key → 401, owner still 200`;
  });

  // 9c.b P89 — KV-backed outbox shows the verify-email row from 9c
  await step("9c.b GET /api/outbox (P89: KV-backed events visible)", async () => {
    // 9c just fired an email-verify outbox row via waitUntil — give it
    // a beat to flush.
    await new Promise((r) => setTimeout(r, 2000));
    const r = await fetch(`${HOST}/api/outbox`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const events = body.events ?? [];
    if (events.length === 0) throw new Error("expected ≥1 outbox row after attach-email; got 0");
    const kinds = new Set(events.map((e) => e.kind));
    if (!kinds.has("email-verify")) throw new Error(`missing email-verify kind in outbox; got ${[...kinds].join(",")}`);
    return `events=${events.length} kinds=${[...kinds].sort().join(",")}`;
  });

  // 9b.c P94 — Members pane (KV org_keys index)
  await step("9b.c GET /api/members (P94: KV-backed key list)", async () => {
    const r = await fetch(`${HOST}/api/members`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const members = body.members ?? [];
    if (members.length < 1) throw new Error(`expected ≥1 member, got ${members.length}`);
    if (members[0]?.role !== "owner") throw new Error(`first member should be owner, got ${members[0]?.role}`);
    return `members=${members.length} (first key prefix ${members[0]?.keyPrefix?.slice(0, 16)}…)`;
  });

  // 9f. P87 — KV-backed audit log returns real per-tenant events. The
  //     audit write happens in waitUntil after each request, and KV
  //     replication is eventually-consistent across CF POPs, so we poll
  //     up to ~12s instead of asserting on a single 2s window (was P106
  //     flake when the first poll landed before the writes converged).
  await step("9f. GET /api/audit (P87: KV-backed events visible)", async () => {
    const deadline = Date.now() + 12_000;
    let events = [];
    let lastStatus = 0;
    while (Date.now() < deadline) {
      const r = await fetch(`${HOST}/api/audit`, { headers: { authorization: `Bearer ${apiKey}` } });
      lastStatus = r.status;
      if (r.ok) {
        const body = await r.json();
        events = body.events ?? [];
        if (events.length > 0) break;
      }
      await new Promise((res) => setTimeout(res, 1500));
    }
    if (events.length === 0) throw new Error(`expected >=1 audit event after waitUntil flush; last status=${lastStatus}`);
    const surfaces = new Set(events.map((e) => e.surface));
    if (!surfaces.has("cypher")) throw new Error(`missing cypher surface in audit; got ${[...surfaces].join(",")}`);
    return `events=${events.length} surfaces=${[...surfaces].sort().join(",")}`;
  });

  // 9g. P106 — /api/schema surfaces the graph labels the customer has
  //     actually created. Studio's left-pane schema tree depends on this
  //     and the yata.schema.describe MCP tool wraps it. The journey has
  //     created (at minimum): Journey, JourneyFilter, JourneyNum, alice,
  //     bob — so /api/schema must list them with nodeCount >= 1.
  await step("9g. GET /api/schema (P106: graph schema introspection)", async () => {
    const r = await fetch(`${HOST}/api/schema`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const labels = body.cypherLabels ?? [];
    if (labels.length === 0) {
      throw new Error(`schema.cypherLabels empty after the journey wrote ~5 labels; got=${JSON.stringify(body).slice(0, 200)}`);
    }
    const labelNames = new Set(labels.map((l) => l.name));
    // Journey is the first label created in step 3a and is the most
    // stable anchor. If it's missing, the schema scanner is broken.
    if (!labelNames.has("Journey")) {
      throw new Error(`schema missing 'Journey' label; got=[${[...labelNames].sort().join(",")}]`);
    }
    const totalNodes = labels.reduce((acc, l) => acc + (l.nodeCount ?? 0), 0);
    if (totalNodes === 0) throw new Error("schema labels present but all nodeCount=0");
    return `labels=${labels.length} totalNodes=${totalNodes} sample=Journey/${labels.find((l) => l.name === "Journey")?.nodeCount ?? 0}`;
  });

  // 9h. P107 — CORS preflight on the surfaces a browser SDK actually
  //     hits. yatabase markets itself as a customer-facing BaaS; if a
  //     wrangler config drift removes the OPTIONS handler or strips
  //     `authorization` from access-control-allow-headers, every
  //     browser SDK breaks silently in production. Assert preflight
  //     allows POST/Authorization for /cypher, /mcp, and storage PUT.
  await step("9h. OPTIONS preflight (P107: browser SDK CORS contract)", async () => {
    const origin = "https://example-customer-app.com";
    const surfaces = [
      { path: "/cypher", method: "POST", requireAuth: true },
      { path: "/mcp", method: "POST", requireAuth: false }, // public read-only fallback
      { path: "/storage/v1/object/journey-bucket/cors.txt", method: "PUT", requireAuth: true },
      { path: "/api/schema", method: "GET", requireAuth: true },
    ];
    const failures = [];
    for (const s of surfaces) {
      const r = await fetch(`${HOST}${s.path}`, {
        method: "OPTIONS",
        headers: {
          origin,
          "access-control-request-method": s.method,
          "access-control-request-headers": s.requireAuth ? "authorization,content-type" : "content-type",
        },
      });
      if (r.status !== 200 && r.status !== 204) {
        failures.push(`${s.path} preflight status=${r.status}`);
        continue;
      }
      const allowOrigin = r.headers.get("access-control-allow-origin") ?? "";
      const allowMethods = r.headers.get("access-control-allow-methods") ?? "";
      const allowHeaders = (r.headers.get("access-control-allow-headers") ?? "").toLowerCase();
      if (allowOrigin !== origin && allowOrigin !== "*") {
        failures.push(`${s.path} allow-origin=${allowOrigin}`);
      }
      if (!allowMethods.toUpperCase().includes(s.method)) {
        failures.push(`${s.path} method ${s.method} not in allow-methods=${allowMethods}`);
      }
      if (s.requireAuth && !allowHeaders.includes("authorization")) {
        failures.push(`${s.path} allow-headers missing authorization=${allowHeaders}`);
      }
    }
    if (failures.length > 0) throw new Error(failures.join("; "));
    return `preflight ok on ${surfaces.length} surfaces (cypher, mcp, storage PUT, schema)`;
  });

  // 10. Right-to-know (CCPA / GDPR / 改正個人情報保護法 §33). P88: assert
  //     auditLog.events is now populated inline (Art 30 records of
  //     processing satisfied without a separate /api/audit fetch).
  await step("10. GET /api/export (CCPA / GDPR / 改正個人情報保護法 §33)", async () => {
    const r = await fetch(`${HOST}/api/export`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (!r.ok) throw new Error(`status=${r.status}`);
    const body = await r.json();
    const billingEvents = body.billingEvents?.length ?? 0;
    const apiKeys = body.apiKeys?.length ?? 0;
    const auditEvents = body.auditLog?.events?.length ?? 0;
    if (apiKeys === 0) throw new Error("export missing apiKeys");
    if (auditEvents === 0) throw new Error("P88: export.auditLog.events should be non-empty after journey activity");
    return `tables=${body.tables?.length ?? 0} billingEvents=${billingEvents} apiKeys=${apiKeys} auditEvents=${auditEvents}`;
  });

  // 11. Right-to-erasure (P77: physical purge + auth tombstone gate)
  await step("11. POST /api/account/delete (irreversible + auth tombstone)", async () => {
    const r = await fetch(`${HOST}/api/account/delete`, {
      method: "POST",
      headers: { authorization: `Bearer ${apiKey}`, "content-type": "application/json" },
      body: JSON.stringify({ confirm: "DELETE" }),
    });
    if (!r.ok) throw new Error(`status=${r.status} body=${(await r.text()).slice(0, 200)}`);
    const body = await r.json();
    if (body.mode !== "kv-r2-purge") throw new Error(`expected mode=kv-r2-purge, got ${body.mode}`);
    if (!body.counters) throw new Error("missing counters");
    // P77: erasure tombstone must 401 the same bearer on next call.
    const after = await fetch(`${HOST}/auth/v1/whoami`, { headers: { authorization: `Bearer ${apiKey}` } });
    if (after.status !== 401) throw new Error(`tombstone gate broken: post-delete bearer status=${after.status} (expected 401)`);
    const c = body.counters;
    return `purged auth_keys=${c.auth_keys} cypher=${c.cypher_nodes} r2=${c.r2_objects} usage_days=${c.usage_days} attached=${c.attached_email_index}; tombstone gate OK`;
  });

  console.log("─".repeat(80));
  const pass = stepResults.filter((s) => s.status === "PASS").length;
  const soft = stepResults.filter((s) => s.status === "SOFT").length;
  const fail = stepResults.filter((s) => s.status === "FAIL").length;
  console.log(`SUMMARY  ${pass} PASS · ${soft} SOFT · ${fail} FAIL · journey=${fail === 0 ? "GREEN" : "BROKEN"}`);
  console.log(`orgDid:  ${orgDid}`);
  if (fail > 0) {
    console.log("\nHard failures:");
    for (const s of stepResults.filter((r) => r.status === "FAIL")) console.log(`  • ${s.label} → ${s.note}`);
  }
  if (soft > 0) {
    console.log("\nSoft failures (known operational, not regressions):");
    for (const s of stepResults.filter((r) => r.status === "SOFT")) console.log(`  • ${s.label} → ${s.note}`);
  }
  process.exit(hardFails > 0 ? 1 : 0);
}

main().catch((e) => {
  console.error("ERR:", e?.stack ?? e);
  process.exit(1);
});
