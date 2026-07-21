import { handle } from "../../cljs-out/worker_core.js";

const deps = {
  didDoc: { id: "did:web:etzhayyim.com", "@context": ["https://www.w3.org/ns/did/v1"] },
  donationPolicy: { entity: "etzhayyim", fundedBy: "donation-only" },
  donateHtml: "<!DOCTYPE html><html>donate</html>",
  unispscTotal: 18342,
  govProcMeta: { generatedAt: "2026-06-01", total: 3, owners: 2, jurisdictions: 1 },
  govProcList: [{ id: "p1" }],
  actorsHtml: () => "<html>actors</html>",
  organismHtml: () => "<html>organism</html>",
  buildActorsJson: async () => ({ graph: "actors-v1", count: 2 }),
  kvGet: async (_env, _k) => null,
  resolveActorRecord: async (h) => (h === "tsumugi" ? { source: "compiled", displayNameEn: "Tsumugi" } : null),
  toDidDoc: (rec) => ({ id: "did:web:etzhayyim.com:actor:tsumugi", source: rec.source }),
  buildPerActorDidDoc: (h) => ({ id: `did:web:etzhayyim.com:actor:${h}`, scaffold: true }),
  didDocCid: async () => "bafkreitestcid",
  toGetProfileView: (rec) => ({ displayName: rec.displayNameEn }),
  handleValid: (h) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(h),
  isKnownHandle: (h) => h === "tsumugi" || h === "gov-jp-somu",
  govProcsByOwner: (h) => (h === "gov-jp-somu" ? [{ id: "passport" }] : []),
  // xrpc registry surface
  searchEntityActors: (q, limit, offset) => ({
    records: q.includes("none") ? [] : [{ handle: "gov-x", displayNameEn: "Gov X" }],
    total: q.trim() ? 1 : 0,
    nextOffset: offset === 0 ? 50 : null,
  }),
  entityTotalCount: 8888,
  compiledActorRecord: (h) => (h === "tsumugi" ? { handle: "tsumugi", displayNameEn: "Tsumugi" } : null),
  compiledActorHandlesList: ["tsumugi", "ooyake"],
  compiledActorHas: (h) => h === "tsumugi" || h === "ooyake",
  actorHandleFromParam: (p) => {
    if (p.startsWith("did:web:etzhayyim.com:actor:")) return p.slice("did:web:etzhayyim.com:actor:".length);
    return p || null;
  },
  isEntityHandle: (h) => h.startsWith("gov-"),
};
const fallbackSentinel = new Response("FALLBACK", { status: 299 });
const fallback = async () => fallbackSentinel;

async function call(method, path) {
  const req = new Request("https://etzhayyim.com" + path, { method });
  return await handle(req, {}, {}, deps, fallback);
}

let fails = 0;
function check(name, cond, extra="") { if (cond) console.log("ok  -", name); else { console.log("FAIL-", name, extra); fails++; } }

