import { mkdir, rm, writeFile, readdir, readFile, stat } from "node:fs/promises";
import { join } from "node:path";
import { deterministicRkey, sha256Hex } from "./rkey.js";
import type {
  KgEdgeRecord,
  KgNodeRecord,
  KgProjection,
  KgRecord,
} from "./types.js";

export interface Manifest {
  schema_version: 1;
  node_count: number;
  edge_count: number;
  source_counts: Record<string, number>;
  content_hash: string;
  /** Path (relative to out/) of the JSONL bundle: one record per line, sorted by rkey path. */
  bundle_path: string;
  generated_at: string;
}

const FROZEN_TIMESTAMP = "2026-05-19T00:00:00.000Z";

export function nodeCanonicalKey(rec: KgNodeRecord): string {
  return `node|${rec.nodeType}|${rec.nodeId}`;
}

export function edgeCanonicalKey(rec: KgEdgeRecord): string {
  const target = rec.object ?? (rec.literal !== undefined ? `lit:${rec.literal}` : "");
  return `edge|${rec.subject}|${rec.predicate}|${target}`;
}

export function rkeyFor(rec: KgRecord): string {
  if (rec.$type === "com.etzhayyim.kg.node") {
    return deterministicRkey(nodeCanonicalKey(rec));
  }
  return deterministicRkey(edgeCanonicalKey(rec));
}

function canonicalJson(rec: KgRecord): string {
  const obj = rec as unknown as Record<string, unknown>;
  const keys = Object.keys(obj).sort();
  const ordered: Record<string, unknown> = {};
  for (const k of keys) {
    const v = obj[k];
    if (v !== undefined) ordered[k] = v;
  }
  return JSON.stringify(ordered, null, 2) + "\n";
}

export function buildManifest(proj: KgProjection): {
  manifest: Manifest;
  files: Map<string, string>;
} {
  const files = new Map<string, string>();
  const seen = new Set<string>();
  const lines: string[] = [];

  for (const node of proj.nodes) {
    const rkey = rkeyFor(node);
    const path = `nodes/${rkey}.json`;
    if (seen.has(path)) {
      throw new Error(
        `kg-projector: rkey collision at ${path} for node ${node.nodeType}:${node.nodeId}`,
      );
    }
    seen.add(path);
    const body = canonicalJson(node);
    files.set(path, body);
    lines.push(`${path} ${sha256Hex(body)}`);
  }

  for (const edge of proj.edges) {
    const rkey = rkeyFor(edge);
    const path = `edges/${rkey}.json`;
    if (seen.has(path)) {
      throw new Error(
        `kg-projector: rkey collision at ${path} for edge ${edge.subject} ${edge.predicate} ${edge.object ?? edge.literal}`,
      );
    }
    seen.add(path);
    const body = canonicalJson(edge);
    files.set(path, body);
    lines.push(`${path} ${sha256Hex(body)}`);
  }

  lines.sort();
  const content_hash = sha256Hex(lines.join("\n"));

  // bundle.jsonl — every record on one line, sorted by rkey path so the
  // bundle bytes are deterministic and content_hash above stays meaningful
  // (the bundle is just a different framing of the same records).
  const bundleLines = [...files.entries()]
    .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
    .map(([, body]) => JSON.stringify(JSON.parse(body)));
  const bundle = bundleLines.join("\n") + "\n";
  files.set("bundle.jsonl", bundle);

  const source_counts: Record<string, number> = {};
  for (const n of proj.nodes) {
    source_counts[n.source] = (source_counts[n.source] ?? 0) + 1;
  }

  const manifest: Manifest = {
    schema_version: 1,
    node_count: proj.nodes.length,
    edge_count: proj.edges.length,
    source_counts,
    content_hash,
    bundle_path: "bundle.jsonl",
    generated_at: FROZEN_TIMESTAMP,
  };

  return { manifest, files };
}

export async function writeOut(
  outDir: string,
  proj: KgProjection,
): Promise<Manifest> {
  const { manifest, files } = buildManifest(proj);

  // Wipe then rewrite to ensure deletions propagate.
  await rm(outDir, { recursive: true, force: true });
  await mkdir(join(outDir, "nodes"), { recursive: true });
  await mkdir(join(outDir, "edges"), { recursive: true });

  for (const [relPath, body] of files) {
    await writeFile(join(outDir, relPath), body, "utf8");
  }
  await writeFile(
    join(outDir, "manifest.json"),
    JSON.stringify(manifest, null, 2) + "\n",
    "utf8",
  );

  return manifest;
}

export async function readManifest(outDir: string): Promise<Manifest | null> {
  try {
    const raw = await readFile(join(outDir, "manifest.json"), "utf8");
    return JSON.parse(raw) as Manifest;
  } catch (err) {
    if ((err as NodeJS.ErrnoException).code === "ENOENT") return null;
    throw err;
  }
}

export async function outDirExists(outDir: string): Promise<boolean> {
  try {
    const s = await stat(outDir);
    return s.isDirectory();
  } catch {
    return false;
  }
}

export async function diffAgainstExisting(
  outDir: string,
  proj: KgProjection,
): Promise<{ matches: boolean; fresh: Manifest; existing: Manifest | null }> {
  const { manifest: fresh, files } = buildManifest(proj);
  const existing = await readManifest(outDir);
  if (!existing) return { matches: false, fresh, existing: null };
  if (existing.content_hash !== fresh.content_hash)
    return { matches: false, fresh, existing };

  // Spot-check that on-disk files match the freshly serialized bodies.
  for (const [relPath, body] of files) {
    try {
      const onDisk = await readFile(join(outDir, relPath), "utf8");
      if (onDisk !== body) return { matches: false, fresh, existing };
    } catch {
      return { matches: false, fresh, existing };
    }
  }
  // Catch stray files not in fresh projection.
  const onDiskFiles = new Set<string>();
  for (const sub of ["nodes", "edges"]) {
    try {
      for (const f of await readdir(join(outDir, sub))) {
        onDiskFiles.add(`${sub}/${f}`);
      }
    } catch {
      /* directory may not exist yet */
    }
  }
  for (const path of onDiskFiles) {
    if (!files.has(path)) return { matches: false, fresh, existing };
  }

  return { matches: true, fresh, existing };
}
