/**
 * W3C DID Core 1.0 conformant DID Document construction for did:etzhayyim.
 *
 * Returns ONLY standard DID Core properties (no proprietary top-level fields).
 * Path-related metadata (root / parent / segment / depth) lives in the platform
 * graph layer (RisingWave vertex_etzhayyim_identity), NOT in this Document.
 *
 * Spec: https://www.w3.org/TR/did-core/
 */

import type { GenesisResult, VerificationMethodInput } from "./genesis";

export interface DidetzhayyimDocument {
  "@context": string[];
  id: string;
  controller?: string[];
  verificationMethod: Array<{
    id: string;
    type: "Multikey";
    controller: string;
    publicKeyMultibase: string;
  }>;
  authentication: string[];
  assertionMethod: string[];
  capabilityInvocation: string[];
  alsoKnownAs?: string[];
  service?: unknown[];
  deactivated?: boolean;
}

export interface DidDocOptions {
  controller?: string[];           // RBAC owner DIDs
  alsoKnownAs?: string[];          // handles, legacy DIDs (e.g. did:web:...)
  service?: unknown[];
  deactivated?: boolean;
}

export function buildDidDocument(
  did: string,
  vms: VerificationMethodInput[],
  opts: DidDocOptions = {},
): DidetzhayyimDocument {
  const verificationMethod = vms.map((m) => ({
    id: did + m.id,                 // m.id already starts with "#"
    type: m.type,
    controller: did,
    publicKeyMultibase: m.publicKeyMultibase,
  }));

  const keyRefs = vms.map((m) => m.id);

  const doc: DidetzhayyimDocument = {
    "@context": [
      "https://www.w3.org/ns/did/v1",
      "https://w3id.org/security/multikey/v1",
    ],
    id: did,
    verificationMethod,
    authentication:       keyRefs,
    assertionMethod:      keyRefs,
    capabilityInvocation: keyRefs,
  };

  if (opts.controller && opts.controller.length > 0) doc.controller = opts.controller;
  if (opts.alsoKnownAs && opts.alsoKnownAs.length > 0) doc.alsoKnownAs = opts.alsoKnownAs;
  if (opts.service && opts.service.length > 0) doc.service = opts.service;
  if (opts.deactivated) doc.deactivated = true;

  return doc;
}

export function buildDidDocumentFromGenesis(
  genesis: GenesisResult,
  opts: DidDocOptions = {},
): DidetzhayyimDocument {
  const vms = (genesis.op.vm as unknown as VerificationMethodInput[]) ?? [];
  const merged: DidDocOptions = {
    ...opts,
    alsoKnownAs: opts.alsoKnownAs ?? (genesis.op.alsoKnownAs as string[] | undefined),
    service:     opts.service     ?? (genesis.op.service as unknown[] | undefined),
  };
  return buildDidDocument(genesis.did, vms, merged);
}
