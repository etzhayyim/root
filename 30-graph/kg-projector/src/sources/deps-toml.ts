import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { parse as parseToml } from "smol-toml";
import type { KgEdgeRecord, KgNodeRecord, KgProjection } from "../types.js";

const FROZEN_TIMESTAMP = "2026-05-19T00:00:00.000Z";

interface DepsToml {
  platform?: {
    operating_entity?: Record<string, unknown>;
    l2?: {
      anchor_contract?: Record<string, unknown>;
      paymaster?: Record<string, unknown>;
      membership_contract?: Record<string, unknown>;
      [k: string]: unknown;
    };
  };
}

function asString(v: unknown): string | undefined {
  return typeof v === "string" && v.length > 0 ? v : undefined;
}

function adrUrn(rawId: string | undefined): string | undefined {
  if (!rawId) return undefined;
  const m = rawId.match(/^(?:adr-)?(\d{10})/);
  if (m) return `urn:adr:${m[1]}`;
  return `urn:adr:${rawId}`;
}

function l2ContractNode(
  key: string,
  contract: Record<string, unknown> | undefined,
): { node?: KgNodeRecord; adrEdges: KgEdgeRecord[]; sourceEdges: KgEdgeRecord[] } {
  if (!contract) return { adrEdges: [], sourceEdges: [] };
  const nodeId = `etzhayyim:l2-contract:${key}`;
  const tags: string[] = [`role:${key}`];
  const status = asString(contract.deploy_status);
  if (status) tags.push(`status:${status}`);
  const node: KgNodeRecord = {
    $type: "com.etzhayyim.kg.node",
    nodeId,
    nodeType: "l2-contract",
    label: key,
    summary: asString(contract.source) ? `Source: ${asString(contract.source)}` : undefined,
    tags,
    source: "deps.toml",
    createdAt: FROZEN_TIMESTAMP,
  };
  const adrEdges: KgEdgeRecord[] = [];
  const adr = adrUrn(asString(contract.adr));
  if (adr) {
    adrEdges.push({
      $type: "com.etzhayyim.kg.edge",
      subject: nodeId,
      predicate: "specified-by",
      object: adr,
      context: "deps.toml",
      createdAt: FROZEN_TIMESTAMP,
    });
  }
  const sourceEdges: KgEdgeRecord[] = [];
  const src = asString(contract.source);
  if (src) {
    sourceEdges.push({
      $type: "com.etzhayyim.kg.edge",
      subject: nodeId,
      predicate: "source-path",
      literal: src,
      context: "deps.toml",
      createdAt: FROZEN_TIMESTAMP,
    });
  }
  return { node, adrEdges, sourceEdges };
}

export async function projectDepsToml(repoRoot: string): Promise<KgProjection> {
  const raw = await readFile(join(repoRoot, "deps.toml"), "utf8");
  const parsed = parseToml(raw) as DepsToml;
  const nodes: KgNodeRecord[] = [];
  const edges: KgEdgeRecord[] = [];

  // Operating-entity node.
  const oe = parsed.platform?.operating_entity;
  if (oe) {
    const did = asString(oe.did);
    const orgNodeId = did ?? "etzhayyim:org:etzhayyim";
    const tags: string[] = ["role:operating-entity"];
    const form = asString(oe.form);
    if (form) tags.push(`form:${form}`);
    nodes.push({
      $type: "com.etzhayyim.kg.node",
      nodeId: orgNodeId,
      nodeType: "organization",
      label: asString(oe.name) ?? "etzhayyim",
      summary: asString(oe.form_en),
      tags,
      source: "deps.toml",
      createdAt: FROZEN_TIMESTAMP,
    });

    const domain = asString(oe.domain);
    if (domain) {
      edges.push({
        $type: "com.etzhayyim.kg.edge",
        subject: orgNodeId,
        predicate: "owns-domain",
        literal: domain,
        context: "deps.toml",
        createdAt: FROZEN_TIMESTAMP,
      });
    }

    // L2 contracts.
    const l2 = parsed.platform?.l2 ?? {};
    for (const key of ["anchor_contract", "paymaster", "membership_contract"] as const) {
      const ctx = l2[key] as Record<string, unknown> | undefined;
      const { node, adrEdges, sourceEdges } = l2ContractNode(key, ctx);
      if (!node) continue;
      nodes.push(node);
      edges.push(...adrEdges, ...sourceEdges);
      edges.push({
        $type: "com.etzhayyim.kg.edge",
        subject: orgNodeId,
        predicate: "owns",
        object: node.nodeId,
        context: "deps.toml",
        createdAt: FROZEN_TIMESTAMP,
      });
    }
  }

  return { nodes, edges };
}
