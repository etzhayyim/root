/**
 * CARv1 + dag-pb/UnixFS verification (ADR-2606015200). Makes multi-block IPFS
 * content (large componentize-py actors, `bafy…` dag-pb CIDs) trustless-gateway-
 * verifiable too — closing the T2 gap left by ADR-2606014600 where dag-pb CIDs
 * returned 501.
 *
 * Given a CARv1 stream (`<gateway>/ipfs/<cid>?format=car`) and a requested root
 * CID, this:
 *   1. parses each block, VERIFIES `sha2-256(block) == block.cid.digest`
 *   2. reassembles the file from the root by walking dag-pb links (UnixFS),
 *      recomputing nothing it didn't hash — every byte returned descends from a
 *      block whose CID was verified, and the walk starts at the requested CID.
 * The untrusted gateway therefore cannot substitute content (no server key,
 * ADR-2605231525). Scope: sha2-256, CIDv1, raw + dag-pb codecs, UnixFS files
 * (raw or dag-pb leaves) — the shape `ipfs add --cid-version=1` produces.
 */

// base32 lower (RFC4648, no pad) — inlined (no internal import) so this module
// runs unchanged under the worker bundler AND node --experimental-strip-types.
const B32 = "abcdefghijklmnopqrstuvwxyz234567";
function base32(bytes: Uint8Array): string {
  let bits = 0,
    val = 0,
    out = "";
  for (const b of bytes) {
    val = (val << 8) | b;
    bits += 8;
    while (bits >= 5) {
      out += B32[(val >>> (bits - 5)) & 31];
      bits -= 5;
    }
  }
  if (bits > 0) out += B32[(val << (5 - bits)) & 31];
  return out;
}

const RAW = 0x55;
const DAG_PB = 0x70;
const SHA2_256 = 0x12;

function readVarint(buf: Uint8Array, pos: number): [number, number] {
  let result = 0,
    shift = 0,
    p = pos;
  for (;;) {
    const b = buf[p++];
    result |= (b & 0x7f) << shift;
    if ((b & 0x80) === 0) break;
    shift += 7;
    if (shift > 35) throw new Error("varint too long");
  }
  return [result >>> 0, p];
}

interface ParsedCid {
  cidStr: string;
  codec: number;
  mhCode: number;
  digest: Uint8Array;
  end: number; // byte offset just past the CID
}

function parseCid(buf: Uint8Array, pos: number): ParsedCid {
  const start = pos;
  let version: number;
  [version, pos] = readVarint(buf, pos);
  if (version !== 1) throw new Error(`only CIDv1 supported, got v${version}`);
  let codec: number, mhCode: number, mhLen: number;
  [codec, pos] = readVarint(buf, pos);
  [mhCode, pos] = readVarint(buf, pos);
  [mhLen, pos] = readVarint(buf, pos);
  const digest = buf.subarray(pos, pos + mhLen);
  pos += mhLen;
  const cidBytes = buf.subarray(start, pos);
  return { cidStr: "b" + base32(cidBytes), codec, mhCode, digest, end: pos };
}

function eqBytes(a: Uint8Array, b: Uint8Array): boolean {
  if (a.length !== b.length) return false;
  for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) return false;
  return true;
}

interface Block {
  data: Uint8Array;
  codec: number;
}

/** Parse a CARv1, verifying every block's multihash. Returns blocks by CID. */
export async function parseAndVerifyCar(
  car: Uint8Array,
): Promise<Map<string, Block>> {
  let pos = 0;
  let hdrLen: number;
  [hdrLen, pos] = readVarint(car, pos);
  pos += hdrLen; // skip the DAG-CBOR header (roots are re-derived from the request)
  const blocks = new Map<string, Block>();
  while (pos < car.length) {
    let secLen: number;
    [secLen, pos] = readVarint(car, pos);
    const secEnd = pos + secLen;
    const cid = parseCid(car, pos);
    const data = car.subarray(cid.end, secEnd);
    if (cid.mhCode !== SHA2_256) {
      throw new Error(`unsupported multihash 0x${cid.mhCode.toString(16)}`);
    }
    const got = new Uint8Array(await crypto.subtle.digest("SHA-256", data));
    if (!eqBytes(got, cid.digest)) {
      throw new Error(`block hash mismatch for ${cid.cidStr}`);
    }
    blocks.set(cid.cidStr, { data, codec: cid.codec });
    pos = secEnd;
  }
  return blocks;
}

// ── minimal protobuf reader (wire types 0 varint, 2 len-delimited) ──────────
interface PbField {
  field: number;
  wire: number;
  bytes?: Uint8Array;
  varint?: number;
}
function readProto(buf: Uint8Array): PbField[] {
  const out: PbField[] = [];
  let pos = 0;
  while (pos < buf.length) {
    let tag: number;
    [tag, pos] = readVarint(buf, pos);
    const field = tag >>> 3,
      wire = tag & 7;
    if (wire === 0) {
      let v: number;
      [v, pos] = readVarint(buf, pos);
      out.push({ field, wire, varint: v });
    } else if (wire === 2) {
      let len: number;
      [len, pos] = readVarint(buf, pos);
      out.push({ field, wire, bytes: buf.subarray(pos, pos + len) });
      pos += len;
    } else {
      throw new Error(`unsupported protobuf wire type ${wire}`);
    }
  }
  return out;
}

/** Reassemble the UnixFS file rooted at `cidStr` from verified blocks. */
export function reassemble(cidStr: string, blocks: Map<string, Block>): Uint8Array {
  const blk = blocks.get(cidStr);
  if (!blk) throw new Error(`missing block ${cidStr} in CAR`);
  if (blk.codec === RAW) return blk.data;
  if (blk.codec !== DAG_PB) {
    throw new Error(`unsupported codec 0x${blk.codec.toString(16)} for ${cidStr}`);
  }
  // dag-pb: field 1 = Data (UnixFS), field 2 = Links (repeated PBLink)
  const fields = readProto(blk.data);
  const links = fields.filter((f) => f.field === 2 && f.bytes);
  if (links.length > 0) {
    const parts: Uint8Array[] = [];
    for (const lk of links) {
      const lf = readProto(lk.bytes!);
      const hash = lf.find((f) => f.field === 1 && f.bytes)?.bytes;
      if (!hash) throw new Error("PBLink without Hash");
      const child = parseCid(hash, 0);
      parts.push(reassemble(child.cidStr, blocks));
    }
    return concat(parts);
  }
  // leaf: dag-pb Data → UnixFS message → field 2 = file bytes
  const unixfsBytes = fields.find((f) => f.field === 1 && f.bytes)?.bytes;
  if (!unixfsBytes) return new Uint8Array(0);
  const u = readProto(unixfsBytes);
  return u.find((f) => f.field === 2 && f.bytes)?.bytes ?? new Uint8Array(0);
}

function concat(parts: Uint8Array[]): Uint8Array {
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

/** Verify a CARv1 and return the trustlessly-reconstructed bytes for `rootCid`. */
export async function verifyCarToBytes(
  rootCid: string,
  car: Uint8Array,
): Promise<Uint8Array> {
  const blocks = await parseAndVerifyCar(car);
  if (!blocks.has(rootCid)) {
    throw new Error(`requested root ${rootCid} not present in CAR`);
  }
  return reassemble(rootCid, blocks);
}
