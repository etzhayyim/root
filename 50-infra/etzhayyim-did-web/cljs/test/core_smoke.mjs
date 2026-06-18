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
{ const r = await call("GET", "/some/spa/route");
  check("fallback delegated", r.status === 299); }
{ const r = await call("POST", "/xrpc/app.bsky.feed.getTimeline");
  check("xrpc fallback (POST allowed through)", r.status === 299); }

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

console.log(fails === 0 ? "\nALL SMOKE PASS" : `\n${fails} SMOKE FAILS`);
process.exit(fails === 0 ? 0 : 1);