{ const r = await call("GET", "/.well-known/did.json");
  const b = await r.text();
  check("did.json status 200", r.status === 200);
  check("did.json content-type did+json", r.headers.get("content-type") === "application/did+json; charset=utf-8", r.headers.get("content-type"));
  check("did.json pretty+newline", b.endsWith("\n") && b.includes("\n  "));
  check("did.json perm-policy", r.headers.get("permissions-policy") === "interest-cohort=(), browsing-topics=()");
}
{ const r = await call("POST", "/.well-known/did.json");
  check("did.json POST 405", r.status === 405 && r.headers.get("allow") === "GET, HEAD"); }
{ const r = await call("GET", "/.well-known/donation.json");
  check("donation 200 json", r.status === 200 && r.headers.get("content-type") === "application/json; charset=utf-8"); }
{ const r = await call("GET", "/donate");
  check("donate html + CSP", r.status === 200 && r.headers.get("content-type").startsWith("text/html") && r.headers.get("content-security-policy").includes("default-src 'none'") && r.headers.get("access-control-allow-origin") === null); }
{ const r = await call("GET", "/.well-known/actors.json");
  const b = await r.text();
  check("actors.json async 200", r.status === 200 && b.includes("actors-v1")); }
{ const r = await call("GET", "/.well-known/gov-units.json");
  check("gov-units 503 when KV empty", r.status === 503); }
{ const r = await call("GET", "/.well-known/gov-procedures.json");
  const b = await r.text();
  check("gov-procedures compact 200", r.status === 200 && b.includes("\"count\":3") && !b.includes("\n  ")); }
{ const r = await call("GET", "/organism");
  check("organism html", r.status === 200 && (await r.text()).includes("organism")); }
{ const r = await call("GET", "/actor/tsumugi/did.json");
  const b = await r.text();
  check("actor did.json 200 + cid header", r.status === 200 && r.headers.get("x-etzhayyim-did-doc-cid") === "bafkreitestcid" && r.headers.get("x-etzhayyim-actor-source") === "compiled" && b.includes("tsumugi")); }
{ const r = await call("GET", "/actor/UNKNOWNXYZ/did.json");
  check("actor did.json unknown 404", r.status === 404 && (await r.text()).includes("HandleNotInRegistry")); }
{ const r = await call("GET", "/actor/-bad-/did.json");
  check("actor did.json invalid handle 400", r.status === 400); }
{ const r = await call("GET", "/actor/tsumugi/profile.json");
  check("actor profile 200", r.status === 200 && (await r.text()).includes("Tsumugi")); }
{ const r = await call("GET", "/actor/nope/profile.json");
  check("actor profile not-found 404", r.status === 404); }
{ const r = await call("GET", "/actor/gov-jp-somu/procedures.json");
  const b = await r.text();
  check("actor procedures 200 count1", r.status === 200 && b.includes("\"count\": 1") && b.includes("passport")); }
{ // /gov is now cljs-owned (:gov-html) per did-web.router — this assertion
  // was stale (pre-dated the /gov cut-over; see router-test.cljc's
  // gov-html-now-owned-by-cljs). Fixed while touching this file for the
  // discovery-surface checks below.
  const r = await call("GET", "/gov");
  check("/gov owned by cljs (civic wayfinding page)", r.status === 200 && r.headers.get("content-type") === "text/html; charset=utf-8"); }
{ // POST to a known route with no upstream configured → cljs xrpc 503
  const r = await call("POST", "/xrpc/app.bsky.feed.getTimeline");
  check("xrpc POST no-upstream → 503", r.status === 503); }

// ─── discovery surface (robots.txt / sitemap.xml family, fixed 2026-07-21) ───
// Previously unowned → silently reverse-proxied (status 299 sentinel here) and
// served the retired YORO app's leftover files. Now owned locally.
{ const r = await call("GET", "/robots.txt");
  const b = await r.text();
  check("robots.txt 200", r.status === 200);
  check("robots.txt content-type", r.headers.get("content-type") === "text/plain; charset=utf-8");
  check("robots.txt is etzhayyim, not YORO", b.includes("etzhayyim.com") && !b.toLowerCase().includes("yoro"));
  check("robots.txt permissive", b.includes("Allow: /"));
  check("robots.txt sitemap pointer", b.includes("Sitemap: https://etzhayyim.com/sitemap.xml")); }
{ const r = await call("POST", "/robots.txt");
  check("robots.txt POST 405", r.status === 405); }
{ const r = await call("GET", "/sitemap.xml");
  const b = await r.text();
  check("sitemap.xml 200", r.status === 200);
  check("sitemap.xml content-type", r.headers.get("content-type") === "application/xml; charset=utf-8");
  check("sitemap.xml no yoro reference", !b.toLowerCase().includes("yoro"));
  check("sitemap.xml references the 2 sub-sitemaps", b.includes("/sitemaps/static.xml") && b.includes("/sitemaps/actors/index.xml")); }
{ const r = await call("GET", "/sitemaps/static.xml");
  const b = await r.text();
  check("sitemaps/static.xml 200", r.status === 200);
  check("sitemaps/static.xml no yoro reference", !b.toLowerCase().includes("yoro"));
  check("sitemaps/static.xml has real etzhayyim URLs", b.includes("https://etzhayyim.com/") && b.includes("https://etzhayyim.com/actors")); }
{ const r = await call("GET", "/sitemaps/actors/index.xml");
  const b = await r.text();
  check("sitemaps/actors/index.xml 200", r.status === 200);
  check("sitemaps/actors/index.xml no yoro reference", !b.toLowerCase().includes("yoro"));
  check("sitemaps/actors/index.xml has real etzhayyim URL", b.includes("https://etzhayyim.com/actors")); }

