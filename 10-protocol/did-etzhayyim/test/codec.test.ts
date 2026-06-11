/**
 * Codec unit tests for did:etzhayyim (ADR-0029): DAG-CBOR canonical encoder,
 * multibase (base32/16/58btc), and multihash (varint-framed).
 *
 * These three modules are the content-addressing foundation of the DID method —
 * a genesis-op CID is `multibaseEncode('b', cidv1Bytes)` over a multihash over
 * the canonical-CBOR of the op. A regression in key ordering, integer-width
 * minimality, base32 bit-packing, or varint framing silently changes every CID,
 * so the boundaries are worth pinning against known vectors.
 *
 * Run: pnpm -F @etzhayyim/did-etzhayyim test
 */
import { describe, it, expect } from "vitest";
import {
  encodeCanonicalCbor,
} from "../src/cbor";
import {
  encodeBase32, decodeBase32,
  encodeBase16, decodeBase16,
  encodeBase58btc,
  multibaseEncode, multibaseDecode,
} from "../src/multibase";
import {
  multihashCodeFromName, multihashNameFromCode,
  encodeMultihash, decodeMultihash,
  MULTIHASH_CODES,
} from "../src/multihash";

const bytes = (...n: number[]) => new Uint8Array(n);

// ─── DAG-CBOR canonical encoder ───────────────────────────────────────────────

describe("encodeCanonicalCbor — atoms", () => {
  it("encodes null / booleans to their CBOR simple values", () => {
    expect(Array.from(encodeCanonicalCbor(null))).toEqual([0xf6]);
    expect(Array.from(encodeCanonicalCbor(false))).toEqual([0xf4]);
    expect(Array.from(encodeCanonicalCbor(true))).toEqual([0xf5]);
  });

  it("encodes small unsigned ints inline (< 24) and rejects floats", () => {
    expect(Array.from(encodeCanonicalCbor(0))).toEqual([0x00]);
    expect(Array.from(encodeCanonicalCbor(23))).toEqual([0x17]);
    expect(() => encodeCanonicalCbor(3.14)).toThrow(/forbids floats/);
  });

  it("uses the SMALLEST integer width at each boundary (canonical minimality)", () => {
    expect(Array.from(encodeCanonicalCbor(24))).toEqual([0x18, 24]);       // 1-byte
    expect(Array.from(encodeCanonicalCbor(255))).toEqual([0x18, 0xff]);
    expect(Array.from(encodeCanonicalCbor(256))).toEqual([0x19, 0x01, 0x00]); // 2-byte
    expect(Array.from(encodeCanonicalCbor(65535))).toEqual([0x19, 0xff, 0xff]);
    expect(Array.from(encodeCanonicalCbor(65536))).toEqual([0x1a, 0x00, 0x01, 0x00, 0x00]); // 4-byte
  });

  it("encodes negative ints via major-type 1 (-1-n)", () => {
    expect(Array.from(encodeCanonicalCbor(-1))).toEqual([0x20]);   // 1<<5 | 0
    expect(Array.from(encodeCanonicalCbor(-24))).toEqual([0x37]);  // 1<<5 | 23
    expect(Array.from(encodeCanonicalCbor(-25))).toEqual([0x38, 24]);
  });

  it("throws when an unsigned int exceeds the supported 32-bit range", () => {
    expect(() => encodeCanonicalCbor(0x100000000)).toThrow(/32-bit/);
  });
});

describe("encodeCanonicalCbor — strings & byte strings", () => {
  it("frames a string as major-3 len-prefix + UTF-8 bytes", () => {
    // "a" → 0x61 (major 3, len 1) + 0x61
    expect(Array.from(encodeCanonicalCbor("a"))).toEqual([0x61, 0x61]);
    expect(Array.from(encodeCanonicalCbor(""))).toEqual([0x60]);
  });

  it("counts UTF-8 BYTE length, not code-point length, for multibyte text", () => {
    // "é" is 2 UTF-8 bytes (0xC3 0xA9) → header 0x62
    const out = encodeCanonicalCbor("é");
    expect(out[0]).toBe(0x62);
    expect(out.length).toBe(3);
  });

  it("frames a Uint8Array as major-2 byte string", () => {
    expect(Array.from(encodeCanonicalCbor(bytes(0xde, 0xad)))).toEqual([0x42, 0xde, 0xad]);
  });
});

describe("encodeCanonicalCbor — arrays & maps", () => {
  it("frames arrays with a major-4 count header", () => {
    expect(Array.from(encodeCanonicalCbor([1, 2, 3]))).toEqual([0x83, 0x01, 0x02, 0x03]);
    expect(Array.from(encodeCanonicalCbor([]))).toEqual([0x80]);
  });

  it("sorts map keys length-ascending THEN bytewise (DAG-CBOR canonical order)", () => {
    // input deliberately out of order; "b" (len1) < "aa" (len2); "aa" < "ab" bytewise
    const out = encodeCanonicalCbor({ ab: 2, b: 3, aa: 1 });
    // map header (3 pairs) = 0xa3, then keys in canonical order b, aa, ab
    expect(out[0]).toBe(0xa3);
    // key "b" first (shortest)
    expect(out[1]).toBe(0x61); // str len 1
    expect(out[2]).toBe(0x62); // 'b'
    // then "aa" before "ab"
    const s = Array.from(out);
    const posAA = s.findIndex((_, i) => s[i] === 0x62 && s[i + 1] === 0x61 && s[i + 2] === 0x61);
    const posAB = s.findIndex((_, i) => s[i] === 0x62 && s[i + 1] === 0x61 && s[i + 2] === 0x62);
    expect(posAA).toBeGreaterThan(0);
    expect(posAB).toBeGreaterThan(posAA);
  });

  it("is deterministic regardless of object insertion order", () => {
    const a = encodeCanonicalCbor({ x: 1, y: 2 });
    const b = encodeCanonicalCbor({ y: 2, x: 1 });
    expect(Array.from(a)).toEqual(Array.from(b));
  });
});

