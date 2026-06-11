/**
 * CIDv1 assembler/parser tests for did:etzhayyim (ADR-0029).
 *
 * cid.ts sits on top of the multibase/multihash/cbor codecs (covered in
 * codec.test.ts) and assembles `varint(version) || varint(codec) || multihash`
 * into a CIDv1, plus the inverse parsers. genesis.test.ts only smoke-touches
 * createCidV1/cidv1ToString; this file pins the multicodec table, the
 * round-trip through cidv1FromString/FromBytes (including a multi-byte-varint
 * codec), every parser error path, and verifyCidV1 — against the canonical
 * IPFS vector for "hello".
 *
 * Run: pnpm -F @etzhayyim/did-etzhayyim test
 */
import { describe, it, expect } from "vitest";
import {
  MULTICODECS,
  multicodecFromName, multicodecToName,
  createCidV1, cidv1ToString, cidv1FromString, cidv1FromBytes,
  verifyCidV1,
  type CIDv1,
} from "../src/cid";

const enc = (s: string) => new TextEncoder().encode(s);
const bytes = (...n: number[]) => new Uint8Array(n);

// Canonical IPFS CIDv1 vectors for the content "hello" (no newline), sha2-256.
// raw codec (0x55) and dag-cbor (0x71) share the digest, differing only in the
// codec byte → "bafkrei…" vs "bafyrei…".
const HELLO_RAW = "bafkreibm6jg3ux5qumhcn2b3flc3tyu6dmlb4xa7u5bf44yegnrjhc4yeq";
const HELLO_DAGCBOR = "bafyreibm6jg3ux5qumhcn2b3flc3tyu6dmlb4xa7u5bf44yegnrjhc4yeq";

// ─── multicodec table ─────────────────────────────────────────────────────────

describe("multicodec name ⇄ code", () => {
  it("maps the supported codecs", () => {
    expect(multicodecFromName("raw")).toBe(0x55);
    expect(multicodecFromName("dag-cbor")).toBe(0x71);
    expect(multicodecFromName("dag-pb")).toBe(0x70);
    expect(multicodecFromName("json")).toBe(0x0200);
    expect(MULTICODECS.raw).toBe(0x55);
  });

  it("reverses code → name and returns null for unknown codes", () => {
    expect(multicodecToName(0x55)).toBe("raw");
    expect(multicodecToName(0x0200)).toBe("json");
    expect(multicodecToName(0x99)).toBeNull();
  });
});

// ─── createCidV1 ──────────────────────────────────────────────────────────────

describe("createCidV1", () => {
  it("defaults to raw / sha2-256 / base32 and matches the canonical IPFS vector", async () => {
    const cid = await createCidV1(enc("hello"));
    expect(cid.version).toBe(1);
    expect(cid.codec).toBe("raw");
    expect(cid.multihashCode).toBe("sha2-256");
    expect(cid.digest.length).toBe(32);
    // byte layout: 0x01 (v1) 0x55 (raw) 0x12 (sha2-256) 0x20 (len 32) ...
    expect(Array.from(cid.bytes.slice(0, 4))).toEqual([0x01, 0x55, 0x12, 0x20]);
    expect(cidv1ToString(cid)).toBe(HELLO_RAW);
  });

  it("honors the codec option (dag-cbor → bafyrei, same digest)", async () => {
    const cid = await createCidV1(enc("hello"), { codec: "dag-cbor" });
    expect(cid.bytes[1]).toBe(0x71);
    expect(cidv1ToString(cid)).toBe(HELLO_DAGCBOR);
  });

  it("emits a MULTI-BYTE codec varint for json (0x0200 → 0x80 0x04)", async () => {
    const cid = await createCidV1(enc("hello"), { codec: "json" });
    // version 0x01, then codec varint 0x80 0x04, then multihash 0x12 ...
    expect(Array.from(cid.bytes.slice(0, 4))).toEqual([0x01, 0x80, 0x04, 0x12]);
    expect(cid.codec).toBe("json");
  });

  it("rejects an unimplemented multihash", async () => {
    await expect(createCidV1(enc("x"), { multihash: "sha2-512" })).rejects.toThrow(/only sha2-256/);
  });

  it("is content-deterministic and content-sensitive", async () => {
    const a = await createCidV1(enc("hello"));
    const b = await createCidV1(enc("hello"));
    const c = await createCidV1(enc("hellp"));
    expect(cidv1ToString(a)).toBe(cidv1ToString(b));
    expect(cidv1ToString(a)).not.toBe(cidv1ToString(c));
  });
});

// ─── parsers: round-trip + error paths ──────────────────────────────────────────

describe("cidv1FromString / cidv1FromBytes", () => {
  it("round-trips a created CID through its string form", async () => {
    for (const codec of ["raw", "dag-cbor", "json"] as const) {
      const cid = await createCidV1(enc("round-trip me"), { codec });
      const parsed = cidv1FromString(cidv1ToString(cid));
      expect(parsed.version).toBe(1);
      expect(parsed.codec).toBe(codec);
      expect(parsed.multihashCode).toBe("sha2-256");
      expect(Array.from(parsed.digest)).toEqual(Array.from(cid.digest));
    }
  });

  it("parses the canonical hello vector back to raw/sha2-256", () => {
    const cid = cidv1FromString(HELLO_RAW);
    expect(cid.codec).toBe("raw");
    expect(cid.multihashCode).toBe("sha2-256");
    expect(cid.digest.length).toBe(32);
    expect(cid.multibasePrefix).toBe("b");
  });

  it("rejects a non-CIDv1 version byte", () => {
    // version 0x00, raw codec, sha2-256 multihash header — version 0 ≠ 1
    expect(() => cidv1FromBytes(bytes(0x00, 0x55, 0x12, 0x20))).toThrow(/expected CIDv1/);
  });

  it("rejects an unsupported multicodec", () => {
    // version 1, codec 0x99 (unknown single-byte varint)
    expect(() => cidv1FromBytes(bytes(0x01, 0x99, 0x12, 0x20))).toThrow(/unsupported multicodec/);
  });

  it("rejects an unsupported multihash code", () => {
    // version 1, raw codec, multihash code 0x09 (unknown single-byte varint), len 0
    expect(() => cidv1FromBytes(bytes(0x01, 0x55, 0x09, 0x00))).toThrow(/unsupported multihash code/);
  });
});

// ─── verifyCidV1 ────────────────────────────────────────────────────────────────

describe("verifyCidV1", () => {
  it("confirms a CID against its own content and rejects tampered content", async () => {
    const cid = await createCidV1(enc("attested payload"));
    expect(await verifyCidV1(enc("attested payload"), cid)).toBe(true);
    expect(await verifyCidV1(enc("attested paylo@d"), cid)).toBe(false);
  });

  it("rejects when the expected CID uses a different codec for the same bytes", async () => {
    const rawCid = await createCidV1(enc("same bytes"), { codec: "raw" });
    const dagCid = await createCidV1(enc("same bytes"), { codec: "dag-cbor" });
    // same content+digest but different codec → different cid bytes → not equal
    expect(await verifyCidV1(enc("same bytes"), { ...rawCid, codec: dagCid.codec, bytes: dagCid.bytes } as CIDv1)).toBe(true);
    expect(await verifyCidV1(enc("same bytes"), { ...rawCid, bytes: dagCid.bytes } as CIDv1)).toBe(false);
  });
});
