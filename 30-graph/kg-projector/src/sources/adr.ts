import { readdir, readFile } from "node:fs/promises";
import { basename, join } from "node:path";
import { parse as parseYaml } from "yaml";
import type { KgEdgeRecord, KgNodeRecord, KgProjection } from "../types.js";

const FROZEN_TIMESTAMP = "2026-05-19T00:00:00.000Z";

interface AdrFrontMatter {
  id: string;
  title: string;
  status?: string;
  doc_type?: string;
  topic?: string;
  authoritative?: boolean;
  last_verified?: string;
  authoritative_for?: string[];
  depends_on?: string[];
  related?: (string | null)[];
  supersedes?: string[];
  superseded_by?: string[];
  axis?: string;
  weight?: number;
}

/**
 * Convert ADR id (front-matter `id:`) into a stable URN nodeId.
 *
 * Examples:
 *   "adr-2605190900-kg-as-lexicon-…" → "urn:adr:2605190900-kg-as-lexicon-…"
 *   "2605171300"                     → "urn:adr:2605171300"
 *   "2605182312-local-bring-up-…"    → "urn:adr:2605182312-local-bring-up-…"
 *
 * Two ADRs sharing the same minute-prefix (e.g. 2605172800) get distinct URNs
 * because the topic slug is preserved. Tolerates YAML number coercion of
 * digit-only ids.
 */
function adrUrn(rawId: unknown): string {
  let s = String(rawId).trim();
  if (s.startsWith("adr-")) s = s.slice(4);
  return `urn:adr:${s}`;
}

async function readAdrFile(path: string): Promise<AdrFrontMatter | null> {
  const raw = await readFile(path, "utf8");
  if (!raw.startsWith("---")) return null;
  const end = raw.indexOf("\n---", 3);
  if (end < 0) return null;
  const fmText = raw.slice(3, end).replace(/^\n/, "");
  let fm: unknown;
  try {
    fm = parseYaml(fmText);
  } catch (err) {
    console.warn(`[kg-projector] skip ${basename(path)}: yaml parse error: ${(err as Error).message}`);
    return null;
  }
  if (!fm || typeof fm !== "object") return null;
  const obj = fm as AdrFrontMatter;
  if (obj.id === undefined || obj.id === null || !obj.title) return null;
  return obj;
}

function cleanRefs(refs: (string | null | undefined)[] | undefined): string[] {
  if (!refs) return [];
  return refs
    .filter((s): s is string => typeof s === "string" && s.trim().length > 0)
    .map((s) => s.trim());
}

function isAdrId(s: string): boolean {
  return /^adr-\d{10}/.test(s) || /^\d{10}/.test(s);
}

function refToObject(ref: string): string {
  // ADR ID → urn:adr:<id>; otherwise treat as opaque nodeId.
  if (isAdrId(ref)) return adrUrn(ref);
  return ref;
}

export async function projectAdrs(repoRoot: string): Promise<KgProjection> {
  const adrDir = join(repoRoot, "90-docs", "adr");
  const entries = await readdir(adrDir);
  const files = entries
    .filter((f) => f.endsWith(".md") && f !== "template.md" && f !== "README.md")
    .sort();

  const nodes: KgNodeRecord[] = [];
  const edges: KgEdgeRecord[] = [];

  for (const file of files) {
    const path = join(adrDir, file);
    const fm = await readAdrFile(path);
    if (!fm) continue;

    const nodeId = adrUrn(fm.id);
    const tags: string[] = [];
    if (fm.status) tags.push(`status:${fm.status}`);
    if (fm.doc_type) tags.push(`doc_type:${fm.doc_type}`);
    if (fm.axis) tags.push(`axis:${fm.axis}`);
    if (fm.authoritative) tags.push("authoritative");

    nodes.push({
      $type: "com.etzhayyim.kg.node",
      nodeId,
      nodeType: "adr",
      label: fm.title.slice(0, 256),
      tags: tags.length ? tags : undefined,
      source: "adr-frontmatter",
      createdAt: FROZEN_TIMESTAMP,
    });

    const predicates: Array<[string, string[]]> = [
      ["depends_on", cleanRefs(fm.depends_on)],
      ["related", cleanRefs(fm.related)],
      ["supersedes", cleanRefs(fm.supersedes)],
      ["superseded_by", cleanRefs(fm.superseded_by)],
    ];
    for (const [predicate, refs] of predicates) {
      for (const ref of refs) {
        edges.push({
          $type: "com.etzhayyim.kg.edge",
          subject: nodeId,
          predicate,
          object: refToObject(ref),
          context: nodeId,
          createdAt: FROZEN_TIMESTAMP,
        });
      }
    }

    for (const lit of cleanRefs(fm.authoritative_for)) {
      edges.push({
        $type: "com.etzhayyim.kg.edge",
        subject: nodeId,
        predicate: "authoritative-for",
        literal: lit.slice(0, 1024),
        context: nodeId,
        createdAt: FROZEN_TIMESTAMP,
      });
    }
  }

  return { nodes, edges };
}
