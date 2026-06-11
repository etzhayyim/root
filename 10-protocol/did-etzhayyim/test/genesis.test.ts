/**
 * Spec compliance tests for did:etzhayyim (ADR-0029).
 *
 * Run: pnpm -F @etzhayyim/did-etzhayyim test
 */

import { describe, it, expect } from "vitest";
import {
  createGenesis,
  verifyGenesis,
  isValidDidetzhayyim,
  didDepth,
  didParent,
  didRoot,
  buildDidDocumentFromGenesis,
  encodeCanonicalCbor,
  createCidV1,
  cidv1ToString,
  DID_etzhayyim_PREFIX,
  MAX_PATH_DEPTH,
} from "../src/index";

const SAMPLE_VM = [{
  id: "#key-1" as const,
  type: "Multikey" as const,
  publicKeyMultibase: "zDnaerDaTF5BXEavCrfRZEk316dpbLsfPDZ3WJ5hRTPFU2169",
}];

describe("did:etzhayyim genesis", () => {
  it("creates a root DID with did:etzhayyim: prefix and bafkrei... CID", async () => {
    const g = await createGenesis({
      type: "root",
      vm: SAMPLE_VM,
      createdAt: "2026-04-17T00:00:00Z",
    });
    expect(g.did.startsWith(DID_etzhayyim_PREFIX)).toBe(true);
    // genesis.ts builds the CID with the RAW codec (0x55), not dag-cbor (0x71),
    // so the base32 multibase string is "bafkrei…" not "bafy…":
    // multibase 'b' + version 0x01 + codec 0x55 + sha2-256 multihash 0x12 0x20
    // → base32(0x01 0x55 0x12 0x20 …) = "bafkrei…"
    expect(g.did.startsWith("did:etzhayyim:bafk")).toBe(true);
    expect(g.did).toMatch(/^did:etzhayyim:bafkrei[a-z2-7]+$/);
    expect(g.depth).toBe(0);
    expect(g.parent).toBeNull();
    expect(g.segment).toBeNull();
  });

  it("genesis op verification round-trips", async () => {
    const g = await createGenesis({
      type: "root",
      vm: SAMPLE_VM,
      createdAt: "2026-04-17T00:00:00Z",
    });
    const verified = await verifyGenesis(g.did, g.op);
    expect(verified).toBe(true);
  });

  it("creates a child DID nested under parent and verifies", async () => {
    const root = await createGenesis({
      type: "root",
      vm: SAMPLE_VM,
      createdAt: "2026-04-17T00:00:00Z",
    });
    const child = await createGenesis({
      type: "child",
      parent: root.did,
      segment: "wiki:1968_flu_pandemic",
      vm: SAMPLE_VM,
      createdAt: "2026-04-17T00:01:00Z",
    });
    expect(child.did.startsWith(root.did + ":")).toBe(true);
    expect(child.depth).toBe(1);
    expect(didParent(child.did)).toBe(root.did);
    expect(didRoot(child.did)).toBe(root.did);
    const verified = await verifyGenesis(child.did, child.op);
    expect(verified).toBe(true);
  });

  it("rejects depth beyond MAX_PATH_DEPTH", async () => {
    let parent = (await createGenesis({
      type: "root", vm: SAMPLE_VM, createdAt: "2026-04-17T00:00:00Z",
    })).did;
    for (let i = 0; i < MAX_PATH_DEPTH; i += 1) {
      const next = await createGenesis({
        type: "child", parent, segment: `s${i}`, vm: SAMPLE_VM, createdAt: "2026-04-17T00:00:00Z",
      });
      parent = next.did;
    }
    await expect(createGenesis({
      type: "child", parent, segment: "overflow", vm: SAMPLE_VM, createdAt: "2026-04-17T00:00:00Z",
    })).rejects.toThrow(/MAX_PATH_DEPTH/);
  });

  it("isValidDidetzhayyim accepts well-formed and rejects malformed", () => {
    expect(isValidDidetzhayyim("did:etzhayyim:bafkreiabcdef")).toBe(true);
    expect(isValidDidetzhayyim("did:etzhayyim:bafkreiabcdef:bafkreichild")).toBe(true);
    expect(isValidDidetzhayyim("did:plc:abcdef")).toBe(false);
    expect(isValidDidetzhayyim("did:etzhayyim:")).toBe(false);
    expect(isValidDidetzhayyim("did:etzhayyim:has space")).toBe(false);
  });

  it("DID Document is W3C DID Core conformant (no proprietary top-level fields)", async () => {
    const g = await createGenesis({
      type: "root",
      vm: SAMPLE_VM,
      alsoKnownAs: ["at://example.etzhayyim.com", "did:web:example.etzhayyim.com"],
      createdAt: "2026-04-17T00:00:00Z",
    });
    const doc = buildDidDocumentFromGenesis(g);
    const allowed = new Set([
      "@context", "id", "controller", "verificationMethod",
      "authentication", "assertionMethod", "capabilityInvocation",
      "capabilityDelegation", "keyAgreement", "alsoKnownAs", "service",
      "deactivated",
    ]);
    for (const k of Object.keys(doc)) {
      expect(allowed.has(k), `unexpected top-level key: ${k}`).toBe(true);
    }
    expect(doc.id).toBe(g.did);
    expect(doc.verificationMethod[0].publicKeyMultibase).toBe(SAMPLE_VM[0].publicKeyMultibase);
  });

  it("canonical CBOR is deterministic for re-ordered input", async () => {
    const a = encodeCanonicalCbor({ b: 1, a: 2 });
    const b = encodeCanonicalCbor({ a: 2, b: 1 });
    expect(a).toEqual(b);
  });

  it("CIDv1 string round-trip", async () => {
    const cid = await createCidV1(new TextEncoder().encode("hello"));
    const s = cidv1ToString(cid);
    expect(s.startsWith("bafkrei")).toBe(true);
  });
});
