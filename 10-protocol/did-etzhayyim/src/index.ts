/**
 * @etzhayyim/did-etzhayyim — did:etzhayyim DID method reference implementation.
 *
 * Spec: 90-docs/adr/0029-did-etzhayyim-method-specification.md
 *
 * - W3C DID Core 1.0 conformant DID Document
 * - CIDv1 (multibase 'b' base32 + multicodec 'raw' + multihash sha2-256)
 * - Canonical DAG-CBOR genesis op
 * - Path-form sub-DID (max depth 6)
 * - Resolution result per W3C DID Resolution v0.3
 */

export {
  // genesis
  DID_etzhayyim_PREFIX,
  MAX_PATH_DEPTH,
  isValidDidetzhayyim,
  didDepth,
  didParent,
  didRoot,
  createGenesis,
  verifyGenesis,
} from "./genesis";

export type {
  RootGenesisInput,
  ChildGenesisInput,
  GenesisInput,
  GenesisResult,
  VerificationMethodInput,
} from "./genesis";

export {
  buildDidDocument,
  buildDidDocumentFromGenesis,
} from "./did-doc";

export type {
  DidetzhayyimDocument,
  DidDocOptions,
} from "./did-doc";

export {
  ok as resolutionOk,
  err as resolutionErr,
} from "./resolve";

export type {
  DidResolutionResult,
  DidResolutionMetadata,
  DidDocumentMetadata,
} from "./resolve";

export {
  createCidV1,
  verifyCidV1,
  cidv1ToString,
  cidv1FromString,
} from "./cid";

export type { CIDv1, MulticodecName, CreateCidOptions } from "./cid";

export { encodeCanonicalCbor } from "./cbor";
export type { CborValue } from "./cbor";
