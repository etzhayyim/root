// Tests for the kotoba-premise CAR/CID encoder (ADR-2606064600). Asserts the
// *write* half (wasmcar.mjs) is the exact inverse of the committed *read* half
// (cid.ts raw-verify + car.ts CAR-reassemble), for both the single-block raw
// (T1) and multi-block dag-pb (T2) layouts.
//
//   node --experimental-strip-types --test tests/wasmcar.test.mjs
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { buildCar } from "../wasmcar.mjs";
import { verifyCarToBytes } from "../../etzhayyim-did-web/src/car.ts";
import { cidV1Raw, verifyRawCid, isRawCidV1, isDagPbCidV1 } from "../../etzhayyim-did-web/src/cid.ts";

const DIR = dirname(fileURLToPath(import.meta.url));
const KANAE = join(DIR, "../../../orgs/etzhayyim/com-etzhayyim-kanae/wasm/loader/kanae-core.wasm");

test("single-block: raw CID == `ipfs add --raw-leaves`, verifies, CAR round-trips", async () => {
  const wasm = new Uint8Array(readFileSync(KANAE));
  const r = await buildCar(wasm);
  assert.equal(r.codec, "raw");
  assert.equal(r.blockCount, 1);
  assert.equal(r.byteSize, wasm.length);
  assert.ok(isRawCidV1(r.cid));
  // raw single-block CID is byte-identical to the canonical raw-leaf CID
  assert.equal(r.cid, await cidV1Raw(wasm));
  assert.equal(await verifyRawCid(r.cid, wasm), true);
  // the CAR we emit reassembles back to the exact bytes via the trustless reader
  const back = await verifyCarToBytes(r.cid, r.car);
  assert.deepEqual(Buffer.from(back), Buffer.from(wasm));
});

test("multi-block: dag-pb root + raw leaves, CAR reassembles to original bytes", async () => {
  // 600 KB deterministic buffer → 3 chunks at the 256 KiB default + a dag-pb root
  const big = new Uint8Array(600_000);
  for (let i = 0; i < big.length; i++) big[i] = (i * 31 + 7) & 0xff;
  const r = await buildCar(big);
  assert.equal(r.codec, "dag-pb");
  assert.equal(r.blockCount, 4); // 3 leaves + 1 root
  assert.equal(r.byteSize, big.length);
  assert.ok(isDagPbCidV1(r.cid));
  const back = await verifyCarToBytes(r.cid, r.car);
  assert.equal(back.length, big.length);
  assert.deepEqual(Buffer.from(back), Buffer.from(big));
});

test("chunkSize boundary: exactly one chunk stays raw; one byte over splits", async () => {
  const exact = new Uint8Array(1024).fill(0xab);
  const r1 = await buildCar(exact, { chunkSize: 1024 });
  assert.equal(r1.codec, "raw");
  assert.equal(r1.blockCount, 1);

  const over = new Uint8Array(1025).fill(0xab);
  const r2 = await buildCar(over, { chunkSize: 1024 });
  assert.equal(r2.codec, "dag-pb");
  assert.equal(r2.blockCount, 3); // 2 leaves (1024 + 1) + root
  const back = await verifyCarToBytes(r2.cid, r2.car);
  assert.deepEqual(Buffer.from(back), Buffer.from(over));
});

test("deterministic: same bytes → same CID", async () => {
  const a = await buildCar(new Uint8Array([1, 2, 3, 4, 5]));
  const b = await buildCar(new Uint8Array([1, 2, 3, 4, 5]));
  assert.equal(a.cid, b.cid);
});
