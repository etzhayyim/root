import { readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";
import type { KgEdgeRecord, KgNodeRecord, KgProjection } from "../types.js";

const FROZEN_TIMESTAMP = "2026-05-19T00:00:00.000Z";

interface LexiconFile {
  lexicon?: number;
  id?: string;
  description?: string;
  defs?: Record<string, unknown>;
}

async function walk(dir: string): Promise<string[]> {
  const out: string[] = [];
  const entries = await readdir(dir, { withFileTypes: true });
  for (const ent of entries.sort((a, b) => a.name.localeCompare(b.name))) {
    const full = join(dir, ent.name);
    if (ent.isDirectory()) {
      if (ent.name === "_archive" || ent.name === "archive") continue;
      out.push(...(await walk(full)));
    } else if (ent.isFile() && ent.name.endsWith(".json")) {
      out.push(full);
    }
  }
  return out;
}

/**
 * Strip "#defName" fragment from a Lexicon ref string. Returns the NSID alone.
 */
function refTargetNsid(ref: string): string {
  const hash = ref.indexOf("#");
  return hash >= 0 ? ref.slice(0, hash) : ref;
}

/**
 * Walk a lexicon's defs tree and collect every external ref target NSID.
 * Skips local refs (leading "#") and self-refs.
 */
function collectRefs(value: unknown, selfId: string, out: Set<string>): void {
  if (value === null) return;
  if (Array.isArray(value)) {
    for (const item of value) collectRefs(item, selfId, out);
    return;
  }
  if (typeof value !== "object") return;
  const obj = value as Record<string, unknown>;

  const type = typeof obj.type === "string" ? (obj.type as string) : undefined;

  if (type === "ref" && typeof obj.ref === "string") {
    if (!obj.ref.startsWith("#")) {
      const nsid = refTargetNsid(obj.ref);
      if (nsid && nsid !== selfId) out.add(nsid);
    }
  } else if (type === "union" && Array.isArray(obj.refs)) {
    for (const r of obj.refs) {
      if (typeof r === "string" && !r.startsWith("#")) {
        const nsid = refTargetNsid(r);
        if (nsid && nsid !== selfId) out.add(nsid);
      }
    }
  }

  for (const v of Object.values(obj)) collectRefs(v, selfId, out);
}

export async function projectLexicons(repoRoot: string): Promise<KgProjection> {
  const root = join(repoRoot, "00-contracts", "lexicons");
  try {
    await stat(root);
  } catch {
    return { nodes: [], edges: [] };
  }
  const files = await walk(root);

  const nodes: KgNodeRecord[] = [];
  const edges: KgEdgeRecord[] = [];
  const seenIds = new Set<string>();
  /** target NSID → edges referencing it (used to materialize external-lexicon nodes) */
  const referencedNsids = new Set<string>();

  for (const path of files) {
    let parsed: LexiconFile;
    try {
      parsed = JSON.parse(await readFile(path, "utf8"));
    } catch {
      continue;
    }
    if (parsed.lexicon !== 1 || typeof parsed.id !== "string") continue;
    if (seenIds.has(parsed.id)) continue;
    seenIds.add(parsed.id);

    const id = parsed.id;
    const ns = id.split(".").slice(0, 2).join(".");
    const mainDef = (parsed.defs?.main as { type?: string } | undefined) ?? undefined;
    const tags = [`ns:${ns}`];
    if (mainDef?.type) tags.push(`def:${mainDef.type}`);

    nodes.push({
      $type: "com.etzhayyim.kg.node",
      nodeId: `lexicon:${id}`,
      nodeType: "lexicon",
      label: id,
      summary: parsed.description ? parsed.description.slice(0, 2048) : undefined,
      tags,
      source: "lexicon-refs",
      createdAt: FROZEN_TIMESTAMP,
    });

    const refsForFile = new Set<string>();
    collectRefs(parsed.defs, id, refsForFile);
    const sortedRefs = [...refsForFile].sort();
    for (const target of sortedRefs) {
      referencedNsids.add(target);
      edges.push({
        $type: "com.etzhayyim.kg.edge",
        subject: `lexicon:${id}`,
        predicate: "uses-lexicon",
        object: `lexicon:${target}`,
        context: `lexicon:${id}`,
        createdAt: FROZEN_TIMESTAMP,
      });
    }
  }

  // Synthesize external-lexicon nodes for ref targets not present in-repo so
  // every edge has both endpoints anchored in the node set.
  const sortedExternal = [...referencedNsids].filter((n) => !seenIds.has(n)).sort();
  for (const nsid of sortedExternal) {
    const ns = nsid.split(".").slice(0, 2).join(".");
    nodes.push({
      $type: "com.etzhayyim.kg.node",
      nodeId: `lexicon:${nsid}`,
      nodeType: "lexicon",
      label: nsid,
      tags: [`ns:${ns}`, "external"],
      source: "lexicon-refs",
      createdAt: FROZEN_TIMESTAMP,
    });
  }

  return { nodes, edges };
}