// ─── multibase ────────────────────────────────────────────────────────────────

describe("base32 (RFC 4648, no padding)", () => {
  it("round-trips arbitrary bytes", () => {
    for (const v of [bytes(), bytes(0), bytes(0xff), bytes(1, 2, 3, 4, 5), bytes(0, 0, 0, 1)]) {
      expect(Array.from(decodeBase32(encodeBase32(v)))).toEqual(Array.from(v));
    }
  });

  it("matches a known vector (RFC 4648 'f' = 'my')", () => {
    // base32 of 0x66 ('f') in the lowercase alphabet "abcde…234567" is "my"
    expect(encodeBase32(new TextEncoder().encode("f"))).toBe("my");
  });

  it("is case-insensitive on decode and rejects out-of-alphabet chars", () => {
    expect(Array.from(decodeBase32("MY"))).toEqual(Array.from(decodeBase32("my")));
    expect(() => decodeBase32("0189")).toThrow(/invalid base32/); // 0,1,8,9 ∉ alphabet
  });
});

describe("base16", () => {
  it("round-trips and zero-pads each byte to two nibbles", () => {
    expect(encodeBase16(bytes(0x00, 0x0f, 0xff))).toBe("000fff");
    expect(Array.from(decodeBase16("000fff"))).toEqual([0x00, 0x0f, 0xff]);
  });

  it("rejects odd-length and non-hex input", () => {
    expect(() => decodeBase16("abc")).toThrow(/odd-length/);
    expect(() => decodeBase16("zz")).toThrow(/invalid hex/);
  });
});

describe("base58btc (encode-only)", () => {
  it("encodes the Bitcoin canonical vector 'Hello World!'", () => {
    expect(encodeBase58btc(new TextEncoder().encode("Hello World!"))).toBe("2NEpo7TZRRrLZSi2U");
  });

  it("preserves each leading zero byte as a leading '1'", () => {
    expect(encodeBase58btc(bytes(0, 0, 0x28))).toBe("11" + encodeBase58btc(bytes(0x28)));
    expect(encodeBase58btc(bytes())).toBe("");
  });
});

describe("multibaseEncode/Decode dispatch", () => {
  it("prefixes b/f and round-trips through decode", () => {
    const v = bytes(0x12, 0x20, 0xab, 0xcd);
    const b = multibaseEncode("b", v);
    expect(b[0]).toBe("b");
    expect(Array.from(multibaseDecode(b).bytes)).toEqual(Array.from(v));
    const f = multibaseEncode("f", v);
    expect(f[0]).toBe("f");
    expect(Array.from(multibaseDecode(f).bytes)).toEqual(Array.from(v));
  });

  it("z encodes but decode is intentionally unimplemented", () => {
    expect(multibaseEncode("z", bytes(1)).startsWith("z")).toBe(true);
    expect(() => multibaseDecode("z123")).toThrow(/not implemented/);
  });

  it("rejects too-short strings and unknown prefixes", () => {
    expect(() => multibaseDecode("b")).toThrow(/too short/);
    expect(() => multibaseDecode("q99")).toThrow(/unsupported multibase prefix/);
  });
});

// ─── multihash ────────────────────────────────────────────────────────────────

describe("multihash code lookup", () => {
  it("maps names ⇄ codes and returns null for unknown codes", () => {
    expect(multihashCodeFromName("sha2-256")).toBe(0x12);
    expect(multihashNameFromCode(0x12)).toBe("sha2-256");
    expect(multihashNameFromCode(0x1e)).toBe("blake3");
    expect(multihashNameFromCode(0x99)).toBeNull();
    expect(MULTIHASH_CODES["sha2-256"]).toBe(0x12);
  });
});

describe("encodeMultihash / decodeMultihash", () => {
  it("produces the canonical sha2-256 two-byte prefix 0x12 0x20", () => {
    const digest = new Uint8Array(32).fill(0xaa);
    const mh = encodeMultihash("sha2-256", digest);
    expect(mh[0]).toBe(0x12);   // code
    expect(mh[1]).toBe(0x20);   // length 32
    expect(mh.length).toBe(34);
    const dec = decodeMultihash(mh);
    expect(dec.code).toBe(0x12);
    expect(dec.codeName).toBe("sha2-256");
    expect(Array.from(dec.digest)).toEqual(Array.from(digest));
  });

  it("round-trips a digest whose length forces a MULTI-BYTE varint (>127)", () => {
    // length 200 → varint [0xC8, 0x01]; exercises the private varint encode+decode path
    const digest = new Uint8Array(200).fill(0x5a);
    const mh = encodeMultihash("blake3", digest);
    const dec = decodeMultihash(mh);
    expect(dec.code).toBe(0x1e);
    expect(dec.codeName).toBe("blake3");
    expect(dec.digest.length).toBe(200);
    expect(Array.from(dec.digest)).toEqual(Array.from(digest));
  });

  it("throws when the framed length exceeds the available bytes", () => {
    // code 0x12, claims length 32, but only 1 digest byte present
    expect(() => decodeMultihash(bytes(0x12, 0x20, 0x01))).toThrow(/length mismatch/);
  });

  it("throws on a truncated varint", () => {
    // 0x80 sets the continuation bit but nothing follows
    expect(() => decodeMultihash(bytes(0x80))).toThrow(/truncated/);
  });
});