// ─── reverse proxy (default site path → YORO service binding) ────────────────
function proxyEnv(upstreamResp, throwIt = false) {
  return { YORO: { fetch: async (_req) => { if (throwIt) throw new Error("binding down"); return upstreamResp; } } };
}
async function callEnv(method, path, env) {
  return await handle(new Request("https://etzhayyim.com" + path, { method }), env, {}, deps, fallback);
}
{ // a SPA route is reverse-proxied; cookies stripped, proxied-by + HSTS set
  const up = new Response("yoro-spa", { status: 200, headers: { "set-cookie": "x=1", "content-type": "text/html" } });
  const r = await callEnv("GET", "/search", proxyEnv(up));
  check("reverse-proxy 200 + headers rewritten",
        r.status === 200 && r.headers.get("x-proxied-by") === "etzhayyim-did-web"
        && r.headers.get("set-cookie") === null
        && r.headers.get("strict-transport-security")?.includes("max-age=31536000")
        && (await r.text()) === "yoro-spa");
}
{ // Location header host rewrite yoro.etzhayyim.com → etzhayyim.com
  const up = new Response(null, { status: 302, headers: { location: "https://yoro.etzhayyim.com/welcome" } });
  const r = await callEnv("GET", "/x", proxyEnv(up));
  check("reverse-proxy rewrites Location host", r.headers.get("location") === "https://etzhayyim.com/welcome", r.headers.get("location"));
}
{ // service binding throws → 502
  const r = await callEnv("GET", "/y", proxyEnv(null, true));
  check("reverse-proxy binding failure → 502", r.status === 502 && (await r.text()).includes("kotodama-yoro"));
}

// ─── /ipfs gateway: codec faithfulness + trustless verification ──────────────
// Reference base32 copied verbatim from src/cid.ts — proves the cljs base32
// produces byte-identical CIDs (if it didn't, the round-trip verify would fail).
const B32 = "abcdefghijklmnopqrstuvwxyz234567";
function tsBase32(bytes) {
  let bits = 0, val = 0, out = "";
  for (const b of bytes) { val = (val << 8) | b; bits += 8;
    while (bits >= 5) { out += B32[(val >>> (bits - 5)) & 31]; bits -= 5; } }
  if (bits > 0) out += B32[(val << (5 - bits)) & 31];
  return out;
}
async function rawCidOf(bytes) {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const cid = new Uint8Array(4 + digest.length);
  cid.set([0x01, 0x55, 0x12, 0x20], 0); cid.set(digest, 4);
  return "b" + tsBase32(cid);
}
const ipfsBytes = new TextEncoder().encode("etzhayyim trustless gateway cljs port test\n");
const ipfsCid = await rawCidOf(ipfsBytes);
check("raw CID computed (bafkrei shape)", /^bafkrei[a-z2-7]{52}$/.test(ipfsCid), ipfsCid);

const realFetch = globalThis.fetch;
function mockFetch(bodyBytes, status = 200) {
  globalThis.fetch = async () => new Response(status === 200 ? bodyBytes : "err", { status });
}
{ // happy path: gateway returns the correct bytes → 200 + verified header
  mockFetch(ipfsBytes);
  const r = await call("GET", "/ipfs/" + ipfsCid);
  const body = new Uint8Array(await r.arrayBuffer());
  check("ipfs raw 200 + verified header",
        r.status === 200 && r.headers.get("x-etzhayyim-cid-verified") === "sha256"
        && r.headers.get("cache-control") === "public, max-age=31536000, immutable"
        && body.length === ipfsBytes.length, r.status + " " + r.headers.get("x-etzhayyim-cid-verified"));
}
{ // HEAD → 200, null body
  mockFetch(ipfsBytes);
  const r = await call("HEAD", "/ipfs/" + ipfsCid);
  check("ipfs HEAD 200", r.status === 200);
}
{ // tampered bytes from an untrusted gateway → rejected → 502
  mockFetch(new TextEncoder().encode("TAMPERED"));
  const r = await call("GET", "/ipfs/" + ipfsCid);
  check("ipfs tampered → 502 rejected", r.status === 502 && (await r.text()).includes("IpfsUnavailable"));
}
{ // non-verifiable CID shape → 501
  const r = await call("GET", "/ipfs/notarealcid");
  check("ipfs bad cid → 501", r.status === 501 && (await r.text()).includes("CidNotVerifiable"));
}
{ // POST → 405 (GET/HEAD only)
  const r = await call("POST", "/ipfs/" + ipfsCid);
  check("ipfs POST → 405", r.status === 405);
}
globalThis.fetch = realFetch;

