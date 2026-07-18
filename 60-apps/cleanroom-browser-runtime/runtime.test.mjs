// runtime.test.mjs — exercise the browser-local runtime against real actor
// manifests (stripe = L4, aadhaar = L3). Run: node runtime.test.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import assert from "node:assert";
import { KotobaActor } from "./kotoba-runtime.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, "../..");
const WEST_ROOT = process.env.ETZHAYYIM_WEST_ROOT || resolve(ROOT, "../../..");
const FIXTURE_REPOS = {
  "stripe-compat": ["orgs", "kotoba-lang", "com-stripe"],
  "aadhaar-compat": ["orgs", "kotoba-lang", "com-aadhaar"],
};
const load = (h) => JSON.parse(readFileSync(resolve(WEST_ROOT, ...FIXTURE_REPOS[h], "manifest.json"), "utf8"));

let passed = 0;
const ok = (c, m) => { assert.ok(c, m); passed++; };

// ── L4 actor: stripe — CRUD + pagination + filtering + relationship expand ──
{
  const a = new KotobaActor(load("stripe-compat"));
  ok(a.entities.includes("Customer"), "stripe has Customer entity");

  const [cs, cust] = a.request("POST", "/v1/customers", { body: { email: "a@b.co", name: "Ada" } });
  ok(cs === 201 && cust.id.startsWith("cus_"), "create customer → 201 + id");
  ok(cust.createdAt && cust.updatedAt, "timestamps set");

  // create 25 payment intents referencing the customer
  for (let i = 0; i < 25; i++)
    a.request("POST", "/v1/paymentintents", { body: { customer: cust.id, amount: 100 + i, currency: i % 2 ? "usd" : "eur" } });

  // pagination: default limit 20, has_more true
  const [, page1] = a.request("GET", "/v1/paymentintents", { query: {} });
  ok(page1.count === 20 && page1.has_more === true && page1.total === 25, "pagination page1 (20/25, has_more)");
  const last = page1.data[page1.data.length - 1].id;
  const [, page2] = a.request("GET", "/v1/paymentintents", { query: { starting_after: last } });
  ok(page2.count === 5 && page2.has_more === false, "pagination page2 (5, no more)");

  // filtering by field
  const [, eur] = a.request("GET", "/v1/paymentintents", { query: { currency: "eur", limit: 100 } });
  ok(eur.data.every((r) => r.currency === "eur") && eur.count === 13, "filter currency=eur → 13");

  // relationship expansion
  const piId = page1.data[0].id;
  const [, expanded] = a.request("GET", `/v1/paymentintents/${piId}`, { query: { expand: "customer" } });
  ok(expanded.customer_obj && expanded.customer_obj.id === cust.id, "expand customer → inlined object");

  // update + delete
  const [us, upd] = a.request("PATCH", `/v1/customers/${cust.id}`, { body: { name: "Ada L" } });
  ok(us === 200 && upd.name === "Ada L", "update customer");
  const [ds] = a.request("DELETE", `/v1/customers/${cust.id}`);
  ok(ds === 200, "delete customer");
  const [gs] = a.request("GET", `/v1/customers/${cust.id}`);
  ok(gs === 404, "get deleted → 404");

  // MCP dispatch parity
  const [mcs, mcust] = a.callTool("create_customer", { email: "x@y.z", name: "Bob" });
  ok(mcs === 201 && mcust.id.startsWith("cus_"), "mcp create_customer → 201");
  const [, mlist] = a.callTool("list_customers", {});
  ok(mlist.object === "list" && mlist.total === 1, "mcp list_customers");
  ok(a.listTools().includes("create_customer"), "listTools advertises create_customer");

  // healthz
  const [hs, hb] = a.request("GET", "/healthz");
  ok(hs === 200 && hb.status === "ok", "healthz ok");

  // socialpost: Datom writes emit dry-run app.bsky.feed.post events, G8-gated
  const feed = a.socialFeed();
  ok(feed.length > 0, "socialpost feed populated by Datom writes");
  ok(feed.every((p) => p.mode === "dry-run" && p.gate === "G8"), "all posts dry-run + G8-gated");
  ok(feed.every((p) => p["$type"] === "app.bsky.feed.post" && p.via === a.did), "posts well-shaped");
}

// ── L3 actor: aadhaar — generic CRUD still works ────────────────────────────
{
  const a = new KotobaActor(load("aadhaar-compat"));
  const ent0 = a.entities[0];
  const plural = a.plural[ent0];
  const [cs, rec] = a.request("POST", `/v1/${plural}`, { body: { foo: "bar" } });
  ok(cs === 201 && rec.id, `aadhaar create ${ent0}`);
  const [, lst] = a.request("GET", `/v1/${plural}`);
  ok(lst.total === 1, "aadhaar list");
}

console.log(`runtime.test.mjs: ${passed} assertions passed`);
