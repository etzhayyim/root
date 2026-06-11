/**
 * Content-address helpers (ADR-2606014600). IPFS CIDv1, raw codec (0x55),
 * sha2-256 — the address form of a single-block artifact (`ipfs add
 * --cid-version=1` on data ≤ one block, e.g. compact Rust/AssemblyScript edge
 * actors like tsumugi-core). Used by the apex trustless `/ipfs/<cid>` gateway to
 * VERIFY fetched bytes before serving — the gateway never has to be trusted, the
 * CID is the trust anchor (no server key, ADR-2605231525).
 *
 * Multi-block (UnixFS dag-pb, `bafy…`) CIDs — large components such as a
 * componentize-py Python actor — are NOT verifiable here without a full
 * UnixFS/CAR reconstruction; those are served unverified-by-this-gateway and
 * belong to the T2 donated-mesh tier (a full IPFS node verifies them). This is
 * the structural reason T1 browser actors stay small (raw, single-block).
 */

// RFC4648 base32 lower, no padding (multibase prefix 'b').
const B32 = "abcdefghijklmnopqrstuvwxyz234567";
export function base32(bytes: Uint8Array): string {
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

/** A dag-pb (UnixFS) sha2-256 CIDv1 string (`bafybei…`) — multi-block content
 *  verifiable via CAR (`car.ts`), not by a single sha256. */
export function isDagPbCidV1(cid: string): boolean {
  return /^bafybei[a-z2-7]{52}$/.test(cid);
}

/** A raw-codec, sha2-256, CIDv1 string (`bafkrei…`). 59 chars, base32. */
export function isRawCidV1(cid: string): boolean {
  return /^bafkrei[a-z2-7]{52}$/.test(cid);
}

/** Compute the CIDv1 (raw, sha2-256) of `bytes`. Matches `ipfs add
 *  --cid-version=1` for single-block data. Uses Web Crypto (available in CF
 *  Workers and Node ≥ 18). */
export async function cidV1Raw(bytes: BufferSource): Promise<string> {
  const digest = new Uint8Array(await crypto.subtle.digest("SHA-256", bytes));
  const cid = new Uint8Array(4 + digest.length);
  cid.set([0x01, 0x55, 0x12, 0x20], 0); // cidv1 | raw | sha2-256 | 32
  cid.set(digest, 4);
  return "b" + base32(cid);
}

/** Verify that `bytes` content-addresses to `cid`. Returns false for any
 *  non-raw CID (cannot verify here) or on mismatch. */
export async function verifyRawCid(
  cid: string,
  bytes: BufferSource,
): Promise<boolean> {
  if (!isRawCidV1(cid)) return false;
  return (await cidV1Raw(bytes)) === cid;
}
