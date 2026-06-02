/**
 * Multihash encoder (subset for did:etzhayyim genesis op CIDs).
 *
 * Spec: draft-multiformats-multihash-09
 * https://github.com/multiformats/multihash
 *
 * Layout:  varint(code) || varint(digest_length) || digest_bytes
 *
 * For sha2-256 the layout reduces to two single-byte varints:
 *   0x12 (sha2-256 code) || 0x20 (32 = digest length) || 32 digest bytes
 */

export const MULTIHASH_CODES = {
  "sha2-256": 0x12,
  "sha2-512": 0x13,
  "sha3-256": 0x16,
  "blake3":   0x1e,
} as const;

export type MultihashCodeName = keyof typeof MULTIHASH_CODES;

export function multihashCodeFromName(name: MultihashCodeName): number {
  return MULTIHASH_CODES[name];
}

export function multihashNameFromCode(code: number): MultihashCodeName | null {
  for (const [name, c] of Object.entries(MULTIHASH_CODES)) {
    if (c === code) return name as MultihashCodeName;
  }
  return null;
}

function varintEncode(n: number): Uint8Array {
  if (n < 0) throw new Error("varint requires non-negative");
  const bytes: number[] = [];
  while (n > 0x7f) {
    bytes.push((n & 0x7f) | 0x80);
    n >>>= 7;
  }
  bytes.push(n & 0x7f);
  return new Uint8Array(bytes);
}

function varintDecode(bytes: Uint8Array, offset: number): { value: number; bytesRead: number } {
  let value = 0;
  let shift = 0;
  let i = 0;
  while (true) {
    if (offset + i >= bytes.length) throw new Error("varint truncated");
    const b = bytes[offset + i];
    value |= (b & 0x7f) << shift;
    i += 1;
    if ((b & 0x80) === 0) return { value, bytesRead: i };
    shift += 7;
    if (shift > 28) throw new Error("varint too long");
  }
}

export function encodeMultihash(codeName: MultihashCodeName, digest: Uint8Array): Uint8Array {
  const code = varintEncode(multihashCodeFromName(codeName));
  const len  = varintEncode(digest.length);
  const out  = new Uint8Array(code.length + len.length + digest.length);
  out.set(code, 0);
  out.set(len, code.length);
  out.set(digest, code.length + len.length);
  return out;
}

export interface DecodedMultihash {
  codeName: MultihashCodeName | null;
  code: number;
  digest: Uint8Array;
}

export function decodeMultihash(bytes: Uint8Array): DecodedMultihash {
  const c = varintDecode(bytes, 0);
  const l = varintDecode(bytes, c.bytesRead);
  const start = c.bytesRead + l.bytesRead;
  const digest = bytes.slice(start, start + l.value);
  if (digest.length !== l.value) throw new Error("multihash digest length mismatch");
  return { codeName: multihashNameFromCode(c.value), code: c.value, digest };
}

export async function sha256(bytes: Uint8Array): Promise<Uint8Array> {
  const copy = new Uint8Array(bytes.length);
  copy.set(bytes);
  const buf = await crypto.subtle.digest("SHA-256", copy.buffer);
  return new Uint8Array(buf);
}