// ─── kotoba member-signed block CAS (ed25519 verify + KV CAS) ────────────────
function base32Decode(s) { // verbatim from kotoba-publish.ts
  let bits = 0, value = 0; const out = [];
  for (const ch of s) { const idx = B32.indexOf(ch); if (idx < 0) continue;
    value = (value << 5) | idx; bits += 5;
    if (bits >= 8) { out.push((value >>> (bits - 8)) & 0xff); bits -= 8; } }
  return new Uint8Array(out);
}
function hex(bytes) { let s = ""; for (const x of bytes) s += x.toString(16).padStart(2, "0"); return s; }
function mockKV() {
  const m = new Map();
  return { _m: m, get: async (k) => (m.has(k) ? m.get(k) : null), put: async (k, v) => { m.set(k, v); } };
}
async function postJson(path, body, env) {
  const req = new Request("https://etzhayyim.com" + path, {
    method: "POST", headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.7" },
    body: JSON.stringify(body),
  });
  return await handle(req, env, {}, deps, fallback);
}

let kp, didKey, rootCid, sigHex;
try {
  kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pubRaw = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  didKey = "did:key:z" + hex(pubRaw);
  rootCid = ipfsCid; // a valid bafkrei CID string
  const rootBytes = base32Decode(rootCid.slice(1));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, rootBytes));
  sigHex = hex(sig);
} catch (e) { console.log("(!) Ed25519 webcrypto unavailable in this node — skipping kotoba sig tests:", e.message); }

if (sigHex) {
  const env = { ACTOR_KV: mockKV() };
  const blkCid = "bafkreiblockaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa";
  { // valid member signature → 200, blocks + root stored
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.put",
      { graph: "yoro-social-v1", root: rootCid, did: didKey, sig: sigHex, blocks: [{ cid: blkCid, hex: "deadbeef" }] }, env);
    const j = await r.json();
    check("kotoba block.put valid sig → 200 ok",
          r.status === 200 && j.ok === true && j.root === rootCid && j.storedBlocks === 1, r.status + " " + JSON.stringify(j));
    check("kotoba stored block + root in KV",
          env.ACTOR_KV._m.has("kblk:" + blkCid) && env.ACTOR_KV._m.has("kroot:yoro-social-v1"));
    check("kotoba attestation recorded (ipHash, no raw IP)",
          [...env.ACTOR_KV._m.keys()].some(k => k.startsWith("kattest:")) && JSON.stringify(j).includes("ipHash"));
  }
  { // tampered signature → 401
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.put",
      { root: rootCid, did: didKey, sig: "00".repeat(64), blocks: [] }, env);
    check("kotoba block.put bad sig → 401", r.status === 401);
  }
  { // missing fields → 400
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.put", { graph: "x" }, env);
    check("kotoba block.put missing fields → 400", r.status === 400);
  }
  { // CAS conflict: head is now rootCid; a put with mismatched prevRoot → 409
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.put",
      { root: rootCid, did: didKey, sig: sigHex, prevRoot: "bdifferent", blocks: [] }, env);
    check("kotoba block.put CAS conflict → 409", r.status === 409);
  }
  { // block.has → reports only the missing cid
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.has", { cids: [blkCid, "bafkreimissing"] }, env);
    const j = await r.json();
    check("kotoba block.has → missing only", JSON.stringify(j.missing) === JSON.stringify(["bafkreimissing"]));
  }
  { // root GET → manifest with the published root
    const r = await call("GET", "/xrpc/com.etzhayyim.apps.kotoba.root?graph=yoro-social-v1");
    // call() uses the no-KV deps env; re-issue with KV env:
    const req = new Request("https://etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.root?graph=yoro-social-v1");
    const r2 = await handle(req, env, {}, deps, fallback);
    const j = await r2.json();
    check("kotoba root GET → published root", j.root === rootCid);
  }
  { // stats GET → advances counter
    const req = new Request("https://etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.stats?graph=yoro-social-v1");
    const r = await handle(req, env, {}, deps, fallback);
    const j = await r.json();
    check("kotoba stats GET → advances>=1", (j.advances ?? 0) >= 1 && j.root === rootCid);
  }
  { // serve /kotoba/blocks/<cid> from KV → 200 octet-stream
    const req = new Request("https://etzhayyim.com/kotoba/blocks/" + blkCid);
    const r = await handle(req, env, {}, deps, fallback);
    check("kotoba serve block → 200 octet", r.status === 200 && r.headers.get("content-type") === "application/octet-stream");
  }
  { // serve missing block → falls back to TS handler (299)
    const req = new Request("https://etzhayyim.com/kotoba/blocks/bafkreinotstored");
    const r = await handle(req, env, {}, deps, fallback);
    check("kotoba serve missing → fallback", r.status === 299);
  }
  { // no ACTOR_KV → 503
    const r = await postJson("/xrpc/com.etzhayyim.apps.kotoba.block.put",
      { root: rootCid, did: didKey, sig: sigHex, blocks: [] }, {});
    check("kotoba block.put no KV → 503", r.status === 503);
  }
}

