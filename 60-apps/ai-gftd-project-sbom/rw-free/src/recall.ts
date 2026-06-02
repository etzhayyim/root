/**
 * sbom rw-free — recall + health tier (slice 5, +3 → 17/N).
 *
 *   recall    — Takata-style blast-radius for a supplier (software + vehicle BOMs).
 *               Given a supplier name (+ optional MPN + kind), returns every
 *               artifact whose components reference the supplier.
 *   updateComponentSupplier — augment a ComponentRecord with supplier_name + mpn
 *   health    — liveness check (no PDS scan; static response)
 *
 * The recall flow targets two parallel BOM contexts:
 *   - **software** — SbomComponent with supplier_name (vendor of a package)
 *   - **vehicle**  — SbomComponent representing a physical part (hardware BOM)
 *
 * Both live in the same component collection; the `kind` field on the
 * artifact distinguishes them. Phase 3 mst-projector adds a supplier
 * inverted index to push the post-fetch filter server-side.
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import { registerComponent } from "./artifactRegistry.js";
import {
  componentRkey,
  type ArtifactRecord,
  type ComponentRecord,
  type HealthOutput,
  type Purl,
  type RecallInput,
  type RecallMatch,
  type RecallOutput,
  type UpdateComponentSupplierInput,
  type UpdateComponentSupplierOutput,
} from "./types.js";

const ARTIFACT_COLLECTION = "com.etzhayyim.apps.sbom.artifact";
const COMPONENT_COLLECTION = "com.etzhayyim.apps.sbom.component";

const PAGE_LIMIT = 100;
const DEFAULT_MAX_SCAN = 10_000;

export async function recall(
  e: Etzhayyim,
  input: RecallInput
): Promise<RecallOutput> {
  if (!input.supplier) return { error: "missingSupplier" };
  const limit = Math.min(input.limit ?? 50, 500);
  const offset = input.offset ?? 0;
  const maxScan = Math.min(input.maxScan ?? DEFAULT_MAX_SCAN, DEFAULT_MAX_SCAN);

  // 1. Scan components matching supplier.
  const supplierLower = input.supplier.toLowerCase();
  const mpnLower = input.mpn?.toLowerCase();
  let cursor: string | undefined;
  let scanned = 0;
  const matchedComponents: ComponentRecord[] = [];
  while (scanned < maxScan) {
    const page = await e.read<ComponentRecord>({
      collection: COMPONENT_COLLECTION,
      cursor,
      limit: PAGE_LIMIT,
    });
    for (const r of page.records) {
      const v = r.value;
      if (v.supplierName?.toLowerCase() !== supplierLower) continue;
      if (mpnLower && v.supplierMpn?.toLowerCase() !== mpnLower) continue;
      matchedComponents.push(v);
    }
    scanned += page.records.length;
    if (!page.cursor || page.records.length < PAGE_LIMIT) break;
    cursor = page.cursor;
  }

  // 2. Group by artifact + optionally filter artifact kind.
  const byArtifact = new Map<string, ComponentRecord[]>();
  for (const c of matchedComponents) {
    if (!c.artifactDid) continue;
    const list = byArtifact.get(c.artifactDid) ?? [];
    list.push(c);
    byArtifact.set(c.artifactDid, list);
  }

  // 3. Fetch artifacts and (optionally) filter by kind.
  const matches: RecallMatch[] = [];
  for (const [artifactDid, components] of byArtifact) {
    // Read artifact via the embedded sha256-short in the DID's last segment.
    const segment = artifactDid.split(":").pop();
    if (!segment) continue;
    const artResp = await e
      .read<ArtifactRecord>({
        collection: ARTIFACT_COLLECTION,
        rkey: `artifact-${segment}`,
      })
      .catch(() => ({ records: [] }));
    const artifact = artResp.records[0];
    if (!artifact) continue;
    if (input.kind && artifact.value.kind && artifact.value.kind !== input.kind) {
      continue;
    }
    for (const c of components) {
      matches.push({
        artifactUri: artifact.uri,
        artifactDid,
        kind: artifact.value.kind,
        componentBomRef: c.purl,
        supplier: c.supplierName ?? input.supplier,
        mpn: c.supplierMpn,
        name: c.name,
        version: c.version,
      });
    }
  }

  const total = matches.length;
  const sliced = matches.slice(offset, offset + limit);
  return {
    matches: sliced,
    total,
    limit,
    offset,
    truncated: scanned >= maxScan,
  };
}

export async function updateComponentSupplier(
  e: Etzhayyim,
  input: UpdateComponentSupplierInput
): Promise<UpdateComponentSupplierOutput> {
  if (!input.purl || !input.supplierName) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = componentRkey(input.purl);
  const resp = await e
    .read<ComponentRecord>({ collection: COMPONENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  const existing = resp.records[0]?.value;
  if (!existing) return { status: "rejected", error: "componentNotFound" };
  // Re-register with supplier fields. The artifactRegistry registerComponent
  // returns alreadyExists for existing records — so we need a separate update
  // path. For now, the e.write() PDS layer overwrites by rkey; we re-emit a
  // full record with the supplier fields merged.
  const merged: ComponentRecord = {
    ...existing,
    supplierName: input.supplierName,
    supplierMpn: input.supplierMpn,
    supplierCountry: input.supplierCountry,
    supplierUpdatedAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: COMPONENT_COLLECTION,
    record: merged as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "updated",
    componentUri: receipt.uri,
    purl: input.purl as Purl,
  };
}

export async function health(): Promise<HealthOutput> {
  return {
    status: "ok",
    actor: "sbom",
    substrate: "etzhayyim",
    timestamp: new Date().toISOString(),
  };
}

// Tag registerComponent re-export — recall reads from the same collection.
export { registerComponent };
