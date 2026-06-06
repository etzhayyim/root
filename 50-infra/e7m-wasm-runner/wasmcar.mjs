/**
 * wasmcar — a self-contained, dependency-free CARv1 + CID encoder for the
 * kotoba-premise deploy path (ADR-2606064500).
 *
 * The runtime side already had the *read* half: `cid.ts` (raw single-block CID
 * verify) + `car.ts` (multi-block dag-pb CAR verify + reassemble). This is the
 * missing *write* half — it turns a `.wasm` byte buffer into the exact
 * content-addressed artifact that:
 *
 *   1. `kubo /api/v0/dag/import` accepts and pins (CAR), and
 *   2. the apex / any IPFS gateway then serves at `/ipfs/<cid>`, and
 *   3. `runner.mjs` re-verifies trustlessly before running (CID is the only
 *      trust anchor — no server key, ADR-2605231525).
 *
 * Two layouts, picked by size — mirror images of the two read paths:
 *   - single block (≤ chunkSize): raw codec (0x55) → `bafkrei…` CID. This MATCHES
 *     `ipfs add --cid-version=1 --raw-leaves` byte-for-byte and is verifiable by
 *     `cid.ts::verifyRawCid` (the T1 browser-local tier).
 *   - multi block (> chunkSize): raw leaves + one dag-pb (0x70) UnixFS-File root
 *     → `bafybei…` CID, verifiable by `car.ts::verifyCarToBytes` (the T2 mesh
 *     tier). HONEST: a flat (single-level) DAG — equivalent to `ipfs add` only
 *     while leaf-count ≤ the UnixFS fan-out (no intermediate parent layer); the
 *     CID is internally consistent (our encoder ≡ our verifier ≡ kubo round-trip)
 *     but not claimed bit-identical to `ipfs add` for deep DAGs.
 *
 * No IPFS/dag-cbor/protobuf library is imported — the encoders below are the
 * minimal inverse of the readers in `car.ts`, so the two stay lockstep and the
 * module runs unchanged under the worker bundler AND `node --experimental-strip-types`.
 */

import { base32 } from "../etzhayyim-did-web/src/cid.ts";

const RAW = 0x55;
const DAG_PB = 0x70;
const SHA2_256 = 0x12;
const DEFAULT_CHUNK = 262144; // 256 KiB — kubo's default raw-leaf chunk size

// ── LEB128 unsigned varint (53-bit safe; CAR/protobuf lengths + UnixFS sizes) ──
function uvarint(n) {
  if (n < 0 || !Number.isFinite(n)) throw new Error(`uvarint: bad value ${n}`);
  const out = [];
  let v = n;
  for (;;) {
    const byte = v % 128;
    v = Math.floor(v / 128);
    if (v > 0) {
      out.push(byte | 0x80);
    } else {
      out.push(byte);
      break;
    }
  }
  return Uint8Array.from(out);
}

function concat(parts) {
  let n = 0;
  for (const p of parts) n += p.length;
  const out = new Uint8Array(n);
  let o = 0;
  for (const p of parts) {
    out.set(p, o);
    o += p.length;
  }
  return out;
}

async function sha256(bytes) {
  return new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
}

/** The 36-byte CIDv1 binary form: version | codec | sha2-256 | len(32) | digest. */
function cidBytes(codec, digest) {
  const out = new Uint8Array(4 + digest.length);
  out.set([0x01, codec, SHA2_256, digest.length], 0);
  out.set(digest, 4);
  return out;
}

/** `b` + base32(cidBytes) — identical multibase form to `cid.ts` / `car.ts`. */
export function cidToString(cb) {
  return "b" + base32(cb);
}

// ── minimal protobuf writers (inverse of car.ts readProto) ────────────────────
function pbVarintField(field, value) {
  return concat([uvarint((field << 3) | 0), uvarint(value)]);
}
function pbBytesField(field, bytes) {
  return concat([uvarint((field << 3) | 2), uvarint(bytes.length), bytes]);
}

