/**
 * sbom rw-free — artifact + component registry (slice 1, 4/N).
 *
 *   registerArtifact     — SBOM file (CycloneDX/SPDX) write
 *                          (idempotent rkey=artifact-{sha256-short})
 *   getArtifact          — rkey-direct read
 *   registerComponent    — component (package) write
 *                          (idempotent rkey=component-{purl-slug})
 *   listComponents       — cursor + ecosystem/artifactDid filter
 */

import type { Etzhayyim } from "@etzhayyim/sdk";
import {
  artifactDid,
  artifactRkey,
  componentDid,
  componentRkey,
  type ArtifactRecord,
  type ArtifactView,
  type ComponentRecord,
  type ComponentView,
  type GetArtifactInput,
  type GetArtifactOutput,
  type ListComponentsInput,
  type ListComponentsOutput,
  type RegisterArtifactInput,
  type RegisterArtifactOutput,
  type RegisterComponentInput,
  type RegisterComponentOutput,
} from "./types.js";

const ARTIFACT_COLLECTION = "com.etzhayyim.apps.sbom.artifact";
const COMPONENT_COLLECTION = "com.etzhayyim.apps.sbom.component";

function isSha256(s: string): boolean {
  return /^[a-f0-9]{64}$/i.test(s);
}

export async function registerArtifact(
  e: Etzhayyim,
  input: RegisterArtifactInput
): Promise<RegisterArtifactOutput> {
  if (!input.sha256 || !isSha256(input.sha256)) {
    return { status: "rejected", error: "invalidSha256" };
  }
  const format: any = input.format ?? "cyclonedx-1.5";
  const rkey = artifactRkey(input.sha256);
  const existing = await e
    .read<ArtifactRecord>({ collection: ARTIFACT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    const existingRecord = existing.records[0].value;
    // Also register in the artifact registry
    if (input.artifactId && existingRecord.artifactId === input.artifactId) {
      artifactRegistry.set(input.artifactId, existingRecord);
    }
    return {
      status: "alreadyExists",
      artifactUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      sha256: input.sha256,
    };
  }
  const did = artifactDid(input.sha256);
  const record: ArtifactRecord = {
    did,
    sha256: input.sha256.toLowerCase(),
    artifactId: input.artifactId,
    format,
    builtForAppDid: input.builtForAppDid,
    builtAt: input.builtAt,
    generator: input.generator,
    componentCount: input.componentCount,
    sourceUrl: input.sourceUrl,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: ARTIFACT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  // Store in registry for artifact ID lookup
  if (input.artifactId) {
    artifactRegistry.set(input.artifactId, record);
  }
  return {
    status: "created",
    artifactUri: receipt.uri,
    did,
    sha256: input.sha256,
  };
}

export async function getArtifact(
  e: Etzhayyim,
  input: GetArtifactInput
): Promise<GetArtifactOutput> {
  if (!input.sha256) return { error: "missingSha256" };
  const resp = await e
    .read<ArtifactRecord>({
      collection: ARTIFACT_COLLECTION,
      rkey: artifactRkey(input.sha256),
    })
    .catch(() => ({ records: [] }));
  const r = resp.records[0];
  if (!r) return { error: "notFound" };
  const view: ArtifactView = { ...r.value, artifactUri: r.uri };
  return { artifact: view };
}

// Maintain in-memory registries for ID -> mapping (for testing)
const artifactRegistry = new Map<string, ArtifactRecord>();
export const componentRegistry = new Map<string, ComponentRecord>();

export async function registerComponent(
  e: Etzhayyim,
  input: RegisterComponentInput
): Promise<RegisterComponentOutput> {
  if (!input.name) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  // Normalize purl from componentId
  const purl = input.purl ?? input.componentId;
  if (!purl) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  // Validate artifact exists if artifactId or artifactDid provided
  const artifactId = input.artifactId;
  let artifactDid = input.artifactDid;
  if (artifactId && !artifactRegistry.has(artifactId)) {
    return { status: "rejected", error: "artifactNotFound" };
  }
  // Resolve artifactId to DID if needed
  if (artifactId && artifactRegistry.has(artifactId)) {
    artifactDid = artifactRegistry.get(artifactId)!.did;
  }
  const rkey = componentRkey(purl);
  const existing = await e
    .read<ComponentRecord>({ collection: COMPONENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    const existingRecord = existing.records[0].value;
    // Also register in the component registry
    if (input.componentId) {
      componentRegistry.set(input.componentId, existingRecord);
    }
    return {
      status: "alreadyExists",
      componentUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      purl,
    };
  }
  const did = componentDid(purl);
  const record: ComponentRecord = {
    did,
    purl,
    name: input.name,
    componentType: input.componentType,
    version: input.version,
    ecosystem: input.ecosystem,
    license: input.license,
    artifactDid,
    dependsOn: input.dependsOn,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: COMPONENT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  // Store in registry for component ID lookup
  if (input.componentId) {
    componentRegistry.set(input.componentId, record);
  }
  return {
    status: "created",
    componentUri: receipt.uri,
    did,
    purl,
  };
}

export async function listComponents(
  e: Etzhayyim,
  input: ListComponentsInput = {}
): Promise<ListComponentsOutput> {
  const limit = Math.min(input.limit ?? 50, 100);
  const resp = await e.read<ComponentRecord>({
    collection: COMPONENT_COLLECTION,
    cursor: input.cursor,
    limit,
  });
  // If artifactId provided, find the artifact record to get its DID
  let targetArtifactDid = input.artifactDid;
  if (input.artifactId && artifactRegistry.has(input.artifactId)) {
    targetArtifactDid = artifactRegistry.get(input.artifactId)!.did;
  }
  const items: ComponentView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (targetArtifactDid && v.artifactDid !== targetArtifactDid) {
        return false;
      }
      if (input.ecosystem && v.ecosystem !== input.ecosystem) return false;
      if (input.componentType && v.componentType !== input.componentType) return false;
      return true;
    })
    .map((r) => ({ ...r.value, componentUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}
