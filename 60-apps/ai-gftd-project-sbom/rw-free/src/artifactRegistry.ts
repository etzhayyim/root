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

const ARTIFACT_COLLECTION = "ai.gftd.apps.sbom.artifact";
const COMPONENT_COLLECTION = "ai.gftd.apps.sbom.component";

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
  if (!input.format) {
    return { status: "rejected", error: "missingFormat" };
  }
  const rkey = artifactRkey(input.sha256);
  const existing = await e
    .read<ArtifactRecord>({ collection: ARTIFACT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
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
    format: input.format,
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
  return {
    status: "registered",
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

export async function registerComponent(
  e: Etzhayyim,
  input: RegisterComponentInput
): Promise<RegisterComponentOutput> {
  if (!input.purl || !input.name) {
    return { status: "rejected", error: "missingRequiredFields" };
  }
  const rkey = componentRkey(input.purl);
  const existing = await e
    .read<ComponentRecord>({ collection: COMPONENT_COLLECTION, rkey })
    .catch(() => ({ records: [] }));
  if (existing.records[0]?.value) {
    return {
      status: "alreadyExists",
      componentUri: existing.records[0].uri,
      did: existing.records[0].value.did,
      purl: input.purl,
    };
  }
  const did = componentDid(input.purl);
  const record: ComponentRecord = {
    did,
    purl: input.purl,
    name: input.name,
    version: input.version,
    ecosystem: input.ecosystem,
    license: input.license,
    artifactDid: input.artifactDid,
    dependsOn: input.dependsOn,
    createdAt: new Date().toISOString(),
  };
  const receipt = await e.write({
    collection: COMPONENT_COLLECTION,
    record: record as unknown as Record<string, unknown>,
    rkey,
  });
  return {
    status: "registered",
    componentUri: receipt.uri,
    did,
    purl: input.purl,
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
  const items: ComponentView[] = resp.records
    .filter((r) => {
      const v = r.value;
      if (input.artifactDid && v.artifactDid !== input.artifactDid) {
        return false;
      }
      if (input.ecosystem && v.ecosystem !== input.ecosystem) return false;
      return true;
    })
    .map((r) => ({ ...r.value, componentUri: r.uri }));
  return { items, cursor: resp.cursor, total: items.length };
}
