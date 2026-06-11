/**
 * CIDv1 encoder/decoder (subset for did:etzhayyim genesis ops).
 *
 * Spec: https://github.com/multiformats/cid
 *
 * Layout:  varint(version) || varint(codec) || multihash
 * For did:etzhayyim default form:
 *   0x01 (CIDv1) || 0x55 (raw codec) || multihash(sha2-256, 32B)
 *
 * String form: multibase('b', cid_bytes) → "bafy..." (base32 lowercase)
 */

import { multibaseEncode, multibaseDecode, type MultibasePrefix } from "./multibase";
import {
  encodeMultihash,
  decodeMultihash,
  sha256,
  type MultihashCodeName,
} from "./multihash";

export const MULTICODECS = {
  raw:      0x55,
  "dag-cbor": 0x71,
  "dag-pb":   0x70,
  json:     0x0200,
} as const;

export type MulticodecName = keyof typeof MULTICODECS;

export function multicodecFromName(name: MulticodecName): number {
  return MULTICODECS[name];
}

export function multicodecToName(code: number): MulticodecName | null {
  for (const [name, c] of Object.entries(MULTICODECS)) {
    if (c === code) return name as MulticodecName;
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

export interface CIDv1 {
  version: 1;
  codec: MulticodecName;
  multihashCode: MultihashCodeName;
  digest: Uint8Array;
  bytes: Uint8Array;
  multibasePrefix: MultibasePrefix;
}

export function cidv1ToString(cid: CIDv1): string {
  return multibaseEncode(cid.multibasePrefix, cid.bytes);
}

export function cidv1FromString(s: string): CIDv1 {
  const { prefix, bytes } = multibaseDecode(s);
  return cidv1FromBytes(bytes, prefix);
}

export function cidv1FromBytes(bytes: Uint8Array, multibasePrefix: MultibasePrefix = "b"): CIDv1 {
  const v = varintDecode(bytes, 0);
  if (v.value !== 1) throw new Error(`expected CIDv1, got version ${v.value}`);
  const c = varintDecode(bytes, v.bytesRead);
  const codecName = multicodecToName(c.value);
  if (codecName === null) throw new Error(`unsupported multicodec: 0x${c.value.toString(16)}`);
  const mhBytes = bytes.slice(v.bytesRead + c.bytesRead);
  const mh = decodeMultihash(mhBytes);
  if (mh.codeName === null) throw new Error(`unsupported multihash code: 0x${mh.code.toString(16)}`);
  return {
    version: 1,
    codec: codecName,
    multihashCode: mh.codeName,
    digest: mh.digest,
    bytes,
    multibasePrefix,
  };
}

export interface CreateCidOptions {
  codec?: MulticodecName;          // default 'raw'
  multihash?: MultihashCodeName;   // default 'sha2-256'
  multibase?: MultibasePrefix;     // default 'b'
}

export async function createCidV1(content: Uint8Array, opts: CreateCidOptions = {}): Promise<CIDv1> {
  const codec = opts.codec ?? "raw";
  const mhName = opts.multihash ?? "sha2-256";
  const mbPrefix = opts.multibase ?? "b";

  if (mhName !== "sha2-256") {
    throw new Error(`createCidV1: only sha2-256 is implemented in this build (got ${mhName})`);
  }

  const digest = await sha256(content);
  const mhBytes = encodeMultihash(mhName, digest);

  const versionBytes = varintEncode(1);
  const codecBytes = varintEncode(multicodecFromName(codec));
  const total = new Uint8Array(versionBytes.length + codecBytes.length + mhBytes.length);
  total.set(versionBytes, 0);
  total.set(codecBytes, versionBytes.length);
  total.set(mhBytes, versionBytes.length + codecBytes.length);

  return {
    version: 1,
    codec,
    multihashCode: mhName,
    digest,
    bytes: total,
    multibasePrefix: mbPrefix,
  };
}

export async function verifyCidV1(content: Uint8Array, expected: CIDv1): Promise<boolean> {
  const recomputed = await createCidV1(content, {
    codec: expected.codec,
    multihash: expected.multihashCode,
    multibase: expected.multibasePrefix,
  });
  if (recomputed.bytes.length !== expected.bytes.length) return false;
  for (let i = 0; i < recomputed.bytes.length; i += 1) {
    if (recomputed.bytes[i] !== expected.bytes[i]) return false;
  }
  return true;
}
