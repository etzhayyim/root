/**
 * DID resolution helpers (DID Resolution v0.3).
 *
 * Spec: https://w3c-ccg.github.io/did-resolution/
 *
 * The platform resolver is `https://did.etzhayyim.com/{did}`.
 * This module produces the response shape; the actual HTTP layer is
 * implemented in the resolver Worker.
 */

import type { DidetzhayyimDocument } from "./did-doc";

export interface DidResolutionMetadata {
  contentType: "application/did+ld+json";
  retrieved: string;            // RFC 3339
  error?: "notFound" | "invalidDid" | "notSupported" | "internalError";
  errorMessage?: string;
}

export interface DidDocumentMetadata {
  created?: string;
  updated?: string;
  deactivated?: boolean;
  versionId?: string;            // CIDv1 of head op
}

export interface DidResolutionResult {
  "@context": "https://w3id.org/did-resolution/v1";
  didDocument: DidetzhayyimDocument | null;
  didResolutionMetadata: DidResolutionMetadata;
  didDocumentMetadata: DidDocumentMetadata;
}

export function ok(doc: DidetzhayyimDocument, metadata: DidDocumentMetadata = {}): DidResolutionResult {
  return {
    "@context": "https://w3id.org/did-resolution/v1",
    didDocument: doc,
    didResolutionMetadata: {
      contentType: "application/did+ld+json",
      retrieved: new Date().toISOString(),
    },
    didDocumentMetadata: metadata,
  };
}

export function err(
  code: NonNullable<DidResolutionMetadata["error"]>,
  message: string,
): DidResolutionResult {
  return {
    "@context": "https://w3id.org/did-resolution/v1",
    didDocument: null,
    didResolutionMetadata: {
      contentType: "application/did+ld+json",
      retrieved: new Date().toISOString(),
      error: code,
      errorMessage: message,
    },
    didDocumentMetadata: {},
  };
}