/** UnixFS `Data` message for a chunked File: Type=File(2), filesize, blocksizes[]. */
function unixfsFile(totalSize, blockSizes) {
  const parts = [pbVarintField(1, 2), pbVarintField(3, totalSize)];
  for (const bs of blockSizes) parts.push(pbVarintField(4, bs));
  return concat(parts);
}

/** A dag-pb PBNode: Links (field 2, repeated) serialized before Data (field 1),
 *  matching go-ipld-prog canonical order that car.ts's reader expects. */
function dagPbNode(links, data) {
  const parts = [];
  for (const lk of links) {
    // PBLink: Hash (field 1, bytes) + Tsize (field 3) — Name omitted.
    const link = concat([pbBytesField(1, lk.hash), pbVarintField(3, lk.tsize)]);
    parts.push(pbBytesField(2, link));
  }
  parts.push(pbBytesField(1, data));
  return concat(parts);
}

// ── CARv1 framing ─────────────────────────────────────────────────────────────
/** dag-cbor `{roots:[<cid>], version:1}` header (canonical CARv1 header). */
function carHeader(rootCidBytes) {
  const tagged = concat([
    Uint8Array.from([0xd8, 0x2a]), // CBOR tag 42 (CID)
    Uint8Array.from([0x58, rootCidBytes.length + 1]), // byte string, len = 1 + cidlen
    Uint8Array.from([0x00]), // multibase identity prefix for binary CID
    rootCidBytes,
  ]);
  const map = concat([
    Uint8Array.from([0xa2]), // map(2)
    Uint8Array.from([0x65]), // text(5)
    new TextEncoder().encode("roots"),
    Uint8Array.from([0x81]), // array(1)
    tagged,
    Uint8Array.from([0x67]), // text(7)
    new TextEncoder().encode("version"),
    Uint8Array.from([0x01]), // 1
  ]);
  return concat([uvarint(map.length), map]);
}

/** One CAR block section: varint(len(cid)+len(data)) | cid | data. */
function carBlock(cb, data) {
  const len = cb.length + data.length;
  return concat([uvarint(len), cb, data]);
}

/**
 * Encode `bytes` into a CARv1 + its root CID.
 * @returns {Promise<{cid:string, car:Uint8Array, codec:"raw"|"dag-pb", blockCount:number, byteSize:number}>}
 */
export async function buildCar(bytes, { chunkSize = DEFAULT_CHUNK } = {}) {
  const data = bytes instanceof Uint8Array ? bytes : new Uint8Array(bytes);

  // ── single block: raw codec, matches `ipfs add --raw-leaves` exactly ──
  if (data.length <= chunkSize) {
    const cb = cidBytes(RAW, await sha256(data));
    const car = concat([carHeader(cb), carBlock(cb, data)]);
    return { cid: cidToString(cb), car, codec: "raw", blockCount: 1, byteSize: data.length };
  }

  // ── multi block: raw leaves + one dag-pb UnixFS-File root ──
  const leaves = [];
  const blockSizes = [];
  for (let off = 0; off < data.length; off += chunkSize) {
    const slice = data.subarray(off, Math.min(off + chunkSize, data.length));
    const cb = cidBytes(RAW, await sha256(slice));
    leaves.push({ cb, data: slice });
    blockSizes.push(slice.length);
  }
  const rootData = dagPbNode(
    leaves.map((l) => ({ hash: l.cb, tsize: l.data.length })),
    unixfsFile(data.length, blockSizes),
  );
  const rootCb = cidBytes(DAG_PB, await sha256(rootData));
  const sections = [carHeader(rootCb), carBlock(rootCb, rootData)];
  for (const l of leaves) sections.push(carBlock(l.cb, l.data));
  return {
    cid: cidToString(rootCb),
    car: concat(sections),
    codec: "dag-pb",
    blockCount: leaves.length + 1,
    byteSize: data.length,
  };
}
