// IPFS-based DID retrieval tests (ADR-2606015400): the canonical DID document is
// deterministic + content-addressable, and the worker (TS) computes the SAME CID
// the publisher (JS) pins. actor-profiles.ts has internal imports, so it is
// bundled with esbuild (a wrangler dep) before import.
//   node --experimental-strip-types --test scripts/diddoc-cid.test.mjs
import { test, before } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import esbuild from "esbuild";

const HERE = dirname(fileURLToPath(import.meta.url));
let mod;

before(async () => {
  const out = join(tmpdir(), `ap-${createHash("sha1").update(HERE).digest("hex").slice(0, 8)}.mjs`);
  await esbuild.build({
    entryPoints: [join(HERE, "../src/registry/actor-profiles.ts")],
    bundle: true,
    format: "esm",
    platform: "node",
    outfile: out,
  });
  mod = await import(`${out}?t=${Date.now()}`);
});

// publisher's CID algorithm (mirror of cid.ts) — for the cross-impl check.
function pubCid(buf) {
  const A = "abcdefghijklmnopqrstuvwxyz234567";
  const d = createHash("sha256").update(buf).digest();
  const bytes = Buffer.concat([Buffer.from([0x01, 0x55, 0x12, 0x20]), d]);
  let bits = 0, val = 0, s = "";
  for (const b of bytes) { val = (val << 8) | b; bits += 8; while (bits >= 5) { s += A[(val >>> (bits - 5)) & 31]; bits -= 5; } }
  if (bits > 0) s += A[(val << (5 - bits)) & 31];
  return "b" + s;
}

test("canonicalDidDoc normalizes the request-volatile source field", () => {
  const rec = mod.compiledActorRecord("tsumugi");
  const a = mod.canonicalDidDoc({ ...rec, source: "kv" }, {});
  const b = mod.canonicalDidDoc({ ...rec, source: "compiled" }, {});
  assert.equal(a._meta.source, "ipfs");
  assert.equal(b._meta.source, "ipfs");
  assert.deepEqual(a, b); // identical regardless of which tier served the record
});

test("didDocCid is deterministic + a raw CIDv1", async () => {
  const rec = mod.compiledActorRecord("kanae");
  const c1 = await mod.didDocCid(rec, {});
  const c2 = await mod.didDocCid(rec, {});
  assert.equal(c1, c2);
  assert.match(c1, /^bafkrei[a-z2-7]{52}$/);
});

test("didDocCid == publisher CID of the canonical bytes (TS↔JS mirror)", async () => {
  for (const h of ["tsumugi", "kanae", "watatsuna"]) {
    const rec = mod.compiledActorRecord(h);
    const workerCid = await mod.didDocCid(rec, {});
    const bytes = mod.canonicalDidDocBytes(rec, {});
    assert.equal(workerCid, pubCid(Buffer.from(bytes)), `${h}: worker CID must equal CID of the bytes`);
  }
});
