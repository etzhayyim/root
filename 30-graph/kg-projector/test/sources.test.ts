/**
 * kg-projector — source-parser tests (coverage loop iteration 17).
 *
 * The three source parsers (deps.toml / ADR frontmatter / lexicon refs) turn
 * repo artefacts into KG nodes + edges and had no tests. Driven here through
 * tmp-repo fixtures (FROZEN_TIMESTAMP makes the output fully deterministic).
 * Complements iter 16 (emit/rkey) — together the whole projector is covered.
 */
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtemp, mkdir, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";

import { projectDepsToml } from "../src/sources/deps-toml.js";
import { projectAdrs } from "../src/sources/adr.js";
import { projectLexicons } from "../src/sources/lexicon.js";

let repo: string;
beforeEach(async () => { repo = await mkdtemp(join(tmpdir(), "kgsrc-")); });
afterEach(async () => { await rm(repo, { recursive: true, force: true }); });

const ids = (ns: { nodeId: string }[]) => ns.map((n) => n.nodeId).sort();
const edgeKey = (e: any) => `${e.subject}|${e.predicate}|${e.object ?? "lit:" + e.literal}`;

// ── deps.toml ────────────────────────────────────────────────────────────────

describe("projectDepsToml", () => {
  it("emits the operating-entity org node, owns-domain edge, and L2 contracts", async () => {
    await writeFile(join(repo, "deps.toml"), `
[platform.operating_entity]
did = "did:web:etzhayyim.com"
name = "etzhayyim"
form = "religious-corp"
form_en = "Religious Corporation"
domain = "etzhayyim.com"

[platform.l2.anchor_contract]
deploy_status = "deployed"

[platform.l2.paymaster]
deploy_status = "planned"
`, "utf8");
    const { nodes, edges } = await projectDepsToml(repo);

    const org = nodes.find((n) => n.nodeType === "organization")!;
    expect(org.nodeId).toBe("did:web:etzhayyim.com");
    expect(org.label).toBe("etzhayyim");
    expect(org.tags).toContain("role:operating-entity");
    expect(org.tags).toContain("form:religious-corp");

    const keys = edges.map(edgeKey);
    expect(keys).toContain("did:web:etzhayyim.com|owns-domain|lit:etzhayyim.com");
    // both L2 contracts become nodes the org owns
    expect(ids(nodes)).toContain("etzhayyim:l2-contract:anchor_contract");
    expect(ids(nodes)).toContain("etzhayyim:l2-contract:paymaster");
    expect(keys).toContain("did:web:etzhayyim.com|owns|etzhayyim:l2-contract:anchor_contract");
  });

  it("yields nothing when operating_entity is absent", async () => {
    await writeFile(join(repo, "deps.toml"), `[other]\nx = 1\n`, "utf8");
    expect(await projectDepsToml(repo)).toEqual({ nodes: [], edges: [] });
  });
});

// ── ADR frontmatter ──────────────────────────────────────────────────────────

async function writeAdr(name: string, frontmatter: string) {
  const dir = join(repo, "90-docs", "adr");
  await mkdir(dir, { recursive: true });
  await writeFile(join(dir, name), `---\n${frontmatter}\n---\n\n# body\n`, "utf8");
}

describe("projectAdrs", () => {
  it("projects frontmatter into an adr node + relationship edges", async () => {
    await writeAdr("2606111300-pq.md", [
      "id: adr-2606111300",
      'title: "ADR-2606111300: pqh-v1"',
      "status: accepted",
      "doc_type: adr",
      "authoritative: true",
      "depends_on:\n  - adr-2605181100",
      "related:\n  - adr-2605231525",
      "authoritative_for:\n  - the pq hybrid suite",
    ].join("\n"));

    const { nodes, edges } = await projectAdrs(repo);
    const adr = nodes.find((n) => n.nodeType === "adr")!;
    expect(adr.nodeId).toBe("urn:adr:2606111300");
    expect(adr.label).toContain("pqh-v1");
    expect(adr.tags).toContain("status:accepted");
    expect(adr.tags).toContain("authoritative");

    const keys = edges.map(edgeKey);
    expect(keys).toContain("urn:adr:2606111300|depends_on|urn:adr:2605181100");
    expect(keys).toContain("urn:adr:2606111300|related|urn:adr:2605231525");
    expect(keys).toContain("urn:adr:2606111300|authoritative-for|lit:the pq hybrid suite");
  });

  it("skips template.md and README.md", async () => {
    await writeAdr("template.md", "id: adr-template\ntitle: t");
    await writeAdr("README.md", "id: adr-readme\ntitle: r");
    await writeAdr("2606010000-real.md", "id: adr-2606010000\ntitle: real");
    const { nodes } = await projectAdrs(repo);
    expect(ids(nodes)).toEqual(["urn:adr:2606010000"]);
  });
});

// ── lexicon refs ─────────────────────────────────────────────────────────────

async function writeLexicon(relPath: string, doc: unknown) {
  const full = join(repo, "00-contracts", "lexicons", relPath);
  await mkdir(join(full, ".."), { recursive: true });
  await writeFile(full, JSON.stringify(doc), "utf8");
}

describe("projectLexicons", () => {
  it("emits a lexicon node, uses-lexicon edges, and synthesizes external ref nodes", async () => {
    await writeLexicon("com/example/a.json", {
      lexicon: 1, id: "com.example.a", description: "A",
      defs: { main: { type: "record", record: { type: "object", properties: {
        ref1: { type: "ref", ref: "com.example.b#thing" },
        u: { type: "union", refs: ["com.external.c", "#localSkip"] },
        self: { type: "ref", ref: "com.example.a#x" },
      } } } },
    });
    await writeLexicon("com/example/b.json", { lexicon: 1, id: "com.example.b", defs: { main: { type: "object" } } });

    const { nodes, edges } = await projectLexicons(repo);
    const node = nodes.find((n) => n.nodeId === "lexicon:com.example.a")!;
    expect(node.nodeType).toBe("lexicon");
    expect(node.tags).toContain("ns:com.example");
    expect(node.tags).toContain("def:record");

    const keys = edges.map(edgeKey);
    expect(keys).toContain("lexicon:com.example.a|uses-lexicon|lexicon:com.example.b"); // # fragment stripped
    expect(keys).toContain("lexicon:com.example.a|uses-lexicon|lexicon:com.external.c");
    expect(keys).not.toContain("lexicon:com.example.a|uses-lexicon|lexicon:com.example.a"); // self-ref skipped
    // local "#localSkip" ref is skipped entirely (no edge)
    expect(keys.some((k) => k.includes("localSkip"))).toBe(false);

    // com.external.c is referenced but not in-repo → synthesized external node
    const ext = nodes.find((n) => n.nodeId === "lexicon:com.external.c")!;
    expect(ext.tags).toContain("external");
    // com.example.b IS in-repo → not marked external
    const internalB = nodes.find((n) => n.nodeId === "lexicon:com.example.b")!;
    expect(internalB.tags).not.toContain("external");
  });

  it("returns empty when the lexicons dir is absent, and skips _archive + non-lexicon json", async () => {
    expect(await projectLexicons(repo)).toEqual({ nodes: [], edges: [] });

    await writeLexicon("com/x/real.json", { lexicon: 1, id: "com.x.real", defs: {} });
    await writeLexicon("com/x/_archive/old.json", { lexicon: 1, id: "com.x.old", defs: {} });
    await writeLexicon("com/x/notlex.json", { id: "com.x.notlex" }); // no lexicon:1
    const { nodes } = await projectLexicons(repo);
    expect(ids(nodes)).toEqual(["lexicon:com.x.real"]);
  });
});
