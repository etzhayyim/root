/**
 * Canonical DAG-CBOR encoder (subset sufficient for did:etzhayyim genesis ops).
 *
 * Spec: https://ipld.io/specs/codecs/dag-cbor/spec/
 *       RFC 8949 (CBOR)
 *
 * Constraints (DAG-CBOR canonical form):
 *   - Map keys MUST be UTF-8 strings, sorted by length ascending then bytewise.
 *   - Integers MUST use the smallest CBOR encoding.
 *   - No floating-point values.
 *   - No CBOR tags (genesis ops do not use CID-as-link tags here).
 *   - Indefinite-length items are forbidden.
 *
 * Supported value types: null, boolean, integer (number), string,
 * Uint8Array (byte string), array, plain object (string-keyed).
 */

const textEncoder = new TextEncoder();

function encodeUint(major: number, value: number): Uint8Array {
  if (value < 0 || !Number.isInteger(value)) throw new Error("encodeUint requires non-negative integer");
  const head = major << 5;
  if (value < 24) {
    return new Uint8Array([head | value]);
  }
  if (value < 0x100) {
    return new Uint8Array([head | 24, value]);
  }
  if (value < 0x10000) {
    return new Uint8Array([head | 25, (value >>> 8) & 0xff, value & 0xff]);
  }
  if (value < 0x100000000) {
    return new Uint8Array([
      head | 26,
      (value >>> 24) & 0xff,
      (value >>> 16) & 0xff,
      (value >>> 8) & 0xff,
      value & 0xff,
    ]);
  }
  // 64-bit not needed for our genesis op fields (small ints + version=1)
  throw new Error("encodeUint: value exceeds 32-bit range");
}

function concat(parts: Uint8Array[]): Uint8Array {
  let total = 0;
  for (const p of parts) total += p.length;
  const out = new Uint8Array(total);
  let off = 0;
  for (const p of parts) {
    out.set(p, off);
    off += p.length;
  }
  return out;
}

function compareKeys(a: string, b: string): number {
  // DAG-CBOR canonical map key ordering: shorter first, then bytewise on UTF-8 bytes.
  const ab = textEncoder.encode(a);
  const bb = textEncoder.encode(b);
  if (ab.length !== bb.length) return ab.length - bb.length;
  for (let i = 0; i < ab.length; i += 1) {
    if (ab[i] !== bb[i]) return ab[i] - bb[i];
  }
  return 0;
}

export type CborValue =
  | null
  | boolean
  | number
  | string
  | Uint8Array
  | CborValue[]
  | { [k: string]: CborValue };

export function encodeCanonicalCbor(v: CborValue): Uint8Array {
  if (v === null) return new Uint8Array([0xf6]);
  if (typeof v === "boolean") return new Uint8Array([v ? 0xf5 : 0xf4]);
  if (typeof v === "number") {
    if (!Number.isInteger(v)) throw new Error("DAG-CBOR forbids floats; got non-integer number");
    if (v >= 0) return encodeUint(0, v);
    return encodeUint(1, -1 - v);
  }
  if (typeof v === "string") {
    const bytes = textEncoder.encode(v);
    return concat([encodeUint(3, bytes.length), bytes]);
  }
  if (v instanceof Uint8Array) {
    return concat([encodeUint(2, v.length), v]);
  }
  if (Array.isArray(v)) {
    const parts: Uint8Array[] = [encodeUint(4, v.length)];
    for (const item of v) parts.push(encodeCanonicalCbor(item));
    return concat(parts);
  }
  if (typeof v === "object") {
    const keys = Object.keys(v).sort(compareKeys);
    const parts: Uint8Array[] = [encodeUint(5, keys.length)];
    for (const k of keys) {
      parts.push(encodeCanonicalCbor(k));
      parts.push(encodeCanonicalCbor((v as Record<string, CborValue>)[k]));
    }
    return concat(parts);
  }
  throw new Error(`encodeCanonicalCbor: unsupported value type: ${typeof v}`);
}
