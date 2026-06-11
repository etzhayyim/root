// Pure, ipfs-free tests for car.ts (ADR-2606015200). Builds CARv1 streams
// in-memory (raw block; dag-pb root over two raw leaves) and checks trustless
// verification + reassembly + tamper rejection. The full dag-pb path is also
// proven against a real `ipfs dag export` CAR (see ADR-2606015200 / build notes).
//
//   node --experimental-strip-types --test scripts/car.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { verifyCarToBytes, parseAndVerifyCar } from "../src/car.ts";

const B32 = "abcdefghijklmnopqrstuvwxyz234567";
function base32(bytes) {
  let bits = 0, val = 0, out = "";
  for (const b of bytes) { val = (val << 8) | b; bits += 8; while (bits >= 5) { out += B32[(val >>> (bits - 5)) & 31]; bits -= 5; } }
  if (bits > 0) out += B32[(val << (5 - bits)) & 31];
  return out;
}
function sha256(buf) { return new Uint8Array(createHash("sha256").update(buf).digest()); }
function cidBytes(codec, data) {
  const d = sha256(data);
  const b = new Uint8Array(4 + d.length);
  b.set([0x01, codec, 0x12, 0x20], 0); b.set(d, 4);
  return b;
}
const cidStr = (codec, data) => "b" + base32(cidBytes(codec, data));
function varint(n) { const out = []; while (n >= 0x80) { out.push((n & 0x7f) | 0x80); n >>>= 7; } out.push(n); return Uint8Array.from(out); }
function concat(arrs) { let n = 0; for (const a of arrs) n += a.length; const o = new Uint8Array(n); let p = 0; for (const a of arrs) { o.set(a, p); p += a.length; } return o; }
function section(cidB, data) { const body = concat([cidB, data]); return concat([varint(body.length), body]); }
function car(sections) { const hdr = Uint8Array.from([0xa0]); return concat([varint(hdr.length), hdr, ...sections]); } // dummy header (parser skips it)
// protobuf helpers
function lenField(field, bytes) { return concat([varint((field << 3) | 2), varint(bytes.length), bytes]); }
function pbLink(cidB) { return lenField(1, cidB); } // PBLink.Hash = field 1
function dagpbRoot(links) { return concat(links.map((l) => lenField(2, pbLink(l)))); } // PBNode.Links = field 2

test("raw CAR: verify + reassemble", async () => {
  const data = new TextEncoder().encode("hello tsumugi");
  const c = cidBytes(0x55, data);
  const out = await verifyCarToBytes(cidStr(0x55, data), car([section(c, data)]));
  assert.deepEqual([...out], [...data]);
});

test("dag-pb CAR over two raw leaves: reassemble = concat", async () => {
  const a = new TextEncoder().encode("AAAA"), b = new TextEncoder().encode("BBBBBB");
  const ca = cidBytes(0x55, a), cb = cidBytes(0x55, b);
  const rootData = dagpbRoot([ca, cb]);
  const cr = cidBytes(0x70, rootData);
  const c = car([section(cr, rootData), section(ca, a), section(cb, b)]);
  const out = await verifyCarToBytes(cidStr(0x70, rootData), c);
  assert.deepEqual([...out], [...a, ...b]);
});

test("tampered block is REJECTED (hash mismatch)", async () => {
  const data = new TextEncoder().encode("trusted bytes");
  const c = cidBytes(0x55, data);
  const tampered = new Uint8Array(data); tampered[0] ^= 0xff;
  await assert.rejects(() => parseAndVerifyCar(car([section(c, tampered)])), /hash mismatch/);
});

test("requested root absent from CAR is REJECTED", async () => {
  const data = new TextEncoder().encode("x");
  const c = cidBytes(0x55, data);
  const wrong = cidStr(0x55, new TextEncoder().encode("y"));
  await assert.rejects(() => verifyCarToBytes(wrong, car([section(c, data)])), /not present/);
});
