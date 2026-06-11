/**
 * kg-projector — emit + rkey tests (coverage loop iteration 16).
 *
 * kg-projector content-addresses repo artefacts into knowledge-graph
 * node/edge records. Its whole correctness contract is DETERMINISM +
 * IDEMPOTENCY: the same projection must always produce the same rkeys,
 * canonical bodies, and content_hash, and a collision must be loud. 861 LoC,
 * zero tests before. (Package is outside the pnpm workspace → its own lock.)
 */
import { describe, it, expect } from "vitest";
import { deterministicRkey, sha256Hex } from "../src/rkey.js";
import {
  nodeCanonicalKey,
  edgeCanonicalKey,
  rkeyFor,
  buildManifest,
} from "../src/emit.js";
import { mergeProjections, emptyProjection } from "../src/types.js";
import type { KgNodeRecord, KgEdgeRecord } from "../src/types.js";

const TID_ALPHABET = /^[234567a-z]{13}$/;

function node(nodeId: string, nodeType = "actor", source: KgNodeRecord["source"] = "deps.toml"): KgNodeRecord {
  return { $type: "com.etzhayyim.kg.node", nodeId, nodeType, source, createdAt: "2026-05-19T00:00:00.000Z" };
}
function edge(subject: string, predicate: string, object?: string, literal?: string): KgEdgeRecord {
  return { $type: "com.etzhayyim.kg.edge", subject, predicate, object, literal, createdAt: "2026-05-19T00:00:00.000Z" };
}

// ── deterministicRkey ────────────────────────────────────────────────────────

describe("deterministicRkey", () => {
  it("is deterministic, 13 chars, TID alphabet", () => {
    const r = deterministicRkey("node|actor|alpha");
    expect(r).toBe(deterministicRkey("node|actor|alpha"));
    expect(r).toMatch(TID_ALPHABET);
    expect(r.length).toBe(13);
  });

  it("is sensitive to its input", () => {
    expect(deterministicRkey("a")).not.toBe(deterministicRkey("b"));
  });
});

describe("sha256Hex", () => {
  it("matches a known SHA-256 digest", () => {
    expect(sha256Hex("abc")).toBe(
      "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    );
  });
});

// ── canonical keys ───────────────────────────────────────────────────────────

describe("canonical keys", () => {
  it("node key = node|<type>|<id>", () => {
    expect(nodeCanonicalKey(node("alpha", "actor"))).toBe("node|actor|alpha");
  });

  it("edge key uses object, or lit:<literal> when no object", () => {
    expect(edgeCanonicalKey(edge("s", "p", "o"))).toBe("edge|s|p|o");
    expect(edgeCanonicalKey(edge("s", "p", undefined, "v"))).toBe("edge|s|p|lit:v");
    expect(edgeCanonicalKey(edge("s", "p"))).toBe("edge|s|p|");
  });

  it("rkeyFor routes node vs edge through the right canonical key", () => {
    expect(rkeyFor(node("alpha"))).toBe(deterministicRkey(nodeCanonicalKey(node("alpha"))));
    expect(rkeyFor(edge("s", "p", "o"))).toBe(deterministicRkey(edgeCanonicalKey(edge("s", "p", "o"))));
  });
});

// ── buildManifest ────────────────────────────────────────────────────────────

describe("buildManifest", () => {
  const proj = {
    nodes: [node("alpha", "actor", "deps.toml"), node("beta", "actor", "adr-frontmatter")],
    edges: [edge("alpha", "depends-on", "beta")],
  };

  it("counts nodes/edges and per-source, and frames a sorted bundle", () => {
    const { manifest, files } = buildManifest(proj);
    expect(manifest.node_count).toBe(2);
    expect(manifest.edge_count).toBe(1);
    expect(manifest.source_counts).toEqual({ "deps.toml": 1, "adr-frontmatter": 1 });
    expect(files.has("bundle.jsonl")).toBe(true);
    // one node file + one edge file + bundle
    expect([...files.keys()].filter((k) => k.startsWith("nodes/")).length).toBe(2);
    expect([...files.keys()].filter((k) => k.startsWith("edges/")).length).toBe(1);
  });

  it("content_hash is stable across runs and order-independent", () => {
    const a = buildManifest(proj).manifest.content_hash;
    const b = buildManifest(proj).manifest.content_hash;
    expect(a).toBe(b);
    // shuffling input order must not change the hash (lines are sorted)
    const shuffled = { nodes: [proj.nodes[1], proj.nodes[0]], edges: proj.edges };
    expect(buildManifest(shuffled).manifest.content_hash).toBe(a);
  });

  it("content_hash changes when a record changes", () => {
    const base = buildManifest(proj).manifest.content_hash;
    const changed = { ...proj, nodes: [node("alpha", "actor"), node("gamma", "actor")] };
    expect(buildManifest(changed).manifest.content_hash).not.toBe(base);
  });

  it("canonical bodies have sorted keys and drop undefined fields", () => {
    const { files } = buildManifest({ nodes: [], edges: [edge("s", "p", "o")] });
    const body = [...files.entries()].find(([k]) => k.startsWith("edges/"))![1];
    // literal is undefined → must not appear; keys sorted alphabetically
    expect(body).not.toContain("literal");
    const parsed = JSON.parse(body);
    expect(Object.keys(parsed)).toEqual([...Object.keys(parsed)].sort());
  });

  it("throws loudly on a node rkey collision (same canonical key twice)", () => {
    const dup = { nodes: [node("x", "actor"), node("x", "actor")], edges: [] };
    expect(() => buildManifest(dup)).toThrow(/collision/);
  });
});

// ── projection helpers ───────────────────────────────────────────────────────

describe("mergeProjections / emptyProjection", () => {
  it("emptyProjection is empty; merge concatenates nodes and edges", () => {
    expect(emptyProjection()).toEqual({ nodes: [], edges: [] });
    const merged = mergeProjections(
      { nodes: [node("a")], edges: [] },
      { nodes: [node("b")], edges: [edge("a", "p", "b")] },
    );
    expect(merged.nodes.map((n) => n.nodeId)).toEqual(["a", "b"]);
    expect(merged.edges).toHaveLength(1);
  });
});
