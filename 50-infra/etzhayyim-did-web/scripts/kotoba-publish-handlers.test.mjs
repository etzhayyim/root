// Integration tests for the kotoba publish HANDLERS (the branchiest new code:
// sig verify → KV check-and-set → IP attestation), with an in-memory KV mock.
// No Durable Object (the browser-complete design uses no operated server-state
// primitive — ADR-2605262130 / 2605312345; the root advances under KV CAS). No
// browser, no network. Run via: node --experimental-strip-types --test scripts/*.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  handleBlockPut,
  handleBlockHas,
  handleRootGet,
} from "../src/kotoba-publish.ts";

const B32 = "abcdefghijklmnopqrstuvwxyz234567";
const base32 = (bytes) => {
  let bits = 0,
    value = 0,
    out = "";
  for (const b of bytes) {
    value = (value << 8) | b;
    bits += 8;
    while (bits >= 5) {
      out += B32[(value >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) out += B32[(value << (5 - bits)) & 31];
  return out;
};
const hex = (b) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");

// In-memory KV mock ------------------------------------------------------------
function makeKV() {
  const m = new Map();
  return {
    _m: m,
    async get(k) {
      return m.has(k) ? m.get(k) : null;
    },
    async put(k, v) {
      m.set(k, v);
    },
  };
}
const makeEnv = (extra = {}) => ({ ACTOR_KV: makeKV(), ...extra });

// Build a member-signed publish the way kotoba-wasm does: did:key:z+hex(pub),
// ed25519 over the raw 36-byte root CID (0x01 0x71 0x12 0x20 + 32-byte digest).
async function signedPublish(kp, prevRoot, graph = "t") {
  const cid = new Uint8Array(36);
  cid.set([0x01, 0x71, 0x12, 0x20], 0);
  cid.set(crypto.getRandomValues(new Uint8Array(32)), 4);
  const root = "b" + base32(cid);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const sig = new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, cid));
  return { graph, root, prevRoot: prevRoot ?? null, did: "did:key:z" + hex(pub), sig: hex(sig), blocks: [] };
}
const putReq = (body) =>
  new Request("https://etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.block.put", {
    method: "POST",
    headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.9" },
    body: JSON.stringify(body),
  });
const genKey = () => crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);

test("handleBlockPut accepts a valid signed publish and advances the head", async () => {
  const env = makeEnv();
  const kp = await genKey();
  const r = await handleBlockPut(putReq(await signedPublish(kp, null)), env);
  assert.equal(r.status, 200);
  const j = await r.json();
  assert.equal(j.ok, true);
  // root mirrored to KV for the GET path
  const rootResp = await handleRootGet(new URL("https://x/?graph=t"), env);
  assert.equal((await rootResp.json()).root, j.root);
});

test("handleBlockPut rejects a bad signature with 401", async () => {
  const env = makeEnv();
  const kp = await genKey();
  const pub = await signedPublish(kp, null);
  pub.sig = "00".repeat(64); // not a real signature
  const r = await handleBlockPut(putReq(pub), env);
  assert.equal(r.status, 401);
});

test("handleBlockPut returns 409 on a stale prevRoot (no lost update)", async () => {
  const env = makeEnv();
  const kp = await genKey();
  const first = await handleBlockPut(putReq(await signedPublish(kp, null)), env);
  assert.equal(first.status, 200);
  // publish again with a stale prevRoot → conflict (KV check-and-set)
  const stale = await signedPublish(kp, "bafyreistaleprev");
  const r = await handleBlockPut(putReq(stale), env);
  assert.equal(r.status, 409);
  assert.equal((await r.json()).currentRoot, (await first.clone().json()).root);
});

test("handleBlockHas reports only the missing CIDs", async () => {
  const env = makeEnv();
  await env.ACTOR_KV.put("kblk:present", "deadbeef");
  const req = new Request("https://x/xrpc/...has", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ cids: ["present", "absent1", "absent2"] }),
  });
  const j = await (await handleBlockHas(req, env)).json();
  assert.deepEqual(j.missing.sort(), ["absent1", "absent2"]);
});

test("IP is encrypted in the attestation when the oversight key is set", async () => {
  const key = btoa(String.fromCharCode(...crypto.getRandomValues(new Uint8Array(32))));
  const env = makeEnv({ KOTOBA_ATTEST_KEY: key });
  const kp = await genKey();
  const r = await handleBlockPut(putReq(await signedPublish(kp, null)), env);
  assert.equal((await r.json()).attest.ipEncrypted, true);
  // the immutable-blocks invariant: attestation lives in KV, never in a block
  const attestKeys = [...env.ACTOR_KV._m.keys()].filter((k) => k.startsWith("kattest:"));
  assert.equal(attestKeys.length, 1);
});
