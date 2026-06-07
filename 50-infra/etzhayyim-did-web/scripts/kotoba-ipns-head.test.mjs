// Integration test for the apex IPNS head-record relay (ADR-2606066000): a
// member-signed kotoba IpnsRecord sent on block.put is stored in the head
// manifest (only when consistent with the verified root/did) and served back by
// GET root. The apex stays a non-authoritative relay — it verifies the ROOT
// signature (existing gate) + a cheap record-consistency check; full IPNS
// signature verification is the reader's job (kotoba-wasm). Run:
//   node --experimental-strip-types --test scripts/kotoba-ipns-head.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { handleBlockPut, handleRootGet } from "../src/kotoba-publish.ts";

// ── tiny in-memory KV (the subset the handlers use) ─────────────────────────
function makeKV() {
  const m = new Map();
  return {
    async get(k) {
      return m.has(k) ? m.get(k) : null;
    },
    async put(k, v) {
      m.set(k, v);
    },
  };
}

const B32 = "abcdefghijklmnopqrstuvwxyz234567";
function base32Encode(bytes) {
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
}
const hex = (b) => Array.from(b, (x) => x.toString(16).padStart(2, "0")).join("");

// A real member identity + CIDv1 dag-cbor root + ed25519 signature over the raw
// CID bytes — exactly what verifyRootSig (and kotoba-wasm commitSigned) expect.
async function member() {
  const kp = await crypto.subtle.generateKey({ name: "Ed25519" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const did = "did:key:z" + hex(pub);
  const digest = crypto.getRandomValues(new Uint8Array(32));
  const cidBytes = new Uint8Array(36);
  cidBytes.set([0x01, 0x71, 0x12, 0x20], 0);
  cidBytes.set(digest, 4);
  const root = "b" + base32Encode(cidBytes);
  const sig = hex(new Uint8Array(await crypto.subtle.sign({ name: "Ed25519" }, kp.privateKey, cidBytes)));
  return { did, root, sig };
}

function ipnsRecordFor(did, root, { value = root, controller = did } = {}) {
  return {
    name: did,
    value,
    sequence: 1,
    valid_until: "2030-01-01T00:00:00Z",
    controller_did: controller,
    public_key_multibase: "z6Mkexamplepubkey",
    signature_multibase: "z3exampleSignature",
  };
}

const req = (body) =>
  new Request("https://etzhayyim.com/xrpc/com.etzhayyim.apps.kotoba.block.put", {
    method: "POST",
    headers: { "content-type": "application/json", "cf-connecting-ip": "203.0.113.5" },
    body: JSON.stringify(body),
  });

async function publish(env, body) {
  const r = await handleBlockPut(req(body), env);
  return { status: r.status, json: await r.json() };
}

const headOf = async (env, graph) =>
  (await handleRootGet(new URL(`https://e.com/x?graph=${graph}`), env)).json();

test("end-to-end: a signed publish stores + serves the IPNS head record", async () => {
  const env = { ACTOR_KV: makeKV() };
  const { did, root, sig } = await member();

  const put = await publish(env, { graph: "g1", root, did, sig, ipnsRecord: ipnsRecordFor(did, root) });
  assert.equal(put.status, 200);
  assert.equal(put.json.ok, true);

  const head = await headOf(env, "g1");
  assert.equal(head.root, root);
  assert.ok(head.ipnsRecord, "head carries the IPNS record");
  assert.equal(head.ipnsRecord.value, root); // value pins to the published root
  assert.equal(head.ipnsRecord.controller_did, did);
  assert.equal(head.ipnsRecord.sequence, 1);
});

test("an inconsistent ipnsRecord (value != root) is dropped; publish still succeeds (relay-only)", async () => {
  const env = { ACTOR_KV: makeKV() };
  const { did, root, sig } = await member();
  const bad = ipnsRecordFor(did, root, { value: "bafyreih4otherrootxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx" });

  const put = await publish(env, { graph: "g2", root, did, sig, ipnsRecord: bad });
  assert.equal(put.status, 200); // a bad record never blocks the publish (apex is a relay)

  const head = await headOf(env, "g2");
  assert.equal(head.root, root);
  assert.equal(head.ipnsRecord, undefined, "inconsistent record is NOT stored");
});

test("a record whose controller != signer is dropped", async () => {
  const env = { ACTOR_KV: makeKV() };
  const { did, root, sig } = await member();
  const bad = ipnsRecordFor(did, root, { controller: "did:key:zsomeoneelse" });

  await publish(env, { graph: "g3", root, did, sig, ipnsRecord: bad });
  const head = await headOf(env, "g3");
  assert.equal(head.ipnsRecord, undefined, "controller mismatch ⇒ not stored");
});

test("legacy publish without an ipnsRecord still works (back-compat)", async () => {
  const env = { ACTOR_KV: makeKV() };
  const { did, root, sig } = await member();

  const put = await publish(env, { graph: "g4", root, did, sig });
  assert.equal(put.status, 200);
  const head = await headOf(env, "g4");
  assert.equal(head.root, root);
  assert.equal(head.ipnsRecord, undefined);
});