// ─── xrpc dispatch (registry short-circuits + proxy; CACAO → fallback) ───────
{ // verifyCacao POST → delegated to TS fallback (CACAO crypto stays in TS)
  const r = await callEnv("POST", "/xrpc/com.etzhayyim.authz.verifyCacao", {});
  check("xrpc verifyCacao → TS fallback", r.status === 299);
}
{ // registerAccount POST → delegated to TS fallback
  const r = await callEnv("POST", "/xrpc/com.etzhayyim.authz.registerAccount", {});
  check("xrpc registerAccount → TS fallback", r.status === 299);
}
{ // kotobaWriteConfig GET → 200, operatorDid + writeEnabled
  const env = { KOTOBA_OPERATOR_DID: "did:key:zABC", KOTOBA_WRITE_ENDPOINT: "https://node" };
  const r = await callEnv("GET", "/xrpc/com.etzhayyim.authz.kotobaWriteConfig", env);
  const j = await r.json();
  check("xrpc kotobaWriteConfig → 200 enabled",
        r.status === 200 && j.operatorDid === "did:key:zABC" && j.writeEnabled === true
        && r.headers.get("x-etzhayyim-auth") === "cacao-verify-only");
}
{ // searchActors GET → 200, actors + totalActors + entity-mirror source
  const r = await callEnv("GET", "/xrpc/app.bsky.actor.searchActors?q=gov&limit=10", {});
  const j = await r.json();
  check("xrpc searchActors → 200 merged",
        r.status === 200 && Array.isArray(j.actors) && typeof j.totalActors === "number"
        && r.headers.get("x-etzhayyim-actor-source") === "entity-mirror+pds"
        && r.headers.get("x-etzhayyim-entity-total") === "8888", r.status + " " + JSON.stringify(j));
}
{ // getProfile for a registered actor DID → 200 from the registry
  const r = await callEnv("GET", "/xrpc/app.bsky.actor.getProfile?actor=did:web:etzhayyim.com:actor:tsumugi", {});
  const j = await r.json();
  check("xrpc getProfile registered → 200", r.status === 200 && j.displayName === "Tsumugi");
}
{ // generic proxy: unknown NSID → 501 MethodNotImplemented
  const r = await callEnv("GET", "/xrpc/com.unknown.thing", {});
  check("xrpc unknown NSID → 501", r.status === 501 && (await r.text()).includes("MethodNotImplemented"));
}
{ // generic proxy: known route but empty upstream → 503
  const r = await callEnv("GET", "/xrpc/com.etzhayyim.apps.unispsc.foo", { XRPC_UNISPSC_UPSTREAM: "" });
  check("xrpc empty upstream → 503", r.status === 503 && (await r.text()).includes("UpstreamNotConfigured"));
}
{ // generic proxy: GET→POST normalization to a configured upstream (mock fetch)
  let captured = null;
  globalThis.fetch = async (url, opts) => { captured = { url: String(url), method: opts.method, body: opts.body }; return new Response('{"ok":1}', { status: 200 }); };
  const r = await callEnv("GET", "/xrpc/app.bsky.feed.getTimeline?limit=5", { XRPC_ATPROTO_UPSTREAM: "https://up.example" });
  globalThis.fetch = realFetch;
  check("xrpc generic proxy GET→POST normalized",
        r.status === 200 && captured && captured.method === "POST" && captured.url.includes("/xrpc/app.bsky.feed.getTimeline")
        && captured.body.includes("\"limit\":\"5\"") && r.headers.get("x-proxied-by") === "etzhayyim-did-web", JSON.stringify(captured));
}
{ // substrate routing: getFollowers → YORO_XRPC service binding
  const env = { YORO_XRPC: { fetch: async (req) => new Response('{"followers":[]}', { status: 200, headers: { "set-cookie": "z=1" } }) } };
  const r = await callEnv("GET", "/xrpc/app.bsky.graph.getFollowers?actor=x", env);
  check("xrpc substrate getFollowers → proxied",
        r.status === 200 && r.headers.get("x-etzhayyim-substrate") === "mst-ipfs-l2" && r.headers.get("set-cookie") === null);
}

console.log(fails === 0 ? "\nALL SMOKE PASS" : `\n${fails} SMOKE FAILS`);
process.exit(fails === 0 ? 0 : 1);
